#!/usr/bin/env python3
# Sweep frequency and plot commanded (AG) vs measured (RTB) over time.

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
                "AG1022 not found over USB. Close OWON Waveform and check driver."
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
            raise RuntimeError("No BULK IN/OUT endpoints found.")
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)

    def _write_raw(self, s, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (s + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def drain(self):
        # non-blocking flush of any stale acks
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
    # Predictable state for quick reads
    inst.write("SYST:HEAD OFF; HIST:STAT OFF; ACQ:AVER:STAT OFF; ACQ:STOPA SEQ")
    inst.write("FORM REAL,32; FORM:BORD LSBF")
    inst.write("CHAN1:STAT 1; CHAN1:COUP DC; CHAN1:SCAL 1")
    return rm, inst


def capture_ch1_block(rtb, f_hz, points=5000):
    # timebase ≈ 8 periods on screen for stable measurement
    rtb.write(f"TIM:SCAL {1.0/f_hz/8.0:.9f}")
    rtb.write("SING")
    rtb.query("*OPC?")  # wait until captured
    rtb.write(f"CHAN1:DATA:POIN {points}")
    # header for xincr
    h = rtb.query("CHAN1:DATA:HEAD?").strip().split(",")
    try:
        x0, x1 = float(h[0]), float(h[1])
        n = int(float(h[2]))
        xincr = (x1 - x0) / max(1, n - 1)
    except Exception:
        xincr = 1.0 / (f_hz * 1000.0)
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
        return y, xincr
    except pyvisa.errors.VisaIOError:
        # fallback: small ASCII
        rtb.write("FORM ASC")
        rtb.write("CHAN1:DATA:POIN 4000")
        y = np.array(rtb.query_ascii_values("CHAN1:DATA?"), dtype=float)
        rtb.write("FORM REAL,32; FORM:BORD LSBF")
        return y, xincr


# ==================== Frequency estimation ====================
def estimate_freq(y, dt):
    """
    Estimate frequency from a single-channel waveform using zero crossings.
    Fallback to FFT if crossings are insufficient.
    """
    y = np.asarray(y)
    if len(y) < 10:
        return float("nan")
    # remove DC
    y = y - np.mean(y)
    # find zero crossings
    s = np.signbit(y)
    idx = np.flatnonzero(s[:-1] != s[1:])
    if idx.size >= 3:
        # refine by linear interpolation around each crossing
        crossings_t = []
        for k in idx:
            y1, y2 = y[k], y[k + 1]
            if y2 == y1:
                continue
            frac = -y1 / (y2 - y1)
            crossings_t.append((k + frac) * dt)
        crossings_t = np.asarray(crossings_t)
        # period from every second crossing (full cycles)
        if crossings_t.size >= 3:
            periods = np.diff(crossings_t[::2])
            periods = periods[periods > 0]
            if periods.size:
                T = np.median(periods)
                return 1.0 / T
    # FFT fallback
    N = len(y)
    window = np.hanning(N)
    Y = np.fft.rfft(y * window)
    freqs = np.fft.rfftfreq(N, dt)
    i = np.argmax(np.abs(Y[1:])) + 1 if N > 1 else 0
    return freqs[i] if i < len(freqs) else float("nan")


# ==================== Main: sweep & plot ====================
def main():
    START_HZ = 100  # change as needed
    STOP_HZ = 1e6
    N_STEPS = 30  # number of points (log spaced)
    VPP = 1.0  # generator amplitude
    PTS_SCOPE = 5000  # waveform points per read (kept moderate for speed)

    # Build log-spaced sweep list
    freqs = np.logspace(math.log10(START_HZ), math.log10(STOP_HZ), N_STEPS)

    # Open instruments
    gen = AG1022USB()
    print("AG:", gen.idn())
    rm, rtb = open_rtb()
    print("RTB:", rtb.query("*IDN?").strip())

    # Configure generator CH1
    gen.out(1, False)
    gen.set_sine(1, freqs[0], VPP, 0.0, load="OFF")
    gen.out(1, True)

    t0 = time.time()
    t_elapsed, f_cmd, f_meas = [], [], []

    for i, f in enumerate(freqs):
        # set generator frequency
        gen.set_sine(1, float(f), VPP, 0.0)

        # capture short block on CH1 and estimate frequency
        y, dt = capture_ch1_block(rtb, float(f), points=PTS_SCOPE)
        f_est = estimate_freq(y, dt)

        t_elapsed.append(time.time() - t0)
        f_cmd.append(float(f))
        f_meas.append(float(f_est))
        print(
            f"[{i+1:02d}/{len(freqs)}] cmd={f:9.1f} Hz   meas≈{f_est:9.1f} Hz   err={f_est-f:+.1f} Hz"
        )

    # Tidy up
    rtb.close()
    rm.close()
    gen.out(1, False)

    # Plot frequency vs time
    t = np.array(t_elapsed)
    plt.figure()
    plt.title("Frequency vs Time (Commanded vs Measured)")
    plt.plot(t, f_cmd, label="AG command (Hz)")
    plt.plot(t, f_meas, label="RTB measured (Hz)", linestyle="--")
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Frequency (Hz)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
