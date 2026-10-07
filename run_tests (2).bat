@echo off
REM ============================================================
REM  Run AlphyMobileAutomation tests without Android Studio/PyCharm
REM  Double-click this file, or run it from Command Prompt.
REM ============================================================

REM ---- Settings: change these if yours are different ----
set SDK=%LOCALAPPDATA%\Android\Sdk
set ADB=%SDK%\platform-tools\adb.exe
set AVD= Pixel_6
set PROJECT=F:\PycharmProjects\AlphyMobileAutomation
set VENV=.venv

REM ---- 0. Restart adb so it reliably detects the emulator ----
echo Restarting adb...
"%ADB%" kill-server >nul 2>&1
"%ADB%" start-server
timeout /t 3 /nobreak >nul

REM ---- 1. Start the emulator only if one isn't already running ----
"%ADB%" devices | findstr "emulator" >nul
if not errorlevel 1 (
    echo An emulator is already running - using it.
) else (
    echo Starting emulator %AVD% ...
    start "Emulator" "%SDK%\emulator\emulator.exe" -avd %AVD% -memory 2048 -no-boot-anim -gpu host
)

REM ---- 2. Wait for adb to see the emulator (max 3 minutes) ----
echo Waiting for the emulator to connect...
set /a TRIES=0
:waitdevice
"%ADB%" devices | findstr "emulator" | findstr /v "offline unauthorized" >nul
if not errorlevel 1 goto waitboot_start
set /a TRIES+=1
if %TRIES% GEQ 36 (
    echo.
    echo ERROR: Emulator not detected after 3 minutes. Current adb status:
    "%ADB%" devices
    echo Close all emulator windows and run this script again.
    pause
    exit /b 1
)
echo   still waiting... %TRIES%/36
timeout /t 5 /nobreak >nul
goto waitdevice

REM ---- 3. Wait until Android has fully booted ----
:waitboot_start
echo Emulator connected. Waiting for Android to finish booting...
:waitboot
"%ADB%" shell getprop sys.boot_completed 2>nul | findstr /c:"1" >nul
if errorlevel 1 (
    timeout /t 5 /nobreak >nul
    goto waitboot
)
echo Emulator is ready.

REM ---- 4. Start the Appium server in its own window ----
echo Starting Appium server...
start "Appium" cmd /k appium
timeout /t 10 /nobreak >nul

REM ---- 5. Activate the virtual environment and run the tests ----
cd /d "%PROJECT%"
call "%VENV%\Scripts\activate.bat"
echo Running tests...
pytest -v

REM ---- 6. Optional: close the emulator when tests finish ----
REM Remove the REM on the next line to shut the emulator down automatically.
REM "%ADB%" emu kill

echo.
echo Done. Press any key to close.
pause >nul
