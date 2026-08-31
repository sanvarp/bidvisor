import os
import json
import queue
import asyncio
import threading
import traceback
from datetime import datetime
from flask import Blueprint, Response, current_app, stream_with_context, jsonify
from config import Config
from models import ExtractedInfo, ExtractionSession, UploadedFile, db
from services.extraction import extract_field_async, extract_answer_async
from services.openai_client import create_openai_client, vector_stores

from prompts import (
    overview_prompts, schedule_prompts,
    documents_prompts, profiles_prompts, evalation_prompts
)
from schemas import overview_schemas

process_bp = Blueprint('process', __name__)

# ✅ Extensiones válidas permitidas para procesamiento
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# Cada cuántos segundos se emite un comentario SSE de keepalive cuando todavía no
# hay resultados que enviar. El balanceador de Azure App Service corta conexiones
# inactivas a los 230s, así que el stream nunca puede quedarse mudo más que eso.
HEARTBEAT_SECONDS = 15

# Texto que se muestra en una ficha cuando su extracción falló, para distinguirlo
# de "el pliego no menciona esto" (que llega como respuesta vacía del modelo).
ERROR_PLACEHOLDER = "No se pudo extraer esta sección. Intenta reprocesar los documentos."


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _sse(payload):
    """Serializa un evento SSE."""
    return f"data: {json.dumps(payload)}\n\n"


def _build_tasks(client, model, vector_store_id):
    """
    Las siete extracciones, cada una con la sección/campo donde va su resultado.
    Se devuelven como fábricas de corrutinas para poder lanzarlas todas juntas.
    """
    return [
        ("general", "entidad", lambda: extract_field_async(
            client, model, vector_store_id, overview_prompts.ENTITY_TEMPLATE,
            overview_schemas.ENTITY_SCHEMA, "contracting_entity")),
        ("general", "objeto", lambda: extract_field_async(
            client, model, vector_store_id, overview_prompts.OBJECTIVE_TEMPLATE,
            overview_schemas.OBJECTIVE_SCHEMA, "objective")),
        ("general", "presupuesto", lambda: extract_field_async(
            client, model, vector_store_id, overview_prompts.BUDGET_TEMPLATE,
            overview_schemas.BUDGET_SCHEMA, "budget")),
        ("cronograma", None, lambda: extract_answer_async(
            client, model, vector_store_id, schedule_prompts.SCHEDULE_TEMPLATE)),
        ("presentacion", None, lambda: extract_answer_async(
            client, model, vector_store_id, documents_prompts.DOCUMENTS_TEMPLATE)),
        ("perfiles", None, lambda: extract_answer_async(
            client, model, vector_store_id, profiles_prompts.PROFILES_TEMPLATE)),
        ("evaluacion", None, lambda: extract_answer_async(
            client, model, vector_store_id, evalation_prompts.EVALATION_TEMPLATE)),
    ]


@process_bp.route('/process/<session_id>', methods=['GET'])
def process_files(session_id):
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    user_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], session.user_id)
    upload_folder = os.path.join(user_folder, session.id)

    if not os.path.exists(upload_folder):
        return jsonify({"error": "No files found for this session"}), 404

    # 🔥 Eliminar archivos inválidos (NO PDF/DOCX/TXT)
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

    # Idempotencia: si la sesión ya fue procesada, limpiar estado anterior
    # (UploadedFile + ExtractedInfo rows) para soportar reprocesamiento.
    # Se hace después de validar que hay archivos, para no borrar resultados
    # buenos cuando la petición iba a fallar de todos modos.
    # El vector_store viejo de Azure tiene TTL de 1 día, no se borra aquí.
    UploadedFile.query.filter_by(session_id=session_id).delete()
    ExtractedInfo.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    # Cola por la que el hilo de trabajo le pasa eventos al generador SSE.
    events = queue.Queue()

    def worker():
        """
        Pipeline completo (indexar documentos y extraer) fuera del hilo del request.
        Antes esto corría en línea y dejaba la conexión muda varios minutos: gunicorn
        mataba al worker por timeout y el navegador veía un error. Aquí solo se habla
        con Azure; toda la escritura en BD la hace el generador, que es quien tiene el
        contexto de aplicación de Flask.
        """
        try:
            client = create_openai_client()
            stores = vector_stores(client)

            vector_store = stores.create(
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

            file_streams = [open(path, "rb") for path in file_paths]
            try:
                stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id,
                    files=file_streams
                )
            finally:
                for stream in file_streams:
                    stream.close()

            events.put({
                "type": "setup",
                "vector_store_id": vector_store.id
            })

            async def run_all():
                async def run_one(section, field, coro_factory):
                    try:
                        value = await coro_factory()
                    except Exception as exc:
                        print(f"[process] fallo en sección '{section}': "
                              f"{type(exc).__name__}: {exc}", flush=True)
                        value = ""
                    events.put({
                        "type": "result",
                        "section": section,
                        "field": field,
                        "value": value if value else ERROR_PLACEHOLDER,
                        "ok": bool(value)
                    })

                await asyncio.gather(*(
                    run_one(section, field, factory)
                    for section, field, factory in _build_tasks(
                        client, Config.MODEL, vector_store.id)
                ))

            asyncio.run(run_all())

        except Exception as exc:
            print("[process] error fatal en el pipeline:", flush=True)
            print(traceback.format_exc(), flush=True)
            events.put({"type": "fatal", "message": str(exc)})
        finally:
            events.put({"type": "done"})

    def generate():
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

        # Primer byte inmediato: cierra las cabeceras del response y arranca el
        # stream antes de que empiece el trabajo pesado.
        yield _sse({"section": "status", "value": "indexando",
                    "message": "Indexando documentos..."})

        failed = False
        while True:
            try:
                event = events.get(timeout=HEARTBEAT_SECONDS)
            except queue.Empty:
                # Comentario SSE: mantiene viva la conexión sin que el cliente
                # lo reciba como mensaje.
                yield ": keepalive\n\n"
                continue

            kind = event.get("type")

            if kind == "done":
                break

            if kind == "fatal":
                failed = True
                yield _sse({"section": "status", "value": "error",
                            "message": event.get("message", "")})
                continue

            if kind == "setup":
                # `assistant_id` se conserva como quedó en /session/create: ya no
                # existen assistants (API retirada), pero la columna es NOT NULL y
                # el id no se usa para nada. Lo que importa es el vector store.
                session.vector_store_id = event["vector_store_id"]
                for file_path in file_paths:
                    db.session.add(UploadedFile(
                        session_id=session_id,
                        filename=os.path.basename(file_path),
                        filepath=file_path
                    ))
                db.session.commit()
                yield _sse({"section": "status", "value": "extrayendo",
                            "message": "Documentos indexados, extrayendo información..."})
                continue

            if kind == "result":
                # Se persiste apenas llega, no al final: si el usuario cierra la
                # pestaña a mitad de camino no se pierde lo ya extraído.
                db.session.add(ExtractedInfo(
                    session_id=session_id,
                    section=event["section"],
                    field=event["field"],
                    value=event["value"]
                ))
                db.session.commit()
                yield _sse({
                    "section": event["section"],
                    "field": event["field"],
                    "value": event["value"]
                })

        if not failed:
            yield _sse({"section": "status", "value": "completed"})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )
