# Signal Generator Connection Test for Windows

This directory contains comprehensive testing tools for the OWON AG 1022 signal generator on Windows systems.

## Files Overview

- **`test_signal_generator_windows.py`** - Comprehensive test script with detailed diagnostics
- **`quick_signal_test.py`** - Quick connection test for immediate feedback
- **`test_signal_generator.bat`** - Windows batch file for easy execution
- **`README_Signal_Generator_Test.md`** - This documentation file

## Quick Start

### Option 1: Double-click the batch file (Easiest)
1. Connect your OWON AG 1022 signal generator via USB
2. Double-click `test_signal_generator.bat`
3. Follow the on-screen instructions

### Option 2: Run the quick test script
```bash
python quick_signal_test.py
```

### Option 3: Run the comprehensive test
```bash
python test_signal_generator_windows.py
```

## Requirements

### Hardware
- OWON AG 1022 Signal Generator
- USB cable (preferably the original cable)
- Windows 10/11 computer

### Software
- Python 3.7 or higher
- NI-VISA or Keysight VISA drivers
- OWON AG 1022 device drivers
- Python packages: `pyvisa`, `numpy`

## Installation Steps

### 1. Install Python
Download and install Python from [python.org](https://python.org)
- Make sure to check "Add Python to PATH" during installation

### 2. Install VISA Drivers
Choose one of the following:

**Option A: NI-VISA (Recommended)**
- Download from: https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html
- Install and restart your computer

**Option B: Keysight VISA**
- Download from: https://www.keysight.com/find/iosuite
- Install and restart your computer

### 3. Install Python Packages
Open Command Prompt and run:
```bash
pip install pyvisa numpy
```

### 4. Install Device Drivers
- Connect your OWON AG 1022
- Windows should automatically install drivers
- If not, download drivers from OWON website

## Testing Process

### What the Tests Do

1. **System Check**
   - Verify Windows compatibility
   - Check Python installation
   - Verify required packages

2. **VISA Backend Test**
   - Test VISA library functionality
   - Identify which VISA backend is being used
   - Verify communication protocols

3. **Device Detection**
   - Scan for all VISA devices
   - Identify the OWON AG 1022
   - Display device information

4. **Communication Test**
   - Test basic SCPI commands
   - Verify frequency setting
   - Verify voltage setting
   - Verify waveform selection
   - Test output control

5. **Signal Generation Test**
   - Configure a test signal (1 kHz sine wave at 1V)
   - Enable output
   - Verify signal parameters

6. **Advanced Tests** (Comprehensive version only)
   - Frequency sweep accuracy
   - Voltage range testing
   - Waveform type support

### Expected Results

**Successful Test:**
```
🎉 CONNECTION TEST SUCCESSFUL!
Your OWON AG 1022 signal generator is working correctly.
It is now generating a 1 kHz sine wave at 1V.
Connect an oscilloscope to verify the signal.
```

**Failed Test:**
```
❌ TEST FAILED: [error message]
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "No VISA devices found"
**Symptoms:** No devices detected during scan
**Solutions:**
- Check USB connection
- Install VISA drivers
- Try different USB port
- Restart computer after driver installation

#### 2. "OWON AG 1022 not found"
**Symptoms:** VISA devices found but signal generator not identified
**Solutions:**
- Install OWON AG 1022 drivers
- Check Device Manager for USB devices
- Try different USB cable
- Restart the signal generator

#### 3. "Communication error"
**Symptoms:** Device found but commands fail
**Solutions:**
- Check device power status
- Verify USB connection quality
- Try running as administrator
- Update device drivers

#### 4. "VISA backend error"
**Symptoms:** Cannot initialize VISA library
**Solutions:**
- Install NI-VISA or Keysight VISA
- Restart computer after installation
- Check Python pyvisa installation
- Try different VISA backend

#### 5. "Python package missing"
**Symptoms:** Import errors for pyvisa or numpy
**Solutions:**
```bash
pip install pyvisa numpy
```

### Windows-Specific Issues

#### Device Manager Check
1. Open Device Manager (Win+X → Device Manager)
2. Look for "Universal Serial Bus controllers"
3. Check for any devices with warning icons
4. Update drivers for USB devices if needed

#### Administrator Privileges
Some operations may require administrator privileges:
1. Right-click Command Prompt
2. Select "Run as administrator"
3. Navigate to the test directory
4. Run the test script

#### USB Port Issues
- Try different USB ports (preferably USB 2.0)
- Avoid USB hubs
- Use high-quality USB cables
- Check for USB power management issues

## Advanced Testing

### Comprehensive Test Features

The `test_signal_generator_windows.py` script includes:

- **Detailed Diagnostics:** Step-by-step testing with verbose output
- **Accuracy Testing:** Frequency and voltage accuracy verification
- **Range Testing:** Tests across different frequency and voltage ranges
- **Waveform Testing:** Tests different waveform types
- **Error Recovery:** Graceful handling of communication errors
- **Test Report:** Detailed summary of all test results

### Custom Testing

You can modify the test parameters in the scripts:

```python
# In quick_signal_test.py, modify these values:
test_frequency = 1000  # Hz
test_voltage = 1.0     # V
test_waveform = "SIN"  # SIN, SQU, TRI, RAMP
```

## Integration with VNA Software

Once the signal generator test passes, you can use it with the VNA software:

1. **Run VNA with signal generator only:**
   ```bash
   python VNA_Enhanced.py -b 100 -e 10000
   ```

2. **Run VNA with both instruments:**
   ```bash
   python VNA_Enhanced.py -b 100 -e 10000 -z 1000
   ```

## Support

If you continue to have issues:

1. **Check the troubleshooting section above**
2. **Run the comprehensive test for detailed diagnostics**
3. **Check Windows Event Viewer for USB errors**
4. **Contact OWON support for device-specific issues**
5. **Verify VISA installation with vendor tools**

## Technical Details

### SCPI Commands Used

The test scripts use these SCPI commands:

- `*IDN?` - Device identification
- `FREQ <value>` - Set frequency
- `FREQ?` - Query frequency
- `VOLT <value>` - Set voltage
- `VOLT?` - Query voltage
- `FUNC <waveform>` - Set waveform type
- `FUNC?` - Query waveform type
- `OUTP ON/OFF` - Enable/disable output
- `OUTP?` - Query output status

### VISA Resource Formats

The OWON AG 1022 typically appears as:
- `USB0::0x1234::0x5678::12345678::INSTR`
- `ASRL::COM3::INSTR` (if using serial connection)

### Error Codes

Common error codes and meanings:
- `VI_ERROR_RSRC_NFOUND` - Device not found
- `VI_ERROR_TMO` - Communication timeout
- `VI_ERROR_RSRC_BUSY` - Device busy
- `VI_ERROR_INV_OBJECT` - Invalid resource

## Version History

- **v1.0** - Initial release with basic connection testing
- **v1.1** - Added comprehensive diagnostics and error handling
- **v1.2** - Added Windows batch file for easy execution
- **v1.3** - Enhanced troubleshooting and documentation

