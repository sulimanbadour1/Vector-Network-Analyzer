# Enhanced VNA with OWON AG 1022 Direct USB

This is a complete Vector Network Analyzer (VNA) implementation that uses the OWON AG 1022 signal generator with direct USB communication, bypassing VISA issues.

## 🎯 Overview

The Enhanced VNA combines:
- **OWON AG 1022 Signal Generator** (Direct USB - no VISA required)
- **R&S RTB2004 Oscilloscope** (VISA communication)
- **Real-time measurement and plotting**
- **Comprehensive data logging**

### ✅ Key Features
- **Direct USB Communication**: Bypasses VISA issues with OWON AG 1022
- **Full VNA Functionality**: Transfer function, impedance measurement, phase analysis
- **Real-time Plotting**: Live visualization of measurement results
- **Flexible Sweep Modes**: Logarithmic and linear frequency sweeps
- **Comprehensive Logging**: Detailed measurement data saved to files
- **User Control**: Press 'q' to stop measurements, keyboard shortcuts

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install pyusb numpy matplotlib pyvisa keyboard
```

### 2. Connect Devices
- **OWON AG 1022**: Connect via USB (appears as "usb device" in Device Manager)
- **R&S RTB2004**: Connect via USB (requires VISA drivers)

### 3. Run the VNA
```bash
# Default sweep: 1 Hz to 1 MHz, 10 points/decade
python VNA_Enhanced_Direct_USB.py

# Custom frequency range
python VNA_Enhanced_Direct_USB.py -b 100 -e 10000

# Impedance measurement with 1kΩ reference
python VNA_Enhanced_Direct_USB.py -z 1000

# High resolution sweep
python VNA_Enhanced_Direct_USB.py -p 20 -v 2.0
```

## 📋 Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `-b <freq>` | Begin frequency in Hz | `-b 100` |
| `-e <freq>` | End frequency in Hz | `-e 10000` |
| `-p <points>` | Points per decade | `-p 20` |
| `-v <volts>` | Voltage amplitude in V | `-v 2.0` |
| `-z <ohms>` | Enable impedance measurement | `-z 1000` |
| `-s <freq>` | Linear sweep step size | `-s 100` |
| `-f <prefix>` | Output file prefix | `-f MyMeasurement` |
| `-n` | No plotting | `-n` |
| `-l` | List frequencies only | `-l` |
| `-q` | Use square wave | `-q` |
| `-d` | Debug mode | `-d` |
| `-h` | Show help | `-h` |

## 🔧 Device Setup

### OWON AG 1022 Signal Generator
- **Connection**: USB (Direct USB driver)
- **Frequency Range**: 0.1 Hz to 20 MHz
- **Voltage Range**: 0.01V to 20V
- **Waveforms**: SIN, SQU, TRI, RAMP
- **Detection**: Automatic via direct USB

### R&S RTB2004 Oscilloscope
- **Connection**: USB (VISA)
- **Channels**: CH1 (input), CH2 (output)
- **Sample Rate**: Up to 500 MS/s
- **Bandwidth**: 20 MHz
- **Detection**: Automatic via VISA

## 📊 Measurement Types

### 1. Transfer Function Measurement
Measures the ratio of output to input signal:
- **Magnitude**: |S21| in dB
- **Phase**: ∠S21 in degrees
- **Frequency Response**: Across specified frequency range

### 2. Impedance Measurement
Calculates complex impedance using reference resistance:
- **Magnitude**: |Z| in Ω
- **Phase**: ∠Z in degrees
- **Real/Imaginary**: Z = R + jX

### 3. Real-time Analysis
- **Live plotting**: Results displayed as measurement progresses
- **Data logging**: All measurements saved to CSV file
- **Progress tracking**: Real-time status updates

## 📁 Output Files

### Log File
- **Format**: CSV with headers
- **Name**: `{prefix}_VNA.log`
- **Contents**: Frequency, magnitudes, phases, impedance data

### Example Log Format
```csv
# 2025-08-21 15:30:45
# OWON AG 1022: OWON,AG1022,AG10221814147,V15.6.0
# R&S RTB2004: ROHDE&SCHWARZ,RTB2004,...
#Sample, Frequency, Mag1, Mag2, Ratio(dB), Phase
     0,      1.000,  1.00000,  0.99000,    -0.09,    -5.71
     1,      1.259,  1.00000,  0.98000,    -0.17,   -11.31
     2,      1.585,  1.00000,  0.97000,    -0.26,   -16.70
