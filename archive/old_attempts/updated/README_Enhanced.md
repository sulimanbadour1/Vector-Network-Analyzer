# Enhanced Vector Network Analyzer for OWON AG 1022 and R&S RTB2004

A professional-grade Vector Network Analyzer implementation using affordable test equipment. This enhanced version provides improved accuracy, better error handling, and comprehensive features for frequency domain analysis.

## 🎯 Overview

This VNA transforms your **OWON AG 1022 signal generator** and **Rohde & Schwarz RTB2004 oscilloscope** into a sophisticated network analyzer capable of:

- **Frequency Response Analysis** - Measure transfer functions of circuits and components
- **Impedance Measurements** - Complex impedance analysis with reference resistance
- **Filter Characterization** - Low-pass, high-pass, band-pass filter analysis
- **Component Testing** - Capacitor, inductor, and resistor characterization
- **Network Analysis** - S-parameter equivalent measurements
- **Real-time Monitoring** - Live measurement display and status updates

## 📋 Requirements

### Hardware
- **Signal Generator**: OWON AG 1022 (or compatible)
- **Oscilloscope**: Rohde & Schwarz RTB2004 (or compatible)
- **Computer**: Windows/Linux/Mac with USB connectivity
- **Cables**: USB cables for instrument communication
- **Test Setup**: BNC cables, breadboard, components for testing

### Software Dependencies
```bash
pip install pyvisa numpy matplotlib keyboard
```

### VISA Backend
- **Windows**: NI-VISA or Keysight VISA
- **Linux**: `libusb` and `pyvisa-py`
- **Mac**: NI-VISA

## 🚀 Installation

1. **Install Python Dependencies**:
   ```bash
   pip install pyvisa numpy matplotlib keyboard
   ```

2. **Install VISA Backend**:
   - **Windows**: Download and install NI-VISA from National Instruments
   - **Linux**: `sudo apt-get install libusb-1.0-0-dev && pip install pyvisa-py`
   - **Mac**: Download NI-VISA from National Instruments

3. **Connect Equipment**:
   - Connect OWON AG 1022 via USB
   - Connect R&S RTB2004 via USB
   - Install device drivers if required

4. **Test Connections**:
   ```bash
   python test_connections.py
   ```

## 📖 Usage

### Basic Usage
```bash
# Default sweep: 1 Hz to 1 MHz, 10 points per decade
python VNA_Enhanced.py

# Custom frequency range
python VNA_Enhanced.py -b 100 -e 10000

# High resolution sweep
python VNA_Enhanced.py -b 1000 -e 100000 -p 20
```

### Command Line Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `-b` | Begin frequency (Hz) | 1 | `-b 100` |
| `-e` | End frequency (Hz) | 1e6 | `-e 10000` |
| `-p` | Points per decade | 10 | `-p 20` |
| `-z` | Impedance measurement (Ω) | 0 | `-z 1000` |
| `-v` | Voltage amplitude (V) | 1.0 | `-v 2.0` |
| `-f` | File prefix | RTB2004 | `-f MyTest` |
| `-n` | No plotting | False | `-n` |
| `-l` | List frequencies only | False | `-l` |
| `-q` | Square wave (vs sine) | False | `-q` |
| `-s` | Linear sweep step (Hz) | Log | `-s 100` |
| `-d` | Debug mode | False | `-d` |
| `-h` | Show help | - | `-h` |

### Example Commands

#### Filter Analysis
```bash
# Low-pass filter characterization
python VNA_Enhanced.py -b 100 -e 100000 -p 30 -f LowPassFilter

# High-pass filter analysis
python VNA_Enhanced.py -b 1000 -e 1000000 -p 25 -f HighPassFilter

# Band-pass filter testing
python VNA_Enhanced.py -b 10000 -e 1000000 -p 40 -f BandPassFilter
```

#### Component Characterization
```bash
# Capacitor impedance measurement
python VNA_Enhanced.py -z 1000 -b 1000 -e 100000 -f CapacitorTest

# Inductor analysis
python VNA_Enhanced.py -z 100 -b 10000 -e 1000000 -f InductorTest

# Resistor network
python VNA_Enhanced.py -z 50 -b 100 -e 1000000 -f ResistorNetwork
```

#### Circuit Validation
```bash
# Amplifier frequency response
python VNA_Enhanced.py -b 10 -e 1000000 -p 20 -v 0.1 -f AmplifierTest

# Oscillator analysis
python VNA_Enhanced.py -b 1000 -e 10000000 -p 30 -f OscillatorTest

# Transmission line
python VNA_Enhanced.py -b 1000000 -e 100000000 -p 25 -f TransmissionLine
```

## 📊 Output Files

### Data Log
- **Filename**: `RTB2004_VNA.log` (or custom prefix)
- **Format**: CSV with comprehensive measurement data
- **Columns**: Sample, Frequency, Mag1, Mag2, Ratio(dB), Phase, Impedance

Example log file:
```
# 2024-01-15 14:30:25
# OWON AG 1022: OWON,AG1022,12345678,1.0.0
# R&S RTB2004: ROHDE&SCHWARZ,RTB2004,98765432,2.1.0
# Analysing from 100.0 Hz to 10000.0 Hz, 20 points/decade; 2.0 decades
#Sample, Frequency,      Mag1,      Mag2, Ratio (dB),   Phase, Impedance
     0,      100.000,    1.00000,    0.95000,    -0.45,     -5.23, 1000.0000 +j0.0000
     1,      125.893,    1.00000,    0.92000,    -0.72,     -7.15, 1000.0000 +j0.0000
```

### Plots
- **Transfer Function**: Magnitude (dB) and Phase (°) vs Frequency
- **Impedance Plot**: Magnitude and Phase of complex impedance (when `-z` is used)

