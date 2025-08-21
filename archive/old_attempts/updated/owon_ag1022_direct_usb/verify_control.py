#!/usr/bin/env python3
"""
OWON AG 1022 Control Verification Script
=======================================

This script verifies that the code is actually controlling the signal generator
by making visible changes that you can observe on an oscilloscope or hear.

Usage:
    python verify_control.py

What to observe:
1. Connect oscilloscope to signal generator output
2. Run this script
3. Watch for changes in frequency, amplitude, and waveform
4. Listen for audio changes if connected to speakers
"""

import sys
import time
from owon_ag1022_simple import OWONAG1022Simple, find_owon_devices


def verify_frequency_control(device):
    """Verify frequency control by stepping through different frequencies."""
    print("\n🎵 VERIFYING FREQUENCY CONTROL")
    print("=" * 50)
    print("Watch your oscilloscope for frequency changes!")
    print("You should see the waveform period change.")
    print()

    frequencies = [100, 500, 1000, 5000, 10000, 50000, 100000]

    for freq in frequencies:
        print(f"Setting frequency to {freq} Hz...")
        device.set_frequency(freq)

        # Pause so you can observe the change
        print(f"  → Oscilloscope should show {freq} Hz (period = {1000/freq:.1f} ms)")
        print("  → Listen for pitch change if connected to audio")
        input("  Press Enter to continue to next frequency...")

    print("✅ Frequency control verification complete!")


def verify_voltage_control(device):
    """Verify voltage control by stepping through different amplitudes."""
    print("\n📊 VERIFYING VOLTAGE CONTROL")
    print("=" * 50)
    print("Watch your oscilloscope for amplitude changes!")
    print("You should see the waveform height change.")
    print()

    voltages = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

    for voltage in voltages:
        print(f"Setting voltage to {voltage} V...")
        device.set_voltage(voltage)

        # Pause so you can observe the change
        print(f"  → Oscilloscope should show {voltage} V peak-to-peak")
        print("  → Listen for volume change if connected to audio")
        input("  Press Enter to continue to next voltage...")

    print("✅ Voltage control verification complete!")


def verify_waveform_control(device):
    """Verify waveform control by cycling through different waveforms."""
    print("\n🌊 VERIFYING WAVEFORM CONTROL")
    print("=" * 50)
    print("Watch your oscilloscope for waveform shape changes!")
    print("You should see different waveform shapes.")
    print()

    waveforms = [
        ("SIN", "Sine wave - smooth, rounded"),
        ("SQU", "Square wave - sharp edges, harsh sound"),
        ("TRI", "Triangle wave - linear ramps"),
        ("RAMP", "Ramp wave - sawtooth pattern"),
    ]

    for waveform, description in waveforms:
        print(f"Setting waveform to {waveform}...")
        device.set_waveform(waveform)

        # Pause so you can observe the change
        print(f"  → Oscilloscope should show {description}")
        print("  → Listen for tone quality change if connected to audio")
        input("  Press Enter to continue to next waveform...")

    print("✅ Waveform control verification complete!")


def verify_output_control(device):
    """Verify output enable/disable control."""
    print("\n🔌 VERIFYING OUTPUT CONTROL")
    print("=" * 50)
    print("Watch your oscilloscope for signal on/off!")
    print("You should see the signal appear and disappear.")
    print()

    print("Turning output OFF...")
    device.set_output(False)
    print("  → Oscilloscope should show no signal")
    print("  → Listen for silence if connected to audio")
    input("  Press Enter to turn output ON...")

    print("Turning output ON...")
    device.set_output(True)
    print("  → Oscilloscope should show signal again")
    print("  → Listen for sound if connected to audio")
    input("  Press Enter to continue...")

    print("✅ Output control verification complete!")


def verify_rapid_changes(device):
    """Verify rapid changes to show real-time control."""
    print("\n⚡ VERIFYING RAPID CHANGES")
    print("=" * 50)
    print("Watch for rapid frequency changes!")
    print("This shows the code is controlling in real-time.")
    print()

    print("Starting rapid frequency sweep...")
    print("Watch your oscilloscope for smooth frequency changes!")

    # Rapid frequency sweep
    for i in range(10):
        freq = 1000 + i * 1000  # 1 kHz to 10 kHz
        device.set_frequency(freq)
        print(f"  {freq} Hz", end=" ", flush=True)
        time.sleep(0.5)

    print("\n✅ Rapid changes verification complete!")


def main():
    """Main verification function."""
    print("OWON AG 1022 Control Verification")
    print("=" * 60)
    print("This script will verify that the code is actually controlling")
    print("your signal generator. You need to observe the changes on")
    print("an oscilloscope or listen for audio changes.")
    print()

    # Find OWON devices
    print("Scanning for OWON devices...")
    devices = find_owon_devices()

    if not devices:
        print("❌ No OWON devices found!")
        print("Please check your USB connection.")
        sys.exit(1)

    print(f"✅ Found {len(devices)} OWON device(s):")
    for vid, pid, manufacturer, product in devices:
        print(f"  {manufacturer} {product} (VID: 0x{vid:04x}, PID: 0x{pid:04x})")

    # Use the first device
    vid, pid, manufacturer, product = devices[0]
    print(f"\n🎯 Using device: {manufacturer} {product}")

    # Connect to device
    try:
        print("Connecting to device...")
        device = OWONAG1022Simple(vid, pid)
        print("✅ Connected successfully!")

        # Set initial conditions
        print("\nSetting initial conditions...")
        device.set_frequency(1000)  # 1 kHz
        device.set_voltage(1.0)  # 1V
        device.set_waveform("SIN")  # Sine wave
        device.set_output(True)  # Enable output
        print("✅ Initial conditions set!")

        print("\n" + "=" * 60)
        print("READY FOR VERIFICATION")
        print("=" * 60)
        print(
            "Make sure your oscilloscope is connected to the signal generator output."
        )
        print("You should see a 1 kHz sine wave at 1V amplitude.")
        print()

        # Run verification tests
        verify_frequency_control(device)
        verify_voltage_control(device)
        verify_waveform_control(device)
        verify_output_control(device)
        verify_rapid_changes(device)

        # Final state
        print("\n🎉 FINAL VERIFICATION COMPLETE!")
        print("=" * 60)
        print("If you observed all the changes on your oscilloscope,")
        print("then the code is successfully controlling your signal generator!")
        print()
        print("Final settings:")
        print(f"  Frequency: {device.get_frequency()} Hz")
        print(f"  Voltage: {device.get_voltage()} V")
        print(f"  Waveform: {device.get_waveform()}")
        print(f"  Output: {'ON' if device.get_output() else 'OFF'}")

        # Keep output on for final verification
        device.set_output(True)
        print("\nSignal generator is still running. Press Enter to stop...")
        input()

        # Clean up
        device.set_output(False)
        device.close()
        print("✅ Device disconnected.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
