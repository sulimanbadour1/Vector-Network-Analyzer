# Vector Network Analyzer (VNA)

A Python-based Vector Network Analyzer that combines an OWON AG1022 signal generator with a Rohde & Schwarz RTB2004 oscilloscope to perform frequency response measurements and impedance analysis.

## Overview

This VNA system performs swept frequency measurements by:
1. **Signal Generation**: Using an OWON AG1022 function generator to output sine or square waves
2. **Signal Capture**: Using an R&S RTB2004 oscilloscope to capture both input and output signals
3. **Analysis**: Computing gain, phase, and impedance measurements across the frequency sweep

## Features

- **Frequency Sweep**: Logarithmic or linear frequency sweeps from 1 Hz to 25 MHz
- **Dual Channel Analysis**: Measures CH2/CH1 gain and phase relationships
- **Impedance Measurement**: Optional impedance calculation using a sense resistor
- **Real-time Processing**: Performs FFT-based analysis on captured waveforms
- **Data Logging**: Saves measurement results to CSV format
- **Visualization**: Automatic plotting of frequency response and impedance data
- **Flexible Configuration**: Command-line parameters for sweep settings

## Hardware Requirements

### Signal Generator
- **OWON AG1022** function generator
- USB connection with libusbK/WinUSB driver
- VID: 0x5345, PID: 0x1234

### Oscilloscope
- **Rohde & Schwarz RTB2004** oscilloscope
- USB or LAN connection
- VISA-compatible interface

### Connections
```
AG1022 CH1 ──→ Device Under Test ──→ RTB2004 CH2
                    │
                    └──→ RTB2004 CH1 (reference)
```

For impedance measurements, add a sense resistor:
```
AG1022 CH1 ──→ R_sense ──→ Device Under Test ──→ RTB2004 CH2
                    │
                    └──→ RTB2004 CH1
```

## Software Requirements

### Python Dependencies
```bash
pip install numpy matplotlib pyusb pyvisa
```

### System Dependencies
- **Windows**: NI-VISA or R&S VISA
- **Linux**: libusb-1.0, pyusb
- **USB Drivers**: libusbK/WinUSB for AG1022

## Installation

1. **Install Python dependencies**:
   ```bash
   pip install numpy matplotlib pyusb pyvisa
   ```

2. **Install USB drivers** for AG1022:
   - Download libusbK/WinUSB drivers
   - Install using Zadig or similar tool
   - Ensure AG1022 is recognized as USB device

3. **Install VISA backend**:
   - Windows: Install NI-VISA or R&S VISA
   - Linux: Install libusb-1.0 development packages

4. **Verify connections**:
   - Connect AG1022 via USB
   - Connect RTB2004 via USB/LAN
   - Close any OWON Waveform software

## Usage

### Basic Command Line
```bash
python vna_full.py [options]
```

### Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `-b <freq>` | Start frequency (Hz) | 1.0 Hz | `-b 100` |
| `-e <freq>` | End frequency (Hz) | 1 MHz | `-e 10e6` |
| `-p <points>` | Points per decade (log sweep) | 10 | `-p 20` |
| `-s <step>` | Step size (Hz, linear sweep) | Auto | `-s 1000` |
| `-v <voltage>` | Output voltage (Vpp) | 1.0 V | `-v 2.5` |
| `-z <resistance>` | Sense resistor (Ω) for impedance | 0 (off) | `-z 1000` |
| `-f <prefix>` | Output file prefix | "RG1054Z" | `-f my_measurement` |
| `-q` | Square wave output (default: sine) | Sine | `-q` |
| `-n` | No plots (data only) | Plot enabled | `-n` |
| `-h` | Show help | - | `-h` |

### Usage Examples

#### Basic Frequency Response
```bash
python vna_full.py -b 100 -e 10000 -p 20 -v 1.0
```

#### Impedance Measurement
```bash
python vna_full.py -b 1000 -e 100000 -p 15 -z 1000 -f impedance_test
```

#### High-Frequency Sweep
```bash
python vna_full.py -b 1e6 -e 25e6 -s 100000 -v 2.0 -q
```

