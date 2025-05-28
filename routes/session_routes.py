import os
import uuid
import shutil

from models import db, ExtractionSession
from flask import Blueprint, jsonify, request, current_app, session as flask_session

session_bp = Blueprint('session', __name__)

def get_user_id():
    """Obtiene el ID del usuario autenticado desde las cabeceras de Azure."""
    user_id = request.headers.get("X-MS-CLIENT-PRINCIPAL-ID")  # OID de Entra ID
    print(f"User ID: {user_id}")
    if not user_id:
        if not flask_session.get('user_id'):
            flask_session['user_id'] = str(uuid.uuid4())
        return flask_session.get('user_id')
    return user_id

@session_bp.route('/session/create', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    name = data.get('name')
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User authentication failed"}), 401
    
    session_id = str(uuid.uuid4())
    assistant_id = f"assistant_{session_id}"  # Aquí se debería crear con OpenAI
    vector_store_id = f"vector_store_{session_id}"  # Aquí también

    new_session = ExtractionSession(
        id=session_id,
        name=name,
        user_id=user_id,
        assistant_id=assistant_id,
        vector_store_id=vector_store_id
    )
    db.session.add(new_session)
    db.session.commit()

    return jsonify({
        "session_id": session_id, 
        "name": name,
        "assistant_id": assistant_id, 
        "vector_store_id": vector_store_id
    })

@session_bp.route('/sessions', methods=['GET'])
def get_sessions():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "No user session found"}), 401

    sessions = ExtractionSession.query.filter_by(user_id=user_id).all()
    return jsonify([{ 
        "session_id": s.id, 
        "name": s.name,
        "created_at": s.created_at.isoformat() 
    } for s in sessions])

@session_bp.route('/session/<session_id>/details', methods=['GET'])
def get_session_details(session_id):
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    extracted = [{
         "section": info.section,
         "field": info.field,
         "value": info.value
    } for info in session.extracted_info]

    chats = [{
         "role": msg.role,
         "content": msg.content,
         "timestamp": msg.timestamp.isoformat()
    } for msg in session.chat_messages]

    files = [{
         "id": file.id,
         "filename": file.filename,
         "filepath": file.filepath
    } for file in session.files]

    return jsonify({
         "extracted_info": extracted,
         "chat_messages": chats,
         "files": files
    })

@session_bp.route('/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    session_obj = ExtractionSession.query.get(session_id)
    if not session_obj:
        return jsonify({"error": "Session not found"}), 404
    db.session.delete(session_obj)
    db.session.commit()
    return jsonify({"message": "Session deleted successfully"})

@session_bp.route('/clear_folder', methods=['DELETE'])
def clear_session_folder():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "User authentication failed"}), 401
    
    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], user_id)

    if not os.path.exists(user_folder):
        return jsonify({"error": "No files found for this user"}), 404
    
    shutil.rmtree(user_folder, ignore_errors=True)
    return jsonify({"message": "Files deleted successfully"})