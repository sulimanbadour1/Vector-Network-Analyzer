@echo off
REM OWON AG 1022 Signal Generator Test for libusb-win32 Driver
REM =========================================================
REM
REM This batch file runs the specialized test for OWON AG 1022
REM signal generators that appear as "usb device" under 
REM "libusb-win32 devices" in Device Manager.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   OWON AG 1022 Signal Generator Test
echo   (libusb-win32 Driver)
echo ========================================
echo.
echo This test is specifically for OWON AG 1022 devices that
echo appear as "usb device" under "libusb-win32 devices"
echo in Windows Device Manager.
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

REM Check if pyvisa is installed
python -c "import pyvisa" >nul 2>&1
if errorlevel 1 (
    echo ERROR: pyvisa package is not installed
    echo Installing pyvisa...
    pip install pyvisa
    if errorlevel 1 (
        echo Failed to install pyvisa. Please install manually:
        echo pip install pyvisa
        echo.
        pause
        exit /b 1
    )
)

echo Required packages found.
echo.

REM Run the libusb test
echo Running libusb signal generator test...
echo.

python test_signal_generator_libusb.py
set test_result=%errorlevel%

echo.
if %test_result% equ 0 (
    echo ========================================
    echo   TEST COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo Your OWON AG 1022 signal generator is working correctly!
    echo The libusb-win32 driver is functioning properly.
    echo You can now use it with the VNA software.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   TEST FAILED
    echo ========================================
    echo.
    echo The libusb signal generator test failed. Please check:
    echo 1. USB connection to OWON AG 1022
    echo 2. Device appears in Device Manager under 'libusb-win32 devices'
    echo 3. Try different USB ports (preferably USB 2.0)
    echo 4. Avoid USB hubs - connect directly to computer
    echo 5. Restart the signal generator
    echo 6. Try running as administrator
    echo.
    echo For detailed testing, run: python test_signal_generator_libusb.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %test_result%