```

## 🎨 Plotting Features

### Transfer Function Plot
- **Magnitude**: Red line (dB scale)
- **Phase**: Blue line (degree scale)
- **X-axis**: Frequency (log or linear)
- **Grid**: Automatic scaling

### Impedance Plot (when enabled)
- **Magnitude**: Green line (log scale)
- **Phase**: Purple line (degree scale)
- **X-axis**: Frequency (log or linear)

## 🔍 Troubleshooting

### OWON AG 1022 Issues
1. **Device Not Found**
   - Check USB connection
   - Verify device appears in Device Manager under "libusb-win32 devices"
   - Try different USB ports

2. **Communication Errors**
   - Ensure pyusb is installed: `pip install pyusb`
   - Close other applications using the device
   - Restart the signal generator

### R&S RTB2004 Issues
1. **VISA Connection Failed**
   - Install VISA drivers
   - Check USB connection
   - Verify device appears in VISA resource list

2. **Measurement Errors**
   - Check oscilloscope settings
   - Ensure proper trigger configuration
   - Verify channel connections

### General Issues
1. **Import Errors**
   - Install all required packages: `pip install pyusb numpy matplotlib pyvisa keyboard`
   - Check Python version (3.7+ recommended)

2. **Plotting Issues**
   - Install matplotlib: `pip install matplotlib`
   - Check display settings
   - Use `-n` flag to disable plotting

## 📖 Usage Examples

### Basic Frequency Sweep
```bash
# 1 kHz to 100 kHz, 10 points/decade
python VNA_Enhanced_Direct_USB.py -b 1000 -e 100000
```

### High Resolution Measurement
```bash
# 100 Hz to 10 kHz, 20 points/decade, 2V amplitude
python VNA_Enhanced_Direct_USB.py -b 100 -e 10000 -p 20 -v 2.0
```

### Impedance Measurement
```bash
# Impedance measurement with 1kΩ reference
python VNA_Enhanced_Direct_USB.py -z 1000 -b 1000 -e 100000
```

### Linear Sweep
```bash
# Linear sweep with 100 Hz steps
python VNA_Enhanced_Direct_USB.py -s 100 -b 1000 -e 10000
```

### Data Collection Only
```bash
# Collect data without plotting
python VNA_Enhanced_Direct_USB.py -n -b 1000 -e 100000
```

## 🔧 Advanced Configuration

### Custom File Prefix
```bash
python VNA_Enhanced_Direct_USB.py -f MyMeasurement -b 1000 -e 100000
```

### Debug Mode
```bash
python VNA_Enhanced_Direct_USB.py -d -b 1000 -e 100000
```

### Square Wave Testing
```bash
python VNA_Enhanced_Direct_USB.py -q -b 1000 -e 100000
```

## 📊 Performance Tips

1. **Frequency Range**: Keep within device limits (0.1 Hz - 20 MHz)
2. **Points per Decade**: 10-20 points provides good resolution
3. **Voltage Levels**: Use 1-2V for most measurements
4. **Measurement Time**: Higher resolution = longer measurement time
5. **Data Storage**: Large datasets are automatically saved to log files

## 🆘 Support

### Common Issues
1. **Device detection problems**: Check USB connections and drivers
2. **Measurement errors**: Verify device settings and connections
3. **Plotting issues**: Install matplotlib and check display settings
4. **Performance issues**: Reduce points per decade or frequency range

### Getting Help
1. Run with debug mode: `python VNA_Enhanced_Direct_USB.py -d`
2. Check log files for detailed error information
3. Verify all required packages are installed
4. Test individual components with provided test scripts

## 📝 License

This VNA implementation is provided as-is for educational and research purposes. Use at your own risk.

---

**Your Enhanced VNA with OWON AG 1022 Direct USB is ready for professional measurements! 🎉**
