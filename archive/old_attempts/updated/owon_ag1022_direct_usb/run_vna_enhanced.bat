@echo off
REM Enhanced VNA with OWON AG 1022 Direct USB
REM =========================================
REM
REM This batch file runs the enhanced VNA that uses the OWON AG 1022
REM direct USB driver instead of VISA for the signal generator.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   Enhanced VNA with OWON AG 1022
echo   Direct USB Support
echo ========================================
echo.
echo This VNA uses:
echo - OWON AG 1022 Signal Generator (Direct USB)
echo - R&S RTB2004 Oscilloscope (VISA)
echo.
echo Make sure both devices are connected before continuing.
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

REM Check if matplotlib is installed
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo ERROR: matplotlib package is not installed
    echo Installing matplotlib...
    pip install matplotlib
    if errorlevel 1 (
        echo Failed to install matplotlib. Please install manually:
        echo pip install matplotlib
        echo.
        pause
        exit /b 1
    )
)

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

REM Check if keyboard is installed
python -c "import keyboard" >nul 2>&1
if errorlevel 1 (
    echo ERROR: keyboard package is not installed
    echo Installing keyboard...
    pip install keyboard
    if errorlevel 1 (
        echo Failed to install keyboard. Please install manually:
        echo pip install keyboard
        echo.
        pause
        exit /b 1
    )
)

echo Required packages found.
echo.

REM Show usage options
echo Available VNA options:
echo   Default sweep: 1 Hz to 1 MHz, 10 points/decade
echo   -b <freq>     Begin frequency in Hz
echo   -e <freq>     End frequency in Hz
echo   -p <points>   Points per decade
echo   -v <volts>    Voltage amplitude in V
echo   -z <ohms>     Enable impedance measurement
echo   -n            No plotting
echo   -l            List frequencies only
echo   -q            Use square wave instead of sine
echo   -h            Show help
echo.

REM Run the enhanced VNA
echo Running Enhanced VNA with OWON AG 1022 Direct USB...
echo.

python VNA_Enhanced_Direct_USB.py %*
set vna_result=%errorlevel%

echo.
if %vna_result% equ 0 (
    echo ========================================
    echo   VNA MEASUREMENT COMPLETED
    echo ========================================
    echo.
    echo The VNA measurement completed successfully!
    echo Check the generated log file for detailed results.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   VNA MEASUREMENT FAILED
    echo ========================================
    echo.
    echo The VNA measurement failed. Please check:
    echo 1. OWON AG 1022 is connected and appears in Device Manager
    echo 2. R&S RTB2004 is connected and VISA drivers are installed
    echo 3. Both devices are powered on and ready
    echo 4. No other software is using the devices
    echo.
    echo For help, run: python VNA_Enhanced_Direct_USB.py -h
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %vna_result%
