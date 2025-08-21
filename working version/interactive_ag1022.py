#!/usr/bin/env python3
# Interactive CLI for OWON AG1022 (USB via libusbK/WinUSB) using PyUSB
# Commands:  help  idn  ch <1|2>  out <on|off>  wave <sine|square|ramp|dc>
#            freq <value>  ampl <vpp>  offs <v>  duty <pct>  symm <pct>  load <OFF|50|100>
#            get [freq|ampl|offs|wave]  sweep <start> <stop> <points> [lin|log] [dwell_s]
#            presets  status  quit


import re, sys, time
import usb.core, usb.util

VID, PID = 0x5345, 0x1234  # OWON


def parse_number(token: str) -> float:
    """
    Accepts things like: 100, 1k, 10K, 2.5M, 500m, 250u, 3.3V, 1.2vpp, 1e6, etc.
    Returns a float with the unit multiplier applied. Unit letters are ignored.
    """
    s = token.strip().lower()
    s = s.replace("vpp", "").replace("v", "").replace("hz", "").replace("s", "")
    m = re.fullmatch(r"([+-]?\d+(\.\d+)?([eE][+-]?\d+)?)([kmgmun]?)", s)
    if not m:
        raise ValueError(f"Bad number: {token}")
    base = float(m.group(1))
    suf = m.group(4)
    mult = {"": 1, "k": 1e3, "m": 1e-3, "g": 1e9, "u": 1e-6, "n": 1e-9}.get(suf, 1)
    # Note: 'm' taken as milli; if you need mega, use 'M' or 1e6 explicitly
    if token.endswith("M") or token.endswith("m") and "e" not in token.lower():
        # we already used 'm' as milli; handle 'M' (mega) robustly
        if token.endswith("M"):
            mult = 1e6
    return base * mult


def fmt_hz(x: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if abs(x) >= div:
            return f"{x/div:.6g} {unit}"
    return f"{x:.6g} Hz"


def fmt_v(x: float) -> str:
    for unit, mult in (("V", 1), ("mV", 1e-3), ("uV", 1e-6)):
        if abs(x) >= mult:
            return f"{x/mult:.6g} {unit}"
    return f"{x:.6g} V"


class AG1022USB:
    def __init__(self, vid=VID, pid=PID, timeout_ms=2000):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise RuntimeError(
                "AG1022 not found over USB. Check cable/driver and CLOSE OWON Waveform."
            )
        self.timeout = timeout_ms
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        self.intf = self.ep_out = self.ep_in = None
        for intf in cfg:
            outs = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_OUT
            ]
            ins = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_IN
            ]
            if outs and ins:
                self.intf, self.ep_out, self.ep_in = intf, outs[0], ins[0]
                break
        if not self.intf:
            raise RuntimeError(
                "No BULK IN/OUT endpoints found. Driver must be libusbK/WinUSB."
            )
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)
        self.current_ch = 1  # track selected channel for convenience

    # --- low-level ---
    def _write(self, scpi: str, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (scpi + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def write(self, scpi: str):
        self._write(scpi)
        # Some set-commands echo '->' (OK) or '=?'/'NULL' (error). Try to read a short ack; ignore if timeout.
        try:
            data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=50)
            ack = bytes(data).decode("ascii", "ignore").strip()
            if "=?".encode() in data or "NULL".encode() in data:
                raise RuntimeError(f"SCPI error for '{scpi}': {ack}")
        except usb.core.USBError:
            pass

    def query(self, scpi: str) -> str:
        self._write(scpi)
        time.sleep(0.05)
        data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=self.timeout)
        return bytes(data).decode("ascii", "ignore").strip()

    # --- convenience ---
    def idn(self):
        return self.query("*IDN?")

    def cls(self):
        self.write("*CLS")

    def rst(self):
        self.write("*RST")
        time.sleep(0.2)

    def ch(self, ch: int):
        if ch not in (1, 2):
            raise ValueError("Channel must be 1 or 2.")
        self.write(f":CHAN CH{ch}")
        self.current_ch = ch

    def out(self, ch: int, on: bool = True):
        self.write(f":CHAN:CH{ch} {'ON' if on else 'OFF'}")

    def wave(self, kind: str):
        k = kind.strip().upper()
        mp = {
            "SINE": "SINE",
            "SIN": "SINE",
            "SQU": "SQU",
            "SQUARE": "SQU",
            "RAMP": "RAMP",
            "TRI": "RAMP",
            "DC": "DC",
        }
        if k not in mp:
            raise ValueError("Wave must be sine/square/ramp/dc.")
        self.write(f":FUNC {mp[k]}")

    def freq(self, wave: str, hz: float):
        self.write(f":FUNC:{wave}:FREQ {hz}")

    def ampl(self, wave: str, vpp: float):
        self.write(f":FUNC:{wave}:AMPL {vpp}")

    def offs(self, wave: str, v: float):
        self.write(f":FUNC:{wave}:OFFS {v}")

    def duty(self, pct: float):
        self.write(f":FUNC:SQU:DCYC {pct}")

    def symm(self, pct: float):
        self.write(f":FUNC:RAMP:SYMM {pct}")

    def load(self, wave: str, val: str):
        self.write(f":FUNC:{wave}:LOAD {val}")

    def get_wave(self):
        return self.query(":FUNC?")

    def get_freq(self, wave: str):
        return self.query(f":FUNC:{wave}:FREQ?")

    def get_ampl(self, wave: str):
        return self.query(f":FUNC:{wave}:AMPL?")

    def get_offs(self, wave: str):
        return self.query(f":FUNC:{wave}:OFFS?")


