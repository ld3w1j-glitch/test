@echo off
chcp 65001 >nul
title Corrigir erro cv2 / OpenCV

echo Corrigindo erro: ModuleNotFoundError: No module named 'cv2'
echo.

if not exist .venv\Scripts\python.exe (
    echo Ambiente .venv nao existe. Criando com Python 3.12...
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless
pip install --no-cache-dir opencv-python==4.10.0.84 numpy==1.26.4 Flask==3.0.3 Pillow==10.4.0 qrcode==7.4.2 pyopenssl==24.2.1
python -c "import cv2; print('cv2 instalado com sucesso:', cv2.__version__)"

echo.
echo Agora execute iniciar_http.bat ou iniciar_https_camera.bat
pause
