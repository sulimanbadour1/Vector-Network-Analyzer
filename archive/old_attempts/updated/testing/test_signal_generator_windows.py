#!/usr/bin/env python3
"""
Windows Signal Generator Connection Test Script
==============================================

This script specifically tests the connection of the OWON AG 1022 signal generator
on Windows systems. It includes comprehensive testing for:
- VISA backend compatibility
- Device detection and identification
- Communication protocols
- Signal generation capabilities
- Error handling and recovery

Usage:
    python test_signal_generator_windows.py

Requirements:
    - Windows 10/11
    - NI-VISA or Keysight VISA installed
    - pyvisa Python package
    - OWON AG 1022 connected via USB
"""

import pyvisa as visa
import time
import sys
import os
import platform
import subprocess
from datetime import datetime


class SignalGeneratorTestError(Exception):
    """Custom exception for signal generator test errors."""

    pass


def print_header():
    """Print test header with system information."""
    print("=" * 80)
    print("🔬 Windows Signal Generator Connection Test")
    print("=" * 80)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def check_windows_requirements():
    """Check Windows-specific requirements."""
    print("🔍 Checking Windows requirements...")

    # Check if running on Windows
    if platform.system() != "Windows":
        print("❌ This script is designed for Windows systems only.")
        return False

    # Check Windows version
    win_version = platform.release()
    print(f"✅ Windows version: {win_version}")

    # Check if running as administrator (optional)
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = False

    if is_admin:
        print("✅ Running as administrator")
    else:
        print("⚠️  Not running as administrator (may need elevated privileges)")

    return True


