import json
import subprocess
from app.config import get_settings

settings = get_settings()


async def llm_generate(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    """Generate LLM response. Tries Claude API first, falls back to Ollama."""
    if settings.ANTHROPIC_API_KEY:
        return await _claude_generate(system_prompt, user_prompt, json_mode)
    return await _ollama_generate(system_prompt, user_prompt, json_mode)


async def _claude_generate(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    import anthropic
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    if json_mode:
        user_prompt += "\n\nRespond with valid JSON only. No markdown, no explanation."
    message = await client.messages.create(
        model=settings.CLAUDE_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


async def _ollama_generate(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    import ollama as ollama_client
    if json_mode:
        user_prompt += "\n\nRespond with valid JSON only. No markdown, no explanation."
    response = ollama_client.chat(
        model=settings.OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={"temperature": 0.3},
    )
    return response["message"]["content"]


def parse_llm_json(text: str) -> dict | list:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        import re
        match = re.search(r'[\[{].*[\]}]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}
