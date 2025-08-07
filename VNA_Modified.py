import visa
import time
import math
import pdb
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
import os
import keyboard


"""
Key changes:
 - Signal Generator: WON AG 1022
 - Oscilloscope: Rohde & Schwarz RTB2004

 # Basic usage
python VNA_Modified.py

# With custom frequency range
python VNA_Modified.py -b 100 -e 10000 -p 20

# With impedance measurement
python VNA_Modified.py -z 1000

# List frequencies only (no measurement)
python VNA_Modified.py -l

"""


def HelpAndExit():
    print(
        "Usage: ",
        sys.argv[0],
        " [-b BeginF] [-e EndF] [-p Points/Decade] [-f FILE_Prefix]\
  \noptional: [-n] Don't plot after gathering data\
  \noptional: [-z] Set current-measuring resistance and plot Z data\
\nFILE_Prefix defaults to RTB2004\
\nModified for WON AG 1022 Signal Generator and R&S RTB2004 Oscilloscope",
    )
    sys.exit(1)


def NextArg(i):  # Return the next command line argument (if there is one)
    if (i + 1) >= len(sys.argv):
        Fatal("'%s' expected an argument" % sys.argv[i])
    return (1, sys.argv[i + 1])


######################################### main ##################################
debug = 0
FILEPREFIX = "RTB2004"
MDEPTH = 30000
# pdb.set_trace()
StartF = 1
StopF = 1e6
PlotOK = True
ListOnly = False
PointsPerDecade = 10  # Changed from 30, 8/28/2018 KEAP
HighFrequency = (
    False  # used to indicate crossed over max Sync frequency from WON AG 1022
)
SweepModeLog = True
Voltage = 1.0
Resistance = 0.0  # non-zero when -z resistance argument is used -> Z is plotted
Sine = True

# Parse command line
skip = 0
for i in range(1, len(sys.argv)):
    if not skip:
        if sys.argv[i][:2] == "-d":
            debug = 1
        elif sys.argv[i][:2] == "-f":
            (skip, FILEPREFIX) = NextArg(i)
        elif sys.argv[i][:2] == "-n":
            PlotOK = False
        elif sys.argv[i][:2] == "-l":
            ListOnly = True
        elif sys.argv[i][:2] == "-q":
            Sine = False
        elif sys.argv[i][:2] == "-v":
            (skip, Voltage) = 1, float(NextArg(i)[1])
        elif sys.argv[i][:2] == "-z":
            (skip, Resistance) = 1, float(NextArg(i)[1])
        elif sys.argv[i][:2] == "-s":
            (skip, StepSizeF) = 1, float(NextArg(i)[1])
            SweepModeLog = False
        elif sys.argv[i][:2] == "-b":
            (skip, StartF) = 1, float(NextArg(i)[1])
        elif sys.argv[i][:2] == "-e":
            (skip, StopF) = 1, float(NextArg(i)[1])
        elif sys.argv[i][:2] == "-p":
            (skip, PointsPerDecade) = 1, int(NextArg(i)[1])
            SweepModeLog = True
        elif sys.argv[i][:2] == "-h":
            HelpAndExit()
        elif sys.argv[i][:1] == "-":
            sys.stderr.write("%s: Bad argument\n" % (sys.argv[0]))
            sys.exit(1)
        else:
            pass
    else:
        skip = 0

# if (len(sys.argv) <= 1): HelpAndExit()

if ListOnly:
    PlotOK = False  # don't plot if just listing

GPIB = visa.ResourceManager()
# print(GPIB.list_resources())
GPIB_Resources = GPIB.list_resources()
for resource in GPIB_Resources:
    print(resource)
print()

LOGFile = open(FILEPREFIX + "_VNA.log" if (not ListOnly) else os.devnull, "w")
# else: LOGFile = open(os.devnull, 'w')
print(time.strftime("# %Y-%m-%d %H:%M"), file=LOGFile)

# Find and connect to WON AG 1022 Signal Generator
# Look for WON AG 1022 in the resource list
won_resources = [
    _ for _ in GPIB_Resources if "WON" in _ or "AG1022" in _ or "AG 1022" in _
]
if won_resources:
    WON_AG1022 = GPIB.open_resource(won_resources[0])
else:
    # Try common USB patterns for WON devices
    won_resources = [
        _ for _ in GPIB_Resources if "USB" in _ and ("WON" in _ or "AG" in _)
    ]
    if won_resources:
        WON_AG1022 = GPIB.open_resource(won_resources[0])
    else:
        print("WARNING: Could not find WON AG 1022. Please check connection.")
        print("Available resources:", GPIB_Resources)
        # Try to connect anyway with a common pattern
        try:
            WON_AG1022 = GPIB.open_resource("USB0::0x0000::0x0000::AG1022::INSTR")
        except:
            print("ERROR: Cannot connect to WON AG 1022 signal generator")
            sys.exit(1)

