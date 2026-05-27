import base64
import io
import socket
import uuid
from pathlib import Path

import cv2
import numpy as np
import qrcode
from PIL import Image
from flask import Blueprint, current_app, jsonify, render_template, request, send_file, send_from_directory

bp = Blueprint('main', __name__)

ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}


def get_lan_ip() -> str:
    """Tenta descobrir o IP da rede local para o celular acessar o app."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def get_public_app_url() -> str:
    """Monta o link que o celular deve abrir pelo QR Code.

    Local: troca 127.0.0.1 pelo IP da rede.
    Railway: usa o domínio HTTPS real recebido pelo proxy.
    """
    host_only = request.host.split(':')[0]
    if host_only in {'127.0.0.1', 'localhost', '0.0.0.0'}:
        port = request.host.split(':')[1] if ':' in request.host else ('443' if request.scheme == 'https' else '80')
        return f'{request.scheme}://{get_lan_ip()}:{port}'
    return request.url_root.rstrip('/')


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


def read_image_from_file(file_storage):
    data = np.frombuffer(file_storage.read(), dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError('Não consegui ler a imagem enviada.')
    return img


def read_image_from_base64(data_url: str):
    if ',' in data_url:
        data_url = data_url.split(',', 1)[1]
    data = base64.b64decode(data_url)
    pil_img = Image.open(io.BytesIO(data)).convert('RGB')
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return img


def resize_for_processing(img, max_width=1600):
    h, w = img.shape[:2]
    if w <= max_width:
        return img, 1.0
    scale = max_width / float(w)
    resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale


def count_objects(img, *, mode='dark', min_area=250, max_area=999999, blur=5, morph=3, circularity=0.0):
    """Conta objetos por segmentação simples.

    Funciona melhor quando o objeto tem contraste com o fundo e quando as peças não estão muito grudadas.
    """
    working, scale = resize_for_processing(img)
    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)

    blur = int(blur)
    if blur % 2 == 0:
        blur += 1
    blur = max(1, min(31, blur))
    if blur > 1:
        gray = cv2.GaussianBlur(gray, (blur, blur), 0)

    if mode == 'light':
        thresh_type = cv2.THRESH_BINARY + cv2.THRESH_OTSU
    elif mode == 'adaptive':
        mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY_INV, 41, 3)
        thresh_type = None
    else:
        thresh_type = cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU

    if mode != 'adaptive':
        _, mask = cv2.threshold(gray, 0, 255, thresh_type)

    morph = int(morph)
    if morph > 0:
        kernel = np.ones((morph, morph), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    overlay = working.copy()
    items = []
    min_area = float(min_area)
    max_area = float(max_area)
    circularity = float(circularity)

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area or area > max_area:
            continue
        perimeter = cv2.arcLength(c, True)
        circ = 0.0 if perimeter == 0 else 4 * np.pi * area / (perimeter * perimeter)
        if circ < circularity:
            continue
        x, y, w, h = cv2.boundingRect(c)
        M = cv2.moments(c)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
        else:
            cx, cy = x + w // 2, y + h // 2
        items.append({'area': round(float(area), 2), 'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy, 'circularity': round(float(circ), 3)})

    # Ordena de cima para baixo, esquerda para direita, para numeração visual estável.
    items.sort(key=lambda i: (i['cy'] // 80, i['cx']))

    for idx, item in enumerate(items, start=1):
        x, y, w, h = item['x'], item['y'], item['w'], item['h']
        cx, cy = item['cx'], item['cy']
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 180, 0), 2)
        cv2.circle(overlay, (cx, cy), 5, (0, 0, 255), -1)
        cv2.putText(overlay, str(idx), (x, max(20, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA)

    return {
        'count': len(items),
        'items': items,
        'overlay': overlay,
        'mask': mask,
        'scale': scale,
    }




@bp.route('/health')
def health():
    return {'ok': True, 'service': 'contador-fotos-flask'}


@bp.route('/')
def index():
    return render_template('index.html', app_url=get_public_app_url())


@bp.route('/qr')
def qr_page():
    app_url = get_public_app_url()
    return render_template('qr.html', app_url=app_url)


@bp.route('/qr.png')
def qr_png():
    app_url = get_public_app_url()
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=14,
        border=4,
    )
    qr.add_data(app_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white').convert('RGB')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', max_age=0)


@bp.route('/analisar', methods=['POST'])
def analisar():
    try:
        mode = request.form.get('mode', 'dark')
        min_area = request.form.get('min_area', 250)
        max_area = request.form.get('max_area', 999999)
        blur = request.form.get('blur', 5)
        morph = request.form.get('morph', 3)
        circularity = request.form.get('circularity', 0.0)

        if 'image_base64' in request.form and request.form['image_base64']:
            img = read_image_from_base64(request.form['image_base64'])
        elif 'image' in request.files and request.files['image'].filename:
            f = request.files['image']
            if not allowed_file(f.filename):
                return jsonify({'ok': False, 'error': 'Formato inválido. Use PNG, JPG, JPEG ou WEBP.'}), 400
            img = read_image_from_file(f)
        else:
            return jsonify({'ok': False, 'error': 'Envie uma foto ou capture pela câmera.'}), 400

        result = count_objects(img, mode=mode, min_area=min_area, max_area=max_area, blur=blur, morph=morph, circularity=circularity)

        base_name = uuid.uuid4().hex
        result_path = current_app.config['RESULT_FOLDER'] / f'{base_name}_contado.jpg'
        mask_path = current_app.config['RESULT_FOLDER'] / f'{base_name}_mascara.jpg'
        cv2.imwrite(str(result_path), result['overlay'])
        cv2.imwrite(str(mask_path), result['mask'])

        return jsonify({
            'ok': True,
            'count': result['count'],
            'items': result['items'],
            'result_url': f'/resultado/{result_path.name}',
            'mask_url': f'/resultado/{mask_path.name}',
            'message': 'Contagem feita. Ajuste a sensibilidade se algum item ficou de fora ou foi contado errado.'
        })
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 500


@bp.route('/resultado/<path:filename>')
def resultado(filename):
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)
