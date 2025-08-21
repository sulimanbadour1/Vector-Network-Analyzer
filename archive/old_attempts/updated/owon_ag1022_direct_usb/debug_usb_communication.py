#!/usr/bin/env python3
"""
OWON AG 1022 USB Communication Debug
====================================

This script shows the actual USB commands being sent to the device
in real-time, so you can verify that commands are being transmitted.

Usage:
    python debug_usb_communication.py

This will show you exactly what SCPI commands are being sent to the device.
"""

import sys
import time
import usb.core
import usb.util
from owon_ag1022_simple import find_owon_devices


class OWONAG1022Debug:
    """Debug version of OWON AG 1022 driver that shows USB commands."""

    def __init__(self, vendor_id, product_id):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.ep_out = None

        # Find device
        self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)

        if self.device is None:
            raise RuntimeError(
                f"Device not found (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})"
            )

        # Get device configuration
        config = self.device.get_active_configuration()
        interface = config[(0, 0)]

        # Get OUT endpoint
        self.ep_out = None
        for endpoint in interface:
            if endpoint.bEndpointAddress == 3:  # OUT endpoint
                self.ep_out = endpoint
                break

        if not self.ep_out:
            raise RuntimeError("Required USB OUT endpoint not found")

        print(
            f"✅ Connected to device (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})"
        )
        print(f"✅ OUT endpoint: {self.ep_out.bEndpointAddress}")

    def send_command(self, command):
        """Send a command and show it being sent."""
        try:
            # Add newline to command
            cmd_bytes = f"{command}\n".encode("ascii")

            print(f"📤 Sending: '{command}'")
            print(f"   Bytes: {cmd_bytes}")
            print(f"   Length: {len(cmd_bytes)} bytes")

            # Send command
            result = self.device.write(
                self.ep_out.bEndpointAddress, cmd_bytes, timeout=1000
            )

            print(f"   ✅ Sent successfully: {result} bytes written")
            print()

            # Small delay for command processing
            time.sleep(0.1)

        except Exception as e:
            print(f"   ❌ Error sending command: {e}")
            print()

    def test_commands(self):
        """Test various SCPI commands."""
        print("🧪 TESTING USB COMMANDS")
        print("=" * 50)
        print("Watch the output to see commands being sent to the device.")
        print("Each command should show 'Sent successfully' if working.")
        print()

        # Test device identification
        print("1. Testing device identification...")
        self.send_command("*IDN?")

        # Test frequency commands
        print("2. Testing frequency commands...")
        self.send_command("FREQ 1000")
        self.send_command("FREQ 5000")
        self.send_command("FREQ 10000")

        # Test voltage commands
        print("3. Testing voltage commands...")
        self.send_command("VOLT 0.5")
        self.send_command("VOLT 1.0")
        self.send_command("VOLT 2.0")

        # Test waveform commands
        print("4. Testing waveform commands...")
        self.send_command("FUNC SIN")
        self.send_command("FUNC SQU")
        self.send_command("FUNC TRI")
        self.send_command("FUNC RAMP")

        # Test output commands
        print("5. Testing output commands...")
        self.send_command("OUTP ON")
        self.send_command("OUTP OFF")
        self.send_command("OUTP ON")

        # Test query commands (these may timeout, which is normal)
        print("6. Testing query commands (may timeout)...")
        self.send_command("FREQ?")
        self.send_command("VOLT?")
        self.send_command("FUNC?")
        self.send_command("OUTP?")

        print("✅ USB command testing complete!")

    def close(self):
        """Close the device connection."""
        if self.device:
            usb.util.dispose_resources(self.device)
            print("✅ Device connection closed")


def main():
    """Main debug function."""
    print("OWON AG 1022 USB Communication Debug")
    print("=" * 60)
    print("This script will show you exactly what USB commands")
    print("are being sent to your signal generator.")
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

    try:
        # Create debug instance
        debug_device = OWONAG1022Debug(vid, pid)

        # Test commands
        debug_device.test_commands()

        # Clean up
        debug_device.close()

        print("\n🎉 USB communication debug complete!")
        print("=" * 60)
        print("If you saw 'Sent successfully' for all commands,")
        print("then the USB communication is working correctly.")
        print()
        print("Note: Query commands (ending with ?) may timeout,")
        print("which is normal for this device.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
