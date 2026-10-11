"""Optional cloud or local AI adapter with bounded in-memory conversation context."""
from __future__ import annotations

import json
import os
from threading import Lock
from urllib.request import Request, urlopen

_HISTORY = []
_HISTORY_LOCK = Lock()
_MAX_HISTORY_MESSAGES = 12
_SYSTEM_PROMPT = (
    "You are JARVIS, a concise desktop assistant. Remember the recent conversation in this session. "
    "Never claim to perform PC actions unless the application confirms them. "
    "Never ask for passwords or API keys. Explain risky actions and ask the user to do them manually. "
    "You cannot inspect the user's files or control Windows unless a specific tool reports the result."
)


def reset_conversation():
    with _HISTORY_LOCK:
        _HISTORY.clear()


def chat(prompt):
    """Send a prompt to the configured provider; keep only the last few messages in RAM."""
    text = str(prompt).strip()[:8000]
    if not text:
        return ""
    provider = os.getenv("JARVIS_AI_PROVIDER", "openai").strip().lower()
    with _HISTORY_LOCK:
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}, *_HISTORY,
                    {"role": "user", "content": text}]
    if provider == "ollama":
        base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        payload = json.dumps({"model": model, "stream": False, "messages": messages}).encode("utf-8")
        request = Request(base + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data.get("message", {}).get("content", "").strip()
    elif provider == "openai":
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            return ""
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_tokens=700,
        )
        answer = (response.choices[0].message.content or "").strip()
    else:
        return ""
    if answer:
        with _HISTORY_LOCK:
            _HISTORY.extend([{"role": "user", "content": text}, {"role": "assistant", "content": answer[:8000]}])
            del _HISTORY[:-_MAX_HISTORY_MESSAGES]
    return answer
