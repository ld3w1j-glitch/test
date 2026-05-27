from flask import Flask
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    app = Flask(__name__)

    # Necessário no Railway/Render/Nginx para Flask reconhecer HTTPS e host real.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
    app.config['RESULT_FOLDER'] = Path(__file__).parent / 'results'
    app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
    app.config['RESULT_FOLDER'].mkdir(exist_ok=True)

    from .routes import bp
    app.register_blueprint(bp)
    return app
