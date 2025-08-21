#!/usr/bin/env python3
"""
OWON AG 1022 Direct USB Driver
==============================

This module provides a direct USB interface for the OWON AG 1022 signal generator
that appears as "usb device" under "libusb-win32 devices" in Device Manager.

Based on successful testing with:
- VID: 0x5345, PID: 0x1234
- IN endpoint: 129, OUT endpoint: 3
- Device ID: OWON,AG1022,AG10221814147,V15.6.0

Usage:
    from owon_ag1022_driver import OWONAG1022DirectUSB

    # Connect to device
    device = OWONAG1022DirectUSB()

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


class OWONAG1022DirectUSBError(Exception):
    """Custom exception for OWON AG 1022 direct USB errors."""

    pass


class OWONAG1022DirectUSB:
    """
    Direct USB driver for OWON AG 1022 signal generator.

    This driver bypasses VISA and communicates directly with the USB device
    using pyusb. It's specifically designed for devices that appear as
    "usb device" under "libusb-win32 devices" in Device Manager.
    """

    # Device identification
    VENDOR_ID = 0x5345
    PRODUCT_ID = 0x1234

    # USB endpoints (from successful testing)
    IN_ENDPOINT = 129
    OUT_ENDPOINT = 3

    # Timeouts
    WRITE_TIMEOUT = 1000  # ms
    READ_TIMEOUT = 1000  # ms

    # Command delays
    COMMAND_DELAY = 0.1  # seconds
    SETTING_DELAY = 0.2  # seconds

    def __init__(
        self, vendor_id: Optional[int] = None, product_id: Optional[int] = None
    ):
        """
        Initialize the OWON AG 1022 direct USB driver.

        Args:
            vendor_id: USB vendor ID (default: 0x5345)
            product_id: USB product ID (default: 0x1234)
        """
        self.vendor_id = vendor_id or self.VENDOR_ID
        self.product_id = product_id or self.PRODUCT_ID
        self.device = None
        self.ep_in = None
        self.ep_out = None
        self.device_id = None

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
                raise OWONAG1022DirectUSBError(
                    f"OWON AG 1022 not found (VID: 0x{self.vendor_id:04x}, PID: 0x{self.product_id:04x})"
                )

            # Get device configuration
            config = self.device.get_active_configuration()
            interface = config[(0, 0)]

            # Get endpoints
            self.ep_in = None
            self.ep_out = None

            for endpoint in interface:
                if endpoint.bEndpointAddress == self.IN_ENDPOINT:
                    self.ep_in = endpoint
                elif endpoint.bEndpointAddress == self.OUT_ENDPOINT:
                    self.ep_out = endpoint

            if not self.ep_in or not self.ep_out:
                raise OWONAG1022DirectUSBError("Required USB endpoints not found")

            # Get device identification
            self.device_id = self._query("*IDN?")

            print(f"Connected to: {self.device_id}")

        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to connect to device: {e}")

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
            raise OWONAG1022DirectUSBError(f"Failed to send command '{command}': {e}")

    def _read(self, timeout: Optional[int] = None) -> str:
        """
        Read response from the device.

        Args:
            timeout: Read timeout in milliseconds (default: READ_TIMEOUT)

        Returns:
            Response string from device
        """
        try:
            read_timeout = timeout or self.READ_TIMEOUT

            # Read response
            response = self.device.read(self.IN_ENDPOINT, 64, timeout=read_timeout)

            # Convert to string
            response_str = response.tobytes().decode("ascii", errors="ignore").strip()

            return response_str

        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to read response: {e}")

    def _query(self, command: str, timeout: Optional[int] = None) -> str:
        """
        Send a query command and read the response.

        Args:
            command: SCPI query command
            timeout: Read timeout in milliseconds

        Returns:
            Response from device
        """
        self._write(command)
        return self._read(timeout)

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
        time.sleep(self.SETTING_DELAY)

    def get_frequency(self) -> float:
        """
        Get the current output frequency.

        Returns:
            Frequency in Hz
        """
        try:
            response = self._query("FREQ?")
            return float(response)
        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to get frequency: {e}")

    def set_voltage(self, voltage: Union[int, float]):
        """
        Set the output voltage.

        Args:
            voltage: Voltage in V
        """
        if not (0.01 <= voltage <= 20):  # 0.01V to 20V
            raise ValueError("Voltage must be between 0.01V and 20V")

        self._write(f"VOLT {voltage}")
        time.sleep(self.SETTING_DELAY)

    def get_voltage(self) -> float:
        """
        Get the current output voltage.

        Returns:
            Voltage in V
        """
        try:
            response = self._query("VOLT?")
            return float(response)
        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to get voltage: {e}")

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
        time.sleep(self.SETTING_DELAY)

    def get_waveform(self) -> str:
        """
        Get the current output waveform.

        Returns:
            Waveform type
        """
        try:
            response = self._query("FUNC?")
            return response.strip()
        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to get waveform: {e}")

    def set_output(self, enabled: bool):
        """
        Enable or disable the output.

        Args:
            enabled: True to enable output, False to disable
        """
        command = "OUTP ON" if enabled else "OUTP OFF"
        self._write(command)
        time.sleep(self.SETTING_DELAY)

    def get_output(self) -> bool:
        """
        Get the current output status.

        Returns:
            True if output is enabled, False if disabled
        """
        try:
            response = self._query("OUTP?")
            return "1" in response or "on" in response.lower()
        except Exception as e:
            raise OWONAG1022DirectUSBError(f"Failed to get output status: {e}")

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
            idn = self._query("*IDN?")
            print(f"Device ID: {idn}")

            # Test setting and getting frequency
            test_freq = 1000.0
            self.set_frequency(test_freq)
            actual_freq = self.get_frequency()
            print(f"Frequency test: {test_freq} Hz → {actual_freq} Hz")

            # Test setting and getting voltage
            test_voltage = 1.0
            self.set_voltage(test_voltage)
            actual_voltage = self.get_voltage()
            print(f"Voltage test: {test_voltage} V → {actual_voltage} V")

            # Test setting and getting waveform
            test_waveform = "SIN"
            self.set_waveform(test_waveform)
            actual_waveform = self.get_waveform()
            print(f"Waveform test: {test_waveform} → {actual_waveform}")

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
    # Test the driver
    print("OWON AG 1022 Direct USB Driver Test")
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
        device = OWONAG1022DirectUSB(vid, pid)

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
