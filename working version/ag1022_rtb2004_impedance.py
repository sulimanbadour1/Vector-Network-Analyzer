#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Impedance sweep using:
  • Generator: OWON AG1022 (USB via libusbK/WinUSB, PyUSB)
  • Scope:     R&S RTB2004 (USB/LAN via VISA, PyVISA)

Wiring (series sense-resistor):
    AG1022 CH1 (+) ── Rs ──●── DUT ── GND
                           │
                       Scope CH2 (Vdut)
    Scope CH1 (Vin) probes generator side of Rs
    All grounds common. Use 10× probes to reduce loading.

CLI (similar to your original):
  -b <BeginF>            start frequency (Hz), default 10
  -e <EndF>              stop  frequency (Hz), default 1e6
  -p <Pts/Dec>           points per decade (log sweep)
  -s <StepHz>            linear step size (Hz)  [mutually exclusive with -p]
  -f <FILE_Prefix>       log/plot prefix (default RG1054Z)
  -n                     no plots
  -z <R_sense_ohms>      compute Z = V2/(V1-V2) * Rs
  -v <Vpp>               generator amplitude in Vpp (default 1.0)
  -q                     use square instead of sine

Example:
  python ag1022_rtb2004_impedance.py -b 10 -e 1e7 -p 20 -z 1000 -v 1.0 -f C0_043uF

Notes:
  • Close the OWON “Waveform” app while using Python (one client at a time).
  • Requires: pip install pyusb libusb-package pyvisa pyvisa-py numpy matplotlib