Q = WON_AG1022.query("*IDN?")
print("WON AG 1022:", Q, end="")
print("# WON AG 1022:", Q, end="", file=LOGFile)

# Find and connect to R&S RTB2004 Oscilloscope
# Look for R&S RTB2004 in the resource list
rs_resources = [
    _ for _ in GPIB_Resources if "RTB2004" in _ or "R&S" in _ or "ROHDE" in _
]
if rs_resources:
    RTB2004 = GPIB.open_resource(rs_resources[0])
else:
    # Try common USB patterns for R&S devices
    rs_resources = [
        _ for _ in GPIB_Resources if "USB" in _ and ("RTB" in _ or "ROHDE" in _)
    ]
    if rs_resources:
        RTB2004 = GPIB.open_resource(rs_resources[0])
    else:
        print("WARNING: Could not find R&S RTB2004. Please check connection.")
        print("Available resources:", GPIB_Resources)
        # Try to connect anyway with a common pattern
        try:
            RTB2004 = GPIB.open_resource("USB0::0x0000::0x0000::RTB2004::INSTR")
        except:
            print("ERROR: Cannot connect to R&S RTB2004 oscilloscope")
            sys.exit(1)

Q = RTB2004.query("*IDN?")
print("R&S RTB2004:", Q)
print("# R&S RTB2004:", Q, end="", file=LOGFile)

RTB2004.timeout = 2000  # ms

DecadesF = math.log10(StopF / StartF)

print(sys.argv)
if SweepModeLog:
    print(
        "Analysing from %f Hz to %f Hz, %6.1f points/decade; %i decades"
        % (StartF, StopF, PointsPerDecade, DecadesF)
    )
    print(
        "# Analysing from %f Hz to %f Hz, %6.1f points/decade; %i decades"
        % (StartF, StopF, PointsPerDecade, DecadesF),
        file=LOGFile,
    )
else:
    print(
        "Analysing from %f Hz to %f Hz, %f Hz steps; %i total steps"
        % (StartF, StopF, StepSizeF, 1 + math.ceil((StopF - StartF) / StepSizeF))
    )
    print(
        "# Analysing from %f Hz to %f Hz, %f Hz steps; %i total steps"
        % (StartF, StopF, StepSizeF, 1 + math.ceil((StopF - StartF) / StepSizeF)),
        file=LOGFile,
    )

# WON AG 1022 Signal Generator Setup
# Note: WON AG 1022 commands may need adjustment based on exact model specifications
SYNCMax = 2.0e6  # Adjust based on WON AG 1022 specifications

# Set frequency and waveform for WON AG 1022
WON_AG1022.write("FREQ %11.3f" % StartF)  # Set frequency
if Sine:
    WON_AG1022.write("FUNC SIN")  # Set sine wave
else:
    WON_AG1022.write("FUNC SQU")  # Set square wave

WON_AG1022.write("VOLT %5.2f" % Voltage)  # Set voltage amplitude
WON_AG1022.write("OUTP ON")  # Turn output on

# R&S RTB2004 Oscilloscope Setup
RTB2004.write(":ACQ:POIN %i" % MDEPTH)  # Set acquisition points
RTB2004.write(":WAV:FORMAT BYTE")  # Set waveform format
RTB2004.write(":WAV:MODE RAW")  # Set raw mode

RTB2004.write(":STOP")  # Stop acquisition

# Channel 1 Setup
RTB2004.write(":CHAN1:COUP AC")  # AC coupling
RTB2004.write(":CHAN1:DISP ON")  # Display on
RTB2004.write(":CHAN1:SCAL %f" % (Voltage / 3))  # Set scale
RTB2004.write(":CHAN1:BWL 20M")  # Bandwidth limit 20MHz

# Channel 2 Setup
RTB2004.write(":CHAN2:COUP AC")  # AC coupling
RTB2004.write(":CHAN2:DISP ON")  # Display on
RTB2004.write(":CHAN2:SCAL %f" % (Voltage / 3))  # Set scale
RTB2004.write(":CHAN2:BWL 20M")  # Bandwidth limit 20MHz

# Trigger Setup
RTB2004.write(":TRIG:MODE EDGE")  # Edge trigger
RTB2004.write(":TRIG:EDGE:SOUR CHAN1")  # Trigger source CH1
RTB2004.write(":TRIG:EDGE:SLOP POS")  # Positive slope
RTB2004.write(":TRIG:EDGE:LEV %f" % (Voltage / 2))  # Trigger level

RTB2004.write(":RUN")  # Start acquisition

VNA = []
print("#Sample,  Frequency,      Mag1,      Mag2, Ratio (dB),   Phase", file=LOGFile)

if SweepModeLog:
    LastTestPOINT = 1 + math.ceil(PointsPerDecade * math.log10(StopF / StartF))
