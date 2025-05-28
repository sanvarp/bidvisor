import asyncio
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import StructuredOutputParser

async def extract_field_async(client, assistant, template: str, schema: dict, field: str) -> str:
    """
    Extrae un campo específico usando un prompt estructurado.
    """
    output_parser = StructuredOutputParser.from_response_schemas(schema)
    instructions = output_parser.get_format_instructions()
    prompt = ChatPromptTemplate.from_template(template).format(format_instructions=instructions)
    thread = client.beta.threads.create(messages=[{"role": "user", "content": prompt}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    while run.status in ['queued', 'in_progress', 'cancelling']:
        await asyncio.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    
    token_usage = run.usage if hasattr(run, 'usage') else None
    prompt_tokens = token_usage.prompt_tokens if token_usage else None
    completion_tokens = token_usage.completion_tokens if token_usage else None
    total_tokens = token_usage.total_tokens if token_usage else None
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
    
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == 'assistant':
                return output_parser.parse(message.content[0].text.value)[field]
    return ""

async def extract_answer_async(client, assistant, template: str) -> str:
    """
    Extrae una respuesta completa usando el prompt dado.
    """
    thread = client.beta.threads.create(messages=[{"role": "user", "content": template}])
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    while run.status in ['queued', 'in_progress', 'cancelling']:
        await asyncio.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    
    token_usage = run.usage if hasattr(run, 'usage') else None
    prompt_tokens = token_usage.prompt_tokens if token_usage else None
    completion_tokens = token_usage.completion_tokens if token_usage else None
    total_tokens = token_usage.total_tokens if token_usage else None
    print(f"Prompt tokens: {prompt_tokens}, Completion tokens: {completion_tokens}, Total tokens: {total_tokens}")
        
    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        for message in messages.data:
            if message.role == 'assistant':
                text = message.content[0].text.value
                text = re.sub(r'【[^】]*】', '', text)
                return text
    return ""