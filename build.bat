@echo off
:: build.bat  –  Compile server.exe and client.exe using MinGW GCC

set GCC=C:\MinGW\bin\gcc.exe

echo.
echo ============================================================
echo   OSI Model Simulation  --  Build Script
echo ============================================================
echo.

if not exist "%GCC%" (
    echo ERROR: GCC not found at %GCC%
    echo Please install MinGW or update the GCC path in build.bat
    exit /b 1
)

echo [1/2] Compiling server.c ...
"%GCC%" server.c -o server.exe -lws2_32 -Wall -Wno-unused-result
if errorlevel 1 (
    echo ERROR: server.c compilation failed!
    exit /b 1
)
echo       server.exe built successfully.

echo.
echo [2/2] Compiling client.c ...
"%GCC%" client.c -o client.exe -lws2_32 -Wall -Wno-unused-result
if errorlevel 1 (
    echo ERROR: client.c compilation failed!
    exit /b 1
)
echo       client.exe built successfully.

echo.
echo ============================================================
echo   Build complete!  Run:  py osi_visualizer.py
echo ============================================================
echo.
