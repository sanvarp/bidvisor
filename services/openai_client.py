from openai import AzureOpenAI
from config import Config


def create_openai_client() -> AzureOpenAI:
    client = AzureOpenAI(
        azure_endpoint=Config.AZURE_ENDPOINT,
        api_key=Config.API_KEY,
        api_version=Config.API_VERSION
    )
    return client


def create_assistant(client: AzureOpenAI):
    assistant = client.beta.assistants.create(
        model=Config.MODEL,
        name=Config.ASSISTANT_NAME,
        instructions=(
            "Eres un experto en la construcción y gestión de RFIs (Request for Information). "
            "Utiliza todo tu conocimiento para recopilar y organizar la información clave solicitada "
            "por el usuario para dar seguimiento efectivo a un RFI en desarrollo."
        ),
        tools=[
            {
                "type": "file_search",
                "file_search": {
                    "ranking_options": {
                        "ranker": "default_2024_08_21",
                        "score_threshold": 0
                    }
                }
            }
        ],
        tool_resources={
            "file_search": {
                "vector_store_ids": []
            }
        },
        temperature=1,
        top_p=1
    )
    return assistant

def retrieve_assistant(client: AzureOpenAI, assistant_id: str):
    assistant = client.beta.assistants.retrieve(assistant_id)
    return assistant