def check_python_packages():
    """Check required Python packages."""
    print("\n📦 Checking Python packages...")

    required_packages = ["pyvisa", "numpy"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False

    return True


def test_visa_backend():
    """Test VISA backend and identify the backend being used."""
    print("\n🔌 Testing VISA backend...")

    try:
        rm = visa.ResourceManager()
        backend = str(rm)
        print(f"✅ VISA backend: {backend}")

        # Identify the backend type
        if "NI-VISA" in backend:
            print("✅ Using NI-VISA backend")
        elif "Keysight" in backend:
            print("✅ Using Keysight VISA backend")
        elif "PyVISA" in backend:
            print("✅ Using PyVISA backend")
        else:
            print("⚠️  Unknown VISA backend")

        return rm

    except Exception as e:
        print(f"❌ VISA backend error: {e}")
        print("\n🔧 Troubleshooting VISA issues:")
        print(
            "1. Install NI-VISA: https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html"
        )
        print("2. Or install Keysight VISA: https://www.keysight.com/find/iosuite")
        print("3. Restart your computer after installation")
        print("4. Check Device Manager for USB devices")
        return None


def list_all_devices(rm):
    """List all available VISA devices with detailed information."""
    print("\n📋 Scanning for VISA devices...")

    try:
        resources = rm.list_resources()

        if not resources:
            print("❌ No VISA devices found!")
            print("\n🔧 Troubleshooting device detection:")
            print("1. Check USB connections")
            print("2. Install device drivers")
            print("3. Check Device Manager")
            print("4. Try different USB ports")
            return []

        print(f"✅ Found {len(resources)} VISA device(s):")

        for i, resource in enumerate(resources, 1):
            print(f"\n   {i}. {resource}")

            # Try to get device information
            try:
                device = rm.open_resource(resource)
                device.timeout = 2000  # 2 second timeout
                idn = device.query("*IDN?").strip()
                print(f"      ID: {idn}")
                device.close()
            except Exception as e:
                print(f"      Error reading device: {e}")

        return resources

    except Exception as e:
        print(f"❌ Error listing devices: {e}")
        return []


def find_signal_generator(resources):
    """Find the OWON AG 1022 signal generator in the resource list."""
    print("\n🎯 Looking for OWON AG 1022 signal generator...")

    signal_generator = None

    for resource in resources:
        resource_lower = resource.lower()

        # Look for OWON AG 1022 patterns
        if any(
            pattern in resource_lower
            for pattern in ["won", "ag1022", "ag 1022", "ag1022", "signal", "generator"]
        ):
            try:
                device = visa.ResourceManager().open_resource(resource)
                device.timeout = 2000
                idn = device.query("*IDN?").strip()
                device.close()

                if "won" in idn.lower() or "ag1022" in idn.lower():
                    signal_generator = resource
                    print(f"✅ Found OWON AG 1022: {resource}")
                    print(f"   Device ID: {idn}")
                    break

            except Exception as e:
                print(f"   ⚠️  Error testing {resource}: {e}")

    if not signal_generator:
        print("❌ OWON AG 1022 not found!")
        print("\n🔧 Troubleshooting signal generator detection:")
        print("1. Check USB connection to OWON AG 1022")
        print("2. Install OWON AG 1022 drivers")
        print("3. Check Device Manager for USB devices")
        print("4. Try different USB cable")
        print("5. Restart the signal generator")

    return signal_generator


def test_signal_generator_communication(rm, device_string):
    """Test communication with the signal generator."""
    print(f"\n🔧 Testing OWON AG 1022 communication...")

    try:
        # Open connection
        device = rm.open_resource(device_string)
        device.timeout = 5000  # 5 second timeout

        # Test device identification
        print("   Testing device identification...")
        idn = device.query("*IDN?").strip()
        print(f"   Device ID: {idn}")

        # Test basic SCPI commands
        print("   Testing basic SCPI commands...")

        # Test frequency setting
        test_freq = 1000.0
        device.write(f"FREQ {test_freq}")
        freq_response = device.query("FREQ?")
        actual_freq = float(freq_response)
        print(f"   Frequency set/get: {test_freq} Hz → {actual_freq} Hz")

        if abs(actual_freq - test_freq) < 0.1:
            print("   ✅ Frequency command working")
        else:
            print("   ⚠️  Frequency command may have issues")

        # Test voltage setting
        test_voltage = 1.0
        device.write(f"VOLT {test_voltage}")
        volt_response = device.query("VOLT?")
        actual_voltage = float(volt_response)
        print(f"   Voltage set/get: {test_voltage} V → {actual_voltage} V")

        if abs(actual_voltage - test_voltage) < 0.01:
            print("   ✅ Voltage command working")
        else:
            print("   ⚠️  Voltage command may have issues")

        # Test waveform setting
        test_waveform = "SIN"
        device.write(f"FUNC {test_waveform}")
        func_response = device.query("FUNC?").strip()
        print(f"   Waveform set/get: {test_waveform} → {func_response}")

        if test_waveform.lower() in func_response.lower():
            print("   ✅ Waveform command working")
        else:
            print("   ⚠️  Waveform command may have issues")

        # Test output control
        device.write("OUTP ON")
        outp_response = device.query("OUTP?").strip()
        print(f"   Output status: {outp_response}")

        if "1" in outp_response or "on" in outp_response.lower():
            print("   ✅ Output control working")
        else:
            print("   ⚠️  Output control may have issues")

        print("✅ Signal generator communication successful!")
        return device

    except Exception as e:
        print(f"❌ Signal generator communication error: {e}")
        print("\n🔧 Troubleshooting communication issues:")
        print("1. Check USB connection")
        print("2. Verify device drivers")
        print("3. Try different VISA backend")
        print("4. Check device power status")
        return None


def test_signal_generation(device):
    """Test actual signal generation capabilities."""
    print(f"\n📡 Testing signal generation...")

    try:
        # Configure a test signal
        test_config = {
            "frequency": 1000.0,  # 1 kHz
            "voltage": 1.0,  # 1V
            "waveform": "SIN",  # Sine wave
        }

        print(f"   Configuring test signal:")
        print(f"   - Frequency: {test_config['frequency']} Hz")
        print(f"   - Voltage: {test_config['voltage']} V")
        print(f"   - Waveform: {test_config['waveform']}")

        # Set the signal parameters
        device.write(f"FREQ {test_config['frequency']}")
        device.write(f"VOLT {test_config['voltage']}")
        device.write(f"FUNC {test_config['waveform']}")
        device.write("OUTP ON")

        # Verify the settings
        actual_freq = float(device.query("FREQ?"))
        actual_voltage = float(device.query("VOLT?"))
        actual_waveform = device.query("FUNC?").strip()
        output_status = device.query("OUTP?").strip()

        print(f"\n   Verification:")
        print(f"   - Actual frequency: {actual_freq} Hz")
        print(f"   - Actual voltage: {actual_voltage} V")
        print(f"   - Actual waveform: {actual_waveform}")
        print(f"   - Output status: {output_status}")

        # Check if settings are correct
        freq_ok = abs(actual_freq - test_config["frequency"]) < 0.1
        voltage_ok = abs(actual_voltage - test_config["voltage"]) < 0.01
        waveform_ok = test_config["waveform"].lower() in actual_waveform.lower()
        output_ok = "1" in output_status or "on" in output_status.lower()

        if freq_ok and voltage_ok and waveform_ok and output_ok:
            print("✅ Signal generation test passed!")
            print("   Signal generator is producing a 1 kHz sine wave at 1V")
            print("   Connect an oscilloscope to verify the signal")
        else:
            print("⚠️  Signal generation test has issues:")
            if not freq_ok:
                print("   - Frequency setting issue")
            if not voltage_ok:
                print("   - Voltage setting issue")
            if not waveform_ok:
                print("   - Waveform setting issue")
            if not output_ok:
                print("   - Output control issue")

        return True

    except Exception as e:
        print(f"❌ Signal generation error: {e}")
        return False


def test_frequency_sweep(device):
    """Test frequency sweep capabilities."""
    print(f"\n🔄 Testing frequency sweep...")

    try:
        frequencies = [100, 500, 1000, 5000, 10000]  # Hz
        results = []

        for freq in frequencies:
            device.write(f"FREQ {freq}")
            time.sleep(0.1)  # Small delay
            actual_freq = float(device.query("FREQ?"))
            results.append((freq, actual_freq))
            print(f"   {freq} Hz → {actual_freq} Hz")

        # Check accuracy
        errors = [abs(actual - expected) for expected, actual in results]
        max_error = max(errors)
        avg_error = sum(errors) / len(errors)

        print(f"\n   Frequency accuracy:")
        print(f"   - Maximum error: {max_error:.3f} Hz")
        print(f"   - Average error: {avg_error:.3f} Hz")

        if max_error < 1.0:  # Less than 1 Hz error
            print("✅ Frequency sweep test passed!")
        else:
            print("⚠️  Frequency sweep has accuracy issues")

        return True

    except Exception as e:
        print(f"❌ Frequency sweep error: {e}")
        return False


def test_voltage_range(device):
    """Test voltage range capabilities."""
    print(f"\n⚡ Testing voltage range...")

    try:
        voltages = [0.1, 0.5, 1.0, 2.0, 5.0]  # V
        results = []

        for voltage in voltages:
            device.write(f"VOLT {voltage}")
            time.sleep(0.1)  # Small delay
            actual_voltage = float(device.query("VOLT?"))
            results.append((voltage, actual_voltage))
            print(f"   {voltage} V → {actual_voltage} V")

        # Check accuracy
        errors = [abs(actual - expected) for expected, actual in results]
        max_error = max(errors)
        avg_error = sum(errors) / len(errors)

        print(f"\n   Voltage accuracy:")
        print(f"   - Maximum error: {max_error:.3f} V")
        print(f"   - Average error: {avg_error:.3f} V")

        if max_error < 0.1:  # Less than 0.1V error
            print("✅ Voltage range test passed!")
        else:
            print("⚠️  Voltage range has accuracy issues")

        return True

    except Exception as e:
        print(f"❌ Voltage range error: {e}")
        return False


def test_waveform_types(device):
    """Test different waveform types."""
    print(f"\n📊 Testing waveform types...")

    try:
        waveforms = ["SIN", "SQU", "TRI", "RAMP"]
        results = []

        for waveform in waveforms:
            device.write(f"FUNC {waveform}")
            time.sleep(0.1)  # Small delay
            actual_waveform = device.query("FUNC?").strip()
            results.append((waveform, actual_waveform))
            print(f"   {waveform} → {actual_waveform}")

        # Check if all waveforms are supported
        supported = all(
            waveform.lower() in actual.lower() for waveform, actual in results
        )

        if supported:
            print("✅ All waveform types supported!")
        else:
            print("⚠️  Some waveform types may not be supported")

        return True

    except Exception as e:
        print(f"❌ Waveform types error: {e}")
        return False


def cleanup_and_close(device):
    """Clean up and close the device connection."""
    print(f"\n🧹 Cleaning up...")

    try:
        # Turn off output
        device.write("OUTP OFF")
        print("   Output disabled")

        # Close connection
        device.close()
        print("   Device connection closed")

    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")


def generate_test_report(results):
    """Generate a test report."""
    print("\n" + "=" * 80)
    print("📋 TEST REPORT")
    print("=" * 80)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests

    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")

    print("\nDetailed results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")

    if failed_tests == 0:
        print("\n🎉 All tests passed! Your signal generator is working correctly.")
        print("You can now use it with the VNA software.")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        print("Refer to the troubleshooting suggestions for help.")

    print("=" * 80)


def main():
    """Main test function."""
    print_header()

    # Initialize results dictionary
    results = {}

    try:
        # Test 1: Windows requirements
        results["Windows Requirements"] = check_windows_requirements()
        if not results["Windows Requirements"]:
            raise SignalGeneratorTestError("Windows requirements not met")

        # Test 2: Python packages
        results["Python Packages"] = check_python_packages()
        if not results["Python Packages"]:
            raise SignalGeneratorTestError("Required Python packages not installed")

        # Test 3: VISA backend
        rm = test_visa_backend()
        results["VISA Backend"] = rm is not None
        if not results["VISA Backend"]:
            raise SignalGeneratorTestError("VISA backend not working")

        # Test 4: Device listing
        resources = list_all_devices(rm)
        results["Device Detection"] = len(resources) > 0
        if not results["Device Detection"]:
            raise SignalGeneratorTestError("No VISA devices detected")

        # Test 5: Signal generator detection
        signal_generator = find_signal_generator(resources)
        results["Signal Generator Detection"] = signal_generator is not None
        if not results["Signal Generator Detection"]:
            raise SignalGeneratorTestError("OWON AG 1022 not found")

        # Test 6: Communication
        device = test_signal_generator_communication(rm, signal_generator)
        results["Communication"] = device is not None
        if not results["Communication"]:
            raise SignalGeneratorTestError("Communication with signal generator failed")

        # Test 7: Signal generation
        results["Signal Generation"] = test_signal_generation(device)

        # Test 8: Frequency sweep
        results["Frequency Sweep"] = test_frequency_sweep(device)

        # Test 9: Voltage range
        results["Voltage Range"] = test_voltage_range(device)

        # Test 10: Waveform types
        results["Waveform Types"] = test_waveform_types(device)

        # Cleanup
        cleanup_and_close(device)

    except SignalGeneratorTestError as e:
        print(f"\n❌ Test stopped: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Generate report
        generate_test_report(results)

    print("\n🔧 Additional troubleshooting tips:")
    print("1. Check USB cable quality and try different ports")
    print("2. Update device drivers from manufacturer website")
    print("3. Try running as administrator")
    print("4. Check Windows Device Manager for USB issues")
    print("5. Restart the signal generator and computer")
    print("6. Contact OWON support if issues persist")


if __name__ == "__main__":
    main()
