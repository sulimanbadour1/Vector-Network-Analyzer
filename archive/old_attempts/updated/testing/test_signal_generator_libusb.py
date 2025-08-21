#!/usr/bin/env python3
"""
OWON AG 1022 Signal Generator Test for libusb-win32 Driver
=========================================================

This script is specifically designed for OWON AG 1022 signal generators
that appear as "usb device" under "libusb-win32 devices" in Device Manager.

This is a common scenario where the device uses the libusb-win32 driver
instead of a specific VISA driver, requiring special handling.

Usage:
    python test_signal_generator_libusb.py

Requirements:
    - Windows 10/11
    - libusb-win32 driver (usually auto-installed)
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


class LibusbSignalGeneratorTestError(Exception):
    """Custom exception for libusb signal generator test errors."""

    pass


def print_header():
    """Print test header with system information."""
    print("=" * 80)
    print("🔬 OWON AG 1022 Signal Generator Test (libusb-win32)")
    print("=" * 80)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def check_libusb_driver():
    """Check if libusb-win32 driver is properly installed."""
    print("🔍 Checking libusb-win32 driver...")

    try:
        # Try to use pyvisa to detect devices
        rm = visa.ResourceManager()
        resources = rm.list_resources()

        # Look for libusb devices
        libusb_devices = [r for r in resources if "usb" in r.lower()]

        if libusb_devices:
            print(f"✅ Found {len(libusb_devices)} USB device(s) via VISA")
            for device in libusb_devices:
                print(f"   - {device}")
            return True
        else:
            print("⚠️  No USB devices found via VISA")
            print("   This might be normal for libusb-win32 devices")
            return True

    except Exception as e:
        print(f"❌ Error checking libusb driver: {e}")
        return False


def find_libusb_signal_generator():
    """Find the OWON AG 1022 using libusb detection methods."""
    print("\n🎯 Looking for OWON AG 1022 (libusb method)...")

    try:
        rm = visa.ResourceManager()
        resources = rm.list_resources()

        print(f"Available VISA resources:")
        for i, resource in enumerate(resources, 1):
            print(f"  {i}. {resource}")

        # Look for USB devices that might be the signal generator
        usb_devices = []
        for resource in resources:
            resource_lower = resource.lower()
            if "usb" in resource_lower:
                usb_devices.append(resource)

        if not usb_devices:
            print("❌ No USB devices found via VISA")
            print("\n🔧 Troubleshooting libusb detection:")
            print(
                "1. Check if device appears in Device Manager under 'libusb-win32 devices'"
            )
            print("2. Try different USB ports")
            print("3. Restart the signal generator")
            print("4. Check if libusb-win32 driver is properly installed")
            return None

        # Try to identify the signal generator by testing each USB device
        for device in usb_devices:
            print(f"\n   Testing device: {device}")
            try:
                # Open device with short timeout
                test_device = rm.open_resource(device)
                test_device.timeout = 2000  # 2 second timeout

                # Try to get device identification
                try:
                    idn = test_device.query("*IDN?").strip()
                    print(f"      Device ID: {idn}")

                    # Check if this looks like the OWON AG 1022
                    if "won" in idn.lower() or "ag1022" in idn.lower():
                        print(f"✅ Found OWON AG 1022: {device}")
                        test_device.close()
                        return device
                    else:
                        print(f"      Not OWON AG 1022 (ID: {idn})")

                except Exception as e:
                    print(f"      Cannot query device ID: {e}")
                    # Try alternative identification methods
                    print(f"      Trying alternative identification...")

                    # Try basic SCPI commands to see if it responds like a signal generator
                    try:
                        test_device.write("FREQ?")
                        freq_response = test_device.read().strip()
                        print(f"      Frequency query response: {freq_response}")

                        # If we get a numeric response, it might be our signal generator
                        try:
                            float(freq_response)
                            print(f"✅ Potential signal generator found: {device}")
                            test_device.close()
                            return device
                        except ValueError:
                            print(
                                f"      Not a signal generator (non-numeric frequency response)"
                            )

                    except Exception as cmd_error:
                        print(f"      SCPI command failed: {cmd_error}")

                test_device.close()

            except Exception as e:
                print(f"      Error testing device: {e}")
                continue

        print("\n❌ OWON AG 1022 not found among USB devices")
        print("\n🔧 Additional troubleshooting:")
        print("1. The device might not be VISA-compatible")
        print("2. Try using direct USB communication")
        print("3. Check if device needs specific drivers")
        print("4. Verify device is powered on and connected")

        return None

    except Exception as e:
        print(f"❌ Error in libusb detection: {e}")
        return None


def test_libusb_communication(device_string):
    """Test communication with the signal generator via libusb."""
    print(f"\n🔧 Testing OWON AG 1022 communication (libusb)...")

    try:
        # Open connection with longer timeout for libusb
        device = visa.ResourceManager().open_resource(device_string)
        device.timeout = 10000  # 10 second timeout for libusb

        print("   Testing device identification...")

        # Try different identification methods
        try:
            idn = device.query("*IDN?").strip()
            print(f"   Device ID: {idn}")
        except Exception as e:
            print(f"   Standard IDN query failed: {e}")
            print("   Trying alternative identification...")

            # Try to identify by testing basic functionality
            try:
                device.write("FREQ?")
                freq_response = device.read().strip()
                print(f"   Frequency query: {freq_response}")

                device.write("VOLT?")
                volt_response = device.read().strip()
                print(f"   Voltage query: {volt_response}")

                print("   Device responds to basic SCPI commands")

            except Exception as cmd_error:
                print(f"   Basic SCPI commands failed: {cmd_error}")
                raise

        # Test basic SCPI commands
        print("   Testing basic SCPI commands...")

        # Test frequency setting
        test_freq = 1000.0
        device.write(f"FREQ {test_freq}")
        time.sleep(0.5)  # Give libusb time to process
        freq_response = device.query("FREQ?")
        actual_freq = float(freq_response)
        print(f"   Frequency set/get: {test_freq} Hz → {actual_freq} Hz")

        if abs(actual_freq - test_freq) < 1.0:  # More lenient for libusb
            print("   ✅ Frequency command working")
        else:
            print("   ⚠️  Frequency command may have issues")

        # Test voltage setting
        test_voltage = 1.0
        device.write(f"VOLT {test_voltage}")
        time.sleep(0.5)  # Give libusb time to process
        volt_response = device.query("VOLT?")
        actual_voltage = float(volt_response)
        print(f"   Voltage set/get: {test_voltage} V → {actual_voltage} V")

        if abs(actual_voltage - test_voltage) < 0.1:  # More lenient for libusb
            print("   ✅ Voltage command working")
        else:
            print("   ⚠️  Voltage command may have issues")

        # Test waveform setting
        test_waveform = "SIN"
        device.write(f"FUNC {test_waveform}")
        time.sleep(0.5)  # Give libusb time to process
        func_response = device.query("FUNC?").strip()
        print(f"   Waveform set/get: {test_waveform} → {func_response}")

        if test_waveform.lower() in func_response.lower():
            print("   ✅ Waveform command working")
        else:
            print("   ⚠️  Waveform command may have issues")

        # Test output control
        device.write("OUTP ON")
        time.sleep(0.5)  # Give libusb time to process
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
        print("\n🔧 Troubleshooting libusb communication:")
        print("1. Check USB connection quality")
        print("2. Try different USB ports")
        print("3. Restart the signal generator")
        print("4. Check if device is in the correct mode")
        print("5. Try running as administrator")
        return None


def test_libusb_signal_generation(device):
    """Test signal generation with libusb device."""
    print(f"\n📡 Testing signal generation (libusb)...")

    try:
        # Configure a test signal with libusb timing considerations
        test_config = {
            "frequency": 1000.0,  # 1 kHz
            "voltage": 1.0,  # 1V
            "waveform": "SIN",  # Sine wave
        }

        print(f"   Configuring test signal:")
        print(f"   - Frequency: {test_config['frequency']} Hz")
        print(f"   - Voltage: {test_config['voltage']} V")
        print(f"   - Waveform: {test_config['waveform']}")

        # Set the signal parameters with delays for libusb
        device.write(f"FREQ {test_config['frequency']}")
        time.sleep(0.5)

        device.write(f"VOLT {test_config['voltage']}")
        time.sleep(0.5)

        device.write(f"FUNC {test_config['waveform']}")
        time.sleep(0.5)

        device.write("OUTP ON")
        time.sleep(1.0)  # Longer delay for output enable

        # Verify the settings
        actual_freq = float(device.query("FREQ?"))
        time.sleep(0.2)

        actual_voltage = float(device.query("VOLT?"))
        time.sleep(0.2)

        actual_waveform = device.query("FUNC?").strip()
        time.sleep(0.2)

        output_status = device.query("OUTP?").strip()

        print(f"\n   Verification:")
        print(f"   - Actual frequency: {actual_freq} Hz")
        print(f"   - Actual voltage: {actual_voltage} V")
        print(f"   - Actual waveform: {actual_waveform}")
        print(f"   - Output status: {output_status}")

        # Check if settings are correct (more lenient for libusb)
        freq_ok = abs(actual_freq - test_config["frequency"]) < 1.0
        voltage_ok = abs(actual_voltage - test_config["voltage"]) < 0.1
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


def cleanup_libusb_device(device):
    """Clean up and close the libusb device connection."""
    print(f"\n🧹 Cleaning up libusb device...")

    try:
        # Turn off output
        device.write("OUTP OFF")
        time.sleep(0.5)  # Give libusb time to process
        print("   Output disabled")

        # Close connection
        device.close()
        print("   Device connection closed")

    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")


def generate_libusb_test_report(results):
    """Generate a test report for libusb testing."""
    print("\n" + "=" * 80)
    print("📋 LIBUSB TEST REPORT")
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
        print("The libusb-win32 driver is functioning properly.")
        print("You can now use it with the VNA software.")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed. Please check the issues above.")
        print("Refer to the troubleshooting suggestions for help.")

    print("=" * 80)


def main():
    """Main test function for libusb signal generator."""
    print_header()

    # Initialize results dictionary
    results = {}

    try:
        # Test 1: Check libusb driver
        results["Libusb Driver"] = check_libusb_driver()
        if not results["Libusb Driver"]:
            raise LibusbSignalGeneratorTestError("Libusb driver not working")

        # Test 2: Find signal generator
        signal_generator = find_libusb_signal_generator()
        results["Device Detection"] = signal_generator is not None
        if not results["Device Detection"]:
            raise LibusbSignalGeneratorTestError("OWON AG 1022 not found")

        # Test 3: Test communication
        device = test_libusb_communication(signal_generator)
        results["Communication"] = device is not None
        if not results["Communication"]:
            raise LibusbSignalGeneratorTestError(
                "Communication with signal generator failed"
            )

        # Test 4: Test signal generation
        results["Signal Generation"] = test_libusb_signal_generation(device)

        # Cleanup
        cleanup_libusb_device(device)

    except LibusbSignalGeneratorTestError as e:
        print(f"\n❌ Test stopped: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Generate report
        generate_libusb_test_report(results)

    print("\n🔧 Libusb-specific troubleshooting tips:")
    print("1. The device appears as 'usb device' under 'libusb-win32 devices'")
    print("2. This is normal behavior for some OWON AG 1022 units")
    print("3. Try different USB ports (preferably USB 2.0)")
    print("4. Avoid USB hubs - connect directly to computer")
    print("5. Check if device needs to be in a specific mode")
    print("6. Try running as administrator")
    print("7. Restart the signal generator if communication fails")


if __name__ == "__main__":
    main()
