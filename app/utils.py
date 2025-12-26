import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Optional


def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def ensure_dir(path: str) -> None:
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def write_jsonl(path: str, record: Dict[str, Any]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def clamp_chat_history(messages, max_turns: int = 6):
    if not messages:
        return []
    keep = max_turns * 2
    return messages[-keep:]


def safe_strip(text: Optional[str]) -> str:
    if not text:
        return ""
    return " ".join(text.strip().split())


def sleep_backoff(attempt: int) -> None:
    time.sleep(min(8, 2 ** attempt))


def strip_think_blocks(text: str) -> str:
    """
    Remove model reasoning blocks.
    Handles both:
      <think> ... </think>
      <think> ... (missing closing tag)
    """
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<think>.*$", "", text, flags=re.DOTALL | re.IGNORECASE)
    return text.strip()
