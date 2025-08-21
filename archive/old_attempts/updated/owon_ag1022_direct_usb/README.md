# OWON AG 1022 Direct USB Driver

This folder contains a working direct USB driver for the OWON AG 1022 signal generator that appears as "usb device" under "libusb-win32 devices" in Device Manager.

## 🎯 Overview

The OWON AG 1022 signal generator uses a generic USB interface that doesn't work with standard VISA communication. This driver bypasses VISA entirely and communicates directly with the USB device using `pyusb`.

### ✅ What Works
- **Device Detection**: Automatically finds OWON AG 1022 devices
- **Setting Commands**: FREQ, VOLT, FUNC, OUTP (all work reliably)
- **Signal Generation**: Full control over frequency, voltage, waveform, and output
- **VNA Integration**: Ready to use with Vector Network Analyzer software

### ⚠️ Known Limitations
- **Query Commands**: FREQ?, VOLT?, FUNC?, OUTP? timeout (common with this device)
- **Device Tracking**: Driver maintains internal state since queries don't work

## 📁 Files

### Core Driver
- **`owon_ag1022_simple.py`** - Main simplified driver (recommended)
- **`owon_ag1022_driver.py`** - Full driver with query support (may timeout)

### Test Scripts
- **`test_simple_driver.py`** - Test the simplified driver
- **`test_driver.py`** - Test the full driver
- **`test_simple_driver.bat`** - Windows batch file to run tests

### Examples
- **`vna_integration_example.py`** - Example VNA integration

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install pyusb numpy
```

### 2. Test the Driver
```bash
python test_simple_driver.py
```

### 3. Use in Your Code
```python
from owon_ag1022_simple import OWONAG1022Simple

# Connect to device
device = OWONAG1022Simple()

# Configure signal
device.set_frequency(1000)    # 1 kHz
device.set_voltage(1.0)       # 1V
device.set_waveform("SIN")    # Sine wave
device.set_output(True)       # Enable output

# Clean up
device.close()
```

## 🔧 Device Information

Based on successful testing:
- **Vendor ID**: 0x5345
- **Product ID**: 0x1234
- **Device ID**: OWON,AG1022,AG10221814147,V15.6.0
- **USB Endpoints**: IN=129, OUT=3
- **Frequency Range**: 0.1 Hz to 20 MHz
- **Voltage Range**: 0.01V to 20V
- **Waveforms**: SIN, SQU, TRI, RAMP

## 📖 API Reference

### OWONAG1022Simple Class

#### Constructor
```python
OWONAG1022Simple(vendor_id=None, product_id=None)
```
- `vendor_id`: USB vendor ID (default: 0x5345)
- `product_id`: USB product ID (default: 0x1234)

#### Methods

##### Frequency Control
```python
set_frequency(frequency)  # Set frequency in Hz (0.1 to 20M)
get_frequency()          # Get current frequency (cached)
```

##### Voltage Control
```python
set_voltage(voltage)     # Set voltage in V (0.01 to 20)
get_voltage()           # Get current voltage (cached)
```

##### Waveform Control
```python
set_waveform(waveform)   # Set waveform ("SIN", "SQU", "TRI", "RAMP")
get_waveform()          # Get current waveform (cached)
```

##### Output Control
```python
set_output(enabled)     # Enable/disable output
get_output()           # Get output status (cached)
```

##### Utility Methods
```python
configure_signal(freq, volt, waveform, enable_output)  # Configure all at once
test_communication()   # Test basic communication
close()               # Clean up and close connection
```

#### Context Manager
```python
with OWONAG1022Simple() as device:
    device.set_frequency(1000)
    device.set_output(True)
    # Device automatically closed when exiting context
```

## 🔍 Device Detection

### Automatic Detection
```python
from owon_ag1022_simple import find_owon_devices

devices = find_owon_devices()
for vid, pid, manufacturer, product in devices:
    print(f"Found: {manufacturer} {product} (VID: 0x{vid:04x}, PID: 0x{pid:04x})")
```

### Manual Device Selection
```python
# Use specific vendor/product IDs
device = OWONAG1022Simple(vendor_id=0x5345, product_id=0x1234)
```

## 🔌 VNA Integration

### Basic Integration
```python
from owon_ag1022_simple import OWONAG1022Simple

class MyVNA:
    def __init__(self):
        self.signal_gen = OWONAG1022Simple()
    
    def sweep_frequency(self, start_freq, stop_freq, num_points):
        frequencies = np.linspace(start_freq, stop_freq, num_points)
        results = []
        
        for freq in frequencies:
            self.signal_gen.set_frequency(freq)
            # Take VNA measurement here
            # results.append(measurement_data)
        
        return results
```

### Advanced Integration Example
See `vna_integration_example.py` for a complete VNA integration example.

## 🛠️ Troubleshooting

### Device Not Found
1. **Check USB Connection**: Ensure device is connected and powered on
2. **Check Device Manager**: Device should appear under "libusb-win32 devices"
3. **Try Different USB Port**: Some ports may not work properly
4. **Restart Device**: Power cycle the signal generator

### Communication Errors
1. **Check pyusb Installation**: `pip install pyusb`
2. **Check Device Busy**: Close other applications using the device
3. **Check USB Cables**: Try different USB cables
4. **Check Drivers**: Ensure libusb-win32 driver is installed

### Query Timeouts
- **Normal Behavior**: Query commands (FREQ?, VOLT?, etc.) timeout on this device
- **Use Cached Values**: The driver maintains internal state for get_* methods
- **Use Setting Commands**: All set_* commands work reliably

### Permission Errors
1. **Run as Administrator**: Try running Python as administrator
2. **Check USB Permissions**: May need to grant USB access permissions
3. **Close Other Applications**: Ensure no other software is using the device

## 📊 Testing Results

### Successful Tests
- ✅ Device detection and connection
- ✅ Frequency setting (0.1 Hz to 20 MHz)
- ✅ Voltage setting (0.01V to 20V)
- ✅ Waveform selection (SIN, SQU, TRI, RAMP)
- ✅ Output enable/disable
- ✅ VNA integration

### Known Issues
- ❌ Query commands timeout (FREQ?, VOLT?, FUNC?, OUTP?)
- ❌ Some USB ports may not work
- ❌ Device may need restart after connection errors

## 🔄 Version History

### v1.0.0 (Current)
- Initial working driver
- Simplified approach focusing on reliable functionality
- VNA integration example
- Comprehensive testing and documentation

## 📝 License

This driver is provided as-is for educational and research purposes. Use at your own risk.

## 🤝 Contributing

If you find issues or have improvements:
1. Test with your specific OWON AG 1022 model
2. Document any differences in behavior
3. Share your findings and improvements

## 📞 Support

For issues specific to this driver:
1. Check the troubleshooting section above
2. Verify your device appears in Device Manager
3. Test with the provided test scripts
4. Check that pyusb is properly installed

For OWON AG 1022 hardware issues, contact OWON support.
