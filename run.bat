@echo off
:: run.bat  –  Quick launcher: build (if needed) then run the visualizer

echo.
if not exist server.exe goto build
if not exist client.exe goto build
goto run

:build
echo [INFO] Binaries not found, building first ...
call build.bat
if errorlevel 1 exit /b 1

:run
echo [INFO] Starting OSI Visualizer ...
py osi_visualizer.py %*
