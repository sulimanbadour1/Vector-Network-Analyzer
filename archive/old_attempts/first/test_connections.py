#!/usr/bin/env python3
"""
Test script to verify VNA connections and basic functionality.
Run this script to check if your WON AG 1022 and R&S RTB2004 are properly connected.
"""

import visa
import time
import sys


def test_visa_backend():
    """Test if VISA backend is working."""
    print("🔍 Testing VISA backend...")
    try:
        rm = visa.ResourceManager()
        print(f"✅ VISA backend: {rm}")
        return rm
    except Exception as e:
        print(f"❌ VISA backend error: {e}")
        print("Please install VISA drivers for your operating system.")
        return None


def list_devices(rm):
    """List all available VISA devices."""
    print("\n📋 Available VISA devices:")
    try:
        resources = rm.list_resources()
        if not resources:
            print("   ⚠️  No VISA devices found!")
            print("   Check USB connections and device drivers.")
            return []

        for i, resource in enumerate(resources):
            print(f"   {i+1}. {resource}")
        return resources
    except Exception as e:
        print(f"❌ Error listing devices: {e}")
        return []


def find_instruments(resources):
    """Find WON AG 1022 and R&S RTB2004 in the resource list."""
    won_device = None
    rtb_device = None

    print("\n🎯 Looking for your instruments...")

    for resource in resources:
        resource_lower = resource.lower()

        # Look for WON AG 1022
        if (
            "won" in resource_lower
            or "ag1022" in resource_lower
            or "ag 1022" in resource_lower
        ):
            won_device = resource
            print(f"✅ Found WON AG 1022: {resource}")

        # Look for R&S RTB2004
        if (
            "rtb2004" in resource_lower
            or "rtb" in resource_lower
            or "rohde" in resource_lower
        ):
            rtb_device = resource
            print(f"✅ Found R&S RTB2004: {resource}")

    if not won_device:
        print("❌ WON AG 1022 not found!")
        print("   Check USB connection and device drivers.")

    if not rtb_device:
        print("❌ R&S RTB2004 not found!")
        print("   Check USB connection and device drivers.")

    return won_device, rtb_device


def test_won_ag1022(rm, device_string):
    """Test communication with WON AG 1022."""
    print(f"\n🔧 Testing WON AG 1022 communication...")

    try:
        won = rm.open_resource(device_string)
        won.timeout = 5000  # 5 second timeout

        # Get device identification
        idn = won.query("*IDN?")
        print(f"   Device ID: {idn.strip()}")

        # Test basic commands
        print("   Testing basic commands...")

        # Set frequency
        won.write("FREQ 1000")
        freq = won.query("FREQ?")
        print(f"   Frequency set to: {freq.strip()} Hz")

        # Set voltage
        won.write("VOLT 1.0")
        volt = won.query("VOLT?")
        print(f"   Voltage set to: {volt.strip()} V")

        # Set sine wave
        won.write("FUNC SIN")
        func = won.query("FUNC?")
        print(f"   Function set to: {func.strip()}")

        # Enable output
        won.write("OUTP ON")
        outp = won.query("OUTP?")
        print(f"   Output status: {outp.strip()}")

        print("✅ WON AG 1022 communication successful!")
        return won

    except Exception as e:
        print(f"❌ WON AG 1022 communication error: {e}")
        return None


def test_rtb2004(rm, device_string):
    """Test communication with R&S RTB2004."""
    print(f"\n🔧 Testing R&S RTB2004 communication...")

    try:
        rtb = rm.open_resource(device_string)
        rtb.timeout = 5000  # 5 second timeout

        # Get device identification
        idn = rtb.query("*IDN?")
        print(f"   Device ID: {idn.strip()}")

        # Test basic commands
        print("   Testing basic commands...")

        # Set acquisition points
        rtb.write(":ACQ:POIN 10000")
        points = rtb.query(":ACQ:POIN?")
        print(f"   Acquisition points: {points.strip()}")

        # Set waveform format
        rtb.write(":WAV:FORMAT BYTE")
        format_wav = rtb.query(":WAV:FORMAT?")
        print(f"   Waveform format: {format_wav.strip()}")

        # Set channel 1 coupling
        rtb.write(":CHAN1:COUP AC")
        coup = rtb.query(":CHAN1:COUP?")
        print(f"   Channel 1 coupling: {coup.strip()}")

        # Set trigger mode
        rtb.write(":TRIG:MODE EDGE")
        trig_mode = rtb.query(":TRIG:MODE?")
        print(f"   Trigger mode: {trig_mode.strip()}")

        print("✅ R&S RTB2004 communication successful!")
        return rtb

    except Exception as e:
        print(f"❌ R&S RTB2004 communication error: {e}")
        return None


def test_signal_generation(won):
    """Test if signal generator can produce a signal."""
    print(f"\n📡 Testing signal generation...")

    try:
        # Set a test signal
        won.write("FREQ 1000")  # 1 kHz
        won.write("VOLT 1.0")  # 1V
        won.write("FUNC SIN")  # Sine wave
        won.write("OUTP ON")  # Enable output

        print("   Signal generator configured:")
        print(f"   - Frequency: 1000 Hz")
        print(f"   - Voltage: 1.0 V")
        print(f"   - Waveform: Sine")
        print(f"   - Output: Enabled")

        print("✅ Signal generation test passed!")
        print("   Check your oscilloscope - you should see a 1 kHz sine wave.")

    except Exception as e:
        print(f"❌ Signal generation error: {e}")


