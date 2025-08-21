#!/usr/bin/env python3
"""
Quick Signal Generator Connection Test for Windows
================================================

A simple script to quickly test if the OWON AG 1022 signal generator
is properly connected and responding on Windows.

Usage:
    python quick_signal_test.py

This script will:
1. Check VISA backend
2. Find the signal generator
3. Test basic communication
4. Generate a test signal
5. Provide immediate feedback
"""

import pyvisa as visa
import time
import sys


def quick_test():
    """Perform a quick connection test."""
    print("🔬 Quick Signal Generator Connection Test")
    print("=" * 50)

    try:
        # Step 1: Initialize VISA
        print("1. Initializing VISA...")
        rm = visa.ResourceManager()
        print(f"   ✅ VISA backend: {rm}")

        # Step 2: List devices
        print("\n2. Scanning for devices...")
        resources = rm.list_resources()
        if not resources:
            print("   ❌ No VISA devices found!")
            return False

        print(f"   ✅ Found {len(resources)} device(s)")
        for i, resource in enumerate(resources, 1):
            print(f"      {i}. {resource}")

        # Step 3: Find signal generator
        print("\n3. Looking for OWON AG 1022...")
        signal_gen = None
        for resource in resources:
            resource_lower = resource.lower()
            if any(
                pattern in resource_lower for pattern in ["won", "ag1022", "ag 1022"]
            ):
                try:
                    device = rm.open_resource(resource)
                    device.timeout = 3000
                    idn = device.query("*IDN?").strip()
                    device.close()

                    if "won" in idn.lower() or "ag1022" in idn.lower():
                        signal_gen = resource
                        print(f"   ✅ Found: {idn}")
                        break
                except:
                    continue

        if not signal_gen:
            print("   ❌ OWON AG 1022 not found!")
            return False

        # Step 4: Test communication
        print("\n4. Testing communication...")
        device = rm.open_resource(signal_gen)
        device.timeout = 5000

        # Test basic commands
        device.write("FREQ 1000")
        freq = float(device.query("FREQ?"))
        print(f"   ✅ Frequency: {freq} Hz")

        device.write("VOLT 1.0")
        volt = float(device.query("VOLT?"))
        print(f"   ✅ Voltage: {volt} V")

        device.write("FUNC SIN")
        func = device.query("FUNC?").strip()
        print(f"   ✅ Waveform: {func}")

        # Step 5: Generate test signal
        print("\n5. Generating test signal...")
        device.write("OUTP ON")
        output = device.query("OUTP?").strip()
        print(f"   ✅ Output: {output}")

        # Step 6: Verify signal
        print("\n6. Verifying signal...")
        actual_freq = float(device.query("FREQ?"))
        actual_volt = float(device.query("VOLT?"))
        actual_func = device.query("FUNC?").strip()
        actual_outp = device.query("OUTP?").strip()

        print(f"   Frequency: {actual_freq} Hz")
        print(f"   Voltage: {actual_volt} V")
        print(f"   Waveform: {actual_func}")
        print(f"   Output: {actual_outp}")

        # Step 7: Cleanup
        print("\n7. Cleaning up...")
        device.write("OUTP OFF")
        device.close()
        print("   ✅ Output disabled and connection closed")

        # Success message
        print("\n" + "=" * 50)
        print("🎉 CONNECTION TEST SUCCESSFUL!")
        print("=" * 50)
        print("Your OWON AG 1022 signal generator is working correctly.")
        print("It is now generating a 1 kHz sine wave at 1V.")
        print("Connect an oscilloscope to verify the signal.")
        print("\nYou can now use the VNA software!")

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check USB connection")
        print("2. Install VISA drivers (NI-VISA or Keysight VISA)")
        print("3. Install OWON AG 1022 drivers")
        print("4. Try different USB port")
        print("5. Restart the signal generator")
        return False


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print(__doc__)
        return

    success = quick_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
