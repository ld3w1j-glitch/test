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
    # Local Windows: abre QR se OPEN_QR=1.
    # Railway: não abre navegador, apenas usa a porta definida pela plataforma.
    port = int(os.environ.get('PORT', '5000'))
    if os.environ.get('OPEN_QR', '0') == '1':
        threading.Thread(target=abrir_qr_no_navegador, args=(f'http://127.0.0.1:{port}/qr',), daemon=True).start()
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
