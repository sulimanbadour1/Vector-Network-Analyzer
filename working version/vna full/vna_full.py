#!/usr/bin/env python3
"""
Sweep generator (OWON AG1022 over USB/PyUSB) + capture with R&S RTB2004 (PyVISA).
Computes CH2/CH1 gain & phase vs frequency and (optionally) impedance via -z.
Flags (like your original):
  -b <BeginF>  -e <EndF>  -p <Pts/Dec>  -s <StepHz>
  -f <FILE_Prefix>  -n (no plots)  -q (square instead of sine)  -v <Vpp>  -z <R_sense>
"""

import sys, os, re, time, math
import numpy as np
import matplotlib.pyplot as plt

# -------------------- OWON AG1022 over PyUSB --------------------
import usb.core, usb.util

VID_OWON, PID_OWON = 0x5345, 0x1234


class AG1022USB:
    def __init__(self, vid=VID_OWON, pid=PID_OWON, timeout_ms=2000):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise RuntimeError(
                "AG1022 not found over USB. Check cable/driver and close OWON Waveform."
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
                "No BULK endpoints found. Driver must be libusbK/WinUSB."
            )
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)

    def _write(self, scpi, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (scpi + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def write(self, scpi):
        self._write(scpi)
        # ignore short ACK if none
        try:
            self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=20)
        except usb.core.USBError:
            pass

    def query(self, scpi):
        self._write(scpi)
        time.sleep(0.05)
        data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=self.timeout)
        return bytes(data).decode("ascii", "ignore").strip()

    # Convenience
    def idn(self):
        return self.query("*IDN?")

    def ch(self, n):
        self.write(f":CHAN CH{1 if n==1 else 2}")

    def out(self, n, on=True):
        self.write(f":CHAN:CH{1 if n==1 else 2} {'ON' if on else 'OFF'}")

    def set_sine(self, ch, freq, vpp, offs=0.0, load="OFF"):
        self.ch(ch)
        self.write(":FUNC SINE")
        self.write(f":FUNC:SINE:LOAD {load}")
        self.write(f":FUNC:SINE:FREQ {freq}")
        self.write(f":FUNC:SINE:AMPL {vpp}")
        self.write(f":FUNC:SINE:OFFS {offs}")

    def set_square(self, ch, freq, vpp, offs=0.0, duty=50, load="OFF"):
        self.ch(ch)
        self.write(":FUNC SQU")
        self.write(f":FUNC:SQU:LOAD {load}")
        self.write(f":FUNC:SQU:FREQ {freq}")
        self.write(f":FUNC:SQU:AMPL {vpp}")
        self.write(f":FUNC:SQU:OFFS {offs}")
        self.write(f":FUNC:SQU:DCYC {duty}")


# -------------------- RTB2004 via PyVISA --------------------
import pyvisa


def rm_open():
    try:
        return pyvisa.ResourceManager()  # NI-VISA / R&S VISA if present
    except Exception:
        return pyvisa.ResourceManager("@py")  # pure python backend


def open_rtb(resource_manager):
    # Pick the first VISA resource that looks like an RTB
    resources = resource_manager.list_resources()
    cand = None
    for r in resources:
        if re.search(r"RTB|R&S.*RTB", r, re.I):
            cand = r
            break
        if "USB" in r and "0x0AAD" in r:  # R&S vendor ID
            cand = r
    if not cand:
        raise RuntimeError(f"RTB2004 not found. VISA resources: {resources}")
    inst = resource_manager.open_resource(cand)
    inst.timeout = 10000  # ms
    return inst


# -------------------- CLI (compatible with your original) --------------------
FILEPREFIX = "RG1054Z"
StartF = 1.0
StopF = 1e6
PointsPerDecade = 10
SweepModeLog = True
StepSizeF = None
Voltage = 1.0
Resistance = 0.0
Sine = True
PlotOK = True


def NextArg(i):
    if i + 1 >= len(sys.argv):
        raise SystemExit(f"'{sys.argv[i]}' expected an argument")
    return 1, sys.argv[i + 1]


