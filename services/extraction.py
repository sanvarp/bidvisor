import asyncio
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser


async def _run_with_retry(client, assistant, content: str, label: str, max_retries: int = 2):
    """
    Crea un thread/run y espera a que termine. Reintenta hasta `max_retries` veces si
    el run falla por rate_limit_exceeded, respetando el delay sugerido por Azure.
    """
    for attempt in range(max_retries + 1):
        thread = client.beta.threads.create(messages=[{"role": "user", "content": content}])
        run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
        while run.status in ['queued', 'in_progress', 'cancelling']:
            await asyncio.sleep(1)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status == 'completed':
            return run, thread

        last_err = getattr(run, 'last_error', None)
        err_code = getattr(last_err, 'code', None) if last_err else None
        err_msg = getattr(last_err, 'message', '') if last_err else ''
        print(f"[run] FAIL '{label}' attempt={attempt} status={run.status} code={err_code}", flush=True)

        if err_code == 'rate_limit_exceeded' and attempt < max_retries:
            wait_seconds = 30
            m = re.search(r'retry after (\d+)\s*seconds?', err_msg)
            if m:
                wait_seconds = int(m.group(1)) + 2
            print(f"[run] retry '{label}' in {wait_seconds}s", flush=True)
            await asyncio.sleep(wait_seconds)
            continue

        return run, thread
    return run, thread


async def extract_field_async(client, assistant, template: str, schema: dict, field: str) -> str:
    """
    Extrae un campo específico usando un prompt estructurado.
    """
    output_parser = StructuredOutputParser.from_response_schemas(schema)
    instructions = output_parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_template(template).format(format_instructions=instructions)
    label = f"field:{field}"
    run, thread = await _run_with_retry(client, assistant, prompt, label)

    token_usage = run.usage if hasattr(run, 'usage') else None
    total_tokens = token_usage.total_tokens if token_usage else None
    print(f"[extract_field] status={run.status} tokens={total_tokens} field={field}", flush=True)

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == 'assistant':
                try:
                    return output_parser.parse(message.content[0].text.value)[field]
                except Exception as e:
                    print(f"[extract_field] parse error for {field}: {e}", flush=True)
                    return ""
    return ""

async def extract_answer_async(client, assistant, template: str) -> str:
    """
    Extrae una respuesta completa usando el prompt dado.
    """
    label = template[:60].replace('\n', ' ').strip()
    run, thread = await _run_with_retry(client, assistant, template, label)

    token_usage = run.usage if hasattr(run, 'usage') else None
    total_tokens = token_usage.total_tokens if token_usage else None
    print(f"[extract_answer] status={run.status} tokens={total_tokens} prompt='{label}...'", flush=True)

    if run.status != 'completed':
        return ""

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in messages.data:
        if message.role == 'assistant':
            text = message.content[0].text.value
            text = re.sub(r'【[^】]*】', '', text)
            return text
    return ""