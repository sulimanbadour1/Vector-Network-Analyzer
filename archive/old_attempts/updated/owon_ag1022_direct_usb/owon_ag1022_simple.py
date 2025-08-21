#!/usr/bin/env python3
"""
Simplified OWON AG 1022 Direct USB Driver
=========================================

This module provides a simplified direct USB interface for the OWON AG 1022
signal generator that focuses on the working functionality.

Based on successful testing:
- VID: 0x5345, PID: 0x1234
- Setting commands work (FREQ, VOLT, FUNC, OUTP)
- Query commands timeout (FREQ?, VOLT?, FUNC?, OUTP?)

Usage:
    from owon_ag1022_simple import OWONAG1022Simple

    # Connect to device
    device = OWONAG1022Simple()

    # Set frequency and voltage
    device.set_frequency(1000)  # 1 kHz
    device.set_voltage(1.0)     # 1V
    device.set_waveform("SIN")  # Sine wave
    device.set_output(True)     # Enable output

    # Clean up
    device.close()
"""

import usb.core
import usb.util
import time
import sys
from typing import Optional, Union


class OWONAG1022SimpleError(Exception):
    """Custom exception for OWON AG 1022 simple driver errors."""

    pass


class OWONAG1022Simple:
    """
    Simplified direct USB driver for OWON AG 1022 signal generator.

    This driver focuses on setting commands that work reliably and
    avoids query commands that timeout.
    """

    # Device identification
    VENDOR_ID = 0x5345
    PRODUCT_ID = 0x1234

    # USB endpoints (from successful testing)
    IN_ENDPOINT = 129
    OUT_ENDPOINT = 3

    # Timeouts
    WRITE_TIMEOUT = 1000  # ms

    # Command delays
    COMMAND_DELAY = 0.1  # seconds
    SETTING_DELAY = 0.2  # seconds

    def __init__(
        self, vendor_id: Optional[int] = None, product_id: Optional[int] = None
    ):
        """
        Initialize the OWON AG 1022 simple driver.

        Args:
            vendor_id: USB vendor ID (default: 0x5345)
            product_id: USB product ID (default: 0x1234)
        """
        self.vendor_id = vendor_id or self.VENDOR_ID
        self.product_id = product_id or self.PRODUCT_ID
        self.device = None
        self.ep_out = None
        self.device_id = None

        # Current settings (we track these since queries don't work)
        self._current_frequency = 1000.0
        self._current_voltage = 1.0
        self._current_waveform = "SIN"
        self._current_output = False

        # Connect to device
        self._connect()

    def _connect(self):
        """Connect to the OWON AG 1022 device."""
        try:
            # Find device
            self.device = usb.core.find(
                idVendor=self.vendor_id, idProduct=self.product_id
            )

            if self.device is None:
                raise OWONAG1022SimpleError(
                    f"OWON AG 1022 not found (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})"
                )

            # Get device configuration
            config = self.device.get_active_configuration()
            interface = config[(0, 0)]

            # Get OUT endpoint (we only need this for setting commands)
            self.ep_out = None
            for endpoint in interface:
                if endpoint.bEndpointAddress == self.OUT_ENDPOINT:
                    self.ep_out = endpoint
                    break

            if not self.ep_out:
                raise OWONAG1022SimpleError("Required USB OUT endpoint not found")

            # Test basic communication with *IDN? (this usually works)
            try:
                self.device_id = self._query("*IDN?")
                print(f"Connected to: {self.device_id}")
            except:
                print("Connected to OWON AG 1022 (device ID query failed)")
                self.device_id = "OWON AG 1022 (Direct USB)"

        except Exception as e:
            raise OWONAG1022SimpleError(f"Failed to connect to device: {e}")

    def _write(self, command: str):
        """
        Send a command to the device.

        Args:
            command: SCPI command to send
        """
        try:
            # Add newline to command
            cmd_bytes = f"{command}\n".encode("ascii")

            # Send command
            self.device.write(self.OUT_ENDPOINT, cmd_bytes, timeout=self.WRITE_TIMEOUT)

            # Small delay for command processing
            time.sleep(self.COMMAND_DELAY)

        except Exception as e:
            raise OWONAG1022SimpleError(f"Failed to send command '{command}': {e}")

    def _query(self, command: str) -> str:
        """
        Send a query command and read the response.
        Only used for *IDN? which usually works.

        Args:
            command: SCPI query command

        Returns:
            Response from device
        """
        try:
            # Send command
            self._write(command)

            # Read response with short timeout
            response = self.device.read(self.IN_ENDPOINT, 64, timeout=500)
            response_str = response.tobytes().decode("ascii", errors="ignore").strip()

            return response_str

        except Exception as e:
            raise OWONAG1022SimpleError(f"Failed to query '{command}': {e}")

    def get_device_id(self) -> str:
        """
        Get device identification.

        Returns:
            Device identification string
        """
        return self.device_id

    def set_frequency(self, frequency: Union[int, float]):
        """
        Set the output frequency.

        Args:
            frequency: Frequency in Hz
        """
        if not (0.1 <= frequency <= 20000000):  # 0.1 Hz to 20 MHz
            raise ValueError("Frequency must be between 0.1 Hz and 20 MHz")

        self._write(f"FREQ {frequency}")
        self._current_frequency = float(frequency)
        time.sleep(self.SETTING_DELAY)

    def get_frequency(self) -> float:
        """
        Get the current output frequency (from cached value).

        Returns:
            Frequency in Hz
        """
        return self._current_frequency

    def set_voltage(self, voltage: Union[int, float]):
        """
        Set the output voltage.

        Args:
            voltage: Voltage in V
        """
        if not (0.01 <= voltage <= 20):  # 0.01V to 20V
            raise ValueError("Voltage must be between 0.01V and 20V")

        self._write(f"VOLT {voltage}")
        self._current_voltage = float(voltage)
        time.sleep(self.SETTING_DELAY)

    def get_voltage(self) -> float:
        """
        Get the current output voltage (from cached value).

        Returns:
            Voltage in V
        """
        return self._current_voltage

    def set_waveform(self, waveform: str):
        """
        Set the output waveform.

        Args:
            waveform: Waveform type ("SIN", "SQU", "TRI", "RAMP")
        """
        valid_waveforms = ["SIN", "SQU", "TRI", "RAMP"]
        if waveform.upper() not in valid_waveforms:
            raise ValueError(f"Waveform must be one of: {valid_waveforms}")

        self._write(f"FUNC {waveform.upper()}")
        self._current_waveform = waveform.upper()
        time.sleep(self.SETTING_DELAY)

    def get_waveform(self) -> str:
        """
        Get the current output waveform (from cached value).

        Returns:
            Waveform type
        """
        return self._current_waveform

    def set_output(self, enabled: bool):
        """
        Enable or disable the output.

        Args:
            enabled: True to enable output, False to disable
        """
        command = "OUTP ON" if enabled else "OUTP OFF"
        self._write(command)
        self._current_output = enabled
        time.sleep(self.SETTING_DELAY)

    def get_output(self) -> bool:
        """
        Get the current output status (from cached value).

        Returns:
            True if output is enabled, False if disabled
        """
        return self._current_output

    def configure_signal(
        self,
        frequency: Union[int, float],
        voltage: Union[int, float],
        waveform: str = "SIN",
        enable_output: bool = True,
    ):
        """
        Configure a complete signal with all parameters.

        Args:
            frequency: Frequency in Hz
            voltage: Voltage in V
            waveform: Waveform type ("SIN", "SQU", "TRI", "RAMP")
            enable_output: Whether to enable output
        """
        print(f"Configuring signal: {frequency} Hz, {voltage} V, {waveform}")

        self.set_frequency(frequency)
        self.set_voltage(voltage)
        self.set_waveform(waveform)
        self.set_output(enable_output)

        print("Signal configuration complete")

    def test_communication(self) -> bool:
        """
        Test basic communication with the device.

        Returns:
            True if communication is working
        """
        try:
            # Test device identification
            print(f"Device ID: {self.device_id}")

            # Test setting commands (these work)
            test_freq = 1000.0
            self.set_frequency(test_freq)
            print(f"Frequency set to: {test_freq} Hz")

            test_voltage = 1.0
            self.set_voltage(test_voltage)
            print(f"Voltage set to: {test_voltage} V")

            test_waveform = "SIN"
            self.set_waveform(test_waveform)
            print(f"Waveform set to: {test_waveform}")

            return True

        except Exception as e:
            print(f"Communication test failed: {e}")
            return False

    def close(self):
        """Close the device connection and clean up."""
        try:
            if self.device:
                # Disable output before closing
                try:
                    self.set_output(False)
                except:
                    pass

                # Release device resources
                usb.util.dispose_resources(self.device)
                print("Device connection closed")

        except Exception as e:
            print(f"Error during cleanup: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def find_owon_devices():
    """
    Find all OWON devices connected via USB.

    Returns:
        List of (vendor_id, product_id, manufacturer, product) tuples
    """
    devices = []

    try:
        all_devices = list(usb.core.find(find_all=True))

        for device in all_devices:
            try:
                vendor_id = device.idVendor
                product_id = device.idProduct

                # Try to get manufacturer and product strings
                try:
                    manufacturer = usb.util.get_string(device, device.iManufacturer)
                    product = usb.util.get_string(device, device.iProduct)

                    if manufacturer and (
                        "owon" in manufacturer.lower() or "won" in manufacturer.lower()
                    ):
                        devices.append((vendor_id, product_id, manufacturer, product))

                except:
                    pass

            except Exception:
                continue

        return devices

    except Exception as e:
        print(f"Error finding devices: {e}")
        return []


if __name__ == "__main__":
    # Test the simplified driver
    print("OWON AG 1022 Simple Driver Test")
    print("=" * 50)

    # Find OWON devices
    print("Scanning for OWON devices...")
    devices = find_owon_devices()

    if not devices:
        print("No OWON devices found")
        sys.exit(1)

    print(f"Found {len(devices)} OWON device(s):")
    for vid, pid, manufacturer, product in devices:
        print(f"  VID: 0x{vid:04x}, PID: 0x{pid:04x}")
        print(f"  Manufacturer: {manufacturer}")
        print(f"  Product: {product}")

    # Test with the first device
    vid, pid, manufacturer, product = devices[0]
    print(f"\nTesting with device: {manufacturer} {product}")

    try:
        # Create driver instance
        device = OWONAG1022Simple(vid, pid)

        # Test communication
        if device.test_communication():
            print("✅ Communication test passed!")

            # Configure a test signal
            device.configure_signal(1000, 1.0, "SIN", True)
            print("✅ Signal configuration test passed!")

        else:
            print("❌ Communication test failed!")

        # Clean up
        device.close()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
