# Vector Network Analyzer (VNA) for WON AG 1022 and R&S RTB2004

A Python-based Vector Network Analyzer implementation that uses a OWON AG 1022 signal generator and Rohde & Schwarz RTB2004 oscilloscope to perform frequency domain measurements and network analysis.

## Overview

This project transforms basic test equipment into a sophisticated Vector Network Analyzer capable of:
- **Frequency response analysis** of electronic circuits and components
- **Impedance measurements** with complex impedance calculations
- **Transfer function measurements** (magnitude and phase)
- **Filter characterization** (low-pass, high-pass, band-pass filters)
- **Network analysis** equivalent to S-parameter measurements

## Equipment Requirements

### Hardware
- **Signal Generator**: WON AG 1022
- **Oscilloscope**: Rohde & Schwarz RTB2004
- **Computer**: Windows/Linux/Mac with USB or GPIB connectivity
- **Cables**: USB or GPIB cables for instrument communication

### Software Dependencies
```bash
pip install pyvisa numpy matplotlib keyboard
```

## Installation

1. **Install Python Dependencies**:
   ```bash
   pip install pyvisa numpy matplotlib keyboard
   ```

2. **Install VISA Backend**:
   - **Windows**: Install NI-VISA or Keysight VISA
   - **Linux**: Install `libusb` and `pyvisa-py`
   - **Mac**: Install NI-VISA

3. **Download the Script**:
   - `VNA_Modified.py` - Main VNA script for your equipment
   - `VNA.py` - Original script for reference

## Usage

### Basic Usage
```bash
python VNA_Modified.py
```
This runs a default frequency sweep from 1 Hz to 1 MHz with 10 points per decade.

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `-b` | Begin frequency (Hz) | `-b 100` |
| `-e` | End frequency (Hz) | `-e 10000` |
| `-p` | Points per decade | `-p 20` |
| `-z` | Enable impedance measurement with resistance (Ω) | `-z 1000` |
| `-v` | Voltage amplitude (V) | `-v 2.0` |
| `-n` | Don't plot after data collection | `-n` |
| `-l` | List frequencies only (no measurement) | `-l` |
| `-q` | Use square wave instead of sine wave | `-q` |
| `-f` | File prefix for output | `-f MyTest` |
| `-h` | Show help | `-h` |

### Example Commands

```bash
# Basic frequency sweep
python VNA_Modified.py

# High-resolution sweep from 100 Hz to 10 kHz
python VNA_Modified.py -b 100 -e 10000 -p 50

# Impedance measurement with 1kΩ reference
python VNA_Modified.py -z 1000 -b 1000 -e 100000

# Square wave analysis
python VNA_Modified.py -q -v 5.0

# Data collection without plotting
python VNA_Modified.py -n -f FilterTest
```

## Output Files

### Data Log
- **Filename**: `RTB2004_VNA.log` (or custom prefix)
- **Format**: CSV with columns: Sample, Frequency, Mag1, Mag2, Ratio(dB), Phase, Impedance
- **Example**:
  ```
  # 2024-01-15 14:30
  # Analysing from 100.000000 Hz to 10000.000000 Hz, 20.0 points/decade; 2 decades
  #Sample,  Frequency,      Mag1,      Mag2, Ratio (dB),   Phase
      0,      100.000,    1.00000,    0.95000,    -0.45,     -5.23
      1,      125.893,    1.00000,    0.92000,    -0.72,     -7.15
  ```

### Plots
- **Transfer Function Plot**: Magnitude (dB) and Phase (°) vs Frequency
- **Impedance Plot**: Magnitude and Phase of complex impedance (when `-z` is used)

## Technical Details

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

### Frequency Range
- **Default**: 1 Hz to 1 MHz
- **Maximum**: 25 MHz (adjustable based on WON AG 1022 specifications)
- **Resolution**: Configurable points per decade (default: 10)

### Synchronization
- **Low Frequency** (< 2 MHz): Uses external sync signal
- **High Frequency** (≥ 2 MHz): Uses internal trigger from Channel 1
- **Sample Rate**: Automatically adjusts based on frequency

## Circuit Connections

### Basic Setup
```
WON AG 1022 Output ──→ DUT ──→ RTB2004 CH2
                     │
                     └──→ RTB2004 CH1 (Reference)
```

### Impedance Measurement
```
WON AG 1022 ──→ R_ref ──→ DUT ──→ RTB2004 CH2
              │
              └──→ RTB2004 CH1
```

## Troubleshooting

### Common Issues

1. **Device Not Found**
   ```
   WARNING: Could not find WON AG 1022. Please check connection.
   ```
   - Check USB/GPIB connections
   - Verify device drivers are installed
   - Try different VISA backend

2. **Communication Errors**
   ```
   ERROR: Cannot connect to R&S RTB2004 oscilloscope
   ```
   - Check instrument is powered on
   - Verify correct resource string
   - Test with simple SCPI commands

3. **Measurement Issues**
   - **No Signal**: Check output is enabled on signal generator
   - **Poor SNR**: Increase voltage amplitude or averaging
   - **Phase Errors**: Verify trigger settings and synchronization

### Debug Mode
Run with debug flag for verbose output:
```bash
python VNA_Modified.py -d
```

## Performance Optimization

### Speed vs Accuracy Trade-offs
- **High Speed**: Fewer points per decade, lower sample rates
- **High Accuracy**: More points per decade, higher sample rates
- **Recommended**: 10-20 points per decade for most applications

### Memory Usage
- **Default**: 30,000 sample points per acquisition
- **Adjustable**: Modify `MDEPTH` variable in script
- **High Frequency**: Automatically doubles sample rate

## Applications

### Filter Analysis
```bash
# Low-pass filter characterization
python VNA_Modified.py -b 100 -e 100000 -p 30 -f LowPassFilter
```

### Component Characterization
```bash
# Capacitor impedance measurement
python VNA_Modified.py -z 1000 -b 1000 -e 100000 -f CapacitorTest
```

### Circuit Validation
```bash
# Amplifier frequency response
python VNA_Modified.py -b 10 -e 1000000 -p 20 -v 0.1 -f AmplifierTest
```

## Limitations

1. **Frequency Range**: Limited by WON AG 1022 specifications
2. **Accuracy**: Depends on oscilloscope ADC resolution
3. **Noise**: Limited by oscilloscope noise floor
4. **Calibration**: No built-in calibration routines

## Future Enhancements

- [ ] Automatic calibration routines
- [ ] S-parameter export
- [ ] Real-time measurement display
- [ ] Advanced filtering options
- [ ] Calibration kit support

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the VNA functionality.

## License

This project is based on the original VNA implementation by John Pigott (Sep 2, 2018) and has been modified for compatibility with WON AG 1022 and R&S RTB2004 equipment.

## Acknowledgments

- Original VNA concept and implementation by John Pigott
- SCPI command adaptation for WON and R&S equipment
- Python VISA community for instrument communication libraries

---

**Note**: This VNA implementation provides professional-grade network analysis capabilities using affordable test equipment. While not as accurate as commercial VNAs, it offers excellent performance for most engineering applications and educational purposes.
