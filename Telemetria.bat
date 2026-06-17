@echo off
cd /d "%~dp0"
title RACE CONTROL - SISTEMA COMPLETO
color 0b

echo ==========================================
echo       SELECCIÓN DE SIMULADOR - ORIÓN      
echo ==========================================
echo.
echo [1] Assetto Corsa (Shared Memory)
echo [2] Formula 1 (UDP Socket)
echo.
set /p opcion="Selecciona el juego (1 o 2): "

if "%opcion%"=="1" (
    set JUEGO_ACTUAL=ASSETTO_CORSA
    goto iniciar
)
if "%opcion%"=="2" (
    set JUEGO_ACTUAL=F1
    goto iniciar
)

echo.
echo Opción no válida. Cerrando...
timeout /t 3 >nul
exit

:iniciar
cls
echo ==========================================
echo     INICIANDO PUENTE DE TELEMETRIA [%JUEGO_ACTUAL%]
echo ==========================================
echo.

:: 1. Iniciar ngrok en una ventana nueva
echo [1/2] Abriendo tunel ngrok...
start "Tunel ngrok" ngrok http 8765 --url=cleotilde-stroboscopic-jaunita.ngrok-free.dev

:: 2. Esperar 3 segundos para que el tunel estabilice
timeout /t 3 /nobreak >nul

:: 3. Iniciar el Bridge de Python
echo [2/2] Iniciando Bridge Python en modo %JUEGO_ACTUAL%...
python bridge.py

pause