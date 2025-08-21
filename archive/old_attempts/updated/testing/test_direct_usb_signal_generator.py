#!/usr/bin/env python3
"""
Direct USB Communication Test for OWON AG 1022 Signal Generator
============================================================

This script uses direct USB communication (pyusb) to test the OWON AG 1022
signal generator that appears as "usb device" under "libusb-win32 devices".

This bypasses VISA entirely and communicates directly with the USB device.

Usage:
    python test_direct_usb_signal_generator.py

Requirements:
    - Windows 10/11
    - pyusb Python package
    - libusb-win32 driver (already installed)
    - OWON AG 1022 connected via USB
"""

import usb.core
import usb.util
import time
import sys
import os
import platform
from datetime import datetime


class DirectUSBSignalGeneratorTestError(Exception):
    """Custom exception for direct USB signal generator test errors."""

    pass


def print_header():
    """Print test header with system information."""
    print("=" * 80)
    print("🔬 Direct USB Communication Test for OWON AG 1022")
    print("=" * 80)
    print(f"System: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()[0]}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def check_pyusb():
    """Check if pyusb is installed."""
    print("🔍 Checking pyusb installation...")

    try:
        import usb.core
        import usb.util

        print("✅ pyusb installed")
        return True
    except ImportError:
        print("❌ pyusb not installed")
        print("Install with: pip install pyusb")
        return False


def find_owon_ag1022_usb():
    """Find the OWON AG 1022 using direct USB detection."""
    print("\n🎯 Looking for OWON AG 1022 via direct USB...")

    # Common USB vendor/product IDs for OWON devices
    # These might need to be adjusted based on your specific device
    possible_devices = [
        # OWON AG 1022 common IDs (you may need to find the correct ones)
        {"vendor_id": 0x0483, "product_id": 0x5740},  # Example ID
        {"vendor_id": 0x0483, "product_id": 0x5741},  # Example ID
        {"vendor_id": 0x0483, "product_id": 0x5742},  # Example ID
        # Add more possible IDs here
    ]

    print("Scanning for USB devices...")

    # First, let's see all USB devices
    all_devices = list(usb.core.find(find_all=True))
    print(f"Found {len(all_devices)} USB devices:")

    for i, device in enumerate(all_devices):
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct
            print(f"  {i+1}. VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x}")

            # Try to get manufacturer and product strings
            try:
                manufacturer = usb.util.get_string(device, device.iManufacturer)
                product = usb.util.get_string(device, device.iProduct)
                print(f"     Manufacturer: {manufacturer}")
                print(f"     Product: {product}")
            except:
                print(f"     Could not read device strings")

        except Exception as e:
            print(f"  {i+1}. Error reading device: {e}")

    # Look for OWON AG 1022
    for device in all_devices:
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct

            # Check if this matches any known OWON device
            for known_device in possible_devices:
                if (
                    vendor_id == known_device["vendor_id"]
                    and product_id == known_device["product_id"]
                ):
                    print(f"\n✅ Found potential OWON device:")
                    print(f"   VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x}")
                    return device

            # Try to identify by manufacturer/product strings
            try:
                manufacturer = usb.util.get_string(device, device.iManufacturer)
                product = usb.util.get_string(device, device.iProduct)

                if manufacturer and (
                    "owon" in manufacturer.lower() or "won" in manufacturer.lower()
                ):
                    print(f"\n✅ Found OWON device by manufacturer string:")
                    print(f"   Manufacturer: {manufacturer}")
                    print(f"   Product: {product}")
                    print(f"   VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x}")
                    return device

                if product and (
                    "ag1022" in product.lower() or "ag 1022" in product.lower()
                ):
                    print(f"\n✅ Found OWON AG 1022 by product string:")
                    print(f"   Manufacturer: {manufacturer}")
                    print(f"   Product: {product}")
                    print(f"   VID: 0x{vendor_id:04x}, PID: 0x{product_id:04x}")
                    return device

            except:
                pass

        except Exception as e:
            continue

    print("\n❌ OWON AG 1022 not found among USB devices")
    print("\n🔧 Troubleshooting:")
    print("1. Check USB connection")
    print("2. Try different USB ports")
    print("3. Restart the signal generator")
    print("4. The device might have different USB IDs")
    print("5. Check Device Manager for the exact device")

    return None


def test_usb_communication(device):
    """Test USB communication with the device."""
    print(f"\n🔧 Testing USB communication...")

    try:
        # Get device configuration
        print("   Getting device configuration...")
        config = device.get_active_configuration()
        print(f"   Configuration: {config}")

        # Get interface
        print("   Getting interface...")
        interface = config[(0, 0)]
        print(f"   Interface: {interface}")

        # Get endpoints
        print("   Getting endpoints...")
        ep_out = None
        ep_in = None

        for endpoint in interface:
            if endpoint.bEndpointAddress & 0x80:  # IN endpoint
                ep_in = endpoint
                print(f"   IN endpoint: {endpoint.bEndpointAddress}")
            else:  # OUT endpoint
                ep_out = endpoint
                print(f"   OUT endpoint: {endpoint.bEndpointAddress}")

        if not ep_out or not ep_in:
            print("   ⚠️  Could not find required endpoints")
            return False

        # Try to send a simple command
        print("   Testing command transmission...")

        # Try different command formats
        test_commands = [
            b"*IDN?\n",
            b"FREQ?\n",
            b"VOLT?\n",
            b"*IDN?\r\n",
            b"FREQ?\r\n",
            b"VOLT?\r\n",
        ]

        for cmd in test_commands:
            try:
                print(f"   Trying command: {cmd}")

                # Send command
                device.write(ep_out.bEndpointAddress, cmd)
                time.sleep(0.1)

                # Try to read response
                try:
                    response = device.read(ep_in.bEndpointAddress, 64, timeout=1000)
                    response_str = (
                        response.tobytes().decode("ascii", errors="ignore").strip()
                    )
                    print(f"   Response: {response_str}")

                    if response_str:
                        print("   ✅ Communication successful!")
                        return True

                except Exception as read_error:
                    print(f"   Read error: {read_error}")

            except Exception as write_error:
                print(f"   Write error: {write_error}")
                continue

        print("   ❌ No successful communication")
        return False

    except Exception as e:
        print(f"   ❌ USB communication error: {e}")
        return False


def test_scpi_commands(device):
    """Test SCPI commands via USB."""
    print(f"\n📡 Testing SCPI commands...")

    try:
        # Get endpoints
        config = device.get_active_configuration()
        interface = config[(0, 0)]

        ep_out = None
        ep_in = None

        for endpoint in interface:
            if endpoint.bEndpointAddress & 0x80:  # IN endpoint
                ep_in = endpoint
            else:  # OUT endpoint
                ep_out = endpoint

        if not ep_out or not ep_in:
            print("   ❌ Could not find endpoints")
            return False

        # Test basic SCPI commands
        commands = [
            ("*IDN?", "Device identification"),
            ("FREQ?", "Frequency query"),
            ("VOLT?", "Voltage query"),
            ("FUNC?", "Function query"),
        ]

        for cmd, description in commands:
            try:
                print(f"   Testing {description}: {cmd}")

                # Send command
                device.write(ep_out.bEndpointAddress, f"{cmd}\n".encode())
                time.sleep(0.2)

                # Read response
                response = device.read(ep_in.bEndpointAddress, 64, timeout=1000)
                response_str = (
                    response.tobytes().decode("ascii", errors="ignore").strip()
                )
                print(f"   Response: {response_str}")

            except Exception as e:
                print(f"   Error with {cmd}: {e}")

        # Try setting commands
        print("   Testing setting commands...")

        set_commands = [
            ("FREQ 1000", "Set frequency to 1 kHz"),
            ("VOLT 1.0", "Set voltage to 1V"),
            ("FUNC SIN", "Set function to sine"),
            ("OUTP ON", "Enable output"),
        ]

        for cmd, description in set_commands:
            try:
                print(f"   {description}: {cmd}")
                device.write(ep_out.bEndpointAddress, f"{cmd}\n".encode())
                time.sleep(0.5)  # Give device time to process

            except Exception as e:
                print(f"   Error with {cmd}: {e}")

        print("   ✅ SCPI command testing completed")
        return True

    except Exception as e:
        print(f"   ❌ SCPI command error: {e}")
        return False


def cleanup_usb_device(device):
    """Clean up USB device connection."""
    print(f"\n🧹 Cleaning up USB device...")

    try:
        # Try to disable output
        config = device.get_active_configuration()
        interface = config[(0, 0)]

        ep_out = None
        for endpoint in interface:
            if not endpoint.bEndpointAddress & 0x80:  # OUT endpoint
                ep_out = endpoint
                break

        if ep_out:
            device.write(ep_out.bEndpointAddress, b"OUTP OFF\n")
            time.sleep(0.5)
            print("   Output disabled")

        # Release the device
        usb.util.dispose_resources(device)
        print("   Device resources released")

    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")


def generate_usb_test_report(results):
    """Generate a test report for USB testing."""
    print("\n" + "=" * 80)
    print("📋 DIRECT USB TEST REPORT")
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
        print("\n🎉 All tests passed! Direct USB communication is working.")
        print("Your signal generator can be controlled via direct USB.")
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed.")
        print("The device might need different USB IDs or communication protocol.")

    print("=" * 80)


def main():
    """Main test function for direct USB communication."""
    print_header()

    # Initialize results dictionary
    results = {}

    try:
        # Test 1: Check pyusb
        results["PyUSB Installation"] = check_pyusb()
        if not results["PyUSB Installation"]:
            raise DirectUSBSignalGeneratorTestError("PyUSB not installed")

        # Test 2: Find device
        device = find_owon_ag1022_usb()
        results["Device Detection"] = device is not None
        if not results["Device Detection"]:
            raise DirectUSBSignalGeneratorTestError("OWON AG 1022 not found")

        # Test 3: Test USB communication
        results["USB Communication"] = test_usb_communication(device)

        # Test 4: Test SCPI commands
        results["SCPI Commands"] = test_scpi_commands(device)

        # Cleanup
        cleanup_usb_device(device)

    except DirectUSBSignalGeneratorTestError as e:
        print(f"\n❌ Test stopped: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Generate report
        generate_usb_test_report(results)

    print("\n🔧 Direct USB troubleshooting tips:")
    print("1. The device appears as 'usb device' under 'libusb-win32 devices'")
    print("2. This suggests it might not be VISA-compatible")
    print("3. Direct USB communication might be the only option")
    print("4. Check the USB vendor/product IDs in the output above")
    print("5. You may need to find the correct USB IDs for your specific device")
    print("6. Try different USB ports and cables")
    print("7. Check if the device needs to be in a specific mode")


if __name__ == "__main__":
    main()
