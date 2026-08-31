from flask import Blueprint, request, jsonify
from config import Config
from services.openai_client import (
    create_openai_client, file_search_tool, ASSISTANT_INSTRUCTIONS
)
from services.extraction import strip_citations
from models import db, ChatMessage, ExtractionSession

ask_bp = Blueprint('ask', __name__)


def _collect_citations(response) -> list:
    """
    Extrae los nombres de archivo citados por file_search, sin repetir y en el
    orden en que aparecen, para armar el pie de "[n] archivo".
    """
    filenames = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", None) or []:
            for annotation in getattr(content, "annotations", None) or []:
                name = getattr(annotation, "filename", None)
                if name and name not in filenames:
                    filenames.append(name)
    return [f"[{index}] {name}" for index, name in enumerate(filenames)]


@ask_bp.route('/ask/<session_id>', methods=['POST'])
def ask_question(session_id):
    """
    Recibe una pregunta del usuario, la envía al modelo con búsqueda sobre los
    documentos de la sesión y devuelve la respuesta.
    """
    session = ExtractionSession.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"error": "No query provided"}), 400

    # Sin vector store la sesión todavía no se procesó: no hay nada que consultar.
    if not session.vector_store_id or not session.vector_store_id.startswith("vs_"):
        return jsonify({"error": "La sesión aún no ha sido procesada."}), 400

    client = create_openai_client()

    # Reconstruir el historial completo desde la BD para que el modelo tenga
    # contexto de la conversación previa (cada llamada a /ask es independiente,
    # así que sin esto no vería los mensajes anteriores).
    history = (
        ChatMessage.query
        .filter_by(session_id=session_id)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    conversation = [{"role": m.role, "content": m.content} for m in history]
    conversation.append({"role": "user", "content": query})

    response = client.responses.create(
        model=Config.MODEL,
        instructions=ASSISTANT_INSTRUCTIONS,
        input=conversation,
        tools=[file_search_tool(session.vector_store_id)],
    )

    response_text = strip_citations(response.output_text)

    citations = _collect_citations(response)
    if citations:
        response_text += "\n\n" + "\n\n".join(citations)

    user_message = ChatMessage(session_id=session_id, role="user", content=query)
    assistant_message = ChatMessage(session_id=session_id, role="assistant", content=response_text)
    db.session.add(user_message)
    db.session.add(assistant_message)
    db.session.commit()
    return {"answer": response_text, "citations": citations}
