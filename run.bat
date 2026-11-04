@echo off
:: run.bat  –  Quick launcher: build binaries, check dependencies, and launch OSI Visualizer

echo.
echo ============================================================
echo   OSI 7-Layer Simulation Launcher (Akib Jawad)
echo ============================================================
echo.

:: Check python
where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not found on PATH. Please install Python 3.
        exit /b 1
    )
)

:: Check rich dependency
py -c "import rich" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Python 'rich' library not found. Installing now...
    py -m pip install rich
)

:: Check if binaries exist, build if not
if not exist server.exe goto build
if not exist client.exe goto build
goto run

:build
echo [INFO] Binaries not found, compiling C programs...
call build.bat
if errorlevel 1 exit /b 1

:run
echo [INFO] Launching Professional Animated OSI Visualizer...
echo.
py osi_visualizer.py %*