## 🔧 Circuit Connections

### Basic Transfer Function Measurement
```
OWON AG 1022 Output ──→ DUT ──→ RTB2004 CH2
                     │
                     └──→ RTB2004 CH1 (Reference)
```

### Impedance Measurement
```
OWON AG 1022 ──→ R_ref ──→ DUT ──→ RTB2004 CH2
              │
              └──→ RTB2004 CH1
```

### Component Testing Examples

#### Capacitor Test
```
Signal Gen ──→ 1kΩ ──→ Capacitor ──→ CH2
                    │
                    └──→ CH1
```

#### Inductor Test
```
Signal Gen ──→ 100Ω ──→ Inductor ──→ CH2
                    │
                    └──→ CH1
```

#### Filter Test
```
Signal Gen ──→ Filter Circuit ──→ CH2
                    │
                    └──→ CH1
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. Device Not Found
```
VNA Error: OWON AG 1022 not found. Check USB connection and drivers.
```
**Solutions**:
- Check USB connections
- Install device drivers
- Try different USB ports
- Restart instruments
- Check VISA backend installation

#### 2. Communication Errors
```
VNA Error: Cannot connect to R&S RTB2004 oscilloscope
```
**Solutions**:
- Verify instrument is powered on
- Check USB cable quality
- Test with simple SCPI commands
- Update device drivers

#### 3. Measurement Issues
**No Signal**:
- Check output is enabled on signal generator
- Verify cable connections
- Check oscilloscope trigger settings

**Poor Signal Quality**:
- Increase voltage amplitude (`-v` option)
- Check for ground loops
- Use shorter cables
- Verify proper termination

**Phase Errors**:
- Check trigger synchronization
- Verify timebase settings
- Ensure stable signal levels

### Debug Mode
Run with debug flag for detailed output:
```bash
python VNA_Enhanced.py -d -b 1000 -e 10000
```

### Test Connections
Use the test script to verify equipment:
```bash
python test_connections.py
```

## 📈 Performance Optimization

### Speed vs Accuracy Trade-offs
- **High Speed**: Fewer points per decade, lower sample rates
- **High Accuracy**: More points per decade, higher sample rates
- **Recommended**: 10-20 points per decade for most applications

### Memory Usage
- **Default**: 30,000 sample points per acquisition
- **Adjustable**: Modify `MDEPTH` variable in script
- **High Frequency**: Automatically doubles sample rate

### Frequency Range Optimization
- **Low Frequency** (< 1 kHz): Use longer timebase settings
- **Mid Frequency** (1 kHz - 1 MHz): Standard settings
- **High Frequency** (> 1 MHz): Optimized for speed

## 🔬 Applications

### Filter Design and Analysis
```bash
# Design verification
python VNA_Enhanced.py -b 100 -e 100000 -p 30 -f FilterDesign

# Component selection
python VNA_Enhanced.py -z 1000 -b 1000 -e 100000 -f ComponentSelection
```

### Audio Circuit Analysis
```bash
# Audio amplifier
python VNA_Enhanced.py -b 20 -e 20000 -p 25 -v 0.5 -f AudioAmp

# Crossover network
python VNA_Enhanced.py -b 100 -e 10000 -p 30 -f Crossover
```

### RF Circuit Testing
```bash
# Antenna matching
python VNA_Enhanced.py -z 50 -b 1000000 -e 100000000 -f AntennaMatch

# RF filter
python VNA_Enhanced.py -b 10000000 -e 1000000000 -p 20 -f RFFilter
```

### Educational Use
```bash
# Basic concepts
python VNA_Enhanced.py -l -b 100 -e 10000 -p 10

# Hands-on learning
python VNA_Enhanced.py -b 1000 -e 100000 -p 15 -f Learning
```

## 📚 Technical Details

### Measurement Principle
The VNA uses **synchronous detection** (lock-in amplifier technique):
1. Generates test signal at each frequency point
2. Captures waveform data from both channels
3. Correlates with sine/cosine reference signals
4. Extracts magnitude and phase information
5. Calculates transfer function and impedance

### Signal Processing
- **Digital Lock-in**: Uses sine/cosine correlation for noise rejection
- **Multi-cycle Averaging**: Captures multiple cycles for improved accuracy
- **Automatic Scaling**: Adjusts oscilloscope scales based on signal levels
- **Phase Unwrapping**: Centers phase around ±180°

### Accuracy Considerations
- **Frequency Accuracy**: Limited by signal generator specifications
- **Amplitude Accuracy**: Limited by oscilloscope ADC resolution
- **Phase Accuracy**: Depends on trigger stability and synchronization
- **Noise Floor**: Limited by oscilloscope noise performance

## 🔄 Version History

### Enhanced Version (Current)
- Improved error handling and device detection
- Better SCPI command compatibility
- Enhanced measurement accuracy
- Real-time status updates
- Comprehensive logging
- Object-oriented design

### Original Version
- Basic VNA functionality
- Simple command-line interface
- Limited error handling

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional instrument support
- Advanced calibration routines
- S-parameter export
- Real-time measurement display
- Advanced filtering options

## 📄 License

This project is based on the original VNA implementation by John Pigott (Sep 2, 2018) and has been enhanced for compatibility with OWON AG 1022 and R&S RTB2004 equipment.

## 🙏 Acknowledgments

- Original VNA concept and implementation by John Pigott
- SCPI command adaptation for OWON and R&S equipment
- Python VISA community for instrument communication libraries
- Open source community for measurement and analysis tools

---

**Note**: This VNA implementation provides professional-grade network analysis capabilities using affordable test equipment. While not as accurate as commercial VNAs, it offers excellent performance for most engineering applications and educational purposes.

For questions, issues, or feature requests, please refer to the troubleshooting section or create an issue in the project repository.
