import os
import json
from dataclasses import dataclass
from typing import Iterator, Optional

import requests

from .utils import sleep_backoff, safe_strip


@dataclass
class LLMResult:
    text: str
    used_model: str
    raw_status: int


class OllamaClient:
    """
    Minimal Ollama client using /api/chat.
    Supports both streaming and non-streaming.
    """

    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model

    def set_model(self, model: str) -> None:
        self.model = model

    def _payload(self, prompt: str, max_new_tokens: int, temperature: float) -> dict:
        
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "num_predict": int(max_new_tokens),
                "temperature": float(temperature),
                "num_ctx": 512,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "stop": ["\nYou>", "\nUser>", "\nBot>", "\nBOT>"],
            },
        }

    def generate(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2) -> LLMResult:
        url = f"{self.host}/api/chat"
        payload = self._payload(prompt, max_new_tokens, temperature)
        payload["stream"] = False

        last_err: Optional[str] = None
        for attempt in range(3):
            try:
                r = requests.post(url, json=payload, timeout=120)
                status = r.status_code
                if status in (429, 503, 504):
                    last_err = f"Ollama temp error {status}: {safe_strip(r.text)}"
                    sleep_backoff(attempt)
                    continue
                if status >= 400:
                    raise RuntimeError(f"Ollama error {status}: {safe_strip(r.text)}")

                data = r.json()
                msg = data.get("message") or {}
                text = (msg.get("content") or "").strip()
                if not text:
                    raise RuntimeError("Empty response from Ollama.")
                return LLMResult(text=text, used_model=self.model, raw_status=status)

            except Exception as e:
                last_err = str(e)
                sleep_backoff(attempt)

        raise RuntimeError(last_err or "Ollama call failed after retries.")

    def generate_stream(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.2) -> Iterator[str]:
        """
        Yields incremental text chunks from Ollama streaming API.
        """
        url = f"{self.host}/api/chat"
        payload = self._payload(prompt, max_new_tokens, temperature)
        payload["stream"] = True

        last_err: Optional[str] = None
        for attempt in range(3):
            try:
                with requests.post(url, json=payload, timeout=120, stream=True) as r:
                    status = r.status_code
                    if status in (429, 503, 504):
                        last_err = f"Ollama temp error {status}: {safe_strip(r.text)}"
                        sleep_backoff(attempt)
                        continue
                    if status >= 400:
                        raise RuntimeError(f"Ollama error {status}: {safe_strip(r.text)}")

                    for line in r.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        data = json.loads(line)
                        msg = data.get("message") or {}
                        chunk = msg.get("content") or ""
                        if chunk:
                            yield chunk
                    return

            except Exception as e:
                last_err = str(e)
                sleep_backoff(attempt)

        raise RuntimeError(last_err or "Ollama streaming failed after retries.")


def load_client_from_env() -> OllamaClient:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    model = os.getenv("OLLAMA_MODEL", "llama3.2:1b").strip()
    return OllamaClient(host=host, model=model)
