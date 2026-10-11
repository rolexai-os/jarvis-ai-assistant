"""Optional cloud AI adapter. Only used when an API key is configured."""
import os


def chat(prompt):
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
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
