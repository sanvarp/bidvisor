import os
from models import ExtractionSession
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

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "files": file_names,
        "skipped_files": skipped_files
    })
