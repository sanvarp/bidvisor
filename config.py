import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "docs")
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

    # Configuración de Azure OpenAI
    AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT", "https://tu_endpoint.azure.com/")
    API_KEY = os.getenv("AZURE_API_KEY")
    # La API de Responses (que reemplazó a la de Assistants, retirada por Azure)
    # sólo existe desde 2025-03-01-preview. Con una versión anterior toda llamada
    # al modelo falla con 400.
    MIN_API_VERSION = "2025-03-01-preview"
    API_VERSION = os.getenv("AZURE_API_VERSION", "2025-04-01-preview")
    MODEL = os.getenv("AZURE_MODEL", "gpt-4o")
    ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "RFI Builder Assistant")

    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///sessions.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prints de depuración
    print("\n=== CONFIGURACIÓN CARGADA DESDE .env ===")
    print(f"UPLOAD_FOLDER: {UPLOAD_FOLDER}")
    print(f"AZURE_ENDPOINT: {AZURE_ENDPOINT}")
    print(f"AZURE_API_KEY: {'[OK]' if API_KEY else '[FALTANTE]'}")
    print(f"AZURE_API_VERSION: {API_VERSION}")
    print(f"AZURE_MODEL (deployment name): {MODEL}")
    print(f"ASSISTANT_NAME: {ASSISTANT_NAME}")
    print(f"SQLALCHEMY_DATABASE_URI: {SQLALCHEMY_DATABASE_URI}")
    if API_VERSION < MIN_API_VERSION:
        print(f"*** ATENCIÓN: AZURE_API_VERSION={API_VERSION} es anterior a "
              f"{MIN_API_VERSION}. La API de Responses no está disponible en esa "
              f"versión y todas las llamadas al modelo van a fallar con 400. "
              f"Actualiza la variable en el App Service. ***")
    print("=========================================\n")