skip = 0
for i in range(1, len(sys.argv)):
    if skip:
        skip = 0
        continue
    a = sys.argv[i]
    if a.startswith("-f"):
        skip, FILEPREFIX = NextArg(i)
    elif a.startswith("-n"):
        PlotOK = False
    elif a.startswith("-q"):
        Sine = False
    elif a.startswith("-v"):
        skip, Voltage = 1, float(NextArg(i)[1])
    elif a.startswith("-z"):
        skip, Resistance = 1, float(NextArg(i)[1])
    elif a.startswith("-s"):
        skip, StepSizeF = 1, float(NextArg(i)[1])
        SweepModeLog = False
    elif a.startswith("-b"):
        skip, StartF = 1, float(NextArg(i)[1])
    elif a.startswith("-e"):
        skip, StopF = 1, float(NextArg(i)[1])
    elif a.startswith("-p"):
        skip, PointsPerDecade = 1, int(NextArg(i)[1])
        SweepModeLog = True
    elif a.startswith("-h"):
        print(__doc__)
        sys.exit(0)
    elif a.startswith("-"):
        print("Bad arg:", a)
        sys.exit(1)

# -------------------- Open instruments --------------------
rm = rm_open()
rtb = open_rtb(rm)
print("RTB2004:", rtb.query("*IDN?").strip())

gen = AG1022USB()
print("AG1022:", gen.idn())

# -------------------- Configure generator (CH1 as source) --------------------
gen.out(1, False)
if Sine:
    gen.set_sine(1, StartF, Voltage, 0.0, load="OFF")
else:
    gen.set_square(1, StartF, Voltage, 0.0, duty=50, load="OFF")
gen.out(1, True)

# -------------------- Configure RTB channels & transfer format ----------------
# Turn CH1/CH2 on and AC couple (adjust to DC if you prefer).
rtb.write(
    "CHAN1:STAT 1; CHAN2:STAT 1"
)  # enable channels (RTB SCPI)  # see app-card example
rtb.write("CHAN1:COUP AC; CHAN2:COUP AC")
rtb.write("CHAN1:SCAL 5; CHAN2:SCAL 5")

# Use REAL,32 (float) little-endian; fetch full record from memory (not just screen)
rtb.write("FORM REAL,32; FORM:BORD LSBF")  # binary float32, little-endian
# For full resolution you must request it, and acquisition must be stopped.  :contentReference[oaicite:1]{index=1}
rtb.write("CHAN1:DATA:POIN MAX; CHAN2:DATA:POIN MAX")

# Single-acquisition synchronization hint:
# We'll drive each step with SING and wait on *OPC?=1 when finished.  :contentReference[oaicite:2]{index=2}

# -------------------- Prepare sweep --------------------
if SweepModeLog:
    last_point = 1 + math.ceil(PointsPerDecade * math.log10(StopF / StartF))
    freqs = [StartF * (10 ** (i / PointsPerDecade)) for i in range(last_point)]
else:
    last_point = 1 + math.ceil((StopF - StartF) / StepSizeF)
    freqs = [StartF + i * StepSizeF for i in range(last_point)]
freqs = [f for f in freqs if f <= StopF and f <= 25e6]  # AG1022 bandwidth guard

MDEPTH = 30000
VNA = []
ts = time.strftime("%Y-%m-%d %H:%M")
LOGFile = open(FILEPREFIX + "_VNA.log", "w")
print(f"# {ts}", file=LOGFile)
print(
    "#Sample,  Frequency,      Mag1,      Mag2, Ratio (dB),   Phase,  Z(re,im)",
    file=LOGFile,
)

