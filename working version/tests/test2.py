#!/usr/bin/env python3
# AG1022 (CH1) -> RTB2004 (CH1) sweep/verify
# - Sets AG1022 CH1 sine frequency & amplitude
# - Captures RTB2004 CH1 once per step
# - Measures frequency, Vpp, offset; compares to command
# - Plots commanded vs measured frequency (vs time) and measured Vpp (vs time)


import time, math, re
import numpy as np
import matplotlib.pyplot as plt

# ==================== AG1022 over PyUSB ====================
import usb.core, usb.util

VID_OWON, PID_OWON = 0x5345, 0x1234


class AG1022USB:
    def __init__(self, timeout_ms=2000):
        self.dev = usb.core.find(idVendor=VID_OWON, idProduct=PID_OWON)
        if self.dev is None:
            raise RuntimeError(
                "AG1022 not found over USB. Close OWON Waveform and check driver (libusbK/WinUSB)."
            )
        self.timeout = timeout_ms
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        self.intf = self.ep_out = self.ep_in = None
        for itf in cfg:
            outs = [
                ep
                for ep in itf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_OUT
            ]
            ins = [
                ep
                for ep in itf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_IN
            ]
            if outs and ins:
                self.intf, self.ep_out, self.ep_in = itf, outs[0], ins[0]
                break
        if not self.intf:
            raise RuntimeError("No BULK IN/OUT endpoints found on AG1022.")
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)

    def _write_raw(self, s, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (s + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def drain(self):
        # swallow short '->' acks so the next query isn't polluted
        for _ in range(4):
            try:
                _ = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=10)
            except usb.core.USBError:
                break

    def write(self, s):
        self._write_raw(s)

    def query(self, s):
        self.drain()
        self._write_raw(s)
        time.sleep(0.06)
        data = self.dev.read(self.ep_in.bEndpointAddress, 2048, timeout=self.timeout)
        txt = bytes(data).decode("ascii", "ignore").strip()
        if txt == "->":
            try:
                data2 = self.dev.read(self.ep_in.bEndpointAddress, 4096, timeout=300)
                t2 = bytes(data2).decode("ascii", "ignore").strip()
                if t2:
                    txt = t2
            except usb.core.USBError:
                pass
        return txt

    # Convenience
    def idn(self):
        return self.query("*IDN?")

    def ch(self, n):
        self.write(f":CHAN CH{1 if n==1 else 2}")

    def out(self, n, on=True):
        self.write(f":CHAN:CH{1 if n==1 else 2} {'ON' if on else 'OFF'}")

    def set_sine(self, ch, f, vpp=1.0, offs=0.0, load="OFF"):
        self.ch(ch)
        self.write(":FUNC SINE")
        self.write(f":FUNC:SINE:LOAD {load}")
        self.write(f":FUNC:SINE:FREQ {f}")
        self.write(f":FUNC:SINE:AMPL {vpp}")
        self.write(f":FUNC:SINE:OFFS {offs}")


# ==================== RTB2004 over VISA ====================
import pyvisa


def open_rtb():
    try:
        rm = pyvisa.ResourceManager()
    except Exception:
        rm = pyvisa.ResourceManager("@py")
    res = rm.list_resources()
    cand = None
    for r in res:
        if re.search(r"RTB|R&S.*RTB", r, re.I) or ("USB" in r and "0x0AAD" in r):
            cand = r
            break
    if not cand:
        raise RuntimeError(f"RTB2004 not found. VISA resources: {res}")
    inst = rm.open_resource(cand)
    inst.timeout = 30000
    inst.chunk_size = 1024 * 1024
    inst.read_termination = "\n"
    inst.write_termination = "\n"
    # Predictable state for quick single shots
    inst.write("SYST:HEAD OFF; HIST:STAT OFF; ACQ:AVER:STAT OFF; ACQ:STOPA SEQ")
    inst.write("FORM REAL,32; FORM:BORD LSBF")
    inst.write("CHAN1:STAT 1; CHAN1:COUP DC; CHAN1:SCAL 1")
    return rm, inst


def capture_ch1_block(rtb, f_hz, points=8000):
    """Single acquisition from CH1 with bounded points; binary with ASCII fallback."""
    # timebase ≈ 10 periods on screen for good zero-crossing
    rtb.write(f"TIM:SCAL {1.0/f_hz/10.0:.9f}")
    rtb.write("SING")
    rtb.query("*OPC?")  # wait until captured
    rtb.write(f"CHAN1:DATA:POIN {points}")

    # header for dt
    h = rtb.query("CHAN1:DATA:HEAD?").strip().split(",")
    try:
        x0, x1 = float(h[0]), float(h[1])
        n = int(float(h[2]))
        dt = (x1 - x0) / max(1, n - 1)
    except Exception:
        dt = 1.0 / (f_hz * 200.0)  # safe guess

    # primary: binary
    try:
        y = np.array(
            rtb.query_binary_values(
                "CHAN1:DATA?",
                datatype="f",
                is_big_endian=False,
                container=np.array,
                header_fmt="ieee",
            )
        )
        return y, dt
    except pyvisa.errors.VisaIOError:
        # fallback: small ASCII
        rtb.write("FORM ASC")
        rtb.write("CHAN1:DATA:POIN 4000")
        y = np.array(rtb.query_ascii_values("CHAN1:DATA?"), dtype=float)
        rtb.write("FORM REAL,32; FORM:BORD LSBF")
        # recompute dt from updated header if available
        try:
            h = rtb.query("CHAN1:DATA:HEAD?").strip().split(",")
            x0, x1 = float(h[0]), float(h[1])
            n = int(float(h[2]))
            dt = (x1 - x0) / max(1, n - 1)
        except Exception:
            pass
        return y, dt


# ==================== Measurements ====================
def estimate_freq(y, dt):
    """Zero-crossing with interpolation; FFT fallback."""
    y = np.asarray(y)
    if len(y) < 16:
        return float("nan")
    y = y - np.mean(y)
    s = np.signbit(y)
    idx = np.flatnonzero(s[:-1] != s[1:])
    if idx.size >= 3:
        crossings_t = []
        for k in idx:
            y1, y2 = y[k], y[k + 1]
            if y2 == y1:
                continue
            frac = -y1 / (y2 - y1)
            crossings_t.append((k + frac) * dt)
        crossings_t = np.asarray(crossings_t)
        if crossings_t.size >= 3:
            periods = np.diff(crossings_t[::2])
            periods = periods[periods > 0]
            if periods.size:
                T = np.median(periods)
                if T > 0:
                    return 1.0 / T
    # FFT fallback
    N = len(y)
    window = np.hanning(N)
    Y = np.fft.rfft(y * window)
    freqs = np.fft.rfftfreq(N, dt)
    i = np.argmax(np.abs(Y[1:])) + 1 if N > 1 else 0
    return freqs[i] if i < len(freqs) else float("nan")


def measure_vpp_offset(y):
    if len(y) == 0:
        return float("nan"), float("nan")
    return float(np.max(y) - np.min(y)), float(np.mean(y))


# ==================== Main: sweep & plot ====================
def main():
    # ----------- user knobs -----------
    START_HZ = 100  # start frequency
    STOP_HZ = 1e6  # stop frequency
    N_STEPS = 40  # number of points (log spaced)
    VPP_CMD = 1.0  # generator amplitude (Vpp)
    PTS_SCOPE = 8000  # points pulled from the scope per step
    LOAD = "OFF"  # AG output load: OFF (Hi-Z), 50, or 100
    # ----------------------------------

    # Build log-spaced sweep list (clamped to AG1022 limit)
    freqs = np.logspace(math.log10(START_HZ), math.log10(STOP_HZ), N_STEPS)
    freqs = [float(f) for f in freqs if f <= 25e6]

    # Open instruments
    gen = AG1022USB()
    print("AG:", gen.idn())
    rm, rtb = open_rtb()
    print("RTB:", rtb.query("*IDN?").strip())

    # Configure AG CH1
    gen.out(1, False)
    gen.set_sine(1, freqs[0], vpp=VPP_CMD, offs=0.0, load=LOAD)
    gen.out(1, True)

    # Sweep
    t0 = time.time()
    rows = []  # (t, f_cmd, f_meas, vpp_meas, offset)

    for i, f in enumerate(freqs, 1):
        # Program AG
        gen.set_sine(1, f, vpp=VPP_CMD, offs=0.0, load=LOAD)

        # Capture RTB CH1
        y, dt = capture_ch1_block(rtb, f, points=PTS_SCOPE)
        f_meas = estimate_freq(y, dt)
        vpp, voff = measure_vpp_offset(y)

        t = time.time() - t0
        rows.append((t, f, f_meas, vpp, voff))
        print(
            f"[{i:02d}/{len(freqs)}] t={t:6.2f}s  f_cmd={f:10.1f} Hz  f_meas≈{f_meas:10.1f} Hz"
            f"  err={f_meas-f:+.1f} Hz  Vpp≈{vpp:.3f} V  Off≈{voff:+.3f} V"
        )

    # Tidy up
    rtb.close()
    rm.close()
    gen.out(1, False)

    # Convert to arrays
    T = np.array([r[0] for r in rows])
    F_c = np.array([r[1] for r in rows])
    F_m = np.array([r[2] for r in rows])
    Vpp = np.array([r[3] for r in rows])

    # Print quick stats
    valid = np.isfinite(F_m)
    if np.any(valid):
        rel_err_ppm = 1e6 * (F_m[valid] - F_c[valid]) / F_c[valid]
        print(
            f"\nFreq error (median): {np.median(rel_err_ppm):.1f} ppm "
            f"(min {np.min(rel_err_ppm):.1f} / max {np.max(rel_err_ppm):.1f} ppm)"
        )
    else:
        print(
            "\nNo valid frequency estimates — try increasing PTS_SCOPE or changing timebase span."
        )

    # Plots
    plt.figure()
    plt.title("Frequency vs Time (AG1022 CH1 → RTB CH1)")
    plt.plot(T, F_c, label="Commanded (Hz)")
    plt.plot(T, F_m, "--", label="Measured (Hz)")
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.figure()
    plt.title("Measured Vpp vs Time (RTB CH1)")
    plt.plot(T, Vpp)
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Vpp (V)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
