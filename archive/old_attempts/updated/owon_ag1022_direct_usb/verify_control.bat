@echo off
REM OWON AG 1022 Control Verification
REM =================================
REM
REM This script verifies that the code is actually controlling the signal generator
REM by making visible changes that you can observe on an oscilloscope.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   OWON AG 1022 Control Verification
echo ========================================
echo.
echo This script will verify that the code is actually controlling
echo your signal generator by making visible changes.
echo.
echo BEFORE RUNNING:
echo 1. Connect oscilloscope to signal generator output
echo 2. Make sure oscilloscope is running and showing the signal
echo 3. You should see a 1 kHz sine wave initially
echo.
echo The script will then:
echo - Change frequency (watch period change)
echo - Change voltage (watch amplitude change)
echo - Change waveform (watch shape change)
echo - Turn output on/off (watch signal disappear/reappear)
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

echo Are you ready to start verification?
echo Make sure your oscilloscope is connected and showing the signal.
echo.
set /p ready="Press Enter to continue or Ctrl+C to cancel..."

echo.
echo Starting control verification...
echo.

python verify_control.py
set verify_result=%errorlevel%

echo.
if %verify_result% equ 0 (
    echo ========================================
    echo   VERIFICATION COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo If you observed all the changes on your oscilloscope,
    echo then the code is successfully controlling your signal generator!
    echo.
    echo The verification included:
    echo - Frequency changes (period changes)
    echo - Voltage changes (amplitude changes)
    echo - Waveform changes (shape changes)
    echo - Output on/off control
    echo - Rapid real-time changes
    echo.
    echo Your OWON AG 1022 is fully controllable via the code!
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   VERIFICATION FAILED
    echo ========================================
    echo.
    echo The verification failed. Please check:
    echo 1. USB connection to OWON AG 1022
    echo 2. Device appears in Device Manager
    echo 3. pyusb is properly installed
    echo 4. No other software is using the device
    echo.
    echo For detailed error information, run: python verify_control.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %verify_result%
