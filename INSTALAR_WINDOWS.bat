@echo off
chcp 65001 > nul
echo ==========================================
echo Instalando Contador de Pessoas Tempo Real
echo ==========================================

py -3.12 -m venv .venv
if errorlevel 1 (
  echo Nao encontrei Python 3.12. Instale o Python 3.12 e tente novamente.
  pause
  exit /b 1
)

call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Instalacao finalizada.
echo Execute iniciar_http.bat
pause