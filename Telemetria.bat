@echo off
title RACE CONTROL - SISTEMA COMPLETO
color 0b

echo ==========================================
echo    INICIANDO PUENTE DE TELEMETRIA
echo ==========================================
echo.

:: 1. Iniciar ngrok en una ventana nueva
echo [1/2] Abriendo tunel ngrok...
start "Tunel ngrok" ngrok http 8765 --url=cleotilde-stroboscopic-jaunita.ngrok-free.dev

:: 2. Esperar 3 segundos para que el tunel estabilice
timeout /t 3 /nobreak >nul

:: 3. Iniciar el Bridge de Python
echo [2/2] Iniciando Bridge Python...
python bridge.py

pause