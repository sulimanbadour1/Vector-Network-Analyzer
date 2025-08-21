#!/usr/bin/env python3
"""
Simple Equipment Test for OWON AG 1022 and R&S RTB2004
======================================================

This script tests basic connectivity and functionality of your equipment
before running the full VNA measurement.

Usage:
    python test_equipment.py
"""

import pyvisa as visa
import time
import sys


def test_visa():
    """Test VISA backend."""
    print("🔍 Testing VISA backend...")
    try:
        rm = visa.ResourceManager()
        print(f"✅ VISA backend: {rm}")
        return rm
    except Exception as e:
        print(f"❌ VISA error: {e}")
        print("Please install VISA drivers for your operating system.")
        return None


def list_devices(rm):
    """List all available VISA devices."""
    print("\n📋 Available VISA devices:")
    try:
        resources = rm.list_resources()
        if not resources:
            print("   ⚠️  No VISA devices found!")
            return []

        for i, resource in enumerate(resources):
            print(f"   {i+1}. {resource}")
        return resources
    except Exception as e:
        print(f"❌ Error listing devices: {e}")
        return []


def find_equipment(resources):
    """Find OWON AG 1022 and R&S RTB2004."""
    won_device = None
    rtb_device = None

    print("\n🎯 Looking for your equipment...")

    for resource in resources:
        resource_lower = resource.lower()

        # Look for OWON AG 1022
        if any(pattern in resource_lower for pattern in ["won", "ag1022", "ag 1022"]):
            won_device = resource
            print(f"✅ Found OWON AG 1022: {resource}")

        # Look for R&S RTB2004
        if any(
            pattern in resource_lower for pattern in ["rtb2004", "rtb", "rohde", "rs"]
        ):
            rtb_device = resource
            print(f"✅ Found R&S RTB2004: {resource}")

    if not won_device:
        print("❌ OWON AG 1022 not found!")

    if not rtb_device:
        print("❌ R&S RTB2004 not found!")

    return won_device, rtb_device


def test_won_ag1022(rm, device_string):
    """Test OWON AG 1022 communication."""
    print(f"\n🔧 Testing OWON AG 1022...")

    try:
        won = rm.open_resource(device_string)
        won.timeout = 5000

        # Get device identification
        idn = won.query("*IDN?")
        print(f"   Device ID: {idn.strip()}")

        # Test basic commands
        print("   Testing basic commands...")

        # Set frequency
        won.write("FREQ 1000")
        freq = won.query("FREQ?")
        print(f"   Frequency: {freq.strip()} Hz")

        # Set amplitude
        won.write("VOLT 1.0")
        volt = won.query("VOLT?")
        print(f"   Voltage: {volt.strip()} V")

        # Set waveform
        won.write("FUNC SIN")
        func = won.query("FUNC?")
        print(f"   Function: {func.strip()}")

        # Turn output on
        won.write("OUTP ON")
        outp = won.query("OUTP?")
        print(f"   Output: {outp.strip()}")

        # Turn output off
        won.write("OUTP OFF")

        won.close()
        print("   ✅ OWON AG 1022 test passed!")
        return True

    except Exception as e:
        print(f"   ❌ OWON AG 1022 test failed: {e}")
        return False


def test_rtb2004(rm, device_string):
    """Test R&S RTB2004 communication."""
    print(f"\n🔧 Testing R&S RTB2004...")

    try:
        rtb = rm.open_resource(device_string)
        rtb.timeout = 5000

        # Get device identification
        idn = rtb.query("*IDN?")
        print(f"   Device ID: {idn.strip()}")

        # Test basic commands
        print("   Testing basic commands...")

        # Set timebase
        rtb.write(":TIM:SCAL 0.001")
        tb = rtb.query(":TIM:SCAL?")
        print(f"   Timebase: {tb.strip()} s/div")

        # Set channel 1
        rtb.write(":CHAN1:DISP ON")
        rtb.write(":CHAN1:SCAL 1.0")
        ch1_scale = rtb.query(":CHAN1:SCAL?")
        print(f"   CH1 Scale: {ch1_scale.strip()} V/div")

        # Set channel 2
        rtb.write(":CHAN2:DISP ON")
        rtb.write(":CHAN2:SCAL 1.0")
        ch2_scale = rtb.query(":CHAN2:SCAL?")
        print(f"   CH2 Scale: {ch2_scale.strip()} V/div")

        # Set trigger
        rtb.write(":TRIG:MODE EDGE")
        rtb.write(":TRIG:EDGE:SOUR CHAN1")
        trig_source = rtb.query(":TRIG:EDGE:SOUR?")
        print(f"   Trigger Source: {trig_source.strip()}")

        # Set acquisition
        rtb.write(":ACQ:POIN 10000")
        acq_points = rtb.query(":ACQ:POIN?")
        print(f"   Acquisition Points: {acq_points.strip()}")

        rtb.close()
        print("   ✅ R&S RTB2004 test passed!")
        return True

    except Exception as e:
        print(f"   ❌ R&S RTB2004 test failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Equipment Test for OWON AG 1022 and R&S RTB2004")
    print("=" * 60)

    # Test VISA
    rm = test_visa()
    if not rm:
        sys.exit(1)

    # List devices
    resources = list_devices(rm)
    if not resources:
        print("No VISA devices found. Please check connections.")
        sys.exit(1)

    # Find equipment
    won_device, rtb_device = find_equipment(resources)

    # Test equipment
    won_ok = False
    rtb_ok = False

    if won_device:
        won_ok = test_won_ag1022(rm, won_device)

    if rtb_device:
        rtb_ok = test_rtb2004(rm, rtb_device)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if won_ok and rtb_ok:
        print("✅ All equipment tests passed!")
        print("🎉 Your setup is ready for VNA measurements.")
        print("\nYou can now run:")
        print("   python VNA_Enhanced.py")
        print("   python VNA_Enhanced.py -h  # for help")
    else:
        print("❌ Some equipment tests failed.")
        if not won_ok:
            print("   - OWON AG 1022 needs attention")
        if not rtb_ok:
            print("   - R&S RTB2004 needs attention")
        print("\nPlease check:")
        print("   - USB connections")
        print("   - Device drivers")
        print("   - Instrument power")
        print("   - VISA installation")

    rm.close()
    print("\nTest completed.")


if __name__ == "__main__":
    main()
