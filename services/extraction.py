import asyncio
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser

from services.openai_client import ASSISTANT_INSTRUCTIONS, file_search_tool

# Azure intercala marcadores de citación 【...】 dentro del texto cuando usa
# file_search. Se limpian antes de mostrar o de parsear el JSON.
CITATION_RE = re.compile(r'【[^】]*】')


def strip_citations(text: str) -> str:
    return CITATION_RE.sub('', text or '')


async def _respond_with_retry(client, model, vector_store_id, content, label, max_retries=2):
    """
    Lanza una consulta al modelo con file_search sobre el vector store de la sesión.
    Reintenta hasta `max_retries` veces si Azure responde con rate limit,
    respetando el delay que sugiere en el mensaje de error.

    La llamada del SDK es bloqueante, así que va en `to_thread`: es lo que hace
    que las siete extracciones corran realmente en paralelo en vez de irse
    turnando sobre el event loop.
    """
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.to_thread(
                client.responses.create,
                model=model,
                instructions=ASSISTANT_INSTRUCTIONS,
                input=content,
                tools=[file_search_tool(vector_store_id)],
            )
        except Exception as exc:
            message = str(exc)
            print(f"[responses] FAIL '{label}' attempt={attempt} "
                  f"{type(exc).__name__}: {message[:200]}", flush=True)

            is_rate_limit = 'rate_limit' in message or '429' in message
            if is_rate_limit and attempt < max_retries:
                wait_seconds = 30
                m = re.search(r'retry after (\d+)\s*seconds?', message)
                if m:
                    wait_seconds = int(m.group(1)) + 2
                print(f"[responses] retry '{label}' in {wait_seconds}s", flush=True)
                await asyncio.sleep(wait_seconds)
                continue
            raise


def _log_usage(tag: str, response, extra: str):
    usage = getattr(response, 'usage', None)
    total_tokens = getattr(usage, 'total_tokens', None) if usage else None
    print(f"[{tag}] tokens={total_tokens} {extra}", flush=True)


async def extract_field_async(client, model, vector_store_id, template: str, schema: list, field: str) -> str:
    """
    Extrae un campo específico usando un prompt estructurado.
    """
    output_parser = StructuredOutputParser.from_response_schemas(schema)
    instructions = output_parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_template(template).format(format_instructions=instructions)

    response = await _respond_with_retry(client, model, vector_store_id, prompt, f"field:{field}")
    _log_usage("extract_field", response, f"field={field}")

    try:
        return output_parser.parse(strip_citations(response.output_text))[field]
    except Exception as e:
        print(f"[extract_field] parse error for {field}: {e}", flush=True)
        return ""


async def extract_answer_async(client, model, vector_store_id, template: str) -> str:
    """
    Extrae una respuesta completa usando el prompt dado.
    """
    label = template[:60].replace('\n', ' ').strip()

    response = await _respond_with_retry(client, model, vector_store_id, template, label)
    _log_usage("extract_answer", response, f"prompt='{label}...'")

    return strip_citations(response.output_text)
