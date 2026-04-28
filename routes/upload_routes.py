import os
from models import ExtractionSession, UploadedFile, db
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app

upload_bp = Blueprint('upload', __name__)

# Define extensiones permitidas
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/upload', methods=['POST'])
def upload_files():
    """Sube archivos y, si no hay sesión, crea una nueva usando session_routes.py."""

    session_id = request.args.get('session_id')
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    uploaded_files = request.files.getlist("files[]")
    file_names = []
    skipped_files = []

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session.user_id)
    upload_dir = os.path.join(user_folder, session_id)
    os.makedirs(upload_dir, exist_ok=True)

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            file_names.append(filename)
        else:
            skipped_files.append(file.filename)

    # Devolver TODOS los archivos en la carpeta de la sesión, no solo los recién subidos.
    # Así el frontend puede re-renderizar sin perder estado previo si suben en tandas.
    all_files = sorted(
        f for f in os.listdir(upload_dir)
        if os.path.isfile(os.path.join(upload_dir, f))
    )

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "files": all_files,
        "uploaded": file_names,
        "skipped_files": skipped_files
    })


@upload_bp.route('/upload/<session_id>/<path:filename>', methods=['DELETE'])
def delete_uploaded_file(session_id, filename):
    """Elimina un archivo subido antes de procesar la sesión."""
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    safe_name = secure_filename(filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session.user_id, session_id)
    file_path = os.path.join(upload_dir, safe_name)

    # Defensa contra path traversal: el archivo debe estar dentro de upload_dir.
    if not os.path.realpath(file_path).startswith(os.path.realpath(upload_dir)):
        return jsonify({"error": "Invalid path"}), 400

    if os.path.isfile(file_path):
        os.remove(file_path)

    # Si la sesión ya fue procesada, también limpiar la fila de UploadedFile.
    # El próximo reprocesamiento creará un vector store nuevo sin este archivo.
    removed_row = UploadedFile.query.filter_by(session_id=session_id, filename=safe_name).delete()
    db.session.commit()

    if not removed_row and not os.path.exists(file_path):
        # Ni rastro: el archivo no existía
        return jsonify({"error": "File not found"}), 404

    return jsonify({"status": "deleted", "filename": safe_name})
