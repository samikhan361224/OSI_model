@echo off
:: build.bat  –  Compile server.exe and client.exe using MinGW GCC

echo.
echo ============================================================
echo   OSI Model Simulation  --  Build Script (Akib Jawad)
echo ============================================================
echo.

set GCC=
where gcc >nul 2>&1
if not errorlevel 1 (
    set GCC=gcc
) else if exist "C:\MinGW\bin\gcc.exe" (
    set GCC=C:\MinGW\bin\gcc.exe
    set PATH=C:\MinGW\bin;%PATH%
) else if exist "C:\msys64\mingw64\bin\gcc.exe" (
    set GCC=C:\msys64\mingw64\bin\gcc.exe
    set PATH=C:\msys64\mingw64\bin;%PATH%
) else (
    echo ERROR: GCC compiler not found on PATH, C:\MinGW, or C:\msys64.
    echo Please install MinGW-w64 or add GCC to your Windows PATH.
    exit /b 1
)

echo [INFO] Using GCC: %GCC%

echo.
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
echo   Build complete!  Run:  run.bat  or  py osi_visualizer.py
echo ============================================================
echo.
