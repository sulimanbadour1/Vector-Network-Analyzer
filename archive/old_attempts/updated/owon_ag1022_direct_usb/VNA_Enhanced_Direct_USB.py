#!/usr/bin/env python3
"""
Enhanced Vector Network Analyzer with OWON AG 1022 Direct USB
============================================================

A Python-based Vector Network Analyzer implementation that uses:
- Signal Generator: OWON AG 1022 (Direct USB)
- Oscilloscope: Rohde & Schwarz RTB2004 (VISA)

This enhanced version includes:
- Direct USB communication with OWON AG 1022 (bypasses VISA issues)
- Improved error handling and device detection
- Better SCPI command compatibility
- Enhanced measurement accuracy
- Real-time status updates
- Comprehensive logging

Usage:
    python VNA_Enhanced_Direct_USB.py                    # Default sweep 1Hz-1MHz
    python VNA_Enhanced_Direct_USB.py -b 100 -e 10000   # Custom frequency range
    python VNA_Enhanced_Direct_USB.py -z 1000           # Impedance measurement
    python VNA_Enhanced_Direct_USB.py -p 20             # 20 points per decade
    python VNA_Enhanced_Direct_USB.py -v 2.0            # 2V amplitude
    python VNA_Enhanced_Direct_USB.py -n                # No plotting
    python VNA_Enhanced_Direct_USB.py -l                # List frequencies only
"""

import pyvisa as visa
import time
import math
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
import os
import keyboard
from datetime import datetime

# Import our direct USB driver
from owon_ag1022_simple import OWONAG1022Simple, find_owon_devices


class VNAError(Exception):
    """Custom exception for VNA errors."""

    pass


def help_and_exit():
    """Display help information and exit."""
    print(
        """
Enhanced Vector Network Analyzer with OWON AG 1022 Direct USB
============================================================

Usage: python VNA_Enhanced_Direct_USB.py [options]

Options:
  -b <freq>     Begin frequency in Hz (default: 1)
  -e <freq>     End frequency in Hz (default: 1e6)
  -p <points>   Points per decade (default: 10)
  -z <ohms>     Enable impedance measurement with reference resistance
  -v <volts>    Voltage amplitude in V (default: 1.0)
  -f <prefix>   File prefix for output (default: RTB2004)
  -n            Don't plot after data collection
  -l            List frequencies only (no measurement)
  -q            Use square wave instead of sine wave
  -s <freq>     Linear sweep with step size in Hz
  -d            Debug mode (verbose output)
  -h            Show this help

Examples:
  python VNA_Enhanced_Direct_USB.py -b 100 -e 10000 -p 20
  python VNA_Enhanced_Direct_USB.py -z 1000 -v 2.0
  python VNA_Enhanced_Direct_USB.py -l -b 1000 -e 100000
"""
    )
    sys.exit(0)


def next_arg(i):
    """Return the next command line argument."""
    if (i + 1) >= len(sys.argv):
        raise VNAError(f"'{sys.argv[i]}' expected an argument")
    return 1, sys.argv[i + 1]


def find_instruments(rm):
    """Find and return OWON AG 1022 and R&S RTB2004 instruments."""
    resources = rm.list_resources()
    print("Available VISA resources:")
    for resource in resources:
        print(f"  {resource}")
    print()

    won_device = None
    rtb_device = None

    # Look for R&S RTB2004 (VISA)
    for resource in resources:
        resource_lower = resource.lower()
        if any(
            pattern in resource_lower for pattern in ["rtb2004", "rtb", "rohde", "rs"]
        ):
            rtb_device = resource
            print(f"Found R&S RTB2004: {resource}")
            break

    if not rtb_device:
        raise VNAError("R&S RTB2004 not found. Check USB connection and drivers.")

    # Look for OWON AG 1022 (Direct USB)
    print("Looking for OWON AG 1022 via direct USB...")
    owon_devices = find_owon_devices()

    if not owon_devices:
        raise VNAError("OWON AG 1022 not found via direct USB. Check USB connection.")

    # Use the first OWON device found
    vid, pid, manufacturer, product = owon_devices[0]
    won_device = (vid, pid, manufacturer, product)
    print(
        f"Found OWON AG 1022: {manufacturer} {product} (VID: 0x{vid:04x}, PID: 0x{pid:04x})"
    )

    return won_device, rtb_device


