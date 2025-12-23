import os
from dataclasses import dataclass
from typing import Optional

import requests

from .utils import safe_strip, sleep_backoff


@dataclass
class LLMResult:
    text: str
    used_model: str
    raw_status: int


class HFRouterChatClient:
    """
    Hugging Face Router - OpenAI compatible Chat Completions API.

    Base URL: https://router.huggingface.co/v1
    Endpoint: /chat/completions
    """
    def __init__(self, token: str, model: str):
        if not token:
            raise ValueError("HF_TOKEN missing. Add it to your .env file.")
        if not model:
            raise ValueError("HF_MODEL missing. Add it to your .env file.")
        self.token = token
        self.model = model
        self.base_url = "https://router.huggingface.co/v1"

    def set_model(self, model: str) -> None:
        self.model = model

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def generate(self, prompt: str, max_new_tokens: int = 512, temperature: float = 0.2) -> LLMResult:
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_new_tokens,
        }

        last_err: Optional[str] = None
        for attempt in range(3):
            try:
                r = requests.post(url, headers=self._headers(), json=payload, timeout=60)
                status = r.status_code

                if status in (429, 503, 504):
                    last_err = f"Temporary HF router error {status}: {safe_strip(r.text)}"
                    sleep_backoff(attempt)
                    continue

                data = r.json() if "application/json" in r.headers.get("content-type", "") else None

                if status >= 400:
                    msg = safe_strip(str(data)) if data is not None else safe_strip(r.text)
                    raise RuntimeError(f"HF Router API error {status}: {msg}")

                text = ""
                if isinstance(data, dict):
                    choices = data.get("choices") or []
                    if choices and isinstance(choices[0], dict):
                        message = choices[0].get("message") or {}
                        text = message.get("content") or ""

                text = safe_strip(text)
                if not text:
                    raise RuntimeError("Empty response from router. Try a different HF_MODEL.")

                return LLMResult(text=text, used_model=self.model, raw_status=status)

            except Exception as e:
                last_err = str(e)
                sleep_backoff(attempt)

        raise RuntimeError(last_err or "HF Router API call failed after retries.")


def load_client_from_env() -> HFRouterChatClient:
    token = os.getenv("HF_TOKEN", "").strip()
    model = os.getenv("HF_MODEL", "").strip()
    return HFRouterChatClient(token=token, model=model)
