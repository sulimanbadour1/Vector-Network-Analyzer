@echo off
REM OWON AG 1022 Direct USB Driver Test
REM ===================================
REM
REM This batch file tests the OWON AG 1022 direct USB driver.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   OWON AG 1022 Direct USB Driver Test
echo ========================================
echo.
echo This will test the direct USB driver for your OWON AG 1022.
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

REM Run the driver test
echo Running OWON AG 1022 driver test...
echo.

python test_driver.py
set test_result=%errorlevel%

echo.
if %test_result% equ 0 (
    echo ========================================
    echo   TEST COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo Your OWON AG 1022 direct USB driver is working correctly!
    echo You can now use it with the VNA software.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   TEST FAILED
    echo ========================================
    echo.
    echo The driver test failed. Please check:
    echo 1. USB connection to OWON AG 1022
    echo 2. Device appears in Device Manager under 'libusb-win32 devices'
    echo 3. Try different USB ports
    echo 4. Restart the signal generator
    echo.
    echo For detailed testing, run: python test_driver.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %test_result%
