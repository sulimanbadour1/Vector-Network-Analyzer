# Physical Setup Guide for VNA Testing

This guide provides detailed instructions for connecting your WON AG 1022 signal generator and R&S RTB2004 oscilloscope to test the VNA functionality.

## 🔌 Equipment Connections

### Required Equipment
- **WON AG 1022 Signal Generator**
- **Rohde & Schwarz RTB2004 Oscilloscope**
- **Computer with USB ports**
- **USB cables (Type A to Type B or appropriate for your devices)**
- **BNC cables (for signal connections)**
- **BNC T-connectors (for splitting signals)**
- **Test components (resistors, capacitors for testing)**

### Step-by-Step Connection Guide

#### 1. **USB Connections to Computer**

**WON AG 1022:**
- Connect the USB cable from the signal generator to your computer
- Ensure the signal generator is powered on
- The device should appear in Device Manager (Windows) or `lsusb` (Linux)

**R&S RTB2004:**
- Connect the USB cable from the oscilloscope to your computer
- Ensure the oscilloscope is powered on
- The device should appear in Device Manager (Windows) or `lsusb` (Linux)

#### 2. **Signal Connections**

**Basic Test Setup (No DUT - Direct Connection):**
```
WON AG 1022 Output ──→ BNC Cable ──→ RTB2004 CH1
                     │
                     └──→ BNC Cable ──→ RTB2004 CH2
```

**Detailed Connection Steps:**

1. **Signal Generator Output:**
   - Locate the main output connector on WON AG 1022
   - Connect a BNC cable from the output to a BNC T-connector
   - This will split the signal to both oscilloscope channels

2. **Oscilloscope Channel 1 (Reference):**
   - Connect one output of the T-connector to RTB2004 Channel 1
   - This serves as the reference signal

3. **Oscilloscope Channel 2 (Measurement):**
   - Connect the other output of the T-connector to RTB2004 Channel 2
   - This will measure the same signal (for testing)

#### 3. **With Test Component (Impedance Measurement)**

**Setup for Impedance Measurement:**
```
WON AG 1022 ──→ 1kΩ Resistor ──→ Test Component ──→ RTB2004 CH2
              │
              └──→ RTB2004 CH1 (Reference)
```

**Detailed Steps:**

1. **Reference Resistor:**
   - Connect a 1kΩ resistor between signal generator output and test component
   - Use a breadboard or terminal block for secure connections

2. **Test Component:**
   - Connect your test component (capacitor, inductor, etc.) to the other end of the resistor
   - Connect the other terminal of the component to ground

3. **Oscilloscope Connections:**
   - **CH1**: Connect to the signal generator side of the 1kΩ resistor (reference)
   - **CH2**: Connect to the test component side of the 1kΩ resistor (measurement)

## 🔧 Initial Testing Setup

### Test 1: Basic Functionality Check

**Purpose:** Verify that both instruments can communicate and basic signals work.

**Connections:**
```
WON AG 1022 Output ──→ RTB2004 CH1 (Direct connection)
```

**Test Command:**
```bash
python VNA_Modified.py -b 1000 -e 10000 -p 5 -n
```

**Expected Results:**
- Both instruments should be detected
- Signal generator should output sine wave
- Oscilloscope should display the signal
- No errors in communication

### Test 2: Simple Impedance Measurement

**Purpose:** Test impedance measurement with a known component.

**Connections:**
```
WON AG 1022 ──→ 1kΩ ──→ 100nF Capacitor ──→ RTB2004 CH2
              │
              └──→ RTB2004 CH1
```

**Test Command:**
```bash
python VNA_Modified.py -b 1000 -e 100000 -p 10 -z 1000 -v 1.0
```

**Expected Results:**
- Capacitive behavior (decreasing impedance with frequency)
- Phase angle around -90° at low frequencies
- Smooth curves without noise

## 📊 Verification Steps

### Step 1: Check Device Detection

Run this command to verify devices are detected:
```bash
python -c "import visa; rm = visa.ResourceManager(); print('Available devices:'); [print(f'  {i+1}. {dev}') for i, dev in enumerate(rm.list_resources())]"
```

**Expected Output:**
```
Available devices:
  1. USB0::0xXXXX::0xXXXX::WON_AG1022::INSTR
  2. USB0::0xXXXX::0xXXXX::RTB2004::INSTR
```

### Step 2: Test Basic Communication