else:
    LastTestPOINT = 1 + math.ceil((StopF - StartF) / StepSizeF)

# for TestPOINT in range(-1, 1+math.ceil(PointsPerDecade*math.log10(StopF/StartF))):
for TestPOINT in range(-1, LastTestPOINT):
    # 1st cycle which is used to initialize vertical scale isn't logged
    POINT = max(0, TestPOINT)  # -1 maps to 0
    TestF = (
        StartF * math.pow(10, POINT / PointsPerDecade)
        if SweepModeLog
        else StartF + POINT * StepSizeF
    )
    if TestF > StopF:
        break
    if TestF > 25e6:
        break  # Max frequency of WON AG 1022 (adjust as needed)
    if keyboard.is_pressed("q"):
        print("Key pressed")
        break
    print("Sample %3i, %11.3f Hz" % (TestPOINT, TestF), end="")
    if ListOnly:
        print()
        continue  # only list sample frequencies

    if (
        TestF >= SYNCMax
    ) and not HighFrequency:  # Can't generate sync above 2 MHz -- so switch to Channel 1. This also allows S/s to double
        WON_AG1022.write("SYNC OFF")  # Turn off sync if available
        RTB2004.write(":TRIG:EDGE:SOUR CHAN1")  # Use CH1 as trigger source
        time.sleep(0.3)  # wait for this to change

        MDEPTH *= 2  # double sample rate when sync is not used
        HighFrequency = True  # Only switchover once

    WON_AG1022.write("FREQ %11.3f" % TestF)  # Set frequency

    # Set timebase for RTB2004
    time_per_division = 1.0 / (TestF * 12.0)  # 12 divisions for full cycle
    RTB2004.write(":TIM:SCAL %13.9f" % time_per_division)

    # Get actual timebase setting
    ActualTB = float(RTB2004.query(":TIM:SCAL?").rstrip())
    ActualSs = min(
        250e6 if (TestF < SYNCMax) else 500e6, round(MDEPTH / (ActualTB * 12), 0)
    )
    ActualSs_ = str(int(ActualSs))
    if ActualSs_[-9:] == "000000000":
        ActualSs_ = ActualSs_[:-9] + " G"
    if ActualSs_[-6:] == "000000":
        ActualSs_ = ActualSs_[:-6] + " M"
    if ActualSs_[-3:] == "000":
        ActualSs_ = ActualSs_[:-3] + " k"
    print(", %sS/s" % ActualSs_, end="")

    RTB2004.write(":SING")  # Single shot acquisition
    while RTB2004.query(":STAT:OPER:COND?")[:4] != "0":
        pass  # Wait for acquisition complete

    # Get waveform data from RTB2004
    # Get preamble for CH1
    RTB2004.write(":WAV:SOUR CHAN1")
    preamble_str = RTB2004.query(":WAV:PRE?")
    PreambleList = preamble_str.split(",")
    XINCR = float(PreambleList[4])
    YINCR1 = float(PreambleList[7])
    YOFF1 = int(PreambleList[8]) + int(PreambleList[9])

    NPOINTS_PerCycle = 1.0 / (
        TestF * XINCR
    )  # Number of points for 1 cycle of this frequency
    NCYCLES = math.floor(MDEPTH / NPOINTS_PerCycle)
    NPOINTS = int(round(NPOINTS_PerCycle * NCYCLES))
    print(
        ", %i points; %i cycle%s @ %10.1f/cycle"
        % (NPOINTS, NCYCLES, " " if (NCYCLES == 1) else "s", NPOINTS_PerCycle)
    )

    SAMPLEPOINTS = np.linspace(0, NCYCLES * 2 * np.pi, NPOINTS)
    SINEARRAY = np.sin(SAMPLEPOINTS)
    COSARRAY = np.cos(SAMPLEPOINTS)

    # Get CH1 waveform data
    RTB2004.write(":WAV:SOUR CHAN1")
    RTB2004.write(":WAV:STAR 1")
    RTB2004.write(":WAV:STOP %i" % MDEPTH)
    CURVE1 = RTB2004.query_binary_values(
        ":WAV:DATA?", datatype="b", container=np.array, header_fmt="ieee"
    )[:NPOINTS]
    CURVE1 = (CURVE1 - YOFF1) * YINCR1

    # Get preamble for CH2
    RTB2004.write(":WAV:SOUR CHAN2")
    preamble_str = RTB2004.query(":WAV:PRE?")
    PreambleList = preamble_str.split(",")
    YINCR2 = float(PreambleList[7])
    YOFF2 = int(PreambleList[8]) + int(PreambleList[9])

    # Get CH2 waveform data
    RTB2004.write(":WAV:SOUR CHAN2")
    RTB2004.write(":WAV:STAR 1")
    RTB2004.write(":WAV:STOP %i" % MDEPTH)
    CURVE2 = RTB2004.query_binary_values(
        ":WAV:DATA?", datatype="b", container=np.array, header_fmt="ieee"
    )[:NPOINTS]
    CURVE2 = (CURVE2 - YOFF2) * YINCR2

    SINDOT1 = np.dot(CURVE1, SINEARRAY) / NPOINTS
    COSDOT1 = np.dot(CURVE1, COSARRAY) / NPOINTS
    CHANNEL1 = complex(SINDOT1, COSDOT1)
    MAG1 = 2 * abs(CHANNEL1)
    PHASE1 = np.angle(CHANNEL1) * 180 / math.pi
    RTB2004.write(":CHAN1:SCAL %9.4f" % (MAG1 / 3))

    SINDOT2 = np.dot(CURVE2, SINEARRAY) / NPOINTS
    COSDOT2 = np.dot(CURVE2, COSARRAY) / NPOINTS
    CHANNEL2 = complex(SINDOT2, COSDOT2)
    MAG2 = 2 * abs(CHANNEL2)
    PHASE2 = np.angle(CHANNEL2) * 180 / math.pi
    RTB2004.write(":CHAN2:SCAL %9.4f" % (MAG2 / 3))

    Channel_Z = CHANNEL2 / (CHANNEL1 - CHANNEL2) * Resistance

    print(
        "Ch1: Sin, Cos = %9.4f, %9.4f; Mag = %9.5f, Phase = %7.2f deg."
        % (SINDOT1, COSDOT1, MAG1, PHASE1)
    )
    print(
        "Ch2: Sin, Cos = %9.4f, %9.4f; Mag = %9.5f, Phase = %7.2f deg."
        % (SINDOT2, COSDOT2, MAG2, PHASE2)
    )
    Mag_dB = 20 * math.log10(MAG2 / MAG1)
    Phase = (PHASE2 - PHASE1) % 360
    if (Phase) > 180:
        Phase -= 360  # center around +/- 180
    CHZ = "%12.4f %sj%12.4f" % (
        Channel_Z.real,
        "+-"[Channel_Z.imag < 0],
        abs(Channel_Z.imag),
    )
    print("Ch2:Ch1 = %7.2f dB @ %7.2f deg.; Z =" % (Mag_dB, Phase), CHZ, "\n")
    if TestPOINT >= 0:  # only after 1st round
        VNA.append((TestF, Mag_dB, Phase, Channel_Z))
        print(
            "%6i, %12.3f, %9.5f, %9.5f,    %7.2f, %7.2f, "
            % (POINT, TestF, MAG1, MAG2, Mag_dB, Phase),
            CHZ,
            file=LOGFile,
        )

