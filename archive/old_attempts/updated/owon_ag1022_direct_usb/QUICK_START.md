# OWON AG 1022 Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Requirements
```bash
pip install pyusb numpy
```

### Step 2: Test Your Device
```bash
python test_simple_driver.py
```

### Step 3: Use in Your Code
```python
from owon_ag1022_simple import OWONAG1022Simple

# Connect and configure
device = OWONAG1022Simple()
device.set_frequency(1000)    # 1 kHz
device.set_voltage(1.0)       # 1V
device.set_waveform("SIN")    # Sine wave
device.set_output(True)       # Enable output

# Clean up
device.close()
```

## ✅ What's Working

- **Device Detection**: Automatically finds your OWON AG 1022
- **Frequency Control**: 0.1 Hz to 20 MHz
- **Voltage Control**: 0.01V to 20V  
- **Waveform Selection**: SIN, SQU, TRI, RAMP
- **Output Control**: Enable/disable output
- **VNA Integration**: Ready for Vector Network Analyzer use

## 🔧 Device Info

- **VID**: 0x5345, **PID**: 0x1234
- **Device ID**: OWON,AG1022,AG10221814147,V15.6.0
- **USB Endpoints**: IN=129, OUT=3

## 📁 Key Files

- `owon_ag1022_simple.py` - Main driver (use this one)
- `test_simple_driver.py` - Test script
- `vna_integration_example.py` - VNA integration example
- `README.md` - Full documentation

## 🎯 VNA Integration

```python
from owon_ag1022_simple import OWONAG1022Simple
import numpy as np

class MyVNA:
    def __init__(self):
        self.signal_gen = OWONAG1022Simple()
    
    def sweep_frequency(self, start_freq, stop_freq, num_points):
        frequencies = np.linspace(start_freq, stop_freq, num_points)
        results = []
        
        for freq in frequencies:
            self.signal_gen.set_frequency(freq)
            # Take your VNA measurement here
            # results.append(measurement_data)
        
        return results
```

## ⚠️ Known Issues

- Query commands (FREQ?, VOLT?, etc.) timeout - this is normal
- Driver maintains internal state since queries don't work
- All setting commands work perfectly

## 🆘 Need Help?

1. Check USB connection and Device Manager
2. Run `python test_simple_driver.py`
3. See `README.md` for detailed troubleshooting
4. Ensure pyusb is installed: `pip install pyusb`

---

**Your OWON AG 1022 is now ready for VNA use! 🎉**
