#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive Demo for OWON AG1022 Signal Generator
A user-friendly interface for controlling the AG1022 signal generator

Features:
- Menu-driven interface
- Real-time parameter display
- Quick presets for common waveforms
- Interactive frequency/amplitude adjustment
- Status monitoring
- Error handling with helpful messages

Usage:
    python demo.py

Requirements:
    - OWON AG1022 connected via USB
    - libusbK/WinUSB driver installed
    - OWON Waveform software closed
"""

import sys
import time
import re
import usb.core
import usb.util

# AG1022 USB parameters
VID, PID = 0x5345, 0x1234  # OWON AG series


def parse_number(token: str) -> float:
    """
    Parse numbers with units like: 100, 1k, 10K, 2.5M, 500m, 250u, 1e6, etc.
    """
    s = token.strip().lower()
    s = s.replace("vpp", "").replace("v", "").replace("hz", "").replace("s", "")
    m = re.fullmatch(r"([+-]?\d+(\.\d+)?([eE][+-]?\d+)?)([kmgmun]?)", s)
    if not m:
        raise ValueError(f"Bad number: {token}")
    base = float(m.group(1))
    suf = m.group(4)
    mult = {"": 1, "k": 1e3, "m": 1e-3, "g": 1e9, "u": 1e-6, "n": 1e-9}.get(suf, 1)
    if token.endswith("M") and "e" not in token.lower():
        mult = 1e6
    return base * mult


def fmt_hz(x: float) -> str:
    """Format frequency with appropriate units"""
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if abs(x) >= div:
            return f"{x/div:.6g} {unit}"
    return f"{x:.6g} Hz"


def fmt_v(x: float) -> str:
    """Format voltage with appropriate units"""
    for unit, mult in (("V", 1), ("mV", 1e-3), ("uV", 1e-6)):
        if abs(x) >= mult:
            return f"{x/mult:.6g} {unit}"
    return f"{x:.6g} V"


class AG1022USB:
    def __init__(self, vid=VID, pid=PID, timeout_ms=2000):
        self.dev = usb.core.find(idVendor=vid, idProduct=pid)
        if self.dev is None:
            raise RuntimeError(
                "AG1022 not found over USB. Check cable/driver and CLOSE OWON Waveform."
            )
        self.timeout = timeout_ms
        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        self.intf = self.ep_out = self.ep_in = None
        for intf in cfg:
            outs = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_OUT
            ]
            ins = [
                ep
                for ep in intf
                if usb.util.endpoint_type(ep.bmAttributes)
                == usb.util.ENDPOINT_TYPE_BULK
                and usb.util.endpoint_direction(ep.bEndpointAddress)
                == usb.util.ENDPOINT_IN
            ]
            if outs and ins:
                self.intf, self.ep_out, self.ep_in = intf, outs[0], ins[0]
                break
        if not self.intf:
            raise RuntimeError(
                "No BULK IN/OUT endpoints found. Driver must be libusbK/WinUSB."
            )
        usb.util.claim_interface(self.dev, self.intf.bInterfaceNumber)
        self.current_ch = 1

    def _write(self, scpi: str, pause=0.03):
        self.dev.write(
            self.ep_out.bEndpointAddress,
            (scpi + "\n").encode("ascii"),
            timeout=self.timeout,
        )
        time.sleep(pause)

    def write(self, scpi: str):
        self._write(scpi)
        try:
            data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=50)
            ack = bytes(data).decode("ascii", "ignore").strip()
            if "=?".encode() in data or "NULL".encode() in data:
                raise RuntimeError(f"SCPI error for '{scpi}': {ack}")
        except usb.core.USBError:
            pass

    def query(self, scpi: str) -> str:
        self._write(scpi)
        time.sleep(0.05)
        data = self.dev.read(self.ep_in.bEndpointAddress, 512, timeout=self.timeout)
        return bytes(data).decode("ascii", "ignore").strip()

    def idn(self):
        return self.query("*IDN?")

    def cls(self):
        self.write("*CLS")

    def rst(self):
        self.write("*RST")
        time.sleep(0.2)

    def ch(self, ch: int):
        if ch not in (1, 2):
            raise ValueError("Channel must be 1 or 2.")
        self.write(f":CHAN CH{ch}")
        self.current_ch = ch

    def out(self, ch: int, on: bool = True):
        self.write(f":CHAN:CH{ch} {'ON' if on else 'OFF'}")

    def wave(self, kind: str):
        k = kind.strip().upper()
        mp = {
            "SINE": "SINE",
            "SIN": "SINE",
            "SQU": "SQU",
            "SQUARE": "SQU",
            "RAMP": "RAMP",
            "TRI": "RAMP",
            "DC": "DC",
        }
        if k not in mp:
            raise ValueError("Wave must be sine/square/ramp/dc.")
        self.write(f":FUNC {mp[k]}")

    def freq(self, wave: str, hz: float):
        self.write(f":FUNC:{wave}:FREQ {hz}")

    def ampl(self, wave: str, vpp: float):
        self.write(f":FUNC:{wave}:AMPL {vpp}")

    def offs(self, wave: str, v: float):
        self.write(f":FUNC:{wave}:OFFS {v}")

    def duty(self, pct: float):
        self.write(f":FUNC:SQU:DCYC {pct}")

    def symm(self, pct: float):
        self.write(f":FUNC:RAMP:SYMM {pct}")

    def load(self, wave: str, val: str):
        self.write(f":FUNC:{wave}:LOAD {val}")

    def get_wave(self):
        return self.query(":FUNC?")

    def get_freq(self, wave: str):
        return self.query(f":FUNC:{wave}:FREQ?")

    def get_ampl(self, wave: str):
        return self.query(f":FUNC:{wave}:AMPL?")

    def get_offs(self, wave: str):
        return self.query(f":FUNC:{wave}:OFFS?")

    def get_status(self):
        """Get current status of the generator"""
        try:
            w = self.get_wave().strip().upper()
            wave_key = (
                "SQU"
                if "SQU" in w or "SQUARE" in w
                else (
                    "RAMP"
                    if "RAMP" in w or "TRI" in w
                    else "SINE" if "SINE" in w else "DC"
                )
            )

            freq = float(self.get_freq(wave_key))
            ampl = float(self.get_ampl(wave_key))
            offs = float(self.get_offs(wave_key))

            return {
                "channel": self.current_ch,
                "waveform": w,
                "frequency": freq,
                "amplitude": ampl,
                "offset": offs,
                "wave_key": wave_key,
            }
        except Exception as e:
            return {"error": str(e)}


def print_banner():
    """Print welcome banner"""
    print("=" * 60)
    print("           OWON AG1022 Signal Generator Demo")
    print("=" * 60)
    print("Interactive control interface for AG1022 signal generator")
    print("Type 'help' for available commands")
    print("Type 'quit' to exit")
    print("=" * 60)


def print_main_menu():
    """Print main menu options"""
    print("\n" + "=" * 40)
    print("MAIN MENU")
    print("=" * 40)
    print("1.  Quick Setup")
    print("2.  Channel Control")
    print("3.  Waveform Settings")
    print("4.  Frequency Control")
    print("5.  Amplitude Control")
    print("6.  Advanced Settings")
    print("7.  Status & Monitoring")
    print("8.  Presets")
    print("9.  Help")
    print("0.  Quit")
    print("=" * 40)


def print_quick_setup_menu():
    """Print quick setup menu"""
    print("\n" + "-" * 30)
    print("QUICK SETUP")
    print("-" * 30)
    print("1. Sine Wave (1kHz, 1Vpp)")
    print("2. Square Wave (1kHz, 2Vpp, 50% duty)")
    print("3. Ramp Wave (1kHz, 2Vpp)")
    print("4. DC Output (1V)")
    print("5. Audio Test (440Hz sine)")
    print("6. High Frequency (1MHz sine)")
    print("7. Back to Main Menu")
    print("-" * 30)


def print_channel_menu():
    """Print channel control menu"""
    print("\n" + "-" * 30)
    print("CHANNEL CONTROL")
    print("-" * 30)
    print("1. Select Channel 1")
    print("2. Select Channel 2")
    print("3. Turn Output ON")
    print("4. Turn Output OFF")
    print("5. Toggle Output")
    print("6. Back to Main Menu")
    print("-" * 30)


def print_waveform_menu():
    """Print waveform settings menu"""
    print("\n" + "-" * 30)
    print("WAVEFORM SETTINGS")
    print("-" * 30)
    print("1. Set Sine Wave")
    print("2. Set Square Wave")
    print("3. Set Ramp Wave")
    print("4. Set DC")
    print("5. Set Duty Cycle (Square)")
    print("6. Set Symmetry (Ramp)")
    print("7. Set Load Impedance")
    print("8. Back to Main Menu")
    print("-" * 30)


def print_frequency_menu():
    """Print frequency control menu"""
    print("\n" + "-" * 30)
    print("FREQUENCY CONTROL")
    print("-" * 30)
    print("1. Set Frequency (manual input)")
    print("2. Increase Frequency (×2)")
    print("3. Decrease Frequency (÷2)")
    print("4. Set to 1 Hz")
    print("5. Set to 1 kHz")
    print("6. Set to 1 MHz")
    print("7. Back to Main Menu")
    print("-" * 30)


def print_amplitude_menu():
    """Print amplitude control menu"""
    print("\n" + "-" * 30)
    print("AMPLITUDE CONTROL")
    print("-" * 30)
    print("1. Set Amplitude (manual input)")
    print("2. Increase Amplitude (×1.5)")
    print("3. Decrease Amplitude (÷1.5)")
    print("4. Set to 100 mVpp")
    print("5. Set to 1 Vpp")
    print("6. Set to 5 Vpp")
    print("7. Set DC Offset")
    print("8. Back to Main Menu")
    print("-" * 30)


def print_advanced_menu():
    """Print advanced settings menu"""
    print("\n" + "-" * 30)
    print("ADVANCED SETTINGS")
    print("-" * 30)
    print("1. Reset Generator")
    print("2. Clear Status")
    print("3. Set Load Impedance")
    print("4. Back to Main Menu")
    print("-" * 30)


def print_presets_menu():
    """Print presets menu"""
    print("\n" + "-" * 30)
    print("PRESETS")
    print("-" * 30)
    print("1. Audio Test (440Hz sine)")
    print("2. Clock Signal (1MHz square)")
    print("3. Function Generator (1kHz sine)")
    print("4. High Frequency (10MHz sine)")
    print("5. Low Frequency (1Hz ramp)")
    print("6. Back to Main Menu")
    print("-" * 30)


def get_user_input(prompt="Enter your choice: "):
    """Get user input with error handling"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nExiting...")
        sys.exit(0)


