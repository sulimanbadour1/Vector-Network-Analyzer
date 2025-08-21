#!/usr/bin/env python3
# Control OWON AG1022 over USB (libusbK/WinUSB) with PyUSB, using SCPI
import time
import usb.core, usb.util

VID, PID = 0x5345, 0x1234  # OWON AG series


class AG1022USB:
    def __init__(self, vid=VID, pid=PID, timeout_ms=2000):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise RuntimeError(
                "AG1022 not found over USB (check driver/cable and close OWON software)."
            )
        self.timeout = timeout_ms

        # Configure and locate a BULK OUT/IN pair
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        self.intf, self.ep_out, self.ep_in = None, None, None

        for intf in cfg:
            eps_out = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_OUT
            ]
            eps_in = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_IN
            ]
            if eps_out and eps_in:
                self.intf, self.ep_out, self.ep_in = intf, eps_out[0], eps_in[0]
                break

        if self.intf is None:
            raise RuntimeError(
                "No BULK endpoints found on AG1022 interface (driver must be libusbK/WinUSB)."
            )

        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)

    # --- low-level I/O ---
    def _write(self, cmd: str, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (cmd + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def query(self, cmd: str) -> str:
        self._write(cmd)
        time.sleep(0.05)
        data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=self.timeout)
        return bytes(data).decode("ascii", errors="ignore").strip()

    def write(self, cmd: str):
        # many OWON set-commands reply with '->', errors with '=?' or 'NULL'
        self._write(cmd)
        try:
            data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=50)
            ack = bytes(data).decode("ascii", errors="ignore").strip()
            if "=?".encode() in data or "NULL".encode() in data:
                raise RuntimeError(f"SCPI error for '{cmd}': {ack}")
        except usb.core.USBError:
            pass  # some set commands return nothing immediately

    # --- convenience / SCPI helpers ---
    def idn(self):
        return self.query("*IDN?")

    def cls(self):
        self.write("*CLS")

    def rst(self):
        self.write("*RST")
        time.sleep(0.2)

    def select_channel(self, ch: int):
        assert ch in (1, 2)
        self.write(f":CHAN CH{ch}")

    def output(self, ch: int, on=True):
        self.write(f":CHAN:CH{ch} {'ON' if on else 'OFF'}")

    def set_sine(
        self, ch: int, freq_hz: float, vpp: float, offset_v: float = 0.0, load="OFF"
    ):
        self.select_channel(ch)
        self.write(":FUNC SINE")
        self.write(f":FUNC:SINE:LOAD {load}")
        self.write(f":FUNC:SINE:FREQ {freq_hz}")
        self.write(f":FUNC:SINE:AMPL {vpp}")
        self.write(f":FUNC:SINE:OFFS {offset_v}")

    def set_square(
        self,
        ch: int,
        freq_hz: float,
        vpp: float,
        offset_v: float = 0.0,
        duty_pct: float = 50,
        load="OFF",
    ):
        self.select_channel(ch)
        self.write(":FUNC SQU")
        self.write(f":FUNC:SQU:LOAD {load}")
        self.write(f":FUNC:SQU:FREQ {freq_hz}")
        self.write(f":FUNC:SQU:AMPL {vpp}")
        self.write(f":FUNC:SQU:OFFS {offset_v}")
        self.write(f":FUNC:SQU:DCYC {duty_pct}")

    def set_ramp(
        self,
        ch: int,
        freq_hz: float,
        vpp: float,
        offset_v: float = 0.0,
        symmetry_pct: float = 50,
        load="OFF",
    ):
        self.select_channel(ch)
        self.write(":FUNC RAMP")
        self.write(f":FUNC:RAMP:LOAD {load}")
        self.write(f":FUNC:RAMP:FREQ {freq_hz}")
        self.write(f":FUNC:RAMP:AMPL {vpp}")
        self.write(f":FUNC:RAMP:OFFS {offset_v}")
        self.write(f":FUNC:RAMP:SYMM {symmetry_pct}")

    # queries
    def q_wave(self):
        return self.query(":FUNC?")

    def q_freq(self, wave="SINE"):
        return self.query(f":FUNC:{wave}:FREQ?")

    def q_ampl(self, wave="SINE"):
        return self.query(f":FUNC:{wave}:AMPL?")

    def q_offset(self, wave="SINE"):
        return self.query(f":FUNC:{wave}:OFFS?")


if __name__ == "__main__":
    gen = AG1022USB()
    print("IDN:", gen.idn())

    # ===== CH1: square wave sweep over different frequencies =====
    FREQS = [100, 500, 1_000, 5_000, 10_000, 50_000, 100_000]  # Hz
    VPP = 2.0  # volts peak-to-peak
    OFFSET = 0.0  # volts
    DUTY_PCT = 50  # %
    LOAD = "OFF"  # Hi-Z; use 50 or 100 if you want source impedance set
    DWELL_S = 2.0  # seconds per step

    try:
        gen.output(1, False)  # start clean
        for f in FREQS:
            gen.set_square(1, f, VPP, offset_v=OFFSET, duty_pct=DUTY_PCT, load=LOAD)
            gen.output(1, True)
            print(f"CH1 -> SQUARE  f={f} Hz, A={VPP} Vpp, duty={DUTY_PCT}%")
            time.sleep(DWELL_S)
    finally:
        # leave it ON at last frequency; or turn it off by uncommenting:
        # gen.output(1, False)
        pass

    # ===== CH2: (optional) keep as before; comment these out if not needed =====
    gen.set_ramp(2, 5000, 3.0, 1.0, symmetry_pct=33, load="OFF")
    gen.output(2, True)
    print("CH2:", gen.q_wave(), "F=", gen.q_freq("RAMP"), "Hz")
