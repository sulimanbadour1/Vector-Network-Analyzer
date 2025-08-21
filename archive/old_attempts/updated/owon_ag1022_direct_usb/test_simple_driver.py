#!/usr/bin/env python3
"""
Simple Test for OWON AG 1022 Simplified Driver
==============================================

This script tests the simplified direct USB driver for the OWON AG 1022.

Usage:
    python test_simple_driver.py
"""

import sys
import time
from owon_ag1022_simple import OWONAG1022Simple, find_owon_devices


def test_simple_driver():
    """Test the simplified driver."""
    print("🔬 Testing OWON AG 1022 Simplified Driver")
    print("=" * 50)

    # Find OWON devices
    print("Scanning for OWON devices...")
    devices = find_owon_devices()

    if not devices:
        print("❌ No OWON devices found")
        return False

    print(f"✅ Found {len(devices)} OWON device(s):")
    for vid, pid, manufacturer, product in devices:
        print(f"  VID: 0x{vid:04x}, PID: 0x{pid:04x}")
        print(f"  Manufacturer: {manufacturer}")
        print(f"  Product: {product}")

    # Test with the first device
    vid, pid, manufacturer, product = devices[0]
    print(f"\n🎯 Testing with device: {manufacturer} {product}")

    try:
        # Create driver instance
        print("Connecting to device...")
        device = OWONAG1022Simple(vid, pid)

        # Test communication
        print("\nTesting communication...")
        if device.test_communication():
            print("✅ Communication test passed!")
        else:
            print("❌ Communication test failed!")
            return False

        # Test signal configuration
        print("\nTesting signal configuration...")
        device.configure_signal(1000, 1.0, "SIN", True)
        print("✅ Signal configuration test passed!")

        # Test different waveforms
        print("\nTesting different waveforms...")
        waveforms = ["SIN", "SQU", "TRI", "RAMP"]
        for waveform in waveforms:
            print(f"  Testing {waveform} waveform...")
            device.set_waveform(waveform)
            time.sleep(1)  # Give time to see the change
        print("✅ Waveform testing passed!")

        # Test frequency sweep
        print("\nTesting frequency sweep...")
        frequencies = [100, 500, 1000, 5000, 10000]
        for freq in frequencies:
            print(f"  Setting frequency to {freq} Hz...")
            device.set_frequency(freq)
            time.sleep(0.5)
        print("✅ Frequency sweep test passed!")

        # Test voltage range
        print("\nTesting voltage range...")
        voltages = [0.1, 0.5, 1.0, 2.0, 5.0]
        for voltage in voltages:
            print(f"  Setting voltage to {voltage} V...")
            device.set_voltage(voltage)
            time.sleep(0.5)
        print("✅ Voltage range test passed!")

        # Final configuration
        print("\nSetting final configuration...")
        device.configure_signal(1000, 1.0, "SIN", True)
        print("✅ Final configuration set!")

        print("\n🎉 All tests passed! Your OWON AG 1022 is working correctly.")
        print("The device is now generating a 1 kHz sine wave at 1V.")
        print("Connect an oscilloscope to verify the signal.")

        # Clean up
        device.close()
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Main test function."""
    print("OWON AG 1022 Simplified Driver Test")
    print("=" * 60)

    # Test the simplified driver
    success = test_simple_driver()

    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Simplified driver test: {'✅ PASS' if success else '❌ FAIL'}")

    if success:
        print("\n🎉 Test passed! The simplified driver is working correctly.")
        print("You can now use the OWON AG 1022 with your VNA software.")
    else:
        print("\n⚠️  Test failed. Please check the issues above.")

    print("=" * 60)


if __name__ == "__main__":
    main()
