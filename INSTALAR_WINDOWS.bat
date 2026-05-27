@echo off
chcp 65001 >nul
title Instalador - Contador por Foto Flask

echo =============================================
echo  Contador por Foto - Instalacao Windows
echo =============================================
echo.

py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python 3.12 nao encontrado.
    echo Instale o Python 3.12 e marque Add python.exe to PATH.
    echo Link: https://www.python.org/downloads/release/python-3128/
    pause
    exit /b 1
)

if exist .venv (
    echo Ambiente .venv encontrado.
) else (
    echo Criando ambiente virtual com Python 3.12...
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo.
echo Testando bibliotecas...
python -c "import flask, cv2, numpy, PIL, qrcode; print('OK - dependencias instaladas')"
if errorlevel 1 (
    echo.
    echo ERRO: alguma dependencia nao instalou corretamente.
    echo Tente executar este comando manualmente:
    echo .venv\Scripts\python.exe -m pip install --force-reinstall opencv-python numpy Flask Pillow qrcode pyopenssl
    pause
    exit /b 1
)

echo.
echo Instalacao finalizada.
echo Para iniciar em HTTP: iniciar_http.bat
echo Para iniciar em HTTPS: iniciar_https_camera.bat
echo.
pause