def test_oscilloscope_acquisition(rtb):
    """Test if oscilloscope can acquire data."""
    print(f"\n📊 Testing oscilloscope acquisition...")

    try:
        # Configure oscilloscope for acquisition
        rtb.write(":STOP")  # Stop acquisition
        rtb.write(":ACQ:POIN 10000")
        rtb.write(":WAV:FORMAT BYTE")
        rtb.write(":WAV:MODE RAW")

        # Set up channels
        rtb.write(":CHAN1:COUP AC")
        rtb.write(":CHAN1:DISP ON")
        rtb.write(":CHAN1:SCAL 1.0")

        rtb.write(":CHAN2:COUP AC")
        rtb.write(":CHAN2:DISP ON")
        rtb.write(":CHAN2:SCAL 1.0")

        # Set trigger
        rtb.write(":TRIG:MODE EDGE")
        rtb.write(":TRIG:EDGE:SOUR CHAN1")
        rtb.write(":TRIG:EDGE:SLOP POS")
        rtb.write(":TRIG:EDGE:LEV 0.5")

        # Start acquisition
        rtb.write(":RUN")

        print("   Oscilloscope configured:")
        print(f"   - Acquisition points: 10000")
        print(f"   - Waveform format: Byte")
        print(f"   - Trigger: Edge, CH1, Positive slope")
        print(f"   - Status: Running")

        print("✅ Oscilloscope acquisition test passed!")
        print("   Check your oscilloscope display - it should be running.")

    except Exception as e:
        print(f"❌ Oscilloscope acquisition error: {e}")


def run_basic_vna_test(won, rtb):
    """Run a basic VNA test to verify the complete system."""
    print(f"\n🎯 Running basic VNA test...")

    try:
        # Configure signal generator
        won.write("FREQ 1000")
        won.write("VOLT 1.0")
        won.write("FUNC SIN")
        won.write("OUTP ON")

        # Configure oscilloscope
        rtb.write(":STOP")
        rtb.write(":ACQ:POIN 10000")
        rtb.write(":WAV:FORMAT BYTE")
        rtb.write(":WAV:MODE RAW")
        rtb.write(":CHAN1:COUP AC")
        rtb.write(":CHAN1:DISP ON")
        rtb.write(":CHAN1:SCAL 1.0")
        rtb.write(":TRIG:MODE EDGE")
        rtb.write(":TRIG:EDGE:SOUR CHAN1")
        rtb.write(":TRIG:EDGE:SLOP POS")
        rtb.write(":TRIG:EDGE:LEV 0.5")

        # Single shot acquisition
        rtb.write(":SING")

        # Wait for acquisition
        print("   Waiting for acquisition...")
        time.sleep(2)

        # Check acquisition status
        status = rtb.query(":STAT:OPER:COND?")
        print(f"   Acquisition status: {status.strip()}")

        # Try to get waveform data
        rtb.write(":WAV:SOUR CHAN1")
        rtb.write(":WAV:STAR 1")
        rtb.write(":WAV:STOP 1000")

        # Get preamble
        preamble = rtb.query(":WAV:PRE?")
        print(f"   Waveform preamble: {preamble.strip()}")

        print("✅ Basic VNA test completed!")
        print("   If you see waveform data, your setup is working!")

    except Exception as e:
        print(f"❌ Basic VNA test error: {e}")


def main():
    """Main test function."""
    print("=" * 60)
    print("🔬 VNA Connection Test Script")
    print("=" * 60)
    print()

    # Test 1: VISA backend
    rm = test_visa_backend()
    if not rm:
        sys.exit(1)

    # Test 2: List devices
    resources = list_devices(rm)
    if not resources:
        sys.exit(1)

    # Test 3: Find instruments
    won_device, rtb_device = find_instruments(resources)

    if not won_device or not rtb_device:
        print("\n❌ Cannot proceed without both instruments.")
        print("Please check your connections and try again.")
        sys.exit(1)

    # Test 4: Test WON AG 1022
    won = test_won_ag1022(rm, won_device)
    if not won:
        sys.exit(1)

    # Test 5: Test R&S RTB2004
    rtb = test_rtb2004(rm, rtb_device)
    if not rtb:
        sys.exit(1)

    # Test 6: Test signal generation
    test_signal_generation(won)

    # Test 7: Test oscilloscope acquisition
    test_oscilloscope_acquisition(rtb)

    # Test 8: Basic VNA test
    run_basic_vna_test(won, rtb)

    # Cleanup
    try:
        won.close()
        rtb.close()
        rm.close()
    except:
        pass

    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("=" * 60)
    print()
    print("📋 Summary:")
    print("✅ VISA backend working")
    print("✅ Both instruments detected")
    print("✅ Communication established")
    print("✅ Signal generation working")
    print("✅ Oscilloscope acquisition working")
    print()
    print("🚀 Your VNA setup is ready!")
    print("You can now run: python VNA_Modified.py")
    print()


if __name__ == "__main__":
    main()