#### Quick Test (No Plots)
```bash
python vna_full.py -b 1000 -e 10000 -p 5 -n
```

## Output Files

### Data Log
- **Format**: `{prefix}_VNA.log`
- **Content**: CSV format with frequency, magnitude, phase, and impedance data
- **Columns**: Sample, Frequency, Mag1, Mag2, Ratio(dB), Phase, Z(re,im)

### Example Log Format
```
# 2024-01-15 14:30:25
#Sample,  Frequency,      Mag1,      Mag2, Ratio (dB),   Phase,  Z(re,im)
     0,     1000.000,   1.00000,   0.85000,    -1.42,    45.20,   1000.0000  +0.0000j
     1,     1258.925,   1.00000,   0.75000,    -2.50,    60.15,   1500.0000  +0.0000j
```

## Technical Details

### Signal Processing
1. **Waveform Capture**: Full-resolution acquisition from oscilloscope memory
2. **Synchronization**: Single-shot acquisition with *OPC? polling
3. **Analysis**: FFT-based projection onto sine/cosine basis functions
4. **Calculation**: Complex arithmetic for gain, phase, and impedance

### Frequency Sweep Modes
- **Logarithmic**: Points per decade spacing (default)
- **Linear**: Fixed step size spacing

### Impedance Calculation
When `-z <R_sense>` is specified:
```
Z_load = (V2 / (V1 - V2)) × R_sense
```

### Bandwidth Limitations
- **AG1022**: Maximum 25 MHz output frequency
- **RTB2004**: Depends on model (typically 70-300 MHz)
- **USB**: Real-time data transfer limitations

## Troubleshooting

### Common Issues

#### AG1022 Not Found
```
RuntimeError: AG1022 not found over USB
```
**Solutions**:
- Check USB cable connection
- Install libusbK/WinUSB drivers
- Close OWON Waveform software
- Verify VID/PID in device manager

#### RTB2004 Not Found
```
RuntimeError: RTB2004 not found. VISA resources: [...]
```
**Solutions**:
- Check USB/LAN connection
- Install VISA backend (NI-VISA or R&S VISA)
- Verify oscilloscope is powered on
- Check resource string format

#### USB Communication Errors
```
usb.core.USBError: [Errno 110] Operation timed out
```
**Solutions**:
- Increase timeout values in code
- Check USB cable quality
- Reduce data transfer size
- Close other USB applications

#### Measurement Issues
- **Noisy Data**: Check probe connections and grounding
- **Inconsistent Results**: Ensure stable connections and proper triggering
- **Phase Errors**: Verify channel synchronization and coupling settings

### Debug Mode
Enable verbose output by modifying the code:
```python
# Add debug prints in AG1022USB class
print(f"Writing: {scpi}")
print(f"Response: {response}")
```

## Performance Optimization

### Speed Improvements
- Reduce points per decade for faster sweeps
- Use linear sweep mode for narrow ranges
- Disable plotting with `-n` flag
- Optimize USB timeout values

### Accuracy Improvements
- Increase points per decade for better resolution
- Use appropriate voltage levels for signal-to-noise ratio
- Ensure proper probe calibration
- Check oscilloscope bandwidth settings

## Advanced Usage

### Custom Frequency Lists
Modify the frequency generation section:
```python
# Custom frequency points
freqs = [100, 200, 500, 1000, 2000, 5000, 10000]
```

### Different Waveforms
The code supports sine and square waves. To add other waveforms:
1. Implement new waveform methods in `AG1022USB` class
2. Add command-line options
3. Update sweep loop

### External Triggering
For precise synchronization:
```python
# Configure external trigger
rtb.write("TRIG:SOUR EXT")
rtb.write("TRIG:SLOP POS")
```

## License

This project is provided as-is for educational and research purposes. Please ensure compliance with your local regulations and equipment warranties.

## Contributing

Contributions are welcome! Areas for improvement:
- Support for additional oscilloscope models
- Enhanced error handling and recovery
- GUI interface development
- Advanced analysis features
- Documentation improvements

## References

- OWON AG1022 User Manual
- R&S RTB2004 Programming Manual
- PyUSB Documentation
- PyVISA Documentation
- Vector Network Analysis Theory
