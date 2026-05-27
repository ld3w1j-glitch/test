@echo off
chcp 65001 > nul
call .venv\Scripts\activate
echo Abrindo em HTTPS local. O navegador pode dizer que nao e seguro.
echo Isso e normal em certificado local.
python -c "from app import create_app; app=create_app(); app.run(host='0.0.0.0', port=5443, ssl_context='adhoc', debug=True)"
pause