def get_number_input(prompt="Enter value: "):
    """Get numeric input with parsing"""
    while True:
        try:
            value = get_user_input(prompt)
            return parse_number(value)
        except ValueError as e:
            print(f"Invalid number: {e}")
            print("Try formats like: 100, 1k, 10K, 2.5M, 500m, 1e6")


def display_status(gen):
    """Display current generator status"""
    status = gen.get_status()
    if "error" in status:
        print(f"Error reading status: {status['error']}")
        return

    print("\n" + "=" * 50)
    print("CURRENT STATUS")
    print("=" * 50)
    print(f"Channel: {status['channel']}")
    print(f"Waveform: {status['waveform']}")
    print(f"Frequency: {fmt_hz(status['frequency'])}")
    print(f"Amplitude: {fmt_v(status['amplitude'])}pp")
    print(f"Offset: {fmt_v(status['offset'])}")
    print("=" * 50)


def quick_setup_handler(gen):
    """Handle quick setup menu"""
    while True:
        print_quick_setup_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 1000)
                gen.ampl("SINE", 1.0)
                gen.out(1, True)
                print("✓ Set: Sine wave, 1kHz, 1Vpp, Channel 1 ON")

            elif choice == "2":
                gen.ch(1)
                gen.wave("square")
                gen.freq("SQU", 1000)
                gen.ampl("SQU", 2.0)
                gen.duty(50)
                gen.out(1, True)
                print("✓ Set: Square wave, 1kHz, 2Vpp, 50% duty, Channel 1 ON")

            elif choice == "3":
                gen.ch(1)
                gen.wave("ramp")
                gen.freq("RAMP", 1000)
                gen.ampl("RAMP", 2.0)
                gen.out(1, True)
                print("✓ Set: Ramp wave, 1kHz, 2Vpp, Channel 1 ON")

            elif choice == "4":
                gen.ch(1)
                gen.wave("dc")
                gen.ampl("DC", 1.0)
                gen.out(1, True)
                print("✓ Set: DC output, 1V, Channel 1 ON")

            elif choice == "5":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 440)
                gen.ampl("SINE", 1.0)
                gen.out(1, True)
                print("✓ Set: Audio test tone (A4), 440Hz, 1Vpp, Channel 1 ON")

            elif choice == "6":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 1e6)
                gen.ampl("SINE", 1.0)
                gen.out(1, True)
                print("✓ Set: High frequency, 1MHz, 1Vpp, Channel 1 ON")

            elif choice == "7":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def channel_handler(gen):
    """Handle channel control menu"""
    while True:
        print_channel_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                gen.ch(1)
                print("✓ Selected Channel 1")

            elif choice == "2":
                gen.ch(2)
                print("✓ Selected Channel 2")

            elif choice == "3":
                gen.out(gen.current_ch, True)
                print(f"✓ Channel {gen.current_ch} output turned ON")

            elif choice == "4":
                gen.out(gen.current_ch, False)
                print(f"✓ Channel {gen.current_ch} output turned OFF")

            elif choice == "5":
                # Toggle output - first check current status
                status = gen.get_status()
                if "error" not in status:
                    current_on = (
                        gen.query(f":CHAN:CH{gen.current_ch}?").strip().upper() == "ON"
                    )
                    gen.out(gen.current_ch, not current_on)
                    print(
                        f"✓ Channel {gen.current_ch} output toggled to {'ON' if not current_on else 'OFF'}"
                    )

            elif choice == "6":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def waveform_handler(gen):
    """Handle waveform settings menu"""
    while True:
        print_waveform_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                gen.wave("sine")
                print("✓ Set to Sine wave")

            elif choice == "2":
                gen.wave("square")
                print("✓ Set to Square wave")

            elif choice == "3":
                gen.wave("ramp")
                print("✓ Set to Ramp wave")

            elif choice == "4":
                gen.wave("dc")
                print("✓ Set to DC")

            elif choice == "5":
                duty = get_number_input("Enter duty cycle (0-100%): ")
                if 0 <= duty <= 100:
                    gen.duty(duty)
                    print(f"✓ Set duty cycle to {duty}%")
                else:
                    print("Duty cycle must be between 0 and 100%")

            elif choice == "6":
                symm = get_number_input("Enter symmetry (0-100%): ")
                if 0 <= symm <= 100:
                    gen.symm(symm)
                    print(f"✓ Set symmetry to {symm}%")
                else:
                    print("Symmetry must be between 0 and 100%")

            elif choice == "7":
                load = get_user_input("Enter load impedance (OFF/50/100): ").upper()
                if load in ["OFF", "50", "100"]:
                    status = gen.get_status()
                    if "error" not in status:
                        gen.load(status["wave_key"], load)
                        print(f"✓ Set load impedance to {load}")
                else:
                    print("Load must be OFF, 50, or 100")

            elif choice == "8":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def frequency_handler(gen):
    """Handle frequency control menu"""
    while True:
        print_frequency_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                freq = get_number_input("Enter frequency: ")
                status = gen.get_status()
                if "error" not in status:
                    gen.freq(status["wave_key"], freq)
                    print(f"✓ Set frequency to {fmt_hz(freq)}")

            elif choice == "2":
                status = gen.get_status()
                if "error" not in status:
                    new_freq = status["frequency"] * 2
                    gen.freq(status["wave_key"], new_freq)
                    print(f"✓ Increased frequency to {fmt_hz(new_freq)}")

            elif choice == "3":
                status = gen.get_status()
                if "error" not in status:
                    new_freq = status["frequency"] / 2
                    gen.freq(status["wave_key"], new_freq)
                    print(f"✓ Decreased frequency to {fmt_hz(new_freq)}")

            elif choice == "4":
                status = gen.get_status()
                if "error" not in status:
                    gen.freq(status["wave_key"], 1)
                    print("✓ Set frequency to 1 Hz")

            elif choice == "5":
                status = gen.get_status()
                if "error" not in status:
                    gen.freq(status["wave_key"], 1000)
                    print("✓ Set frequency to 1 kHz")

            elif choice == "6":
                status = gen.get_status()
                if "error" not in status:
                    gen.freq(status["wave_key"], 1e6)
                    print("✓ Set frequency to 1 MHz")

            elif choice == "7":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def amplitude_handler(gen):
    """Handle amplitude control menu"""
    while True:
        print_amplitude_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                ampl = get_number_input("Enter amplitude (Vpp): ")
                status = gen.get_status()
                if "error" not in status:
                    gen.ampl(status["wave_key"], ampl)
                    print(f"✓ Set amplitude to {fmt_v(ampl)}pp")

            elif choice == "2":
                status = gen.get_status()
                if "error" not in status:
                    new_ampl = status["amplitude"] * 1.5
                    gen.ampl(status["wave_key"], new_ampl)
                    print(f"✓ Increased amplitude to {fmt_v(new_ampl)}pp")

            elif choice == "3":
                status = gen.get_status()
                if "error" not in status:
                    new_ampl = status["amplitude"] / 1.5
                    gen.ampl(status["wave_key"], new_ampl)
                    print(f"✓ Decreased amplitude to {fmt_v(new_ampl)}pp")

            elif choice == "4":
                status = gen.get_status()
                if "error" not in status:
                    gen.ampl(status["wave_key"], 0.1)
                    print("✓ Set amplitude to 100 mVpp")

            elif choice == "5":
                status = gen.get_status()
                if "error" not in status:
                    gen.ampl(status["wave_key"], 1.0)
                    print("✓ Set amplitude to 1 Vpp")

            elif choice == "6":
                status = gen.get_status()
                if "error" not in status:
                    gen.ampl(status["wave_key"], 5.0)
                    print("✓ Set amplitude to 5 Vpp")

            elif choice == "7":
                offset = get_number_input("Enter DC offset (V): ")
                status = gen.get_status()
                if "error" not in status:
                    gen.offs(status["wave_key"], offset)
                    print(f"✓ Set DC offset to {fmt_v(offset)}")

            elif choice == "8":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def advanced_handler(gen):
    """Handle advanced settings menu"""
    while True:
        print_advanced_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                gen.rst()
                print("✓ Generator reset")

            elif choice == "2":
                gen.cls()
                print("✓ Status cleared")

            elif choice == "3":
                load = get_user_input("Enter load impedance (OFF/50/100): ").upper()
                if load in ["OFF", "50", "100"]:
                    status = gen.get_status()
                    if "error" not in status:
                        gen.load(status["wave_key"], load)
                        print(f"✓ Set load impedance to {load}")
                else:
                    print("Load must be OFF, 50, or 100")

            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def presets_handler(gen):
    """Handle presets menu"""
    while True:
        print_presets_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 440)
                gen.ampl("SINE", 1.0)
                gen.out(1, True)
                print("✓ Audio test preset: 440Hz sine wave (A4 note)")

            elif choice == "2":
                gen.ch(1)
                gen.wave("square")
                gen.freq("SQU", 1e6)
                gen.ampl("SQU", 2.0)
                gen.duty(50)
                gen.out(1, True)
                print("✓ Clock signal preset: 1MHz square wave, 50% duty")

            elif choice == "3":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 1000)
                gen.ampl("SINE", 2.0)
                gen.out(1, True)
                print("✓ Function generator preset: 1kHz sine wave, 2Vpp")

            elif choice == "4":
                gen.ch(1)
                gen.wave("sine")
                gen.freq("SINE", 10e6)
                gen.ampl("SINE", 1.0)
                gen.out(1, True)
                print("✓ High frequency preset: 10MHz sine wave")

            elif choice == "5":
                gen.ch(1)
                gen.wave("ramp")
                gen.freq("RAMP", 1)
                gen.ampl("RAMP", 2.0)
                gen.out(1, True)
                print("✓ Low frequency preset: 1Hz ramp wave")

            elif choice == "6":
                break
            else:
                print("Invalid choice. Please try again.")

        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main demo function"""
    print_banner()

    # Initialize generator
    try:
        gen = AG1022USB()
        print(f"✓ Connected to: {gen.idn()}")
    except Exception as e:
        print(f"❌ Error connecting to AG1022: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure AG1022 is connected via USB")
        print("2. Close OWON Waveform software")
        print("3. Check USB driver installation (libusbK/WinUSB)")
        print("4. Try running as administrator (Windows)")
        sys.exit(1)

    # Main menu loop
    while True:
        print_main_menu()
        choice = get_user_input()

        try:
            if choice == "1":
                quick_setup_handler(gen)
            elif choice == "2":
                channel_handler(gen)
            elif choice == "3":
                waveform_handler(gen)
            elif choice == "4":
                frequency_handler(gen)
            elif choice == "5":
                amplitude_handler(gen)
            elif choice == "6":
                advanced_handler(gen)
            elif choice == "7":
                display_status(gen)
            elif choice == "8":
                presets_handler(gen)
            elif choice == "9":
                print("\n" + "=" * 60)
                print("HELP")
                print("=" * 60)
                print("This demo provides an interactive interface for the OWON AG1022")
                print("signal generator. Use the menu options to control the device.")
                print("\nKey Features:")
                print("- Quick setup presets for common waveforms")
                print("- Real-time parameter adjustment")
                print("- Status monitoring")
                print("- Error handling and validation")
                print("\nHardware Requirements:")
                print("- OWON AG1022 signal generator")
                print("- USB connection")
                print("- libusbK/WinUSB driver")
                print("\nSoftware Requirements:")
                print("- Python 3.6+")
                print("- pyusb library")
                print("- OWON Waveform software closed")
                print("=" * 60)
            elif choice == "0":
                print("\nShutting down generator...")
                try:
                    gen.out(1, False)
                    gen.out(2, False)
                except:
                    pass
                print("✓ Demo completed. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter a number from 0-9.")

        except Exception as e:
            print(f"Error: {e}")
            print("Please try again.")


if __name__ == "__main__":
    main()