"""


import sys, re, math, time
import numpy as np
import matplotlib.pyplot as plt

# ========= OWON AG1022 over PyUSB =========
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
            raise RuntimeError("No BULK IN/OUT endpoints found on AG1022 interface.")
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)

    def _write_raw(self, s, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (s + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def drain(self, tries=4):
        for _ in range(tries):
            try:
                _ = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=10)
            except usb.core.USBError:
                break

    def write(self, s):
        self._write_raw(
            s
        )  # do NOT read here (prevents stealing the next query's response)

    def query(self, s):
        self.drain()
        self._write_raw(s)
        time.sleep(0.06)
        data = self.dev.read(self.ep_in.bEndpointAddress, 2048, timeout=self.timeout)
        txt = bytes(data).decode("ascii", "ignore").strip()
        if txt == "->":  # ack arrived first; try one quick extra read
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

    def set_sine(self, ch, f, vpp, offs=0.0, load="OFF"):
        self.ch(ch)
        self.write(":FUNC SINE")
        self.write(f":FUNC:SINE:LOAD {load}")
        self.write(f":FUNC:SINE:FREQ {f}")
        self.write(f":FUNC:SINE:AMPL {vpp}")
        self.write(f":FUNC:SINE:OFFS {offs}")

    def set_square(self, ch, f, vpp, offs=0.0, duty=50, load="OFF"):
        self.ch(ch)
        self.write(":FUNC SQU")
        self.write(f":FUNC:SQU:LOAD {load}")
        self.write(f":FUNC:SQU:FREQ {f}")
        self.write(f":FUNC:SQU:AMPL {vpp}")
        self.write(f":FUNC:SQU:OFFS {offs}")
        self.write(f":FUNC:SQU:DCYC {duty}")


# ========= RTB2004 over PyVISA =========
import pyvisa


def rm_open():
    try:
        return pyvisa.ResourceManager()
    except Exception:
        return pyvisa.ResourceManager("@py")


def open_rtb(rm):
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
    # make sure scope is in a predictable state for data reads
    inst.write("SYST:HEAD OFF")  # no verbose headers
    inst.write("HIST:STAT OFF")  # history off
    inst.write("ACQ:AVER:STAT OFF")  # averaging off
    inst.write("ACQ:STOPA SEQ")  # single-acquisition mode
    inst.write("FORM REAL,32; FORM:BORD LSBF")
    inst.write("CHAN1:STAT 1; CHAN2:STAT 1")
    inst.write("CHAN1:COUP DC; CHAN2:COUP DC")
    inst.write("CHAN1:SCAL 5; CHAN2:SCAL 5")
    return inst


def rtb_capture_pair(rtb, F, points, dwell_min=0.02):
    """
    Deterministic single acquisition:
      - set timebase for ~12 periods
      - SING and wait *OPC?
      - request bounded points
      - try REAL,32 binary; on timeout, fallback to ASCII for this step
    """
    rtb.write(f"TIM:SCAL {1.0/F/12.0:.9f}")
    rtb.write("SING")
    rtb.query("*OPC?")  # wait until the single acquisition is finished

    # points request (must be after STOP to allow MAX/large requests)
    rtb.write(f"CHAN1:DATA:POIN {points}; CHAN2:DATA:POIN {points}")

    # get time axis info
    h1 = rtb.query("CHAN1:DATA:HEAD?").strip().split(",")
    try:
        x0, x1 = float(h1[0]), float(h1[1])
        n1 = int(float(h1[2]))
        xincr = (x1 - x0) / max(1, n1 - 1)
    except Exception:
        xincr = 1.0 / (F * 1000.0)

    # --- primary path: binary block REAL,32 ---
    try:
        y1 = np.array(
            rtb.query_binary_values(
                "CHAN1:DATA?",
                datatype="f",
                is_big_endian=False,
                container=np.array,
                header_fmt="ieee",
            )
        )
        y2 = np.array(
            rtb.query_binary_values(
                "CHAN2:DATA?",
                datatype="f",
                is_big_endian=False,
                container=np.array,
                header_fmt="ieee",
            )
        )
        N = min(len(y1), len(y2), points)
        return y1[:N], y2[:N], xincr
    except pyvisa.errors.VisaIOError:
        # --- fallback: ASCII (slower but robust) ---
        rtb.write("FORM ASC")
        rtb.write(
            f"CHAN1:DATA:POIN {min(points, 5000)}; CHAN2:DATA:POIN {min(points, 5000)}"
        )
        y1 = np.array(rtb.query_ascii_values("CHAN1:DATA?"), dtype=float)
        y2 = np.array(rtb.query_ascii_values("CHAN2:DATA?"), dtype=float)
        rtb.write("FORM REAL,32; FORM:BORD LSBF")  # restore for next step
        N = min(len(y1), len(y2), min(points, 5000))
        return y1[:N], y2[:N], xincr


# ========= CLI =========
FILEPREFIX = "RG1054Z"
StartF = 10.0
StopF = 1e6
PointsPerDecade = 20
SweepModeLog = True
StepSizeF = None
Voltage = 1.0
Resistance = 0.0
PlotOK = True
UseSquare = False


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
        UseSquare = True
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

# ========= Open instruments =========
rm = rm_open()
rtb = open_rtb(rm)
print("RTB2004:", rtb.query("*IDN?").strip())

gen = AG1022USB()
print("AG1022:", gen.idn())

# ========= Generator init =========
gen.out(1, False)
if UseSquare:
    gen.set_square(1, StartF, Voltage, 0.0, duty=50, load="OFF")
else:
    gen.set_sine(1, StartF, Voltage, 0.0, load="OFF")
gen.out(1, True)

# ========= Sweep list =========
if SweepModeLog:
    last = 1 + math.ceil(PointsPerDecade * math.log10(StopF / StartF))
    freqs = [StartF * (10 ** (i / PointsPerDecade)) for i in range(last)]
else:
    last = 1 + math.ceil((StopF - StartF) / StepSizeF)
    freqs = [StartF + i * StepSizeF for i in range(last)]
freqs = [f for f in freqs if f <= StopF and f <= 25e6]  # AG1022 guard

# ========= Sweep =========
VNA = []
ts = time.strftime("%Y-%m-%d %H:%M")
log = open(FILEPREFIX + "_VNA.log", "w", encoding="utf-8")
print(f"# {ts}", file=log)
print("#Sample,  Frequency,      |Z|,      ∠Z (deg),   Mag(dB),   Phase(dg)", file=log)

MDEPTH = 10000  # 10k points per channel (fast & reliable on RTB)
for idx, F in enumerate(freqs):
    # set generator
    if UseSquare:
        gen.set_square(1, F, Voltage, 0.0, duty=50)
    else:
        gen.set_sine(1, F, Voltage, 0.0)

    # capture both channels
    y1, y2, xincr = rtb_capture_pair(rtb, F, MDEPTH)

    N = min(len(y1), len(y2))
    if N < 32:
        print(f"#{idx:03d}  f={F:.3f} Hz  (too few points: {N})")
        continue

    # fit sin/cos over an integer number of cycles
    n_per_cycle = 1.0 / (F * xincr)
    n_cycles = max(1, math.floor(N / n_per_cycle))
    M = int(max(1, round(n_cycles * n_per_cycle)))
    t = np.linspace(0, n_cycles * 2 * np.pi, M, endpoint=False)
    s = np.sin(t)
    c = np.cos(t)
    x1 = y1[:M]
    x2 = y2[:M]

    S1 = float(np.dot(x1, s) / M)
    C1 = float(np.dot(x1, c) / M)
    S2 = float(np.dot(x2, s) / M)
    C2 = float(np.dot(x2, c) / M)
    V1 = complex(S1, C1)
    V2 = complex(S2, C2)

    MAG1 = 2.0 * abs(V1)
    MAG2 = 2.0 * abs(V2)
    PH1 = float(np.angle(V1, deg=True))
    PH2 = float(np.angle(V2, deg=True))

    # light autoscale for comfort (non-critical)
    rtb.write(f"CHAN1:SCAL {max(1e-3, MAG1/3):.4f}; CHAN2:SCAL {max(1e-3, MAG2/3):.4f}")

    GdB = 20.0 * np.log10(MAG2 / MAG1) if MAG1 > 0 else float("nan")
    Phase = (PH2 - PH1) % 360.0
    if Phase > 180.0:
        Phase -= 360.0

    Z = complex(0.0, 0.0)
    if Resistance:
        denom = V1 - V2
        if abs(denom) > 1e-15:
            Z = (V2 / denom) * Resistance

    print(
        f"#{idx:03d}  f={F:11.3f} Hz  |Z|={abs(Z):.4g} Ω  ∠Z={np.angle(Z,deg=True):6.1f}°   "
        f"G={GdB:7.2f} dB  φ={Phase:7.2f}°"
    )
    print(
        f"{idx:6d}, {F:12.3f}, {abs(Z):12.5g}, {np.angle(Z,deg=True):9.3f}, "
        f"{GdB:9.3f}, {Phase:9.3f}",
        file=log,
    )

    VNA.append((F, GdB, Phase, Z))

log.close()
rtb.close()
rm.close()
print("Done. Log saved to", FILEPREFIX + "_VNA.log")

# ========= Plots =========
if PlotOK and VNA:
    F = np.array([x[0] for x in VNA])
    Zm = np.array([abs(x[3]) for x in VNA])
    Zph = np.array([np.angle(x[3], deg=True) for x in VNA])
    GdB = np.array([x[1] for x in VNA])
    Ph = np.array([x[2] for x in VNA])

    fig, ax1 = plt.subplots()
    ax1.set_title("|Z| and ∠Z vs Frequency")
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("|Z| (Ω)")
    ax1.grid(True, which="both")
    ax1.semilogx(F, Zm)
    ax2 = ax1.twinx()
    ax2.set_ylabel("∠Z (°)")
    ax2.semilogx(F, Zph)
    fig.tight_layout()
    plt.show(block=False)

    fig2, bx1 = plt.subplots()
    bx1.set_title("CH2 / CH1")
    bx1.set_xlabel("Frequency (Hz)")
    bx1.set_ylabel("Gain (dB)")
    bx1.grid(True, which="both")
    bx1.semilogx(F, GdB)
    bx2 = bx1.twinx()
    bx2.set_ylabel("Phase (°)")
    bx2.semilogx(F, Ph)
    fig2.tight_layout()
    plt.show()