class OWONAG1022DirectUSB:
    """OWON AG 1022 Signal Generator interface using direct USB."""

    def __init__(self, device_info):
        self.vid, self.pid, self.manufacturer, self.product = device_info
        self.device = OWONAG1022Simple(self.vid, self.pid)
        self.idn = self.device.get_device_id()
        print(f"Connected to: {self.idn}")

    def set_frequency(self, freq):
        """Set frequency in Hz."""
        self.device.set_frequency(freq)

    def set_amplitude(self, amplitude):
        """Set amplitude in V."""
        self.device.set_voltage(amplitude)

    def set_waveform(self, waveform):
        """Set waveform type (SIN, SQU, TRI, RAMP)."""
        self.device.set_waveform(waveform)

    def set_output(self, state):
        """Set output on/off."""
        self.device.set_output(state)

    def get_frequency(self):
        """Get current frequency (from cached value)."""
        return self.device.get_frequency()

    def get_amplitude(self):
        """Get current amplitude (from cached value)."""
        return self.device.get_voltage()

    def close(self):
        """Close device connection."""
        self.device.close()


class RTB2004:
    """Rohde & Schwarz RTB2004 Oscilloscope interface."""

    def __init__(self, resource_string):
        self.device = visa.ResourceManager().open_resource(resource_string)
        self.device.timeout = 10000
        self.idn = self.device.query("*IDN?").strip()
        print(f"Connected to: {self.idn}")

    def setup_channel(self, channel, coupling="AC", scale=None, bandwidth="20M"):
        """Setup oscilloscope channel."""
        self.device.write(f":CHAN{channel}:COUP {coupling}")
        self.device.write(f":CHAN{channel}:DISP ON")
        if scale:
            self.device.write(f":CHAN{channel}:SCAL {scale}")
        self.device.write(f":CHAN{channel}:BWL {bandwidth}")

    def setup_trigger(self, source="CHAN1", level=None, slope="POS"):
        """Setup trigger."""
        self.device.write(":TRIG:MODE EDGE")
        self.device.write(f":TRIG:EDGE:SOUR {source}")
        self.device.write(f":TRIG:EDGE:SLOP {slope}")
        if level:
            self.device.write(f":TRIG:EDGE:LEV {level}")

    def set_timebase(self, time_per_division):
        """Set timebase scale."""
        self.device.write(f":TIM:SCAL {time_per_division:.9f}")

    def set_acquisition_points(self, points):
        """Set acquisition points."""
        self.device.write(f":ACQ:POIN {points}")

    def setup_waveform(self):
        """Setup waveform acquisition."""
        self.device.write(":WAV:FORMAT BYTE")
        self.device.write(":WAV:MODE RAW")

    def single_shot(self):
        """Start single shot acquisition."""
        self.device.write(":SING")

    def wait_for_acquisition(self):
        """Wait for acquisition to complete."""
        while True:
            status = self.device.query(":STAT:OPER:COND?")
            if status.strip() == "0":
                break
            time.sleep(0.1)

    def get_waveform_preamble(self, channel):
        """Get waveform preamble for channel."""
        self.device.write(f":WAV:SOUR CHAN{channel}")
        preamble_str = self.device.query(":WAV:PRE?")
        return [float(x) for x in preamble_str.split(",")]

    def get_waveform_data(self, channel, start=1, stop=None):
        """Get waveform data for channel."""
        self.device.write(f":WAV:SOUR CHAN{channel}")
        if start > 1:
            self.device.write(f":WAV:STAR {start}")
        if stop:
            self.device.write(f":WAV:STOP {stop}")
        return self.device.query_binary_values(
            ":WAV:DATA?", datatype="b", container=np.array, header_fmt="ieee"
        )

    def run(self):
        """Start continuous acquisition."""
        self.device.write(":RUN")

    def stop(self):
        """Stop acquisition."""
        self.device.write(":STOP")

    def close(self):
        """Close device connection."""
        self.device.close()


