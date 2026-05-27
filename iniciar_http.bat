@echo off
chcp 65001 >nul
title Contador por Foto - HTTP com QR Code

if not exist .venv\Scripts\python.exe (
    echo Ambiente virtual nao encontrado. Executando instalador...
    call INSTALAR_WINDOWS.bat
)

call .venv\Scripts\activate
python -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo OpenCV/cv2 nao encontrado. Instalando dependencias agora...
    python -m pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
)

set OPEN_QR=1
python run.py
pause
