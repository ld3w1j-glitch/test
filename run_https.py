import os
import threading
import time
import webbrowser

from app import create_app

app = create_app()


def abrir_qr_no_navegador(url: str):
    time.sleep(1.2)
    webbrowser.open(url)


if __name__ == '__main__':
    # HTTPS local temporário. Ajuda o navegador do celular a liberar a câmera.
    # O navegador pode mostrar aviso de certificado; avance somente se estiver na sua rede local.
    if os.environ.get('OPEN_QR', '0') == '1':
        threading.Thread(target=abrir_qr_no_navegador, args=('https://127.0.0.1:5443/qr',), daemon=True).start()
    app.run(host='0.0.0.0', port=5443, debug=False, ssl_context='adhoc', use_reloader=False)