def main():
    """Main VNA function."""
    # Default parameters
    debug = False
    file_prefix = "RTB2004"
    start_freq = 1.0
    stop_freq = 1e6
    points_per_decade = 10
    voltage = 1.0
    resistance = 0.0
    sine_wave = True
    plot_ok = True
    list_only = False
    sweep_mode_log = True
    step_size = None

    # Parse command line arguments
    skip = 0
    for i in range(1, len(sys.argv)):
        if not skip:
            if sys.argv[i][:2] == "-d":
                debug = True
            elif sys.argv[i][:2] == "-f":
                skip, file_prefix = next_arg(i)
            elif sys.argv[i][:2] == "-n":
                plot_ok = False
            elif sys.argv[i][:2] == "-l":
                list_only = True
            elif sys.argv[i][:2] == "-q":
                sine_wave = False
            elif sys.argv[i][:2] == "-v":
                skip, voltage = 1, float(next_arg(i)[1])
            elif sys.argv[i][:2] == "-z":
                skip, resistance = 1, float(next_arg(i)[1])
            elif sys.argv[i][:2] == "-s":
                skip, step_size = 1, float(next_arg(i)[1])
                sweep_mode_log = False
            elif sys.argv[i][:2] == "-b":
                skip, start_freq = 1, float(next_arg(i)[1])
            elif sys.argv[i][:2] == "-e":
                skip, stop_freq = 1, float(next_arg(i)[1])
            elif sys.argv[i][:2] == "-p":
                skip, points_per_decade = 1, int(next_arg(i)[1])
                sweep_mode_log = True
            elif sys.argv[i][:2] == "-h":
                help_and_exit()
            elif sys.argv[i][:1] == "-":
                raise VNAError(f"Unknown argument: {sys.argv[i]}")
        else:
            skip = 0

    if list_only:
        plot_ok = False

    try:
        # Initialize VISA for oscilloscope
        rm = visa.ResourceManager()
        if debug:
            print(f"VISA backend: {rm}")

        # Find and connect to instruments
        won_info, rtb_resource = find_instruments(rm)
        won = OWONAG1022DirectUSB(won_info)
        rtb = RTB2004(rtb_resource)

        # Setup logging
        log_filename = f"{file_prefix}_VNA.log" if not list_only else os.devnull
        with open(log_filename, "w") as log_file:
            print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=log_file)
            print(f"# OWON AG 1022: {won.idn}", file=log_file)
            print(f"# R&S RTB2004: {rtb.idn}", file=log_file)

            # Calculate sweep parameters
            if sweep_mode_log:
                decades = math.log10(stop_freq / start_freq)
                total_points = 1 + math.ceil(points_per_decade * decades)
                print(f"# Frequency sweep: {start_freq:.1f} Hz to {stop_freq:.1f} Hz")
                print(
                    f"# Points per decade: {points_per_decade}, Total decades: {decades:.1f}"
                )
                print(f"# Total points: {total_points}")
                print(
                    f"# Analysing from {start_freq:.1f} Hz to {stop_freq:.1f} Hz, "
                    f"{points_per_decade} points/decade; {decades:.1f} decades",
                    file=log_file,
                )
            else:
                total_points = 1 + math.ceil((stop_freq - start_freq) / step_size)
                print(f"# Linear sweep: {start_freq:.1f} Hz to {stop_freq:.1f} Hz")
                print(f"# Step size: {step_size:.1f} Hz, Total points: {total_points}")
                print(
                    f"# Analysing from {start_freq:.1f} Hz to {stop_freq:.1f} Hz, "
                    f"{step_size:.1f} Hz steps; {total_points} total steps",
                    file=log_file,
                )

            # Setup instruments
            print("\nSetting up instruments...")

            # Setup signal generator
            won.set_frequency(start_freq)
            won.set_amplitude(voltage)
            won.set_waveform("SIN" if sine_wave else "SQU")
            won.set_output(True)

            # Setup oscilloscope
            rtb.set_acquisition_points(30000)
            rtb.setup_waveform()
            rtb.setup_channel(1, scale=voltage / 3)
            rtb.setup_channel(2, scale=voltage / 3)
            rtb.setup_trigger(level=voltage / 2)
            rtb.run()

            # Measurement loop
            vna_data = []
            sync_max_freq = 2e6  # Maximum sync frequency
            high_freq_mode = False

            print("\nStarting measurements...")
            print("#Sample, Frequency, Mag1, Mag2, Ratio(dB), Phase", file=log_file)

            for test_point in range(-1, total_points):
                point = max(0, test_point)

                # Calculate frequency
                if sweep_mode_log:
                    test_freq = start_freq * math.pow(10, point / points_per_decade)
                else:
                    test_freq = start_freq + point * step_size

                if test_freq > stop_freq:
                    break

                if test_freq > 25e6:  # Maximum frequency limit
                    print(f"Reached maximum frequency limit: {test_freq:.1f} Hz")
                    break

                if keyboard.is_pressed("q"):
                    print("Measurement stopped by user (q pressed)")
                    break

                print(f"Sample {test_point:3d}, {test_freq:11.3f} Hz", end="")

                if list_only:
                    print()
                    continue

                # Switch to high frequency mode if needed
                if test_freq >= sync_max_freq and not high_freq_mode:
                    print(" (switching to high frequency mode)", end="")
                    rtb.setup_trigger(source="CHAN1", level=0)
                    high_freq_mode = True
                    time.sleep(0.3)

                # Set frequency
                won.set_frequency(test_freq)

                # Set timebase
                time_per_div = 1.0 / (test_freq * 12.0)
                rtb.set_timebase(time_per_div)

                # Get actual timebase and calculate sample rate
                actual_tb = float(rtb.device.query(":TIM:SCAL?"))
                sample_rate = min(
                    250e6 if test_freq < sync_max_freq else 500e6,
                    round(30000 / (actual_tb * 12), 0),
                )

                # Format sample rate for display
                if sample_rate >= 1e9:
                    sample_rate_str = f"{sample_rate/1e9:.1f}G"
                elif sample_rate >= 1e6:
                    sample_rate_str = f"{sample_rate/1e6:.1f}M"
                elif sample_rate >= 1e3:
                    sample_rate_str = f"{sample_rate/1e3:.1f}k"
                else:
                    sample_rate_str = f"{sample_rate:.0f}"

                print(f", {sample_rate_str}S/s", end="")

                # Acquire data
                rtb.single_shot()
                rtb.wait_for_acquisition()

                # Get waveform parameters
                preamble1 = rtb.get_waveform_preamble(1)
                x_incr = preamble1[4]
                y_incr1 = preamble1[7]
                y_off1 = int(preamble1[8]) + int(preamble1[9])

                # Calculate number of points and cycles
                points_per_cycle = 1.0 / (test_freq * x_incr)
                num_cycles = math.floor(30000 / points_per_cycle)
                num_points = int(round(points_per_cycle * num_cycles))

                print(
                    f", {num_points} points; {num_cycles} cycle{'s' if num_cycles != 1 else ''} "
                    f"@ {points_per_cycle:.1f}/cycle"
                )

                # Generate reference signals
                sample_points = np.linspace(0, num_cycles * 2 * np.pi, num_points)
                sine_ref = np.sin(sample_points)
                cosine_ref = np.cos(sample_points)

                # Get channel 1 data
                curve1 = rtb.get_waveform_data(1, stop=30000)[:num_points]
                curve1 = (curve1 - y_off1) * y_incr1

                # Get channel 2 data
                preamble2 = rtb.get_waveform_preamble(2)
                y_incr2 = preamble2[7]
                y_off2 = int(preamble2[8]) + int(preamble2[9])
                curve2 = rtb.get_waveform_data(2, stop=30000)[:num_points]
                curve2 = (curve2 - y_off2) * y_incr2

                # Calculate magnitude and phase for channel 1
                sin_dot1 = np.dot(curve1, sine_ref) / num_points
                cos_dot1 = np.dot(curve1, cosine_ref) / num_points
                channel1_complex = complex(sin_dot1, cos_dot1)
                mag1 = 2 * abs(channel1_complex)
                phase1 = np.angle(channel1_complex) * 180 / math.pi

                # Calculate magnitude and phase for channel 2
                sin_dot2 = np.dot(curve2, sine_ref) / num_points
                cos_dot2 = np.dot(curve2, cosine_ref) / num_points
                channel2_complex = complex(sin_dot2, cos_dot2)
                mag2 = 2 * abs(channel2_complex)
                phase2 = np.angle(channel2_complex) * 180 / math.pi

                # Calculate transfer function
                mag_db = 20 * math.log10(mag2 / mag1)
                phase_diff = (phase2 - phase1) % 360
                if phase_diff > 180:
                    phase_diff -= 360

                # Calculate impedance if requested
                if resistance > 0:
                    channel_z = (
                        channel2_complex
                        / (channel1_complex - channel2_complex)
                        * resistance
                    )
                    z_str = f"{channel_z.real:12.4f} {'+-'[channel_z.imag < 0]}j{abs(channel_z.imag):12.4f}"
                else:
                    channel_z = complex(0, 0)
                    z_str = "N/A"

                # Display results
                print(f"Ch1: Mag={mag1:.5f}V, Phase={phase1:7.2f}°")
                print(f"Ch2: Mag={mag2:.5f}V, Phase={phase2:7.2f}°")
                print(f"Transfer: {mag_db:7.2f}dB @ {phase_diff:7.2f}°")
                if resistance > 0:
                    print(f"Impedance: {z_str} Ω")
                print()

                # Store data
                if test_point >= 0:
                    vna_data.append((test_freq, mag_db, phase_diff, channel_z))
                    print(
                        f"{point:6d}, {test_freq:12.3f}, {mag1:9.5f}, {mag2:9.5f}, "
                        f"{mag_db:7.2f}, {phase_diff:7.2f}, {z_str}",
                        file=log_file,
                    )

        # Cleanup
        won.set_output(False)
        won.close()
        rtb.close()
        rm.close()

        print("Measurement completed successfully!")

        # Plot results
        if plot_ok and vna_data:
            plot_results(vna_data, resistance > 0, sweep_mode_log)

    except VNAError as e:
        print(f"VNA Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def plot_results(vna_data, show_impedance, log_scale):
    """Plot VNA measurement results."""
    frequencies = [data[0] for data in vna_data]
    magnitudes = [data[1] for data in vna_data]
    phases = [data[2] for data in vna_data]

    # Transfer function plot
    fig, ax1 = plt.subplots(figsize=(12, 8))
    fig.canvas.set_window_title("VNA Transfer Function (Direct USB)")
    plt.title("Channel 2 : Channel 1 Transfer Function (OWON AG 1022 Direct USB)")

    color = "tab:red"
    ax1.set_xlabel("Frequency (Hz)")
    ax1.set_ylabel("Magnitude (dB)", color=color)
    if log_scale:
        ax1.semilogx(frequencies, magnitudes, color=color, linewidth=2)
    else:
        ax1.plot(frequencies, magnitudes, color=color, linewidth=2)
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color = "tab:blue"
    ax2.set_ylabel("Phase (°)", color=color)
    if log_scale:
        ax2.semilogx(frequencies, phases, color=color, linewidth=2)
    else:
        ax2.plot(frequencies, phases, color=color, linewidth=2)
    ax2.tick_params(axis="y", labelcolor=color)

    fig.tight_layout()
    plt.show(block=False)

    # Impedance plot if requested
    if show_impedance:
        impedances = [data[3] for data in vna_data]
        impedance_magnitudes = [abs(z) for z in impedances]
        impedance_phases = [np.angle(z) * 180 / math.pi for z in impedances]

        fig2, ax3 = plt.subplots(figsize=(12, 8))
        fig2.canvas.set_window_title("VNA Impedance (Direct USB)")
        plt.title("Complex Impedance (OWON AG 1022 Direct USB)")

        color = "tab:green"
        ax3.set_xlabel("Frequency (Hz)")
        ax3.set_ylabel("|Z| (Ω)", color=color)
        if log_scale:
            ax3.loglog(frequencies, impedance_magnitudes, color=color, linewidth=2)
        else:
            ax3.semilogy(frequencies, impedance_magnitudes, color=color, linewidth=2)
        ax3.tick_params(axis="y", labelcolor=color)
        ax3.grid(True, alpha=0.3)

        ax4 = ax3.twinx()
        color = "tab:purple"
        ax4.set_ylabel("Z∠ (°)", color=color)
        if log_scale:
            ax4.semilogx(frequencies, impedance_phases, color=color, linewidth=2)
        else:
            ax4.plot(frequencies, impedance_phases, color=color, linewidth=2)
        ax4.tick_params(axis="y", labelcolor=color)

        fig2.tight_layout()
        plt.show(block=True)


if __name__ == "__main__":
    main()