for idx, F in enumerate(freqs):
    # Drive generator
    if Sine:
        gen.set_sine(1, F, Voltage)
    else:
        gen.set_square(1, F, Voltage, duty=50)

    # Aim ~12 periods on screen
    rtb.write(
        f"TIM:SCAL {1.0/F/12.0:.9f}"
    )  # timebase scale (s/div). Manual uses TIM:SCAL.  :contentReference[oaicite:3]{index=3}

    # Single run and wait until acquisition done
    rtb.write("SING")
    rtb.query(
        "*OPC?"
    )  # returns "1" when finished  :contentReference[oaicite:4]{index=4}

    # Ensure we grab full record for both channels at this step
    rtb.write(
        "CHAN1:DATA:POIN MAX; CHAN2:DATA:POIN MAX"
    )  # full resolution  :contentReference[oaicite:5]{index=5}

    # Read headers -> [Xstart, Xstop, Npoints, ...]
    h1 = rtb.query("CHAN1:DATA:HEAD?").strip().split(",")
    n1 = int(float(h1[2])) if len(h1) >= 3 else MDEPTH

    h2 = rtb.query("CHAN2:DATA:HEAD?").strip().split(",")
    n2 = int(float(h2[2])) if len(h2) >= 3 else MDEPTH
    NPOINTS = min(n1, n2, MDEPTH)

    # Read binary float32 waveform data (little-endian)  :contentReference[oaicite:6]{index=6}
    cur1 = np.array(
        rtb.query_binary_values(
            "CHAN1:DATA?",
            datatype="f",
            is_big_endian=False,
            container=np.array,
            header_fmt="ieee",
        )[:NPOINTS]
    )
    cur2 = np.array(
        rtb.query_binary_values(
            "CHAN2:DATA?",
            datatype="f",
            is_big_endian=False,
            container=np.array,
            header_fmt="ieee",
        )[:NPOINTS]
    )

    # Project onto sin/cos over an integer number of cycles
    # Approximate samples-per-cycle from header span:
    try:
        x0, x1 = float(h1[0]), float(h1[1])
        xincr = (x1 - x0) / max(1, n1 - 1)
    except Exception:
        xincr = 1.0 / (F * 1000.0)  # fallback
    n_per_cycle = 1.0 / (F * xincr)
    n_cycles = max(1, math.floor(NPOINTS / n_per_cycle))
    N = int(round(n_cycles * n_per_cycle))

    t = np.linspace(0, n_cycles * 2 * np.pi, N)
    s = np.sin(t)
    c = np.cos(t)

    x1c = cur1[:N]
    x2c = cur2[:N]
    S1 = np.dot(x1c, s) / N
    C1 = np.dot(x1c, c) / N
    S2 = np.dot(x2c, s) / N
    C2 = np.dot(x2c, c) / N

    X1 = complex(S1, C1)
    X2 = complex(S2, C2)
    MAG1 = 2 * abs(X1)
    PH1 = np.angle(X1, deg=True)
    MAG2 = 2 * abs(X2)
    PH2 = np.angle(X2, deg=True)

    # Auto-rescale channels a bit for the next shot
    rtb.write(f"CHAN1:SCAL {max(1e-3, MAG1/3):.4f}; CHAN2:SCAL {max(1e-3, MAG2/3):.4f}")

    Mag_dB = 20 * np.log10(MAG2 / MAG1) if MAG1 > 0 else float("nan")
    Phase = (PH2 - PH1) % 360.0
    if Phase > 180.0:
        Phase -= 360.0

    Z = complex(0.0, 0.0)
    if Resistance:
        # divider model: Zload = V2 / (V1 - V2) * R
        Z = (X2 / (X1 - X2)) * Resistance

    print(
        f"Sample {idx:3d}, {F:11.3f} Hz, {N} pts  ->  {Mag_dB:7.2f} dB, {Phase:7.2f}°"
    )
    print(
        f"{idx:6d}, {F:12.3f}, {MAG1:9.5f}, {MAG2:9.5f}, {Mag_dB:7.2f}, {Phase:7.2f},  {Z.real:12.4f} {Z.imag:+12.4f}",
        file=LOGFile,
    )
    VNA.append((F, Mag_dB, Phase, Z))

LOGFile.close()
rtb.close()
rm.close()
print("Done; log ->", FILEPREFIX + "_VNA.log")

# -------------------- Plots --------------------
if PlotOK and VNA:
    F = np.array([x[0] for x in VNA])
    G = np.array([x[1] for x in VNA])
    P = np.array([x[2] for x in VNA])

    fig, ax1 = plt.subplots()
    ax1.set_title("CH2 / CH1")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Gain (dB)")
    ax1.grid(True)
    (ax1.semilogx if SweepModeLog else ax1.plot)(F, G)
    ax2 = ax1.twinx()
    ax2.set_ylabel("Phase (°)")
    (ax2.semilogx if SweepModeLog else ax2.plot)(F, P)
    fig.tight_layout()
    plt.show(block=False)

    if Resistance:
        Zmag = np.array([abs(x[3]) for x in VNA])
        Zph = np.array([np.angle(x[3], deg=True) for x in VNA])
        fig2, ax3 = plt.subplots()
        ax3.set_title("Impedance |Z| & ∠Z")
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("|Z| (Ω)")
        ax3.grid(True)
        (ax3.loglog if SweepModeLog else ax3.semilogy)(F, Zmag)
        ax4 = ax3.twinx()
        ax4.set_ylabel("∠Z (°)")
        (ax4.semilogx if SweepModeLog else ax4.plot)(F, Zph)
        fig2.tight_layout()
        plt.show(block=True)
