@echo off
REM Direct USB Communication Test for OWON AG 1022 Signal Generator
REM =============================================================
REM
REM This batch file runs a direct USB communication test that bypasses
REM VISA entirely and communicates directly with the USB device.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   Direct USB Communication Test
echo   for OWON AG 1022 Signal Generator
echo ========================================
echo.
echo This test bypasses VISA and communicates directly with the USB device.
echo It's designed for devices that appear as "usb device" under
echo "libusb-win32 devices" in Device Manager.
echo.
echo Make sure the device is connected via USB before continuing.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo.
    pause
    exit /b 1
)

echo Python found. Checking for required packages...
echo.

REM Check if pyusb is installed
python -c "import usb.core" >nul 2>&1
if errorlevel 1 (
    echo ERROR: pyusb package is not installed
    echo Installing pyusb...
    pip install pyusb
    if errorlevel 1 (
        echo Failed to install pyusb. Please install manually:
        echo pip install pyusb
        echo.
        pause
        exit /b 1
    )
)

echo Required packages found.
echo.

REM Run the direct USB test
echo Running direct USB communication test...
echo.

python test_direct_usb_signal_generator.py
set test_result=%errorlevel%

echo.
if %test_result% equ 0 (
    echo ========================================
    echo   TEST COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo Direct USB communication is working!
    echo Your signal generator can be controlled via direct USB.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   TEST FAILED
    echo ========================================
    echo.
    echo The direct USB test failed. This could mean:
    echo 1. The device is not VISA-compatible
    echo 2. Different USB vendor/product IDs are needed
    echo 3. The device uses a different communication protocol
    echo 4. The device needs specific drivers or firmware
    echo.
    echo Check the output above for USB device IDs and try:
    echo 1. Different USB ports
    echo 2. Different USB cables
    echo 3. Restart the signal generator
    echo 4. Check Device Manager for device details
    echo.
    echo For detailed testing, run: python test_direct_usb_signal_generator.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %test_result%
