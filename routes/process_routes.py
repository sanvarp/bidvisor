import os
import json
import asyncio
from datetime import datetime
from flask import Blueprint, Response, current_app, stream_with_context, jsonify
from models import ExtractedInfo, ExtractionSession, UploadedFile, db
from services.extraction import extract_field_async, extract_answer_async
from services.openai_client import create_openai_client, create_assistant

from prompts import (
    overview_prompts, schedule_prompts,
    documents_prompts, profiles_prompts, evalation_prompts
)
from schemas import overview_schemas

process_bp = Blueprint('process', __name__)

# ✅ Extensiones válidas permitidas para procesamiento
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@process_bp.route('/process/<session_id>', methods=['GET'])
def process_files(session_id):
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    client = create_openai_client()
    assistant = create_assistant(client)

    vector_store = client.beta.vector_stores.create(
        name=f"RFI_CONTRALORIA_{datetime.now().strftime('%d_%m_%Y_%H_%M_%S')}",
        expires_after={"anchor": "last_active_at", "days": 1},
        chunking_strategy={
            "type": "static",
            "static": {
                "max_chunk_size_tokens": 1000,
                "chunk_overlap_tokens": 250
            }
        }
    )

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session.user_id)
    upload_folder = os.path.join(user_folder, session.id)

    if not os.path.exists(upload_folder):
        return jsonify({"error": "No files found for this session"}), 404

    # 🔥 Eliminar archivos inválidos (NO PDF/DOCX/TXT)
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    for f in os.listdir(upload_folder):
        file_path = os.path.join(upload_folder, f)
        if os.path.isfile(file_path) and not allowed_file(f):
            os.remove(file_path)

    # Filtrar solo los archivos válidos
    file_paths = [
        os.path.join(upload_folder, f)
        for f in os.listdir(upload_folder)
        if os.path.isfile(os.path.join(upload_folder, f)) and allowed_file(f)
    ]

    if not file_paths:
        return jsonify({"error": "No hay archivos válidos para procesar."}), 400

    file_streams = [open(path, "rb") for path in file_paths]

    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id,
        files=file_streams
    )

    client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
    )

    session.vector_store_id = vector_store.id
    session.assistant_id = assistant.id

    for file_path in file_paths:
        uploaded_file = UploadedFile(
            session_id=session_id,
            filename=os.path.basename(file_path),
            filepath=file_path
        )
        db.session.add(uploaded_file)

    db.session.commit()

    def generate_updates():
        async def get_results():
            tasks = [
                extract_field_async(client, assistant, overview_prompts.ENTITY_TEMPLATE, overview_schemas.ENTITY_SCHEMA, "contracting_entity"),
                extract_field_async(client, assistant, overview_prompts.OBJECTIVE_TEMPLATE, overview_schemas.OBJECTIVE_SCHEMA, "objective"),
                extract_field_async(client, assistant, overview_prompts.BUDGET_TEMPLATE, overview_schemas.BUDGET_SCHEMA, "budget"),
                extract_answer_async(client, assistant, schedule_prompts.SCHEDULE_TEMPLATE),
                extract_answer_async(client, assistant, documents_prompts.DOCUMENTS_TEMPLATE),
                extract_answer_async(client, assistant, profiles_prompts.PROFILES_TEMPLATE),
                extract_answer_async(client, assistant, evalation_prompts.EVALATION_TEMPLATE)
            ]
            return await asyncio.gather(*tasks)

        results = asyncio.run(get_results())
        updates = [
            {"section": "general", "field": "entidad", "value": results[0]},
            {"section": "general", "field": "objeto", "value": results[1]},
            {"section": "general", "field": "presupuesto", "value": results[2]},
            {"section": "cronograma", "value": results[3]},
            {"section": "presentacion", "value": results[4]},
            {"section": "perfiles", "value": results[5]},
            {"section": "evaluacion", "value": results[6]},
            {"section": "status", "value": "completed"}
        ]
        for update in updates:
            yield update
        for item in updates:
            extracted_info = ExtractedInfo(
                session_id=session_id,
                section=item['section'],
                field=item.get('field'),
                value=item['value']
            )
            db.session.add(extracted_info)
        db.session.commit()

    return Response(
        stream_with_context(
            (f"data: {json.dumps(update)}\n\n" for update in generate_updates())
        ),
        mimetype='text/event-stream'
    )