LOGFile.close()
RTB2004.close()
WON_AG1022.close()
GPIB.close()
print("Done")

if PlotOK:
    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title("VNA 2:1")
    plt.title("Channel 2 : Channel 1")

    color = "tab:red"
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("dB", color=color)
    if SweepModeLog:
        ax1.semilogx([_[0] for _ in VNA], [_[1] for _ in VNA], color=color)
    else:
        ax1.plot([_[0] for _ in VNA], [_[1] for _ in VNA], color=color)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = "tab:blue"
    ax2.set_ylabel("Phase (°)", color=color)  # we already handled the x-label with ax1
    if SweepModeLog:
        ax2.semilogx([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
        ax2.semilogx([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
    else:
        ax2.plot([_[0] for _ in VNA], [_[2] for _ in VNA], color=color)
    ax2.tick_params(axis="y", labelcolor=color)
    # ax2.grid(True)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show(block=False)  # should only block if R=0 ?
    # plt.show(block=False)

if PlotOK and Resistance != 0:
    fig, ax1 = plt.subplots()
    fig.canvas.set_window_title("VNA Z")

    plt.title("Impedance (ohms)")

    color = "tab:green"
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("|Z| (ohms)", color=color)
    if SweepModeLog:
        ax1.loglog([_[0] for _ in VNA], [abs(_[3]) for _ in VNA], color=color)
    else:
        ax1.semilogy(
            [_[0] for _ in VNA], [abs(_[3]) for _ in VNA], color=color
        )  # Mag(Z)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = "tab:purple"
    ax2.set_ylabel("Z∠ (°)", color=color)  # we already handled the x-label with ax1
    if SweepModeLog:
        ax2.semilogx(
            [_[0] for _ in VNA],
            [np.angle(_[3]) * 180 / math.pi for _ in VNA],
            color=color,
        )
    else:
        ax2.plot(
            [_[0] for _ in VNA],
            [np.angle(_[3]) * 180 / math.pi for _ in VNA],
            color=color,
        )
    ax2.tick_params(axis="y", labelcolor=color)
    # ax2.grid(True)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show(block=True)