def print_help():
    print(
        """
Commands:
  help                         show this help
  idn                          print *IDN?
  ch <1|2>                     select channel
  out <on|off>                 output enable for selected channel
  wave <sine|square|ramp|dc>   set waveform (for selected channel)
  freq <value>                 set frequency (e.g., 1k, 10k, 2.5M)
  ampl <vpp>                   set amplitude Vpp (e.g., 2, 500m, 1.2)
  offs <v>                     set DC offset in volts
  duty <pct>                   set duty for square (%)
  symm <pct>                   set symmetry for ramp (%)
  load <OFF|50|100>            set function load (Hi-Z=OFF)
  get [freq|ampl|offs|wave]    query current value (defaults to wave)
  sweep <start> <stop> <points> [lin|log] [dwell_s]
                               e.g., sweep 100 100k 10 log 1.5
  presets                      quick setup examples
  status                       dump current wave/freq/ampl/offset for channel
  quit                         exit
Examples:
  ch 1
  wave square
  ampl 2
  duty 50
  freq 1k
  out on
""".strip()
    )


def main():
    try:
        gen = AG1022USB()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)

    print(f"Connected: {gen.idn()}")
    print_help()
    wave_for_query = {"SINE": "SINE", "SQU": "SQU", "RAMP": "RAMP", "DC": "DC"}

    def current_wave_key():
        w = gen.get_wave().strip().upper()
        return (
            "SQU"
            if "SQU" in w or "SQUARE" in w
            else (
                "RAMP" if "RAMP" in w or "TRI" in w else "SINE" if "SINE" in w else "DC"
            )
        )

    while True:
        try:
            raw = input(f"[CH{gen.current_ch}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye.")
            break
        if not raw:
            continue
        args = raw.split()
        cmd = args[0].lower()

        try:
            if cmd in ("quit", "exit", "q"):
                break
            elif cmd in ("help", "h", "?"):
                print_help()
            elif cmd == "idn":
                print(gen.idn())

            elif cmd == "ch":
                gen.ch(int(args[1]))
            elif cmd == "out":
                st = args[1].lower()
                gen.out(gen.current_ch, st in ("on", "1", "true", "yes"))
            elif cmd == "wave":
                gen.wave(args[1])
            elif cmd == "freq":
                hz = parse_number(args[1])
                w = current_wave_key()
                gen.freq(w, hz)
                print("freq:", fmt_hz(hz))
            elif cmd == "ampl":
                vpp = parse_number(args[1])
                w = current_wave_key()
                gen.ampl(w, vpp)
                print("ampl:", fmt_v(vpp), "pp")
            elif cmd == "offs":
                v = parse_number(args[1])
                w = current_wave_key()
                gen.offs(w, v)
                print("offset:", fmt_v(v))
            elif cmd == "duty":
                gen.duty(float(args[1]))
            elif cmd == "symm":
                gen.symm(float(args[1]))
            elif cmd == "load":
                val = args[1].upper()
                if val not in ("OFF", "50", "100"):
                    raise ValueError("load must be OFF, 50, or 100")
                w = current_wave_key()
                gen.load(w, val)

            elif cmd == "get":
                which = args[1].lower() if len(args) > 1 else "wave"
                w = current_wave_key()
                if which == "wave":
                    print("wave:", gen.get_wave())
                elif which == "freq":
                    print("freq:", gen.get_freq(w))
                elif which == "ampl":
                    print("ampl:", gen.get_ampl(w))
                elif which == "offs":
                    print("offs:", gen.get_offs(w))
                else:
                    print("unknown get field (use wave|freq|ampl|offs)")

            elif cmd == "status":
                w = current_wave_key()
                print("wave:", gen.get_wave())
                print("freq:", gen.get_freq(w))
                print("ampl:", gen.get_ampl(w))
                print("offs:", gen.get_offs(w))

            elif cmd == "presets":
                print("Examples:")
                print("  ch 1; wave square; ampl 2; duty 50; freq 1k; out on")
                print("  ch 2; wave ramp;   ampl 3; symm 33;  freq 5k; out on")

            elif cmd == "sweep":
                if len(args) < 4:
                    print("usage: sweep <start> <stop> <points> [lin|log] [dwell_s]")
                    continue
                start = parse_number(args[1])
                stop = parse_number(args[2])
                pts = int(args[3])
                mode = args[4].lower() if len(args) > 4 else "lin"
                dwell = float(args[5]) if len(args) > 5 else 1.0
                if pts < 2:
                    raise ValueError("points must be >= 2")
                w = current_wave_key()
                freqs = []
                if mode.startswith("log"):
                    import math

                    a, b = math.log10(start), math.log10(stop)
                    freqs = [10 ** (a + i * (b - a) / (pts - 1)) for i in range(pts)]
                else:
                    step = (stop - start) / (pts - 1)
                    freqs = [start + i * step for i in range(pts)]
                gen.out(gen.current_ch, False)
                for f in freqs:
                    gen.freq(w, f)
                    gen.out(gen.current_ch, True)
                    print(f" -> {fmt_hz(f)}")
                    time.sleep(dwell)
                print("sweep done.")

            else:
                print("unknown command; type 'help'")

        except Exception as e:
            print("ERR:", e)

    print("Done.")


if __name__ == "__main__":
    main()
