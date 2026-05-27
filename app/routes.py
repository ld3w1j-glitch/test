import base64
import io
import socket
import uuid

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


def count_people_faces(img, *, scale_factor=1.08, min_neighbors=5, min_size=35):
    """Conta pessoas pela detecção de rostos frontais/perfil usando Haar Cascade do OpenCV.

    Observação: conta pessoas com rosto visível. Pessoas de costas, muito longe,
    cobertas ou com rosto muito inclinado podem não ser detectadas.
    """
    working, scale = resize_for_processing(img)
    gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    frontal_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    profile_path = cv2.data.haarcascades + 'haarcascade_profileface.xml'
    frontal = cv2.CascadeClassifier(frontal_path)
    profile = cv2.CascadeClassifier(profile_path)

    scale_factor = max(1.01, min(1.5, float(scale_factor)))
    min_neighbors = max(1, min(20, int(min_neighbors)))
    min_size = max(10, min(500, int(min_size)))

    detections = []
    faces = frontal.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=min_neighbors,
        minSize=(min_size, min_size),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    detections.extend([(int(x), int(y), int(w), int(h), 'rosto frontal') for (x, y, w, h) in faces])

    # Perfil direito/esquerdo. Usamos a imagem original e a imagem espelhada.
    profiles = profile.detectMultiScale(
        gray,
        scaleFactor=scale_factor,
        minNeighbors=max(3, min_neighbors),
        minSize=(min_size, min_size),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    detections.extend([(int(x), int(y), int(w), int(h), 'perfil') for (x, y, w, h) in profiles])

    flipped = cv2.flip(gray, 1)
    profiles_flipped = profile.detectMultiScale(
        flipped,
        scaleFactor=scale_factor,
        minNeighbors=max(3, min_neighbors),
        minSize=(min_size, min_size),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    width = gray.shape[1]
    for (x, y, w, h) in profiles_flipped:
        detections.append((int(width - x - w), int(y), int(w), int(h), 'perfil'))

    # Remove duplicados por sobreposição.
    boxes = []
    labels = []
    for x, y, w, h, label in detections:
        boxes.append([x, y, w, h])
        labels.append(label)

    if boxes:
        # groupRectangles precisa de duplicatas para agrupar; aqui usamos NMS manual.
        rects = np.array(boxes, dtype=float)
        scores = np.array([w * h for x, y, w, h in boxes], dtype=float)
        keep = non_max_suppression(rects, scores, overlap_thresh=0.35)
        boxes = [boxes[i] for i in keep]
        labels = [labels[i] for i in keep]

    overlay = working.copy()
    items = []
    for idx, ((x, y, w, h), label) in enumerate(zip(boxes, labels), start=1):
        cx, cy = x + w // 2, y + h // 2
        items.append({'tipo': label, 'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy})
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 180, 0), 3)
        cv2.putText(overlay, f'Pessoa {idx}', (x, max(25, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 0, 255), 2, cv2.LINE_AA)

    mask = np.zeros(gray.shape, dtype=np.uint8)
    for x, y, w, h in boxes:
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    return {
        'count': len(items),
        'items': items,
        'overlay': overlay,
        'mask': mask,
        'scale': scale,
        'method': 'rostos',
    }


def count_people_bodies(img):
    """Conta pessoas por corpo inteiro com HOG do OpenCV. Experimental."""
    working, scale = resize_for_processing(img, max_width=1200)
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, weights = hog.detectMultiScale(
        working,
        winStride=(8, 8),
        padding=(16, 16),
        scale=1.05,
    )
    boxes = [[int(x), int(y), int(w), int(h)] for (x, y, w, h) in rects]
    scores = np.array(weights).reshape(-1) if len(weights) else np.array([])
    if boxes:
        keep = non_max_suppression(np.array(boxes, dtype=float), scores if len(scores) else None, overlap_thresh=0.45)
        boxes = [boxes[i] for i in keep]

    overlay = working.copy()
    items = []
    for idx, (x, y, w, h) in enumerate(boxes, start=1):
        cx, cy = x + w // 2, y + h // 2
        items.append({'tipo': 'corpo', 'x': x, 'y': y, 'w': w, 'h': h, 'cx': cx, 'cy': cy})
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 180, 0), 3)
        cv2.putText(overlay, f'Pessoa {idx}', (x, max(25, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 0, 255), 2, cv2.LINE_AA)

    mask = np.zeros(working.shape[:2], dtype=np.uint8)
    for x, y, w, h in boxes:
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

    return {
        'count': len(items),
        'items': items,
        'overlay': overlay,
        'mask': mask,
        'scale': scale,
        'method': 'corpo inteiro experimental',
    }


def non_max_suppression(boxes, scores=None, overlap_thresh=0.35):
    """NMS simples para remover caixas duplicadas."""
    if len(boxes) == 0:
        return []
    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    if scores is None or len(scores) != len(boxes):
        scores = area
    idxs = np.argsort(scores)
    keep = []
    while len(idxs) > 0:
        last = len(idxs) - 1
        i = idxs[last]
        keep.append(int(i))
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)
        overlap = (w * h) / area[idxs[:last]]
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_thresh)[0])))
    return keep


@bp.route('/health')
def health():
    return {'ok': True, 'service': 'contador-pessoas-flask'}


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
        person_method = request.form.get('person_method', 'faces')
        scale_factor = request.form.get('scale_factor', 1.08)
        min_neighbors = request.form.get('min_neighbors', 5)
        min_size = request.form.get('min_size', 35)

        if 'image_base64' in request.form and request.form['image_base64']:
            img = read_image_from_base64(request.form['image_base64'])
        elif 'image' in request.files and request.files['image'].filename:
            f = request.files['image']
            if not allowed_file(f.filename):
                return jsonify({'ok': False, 'error': 'Formato inválido. Use PNG, JPG, JPEG ou WEBP.'}), 400
            img = read_image_from_file(f)
        else:
            return jsonify({'ok': False, 'error': 'Envie uma foto ou capture pela câmera.'}), 400

        if person_method == 'body':
            result = count_people_bodies(img)
        else:
            result = count_people_faces(img, scale_factor=scale_factor, min_neighbors=min_neighbors, min_size=min_size)

        base_name = uuid.uuid4().hex
        result_path = current_app.config['RESULT_FOLDER'] / f'{base_name}_pessoas.jpg'
        mask_path = current_app.config['RESULT_FOLDER'] / f'{base_name}_deteccao.jpg'
        cv2.imwrite(str(result_path), result['overlay'])
        cv2.imwrite(str(mask_path), result['mask'])

        message = 'Contagem de pessoas feita.'
        if result['method'] == 'rostos':
            message += ' Este modo conta pessoas com rosto visível na imagem.'
        else:
            message += ' Modo de corpo inteiro é experimental e funciona melhor com pessoas em pé e corpo visível.'

        return jsonify({
            'ok': True,
            'count': result['count'],
            'items': result['items'],
            'method': result['method'],
            'result_url': f'/resultado/{result_path.name}',
            'mask_url': f'/resultado/{mask_path.name}',
            'message': message,
        })
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 500


@bp.route('/resultado/<path:filename>')
def resultado(filename):
    return send_from_directory(current_app.config['RESULT_FOLDER'], filename)