Create a simple test script:
```python
import visa

# Test WON AG 1022
try:
    rm = visa.ResourceManager()
    won = rm.open_resource('USB0::0xXXXX::0xXXXX::WON_AG1022::INSTR')
    print("WON AG 1022:", won.query("*IDN?"))
    won.write("FREQ 1000")
    won.write("VOLT 1.0")
    won.write("OUTP ON")
    print("✅ WON AG 1022 communication successful")
except Exception as e:
    print(f"❌ WON AG 1022 error: {e}")

# Test RTB2004
try:
    rtb = rm.open_resource('USB0::0xXXXX::0xXXXX::RTB2004::INSTR')
    print("RTB2004:", rtb.query("*IDN?"))
    print("✅ RTB2004 communication successful")
except Exception as e:
    print(f"❌ RTB2004 error: {e}")
```

### Step 3: Visual Verification

**On the Oscilloscope:**
1. **Channel 1**: Should show a clean sine wave
2. **Channel 2**: Should show the same signal (for direct connection test)
3. **Trigger**: Should be stable and synchronized
4. **Amplitude**: Should be around 1V peak-to-peak

**On the Signal Generator:**
1. **Frequency display**: Should show the test frequency
2. **Output indicator**: Should show output is enabled
3. **Amplitude display**: Should show 1V

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. **Device Not Found**
```
WARNING: Could not find WON AG 1022
```

**Solutions:**
- Check USB cable connections
- Verify devices are powered on
- Install/update VISA drivers
- Try different USB ports
- Check Device Manager for device recognition

#### 2. **Communication Errors**
```
ERROR: Cannot connect to R&S RTB2004
```

**Solutions:**
- Verify correct resource string
- Check if device is in use by another application
- Restart the instrument
- Try different VISA backend

#### 3. **No Signal on Oscilloscope**
- Check BNC cable connections
- Verify signal generator output is enabled
- Check oscilloscope trigger settings
- Ensure proper ground connections

#### 4. **Poor Signal Quality**
- Use shorter, higher-quality cables
- Check for loose connections
- Verify proper impedance matching
- Reduce frequency range for testing

#### 5. **Phase Measurement Errors**
- Ensure proper trigger synchronization
- Check for ground loops
- Verify both channels are properly connected
- Use identical cables for both channels

### Debug Commands

**Test with minimal parameters:**
```bash
python VNA_Modified.py -b 1000 -e 2000 -p 3 -n -d
```

**List available devices:**
```bash
python -c "import visa; rm = visa.ResourceManager(); print(rm.list_resources())"
```

**Test individual instrument:**
```bash
python -c "import visa; rm = visa.ResourceManager(); dev = rm.open_resource('YOUR_DEVICE_STRING'); print(dev.query('*IDN?'))"
```

## 📋 Pre-Test Checklist

Before running the VNA:

- [ ] **Hardware:**
  - [ ] WON AG 1022 powered on and connected via USB
  - [ ] R&S RTB2004 powered on and connected via USB
  - [ ] BNC cables properly connected
  - [ ] Test components ready (if measuring impedance)
  - [ ] Ground connections secure

- [ ] **Software:**
  - [ ] VISA drivers installed
  - [ ] Python dependencies installed (`pyvisa`, `numpy`, `matplotlib`)
  - [ ] VNA_Modified.py in current directory
  - [ ] No other applications using the instruments

- [ ] **Verification:**
  - [ ] Devices appear in VISA resource list
  - [ ] Basic communication test passes
  - [ ] Oscilloscope displays signal
  - [ ] Signal generator output enabled

## 🎯 Success Indicators

Your setup is working correctly if:

1. ✅ **Device Detection**: Both instruments are found automatically
2. ✅ **Communication**: No error messages during connection
3. ✅ **Signal Display**: Oscilloscope shows clean sine wave
4. ✅ **Measurement**: VNA completes without errors
5. ✅ **Data Quality**: Smooth curves without excessive noise
6. ✅ **Phase Accuracy**: Phase measurements are reasonable

## 🔄 Testing Sequence

**Recommended testing order:**

1. **Basic connectivity test** (direct connection)
2. **Simple impedance measurement** (known capacitor)
3. **Frequency sweep test** (wider range)
4. **High-resolution measurement** (more points per decade)

**Start with simple tests and gradually increase complexity:**

```bash
# Test 1: Basic functionality
python VNA_Modified.py -b 1000 -e 2000 -p 3 -n

# Test 2: Simple impedance
python VNA_Modified.py -b 1000 -e 10000 -p 10 -z 1000

# Test 3: Wider range
python VNA_Modified.py -b 100 -e 100000 -p 20 -z 1000

# Test 4: High resolution
python VNA_Modified.py -b 10 -e 1000000 -p 30 -z 1000
```

---

**Follow this guide step-by-step, and you'll have a working VNA setup! 🎉**
