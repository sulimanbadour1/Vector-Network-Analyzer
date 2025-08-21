@echo off
REM OWON AG 1022 Simplified Driver Test
REM ===================================
REM
REM This batch file tests the simplified OWON AG 1022 direct USB driver.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   OWON AG 1022 Simplified Driver Test
echo ========================================
echo.
echo This will test the simplified direct USB driver for your OWON AG 1022.
echo This version focuses on the working functionality and avoids timeout issues.
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

REM Check if numpy is installed
python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo ERROR: numpy package is not installed
    echo Installing numpy...
    pip install numpy
    if errorlevel 1 (
        echo Failed to install numpy. Please install manually:
        echo pip install numpy
        echo.
        pause
        exit /b 1
    )
)

echo Required packages found.
echo.

REM Run the simplified driver test
echo Running OWON AG 1022 simplified driver test...
echo.

python test_simple_driver.py
set test_result=%errorlevel%

echo.
if %test_result% equ 0 (
    echo ========================================
    echo   TEST COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo Your OWON AG 1022 simplified driver is working correctly!
    echo This driver focuses on the reliable functionality:
    echo - Setting frequency, voltage, and waveform
    echo - Enabling/disabling output
    echo - VNA integration
    echo.
    echo You can now use it with the VNA software.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   TEST FAILED
    echo ========================================
    echo.
    echo The simplified driver test failed. Please check:
    echo 1. USB connection to OWON AG 1022
    echo 2. Device appears in Device Manager under 'libusb-win32 devices'
    echo 3. Try different USB ports
    echo 4. Restart the signal generator
    echo 5. Check that pyusb and numpy are installed
    echo.
    echo For detailed testing, run: python test_simple_driver.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %test_result%
