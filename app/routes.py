import os, base64, uuid, io
from functools import wraps
from urllib.parse import urljoin

import cv2
import numpy as np
import qrcode
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app, send_file
from PIL import Image
from fpdf import FPDF

from .detector import detector
from .storage import add_history, list_history, update_corrected, export_csv

bp = Blueprint("main", __name__)

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged"):
            return redirect(url_for("main.login"))
        return fn(*args, **kwargs)
    return wrapper

def public_url():
    env = os.environ.get("PUBLIC_URL", "").strip().rstrip("/")
    if env:
        return env
    return request.host_url.rstrip("/")

@bp.route("/health")
def health():
    return {"ok": True}

@bp.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html", base_url=public_url())

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = os.environ.get("APP_USER", "admin")
        password = os.environ.get("APP_PASSWORD", "admin")
        if request.form.get("username") == user and request.form.get("password") == password:
            session["logged"] = True
            return redirect(url_for("main.index"))
        return render_template("login.html", error="Usuário ou senha inválidos.")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

@bp.route("/qr")
@login_required
def qr_page():
    return render_template("qr.html", base_url=public_url())

@bp.route("/qr.png")
@login_required
def qr_png():
    url = public_url()
    img = qrcode.make(url)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return send_file(bio, mimetype="image/png")

def decode_image_from_request():
    if "image" in request.files:
        file = request.files["image"]
        data = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        return image

    payload = request.get_json(silent=True) or {}
    data_url = payload.get("image", "")
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    raw = base64.b64decode(data_url)
    data = np.frombuffer(raw, np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return image

@bp.route("/api/detect_frame", methods=["POST"])
@login_required
def detect_frame():
    try:
        image = decode_image_from_request()
        if image is None:
            return jsonify({"ok": False, "error": "Imagem inválida."}), 400

        mode = request.args.get("mode", "auto")
        result = detector.detect(image, mode=mode, draw=False)
        return jsonify({
            "ok": True,
            "count": result["count"],
            "boxes": result["boxes"]
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/api/upload_detect", methods=["POST"])
@login_required
def upload_detect():
    try:
        image = decode_image_from_request()
        if image is None:
            return jsonify({"ok": False, "error": "Imagem inválida."}), 400

        mode = request.form.get("mode") or (request.get_json(silent=True) or {}).get("mode", "auto")
        result = detector.detect(image, mode=mode, draw=True)

        name = str(uuid.uuid4())
        original_file = f"{name}_original.jpg"
        processed_file = f"{name}_processado.jpg"
        original_path = os.path.join(current_app.config["UPLOAD_FOLDER"], original_file)
        processed_path = os.path.join(current_app.config["PROCESSED_FOLDER"], processed_file)

        cv2.imwrite(original_path, image)
        cv2.imwrite(processed_path, result["annotated"])

        item_id = add_history(
            count=result["count"],
            mode=mode,
            original_file=f"uploads/{original_file}",
            processed_file=f"processed/{processed_file}",
            note=""
        )

        return jsonify({
            "ok": True,
            "id": item_id,
            "count": result["count"],
            "processed_url": url_for("static", filename=f"processed/{processed_file}")
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@bp.route("/history")
@login_required
def history():
    return render_template("history.html", rows=list_history())

@bp.route("/history/<int:item_id>/correct", methods=["POST"])
@login_required
def correct(item_id):
    corrected = request.form.get("corrected_count", "0")
    note = request.form.get("note", "")
    update_corrected(item_id, corrected, note)
    return redirect(url_for("main.history"))

@bp.route("/export.csv")
@login_required
def export_csv_route():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "historico.csv")
    export_csv(path)
    return send_file(path, as_attachment=True, download_name="historico_contagem_pessoas.csv")

@bp.route("/report.pdf")
@login_required
def report_pdf():
    rows = list_history(100)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Relatorio de Contagem de Pessoas", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Total de registros: {len(rows)}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(12, 8, "ID", 1)
    pdf.cell(38, 8, "Data", 1)
    pdf.cell(25, 8, "Detectado", 1)
    pdf.cell(25, 8, "Corrigido", 1)
    pdf.cell(25, 8, "Modo", 1)
    pdf.cell(65, 8, "Obs", 1)
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    for r in rows:
        pdf.cell(12, 7, str(r["id"]), 1)
        pdf.cell(38, 7, str(r["created_at"])[:19], 1)
        pdf.cell(25, 7, str(r["count"]), 1)
        pdf.cell(25, 7, "" if r["corrected_count"] is None else str(r["corrected_count"]), 1)
        pdf.cell(25, 7, str(r["mode"] or ""), 1)
        obs = str(r["note"] or "")[:38]
        pdf.cell(65, 7, obs, 1)
        pdf.ln()

    bio = io.BytesIO(bytes(pdf.output(dest="S")))
    bio.seek(0)
    return send_file(bio, as_attachment=True, download_name="relatorio_contagem_pessoas.pdf", mimetype="application/pdf")