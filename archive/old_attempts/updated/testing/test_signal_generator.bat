@echo off
REM Windows Signal Generator Connection Test Batch File
REM =================================================
REM
REM This batch file runs the signal generator connection test
REM and provides user-friendly feedback for Windows users.
REM
REM Usage: Double-click this file or run from command prompt

echo.
echo ========================================
echo   Signal Generator Connection Test
echo ========================================
echo.
echo This will test your OWON AG 1022 signal generator connection.
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
python -c "import visa" >nul 2>&1
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

REM Run the quick test
echo Running connection test...
echo.

python quick_signal_test.py
set test_result=%errorlevel%

echo.
if %test_result% equ 0 (
    echo ========================================
    echo   TEST COMPLETED SUCCESSFULLY
    echo ========================================
    echo.
    echo Your signal generator is working correctly!
    echo You can now use it with the VNA software.
    echo.
    echo Press any key to exit...
    pause >nul
) else (
    echo ========================================
    echo   TEST FAILED
    echo ========================================
    echo.
    echo The connection test failed. Please check:
    echo 1. USB connection to OWON AG 1022
    echo 2. Device drivers installation
    echo 3. VISA drivers (NI-VISA or Keysight VISA)
    echo 4. Try different USB port
    echo 5. Restart the signal generator
    echo.
    echo For detailed testing, run: python test_signal_generator_windows.py
    echo.
    echo Press any key to exit...
    pause >nul
)

exit /b %test_result%
