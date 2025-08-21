#!/usr/bin/env python3
"""
VNA Integration Example with OWON AG 1022
=========================================

This example shows how to integrate the OWON AG 1022 signal generator
with the VNA software using the simplified direct USB driver.

Usage:
    python vna_integration_example.py
"""

import sys
import time
import numpy as np
from owon_ag1022_simple import OWONAG1022Simple, find_owon_devices


class VNAWithOWONAG1022:
    """
    Example VNA integration class that uses the OWON AG 1022 as the signal source.
    """

    def __init__(self):
        """Initialize the VNA with OWON AG 1022 integration."""
        self.signal_generator = None
        self.frequency_range = None
        self.voltage = 1.0
        self.waveform = "SIN"

        # Connect to signal generator
        self._connect_signal_generator()

    def _connect_signal_generator(self):
        """Connect to the OWON AG 1022 signal generator."""
        print("🔌 Connecting to OWON AG 1022 signal generator...")

        # Find OWON devices
        devices = find_owon_devices()
        if not devices:
            raise RuntimeError("No OWON AG 1022 devices found")

        # Use the first device
        vid, pid, manufacturer, product = devices[0]
        print(f"Found device: {manufacturer} {product}")

        # Create signal generator instance
        self.signal_generator = OWONAG1022Simple(vid, pid)

        # Test communication
        if not self.signal_generator.test_communication():
            raise RuntimeError("Failed to communicate with signal generator")

        print("✅ Signal generator connected successfully")

    def set_frequency_range(self, start_freq: float, stop_freq: float, num_points: int):
        """
        Set the frequency range for VNA measurements.

        Args:
            start_freq: Start frequency in Hz
            stop_freq: Stop frequency in Hz
            num_points: Number of frequency points
        """
        self.frequency_range = np.linspace(start_freq, stop_freq, num_points)
        print(
            f"Frequency range set: {start_freq/1000:.1f} kHz to {stop_freq/1000:.1f} kHz"
        )
        print(f"Number of points: {num_points}")

    def set_voltage(self, voltage: float):
        """
        Set the output voltage.

        Args:
            voltage: Voltage in V
        """
        self.voltage = voltage
        self.signal_generator.set_voltage(voltage)
        print(f"Voltage set to: {voltage} V")

    def set_waveform(self, waveform: str):
        """
        Set the output waveform.

        Args:
            waveform: Waveform type ("SIN", "SQU", "TRI", "RAMP")
        """
        self.waveform = waveform.upper()
        self.signal_generator.set_waveform(self.waveform)
        print(f"Waveform set to: {self.waveform}")

    def enable_output(self, enabled: bool = True):
        """
        Enable or disable the signal generator output.

        Args:
            enabled: True to enable, False to disable
        """
        self.signal_generator.set_output(enabled)
        status = "enabled" if enabled else "disabled"
        print(f"Signal generator output {status}")

    def sweep_frequency(self, callback=None):
        """
        Perform a frequency sweep.

        Args:
            callback: Optional callback function(frequency, data) for each frequency point
        """
        if self.frequency_range is None:
            raise RuntimeError("Frequency range not set")

        print(f"Starting frequency sweep with {len(self.frequency_range)} points...")

        results = []

        for i, frequency in enumerate(self.frequency_range):
            # Set frequency on signal generator
            self.signal_generator.set_frequency(frequency)

            # Simulate measurement (replace with actual VNA measurement)
            # In a real implementation, you would:
            # 1. Wait for signal to stabilize
            # 2. Take VNA measurement
            # 3. Process the data

            time.sleep(0.1)  # Simulate measurement time

            # Simulate measurement data (replace with actual VNA data)
            # This is just an example - replace with real VNA measurements
            magnitude = 1.0 / (
                1.0 + (frequency / 10000.0) ** 2
            )  # Simple low-pass response
            phase = -np.arctan2(frequency, 10000.0) * 180 / np.pi

            data = {
                "frequency": frequency,
                "magnitude": magnitude,
                "phase": phase,
                "real": magnitude * np.cos(phase * np.pi / 180),
                "imaginary": magnitude * np.sin(phase * np.pi / 180),
            }

            results.append(data)

            # Call callback if provided
            if callback:
                callback(frequency, data)

            # Progress indicator
            if (i + 1) % 10 == 0 or i == len(self.frequency_range) - 1:
                progress = (i + 1) / len(self.frequency_range) * 100
                print(
                    f"Progress: {progress:.1f}% ({i + 1}/{len(self.frequency_range)})"
                )

        print("Frequency sweep completed")
        return results

    def measure_at_frequency(self, frequency: float):
        """
        Take a single measurement at a specific frequency.

        Args:
            frequency: Frequency in Hz

        Returns:
            Measurement data dictionary
        """
        # Set frequency
        self.signal_generator.set_frequency(frequency)

        # Wait for signal to stabilize
        time.sleep(0.2)

        # Simulate measurement (replace with actual VNA measurement)
        magnitude = 1.0 / (1.0 + (frequency / 10000.0) ** 2)
        phase = -np.arctan2(frequency, 10000.0) * 180 / np.pi

        data = {
            "frequency": frequency,
            "magnitude": magnitude,
            "phase": phase,
            "real": magnitude * np.cos(phase * np.pi / 180),
            "imaginary": magnitude * np.sin(phase * np.pi / 180),
        }

        return data

    def close(self):
        """Close the VNA integration and clean up."""
        if self.signal_generator:
            self.signal_generator.close()
            print("VNA integration closed")


def measurement_callback(frequency, data):
    """Example callback function for frequency sweep."""
    print(
        f"  {frequency/1000:.1f} kHz: |S21| = {data['magnitude']:.3f}, ∠S21 = {data['phase']:.1f}°"
    )


def main():
    """Main example function."""
    print("VNA Integration Example with OWON AG 1022")
    print("=" * 60)

    try:
        # Create VNA integration
        vna = VNAWithOWONAG1022()

        # Configure measurement parameters
        vna.set_frequency_range(1000, 100000, 50)  # 1 kHz to 100 kHz, 50 points
        vna.set_voltage(1.0)  # 1V output
        vna.set_waveform("SIN")  # Sine wave
        vna.enable_output(True)  # Enable output

        print("\n📊 Starting VNA measurement...")

        # Perform frequency sweep
        results = vna.sweep_frequency(callback=measurement_callback)

        # Display summary
        print(f"\n📋 Measurement Summary:")
        print(f"  Total measurements: {len(results)}")
        print(
            f"  Frequency range: {results[0]['frequency']/1000:.1f} kHz to {results[-1]['frequency']/1000:.1f} kHz"
        )

        # Find maximum and minimum values
        magnitudes = [r["magnitude"] for r in results]
        max_mag = max(magnitudes)
        min_mag = min(magnitudes)
        max_freq = results[magnitudes.index(max_mag)]["frequency"]
        min_freq = results[magnitudes.index(min_mag)]["frequency"]

        print(f"  Maximum magnitude: {max_mag:.3f} at {max_freq/1000:.1f} kHz")
        print(f"  Minimum magnitude: {min_mag:.3f} at {min_freq/1000:.1f} kHz")

        # Example single frequency measurement
        print(f"\n🎯 Single frequency measurement at 10 kHz:")
        single_data = vna.measure_at_frequency(10000)
        print(f"  |S21| = {single_data['magnitude']:.3f}")
        print(f"  ∠S21 = {single_data['phase']:.1f}°")

        # Disable output
        vna.enable_output(False)

        print("\n✅ VNA integration example completed successfully!")

        # Clean up
        vna.close()

    except Exception as e:
        print(f"❌ Example failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
