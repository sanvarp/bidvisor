from openai import AzureOpenAI
from config import Config

# Prompt de sistema del asistente. Antes vivía dentro del objeto `assistant` de la
# API de Assistants (retirada por Azure: devuelve 410 assistants_api_deprecated);
# ahora se envía en cada llamada a la API de Responses.
ASSISTANT_INSTRUCTIONS = (
    "Eres un experto en la construcción y gestión de RFIs (Request for Information). "
    "Utiliza todo tu conocimiento para recopilar y organizar la información clave solicitada "
    "por el usuario para dar seguimiento efectivo a un RFI en desarrollo."
)


def create_openai_client() -> AzureOpenAI:
    client = AzureOpenAI(
        azure_endpoint=Config.AZURE_ENDPOINT,
        api_key=Config.API_KEY,
        api_version=Config.API_VERSION
    )
    return client


def vector_stores(client: AzureOpenAI):
    """
    Acceso al API de vector stores. En openai>=1.66 dejó de colgar de `.beta`,
    así que se soportan ambas ubicaciones y no quedamos atados a una versión
    exacta del SDK.
    """
    return getattr(client, "vector_stores", None) or client.beta.vector_stores


def file_search_tool(vector_store_id: str) -> dict:
    """Herramienta de búsqueda semántica sobre los documentos de la sesión."""
    return {"type": "file_search", "vector_store_ids": [vector_store_id]}
