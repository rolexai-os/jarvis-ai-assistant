"""Optional cloud or local AI adapter. Disabled unless explicitly configured."""
import json
import os
from urllib.request import Request, urlopen


def chat(prompt):
    provider = os.getenv("JARVIS_AI_PROVIDER", "openai").strip().lower()
    if provider == "ollama":
        base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        payload = json.dumps({
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": "You are JARVIS, a concise desktop assistant. Never claim to perform actions unless confirmed. Explain risky actions and ask the user to do them manually."},
                {"role": "user", "content": prompt[:8000]},
            ],
        }).encode("utf-8")
        request = Request(base + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("message", {}).get("content", "").strip()
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if provider != "openai" or not key:
        return ""
    from openai import OpenAI
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": "You are JARVIS, a concise desktop assistant. Never claim to perform actions unless confirmed. Explain risky actions and ask the user to do them manually."},
            {"role": "user", "content": prompt[:8000]},
        ],
        max_tokens=700,
    )
    return (response.choices[0].message.content or "").strip()
