import time
from flask import Blueprint, request, jsonify
from services.openai_client import create_openai_client, retrieve_assistant
from models import db, ChatMessage, ExtractionSession

ask_bp = Blueprint('ask', __name__)

@ask_bp.route('/ask/<session_id>', methods=['POST'])
def ask_question(session_id):
    """
    Recibe una pregunta del usuario, la envía al asistente y devuelve la respuesta.
    """
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    client = create_openai_client()
    assistant = retrieve_assistant(client, session.assistant_id)

    # Crear un hilo con el mensaje del usuario
    thread = client.beta.threads.create(
        messages=[{
            "role": "user",
            "content": query,
        }]
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id, assistant_id=assistant.id
    )

    while run.status in ['queued', 'in_progress', 'cancelling']:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    message_content = messages[0].content[0].text

    # Procesar anotaciones y citas (si las hubiera)
    annotations = message_content.annotations
    citations = []
    response_text = message_content.value
    for index, annotation in enumerate(annotations):
        response_text = response_text.replace(annotation.text, f" [{index}]")
        file_citation = getattr(annotation, "file_citation", None)
        if file_citation:
            cited_file = client.files.retrieve(file_citation.file_id)
            print(f"File citation: {file_citation}")
            print(f"Cited file: {cited_file.filename}")
            citations.append(f"[{index}] {cited_file.filename}")
    
    response_text += "\n\n" + "\n\n".join(citations)

    user_message = ChatMessage(session_id=session_id, role="user", content=query)
    assistant_message = ChatMessage(session_id=session_id, role="assistant", content=response_text)
    db.session.add(user_message)
    db.session.add(assistant_message)
    db.session.commit()
    return {"answer": response_text, "citations": citations}