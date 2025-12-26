import os
from dataclasses import dataclass
from typing import Optional

import requests

from .utils import sleep_backoff, safe_strip


@dataclass
class LLMResult:
    text: str
    used_model: str
    raw_status: int


class OllamaClient:
    """
    Minimal Ollama client using /api/chat (non-streaming).
    """

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def set_model(self, model: str) -> None:
        self.model = model

    def generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2) -> LLMResult:
        url = f"{self.host}/api/chat"
        # inside OllamaClient.generate()

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "num_predict": int(max_new_tokens),
                "temperature": float(temperature),
                "num_ctx": 512,            # smaller ctx = faster
                "num_thread": 8,           # tune (see note below)
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "mirostat": 0,
                "stop": [
                    "\nYou>",               # prevents drifting into chat loop
                    "\nUser>",
                    "\nBOT>",
                    "\nBot>",
                ],
            },
            "stream": False,
            }

        last_err: Optional[str] = None
        for attempt in range(3):
            try:
                r = requests.post(url, json=payload, timeout=120)
                status = r.status_code

                if status in (429, 503, 504):
                    last_err = f"Ollama temporary error {status}: {safe_strip(r.text)}"
                    sleep_backoff(attempt)
                    continue

                if status >= 400:
                    raise RuntimeError(f"Ollama error {status}: {safe_strip(r.text)}")

                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                msg = (data or {}).get("message") or {}
                text = msg.get("content") or ""
                if not text.strip():
                    raise RuntimeError("Empty response from Ollama. Check model/server.")

                return LLMResult(text=text, used_model=self.model, raw_status=status)

            except Exception as e:
                last_err = str(e)
                sleep_backoff(attempt)

        raise RuntimeError(last_err or "Ollama call failed after retries.")


def load_client_from_env() -> OllamaClient:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    model = os.getenv("OLLAMA_MODEL", "phi3:mini").strip()
    return OllamaClient(host=host, model=model)
