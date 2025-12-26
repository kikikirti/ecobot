from dataclasses import dataclass
from typing import Literal

Mode = Literal["explain", "numerical", "notes", "mcq", "exam", "pyq"]


@dataclass
class BotConfig:
    mode: Mode = "explain"
    marks: int = 5
    topic: str = ""


SYSTEM_RULES = """You are an Economics assistant.
Do not invent official statistics.
Return ONLY what is asked. No extra text. No code blocks.
Keep short and exam-friendly.
"""


def notes_fill_prompt(topic: str, marks: int) -> str:
    # Ask model to only generate small content chunks
    return (
        f"{SYSTEM_RULES}\n"
        f"Task: Provide content for IGNOU exam NOTES on topic: {topic}\n"
        f"Return exactly:\n"
        f"1) Key terms: 6 short terms (comma-separated)\n"
        f"2) Core points: {3 if marks==2 else 4 if marks==5 else 6} short numbered points (1 line each)\n"
        f"3) Diagram: axes + one curve/shift line\n"
        f"4) 3 likely exam questions (3 lines)\n"
    )


def mcq_fill_prompt(topic: str) -> str:
    return (
        f"{SYSTEM_RULES}\n"
        f"Task: Create 5 MCQs on: {topic}\n"
        f"Return exactly 5 questions. Each question must have options A/B/C/D.\n"
        f"Then return Answer Key in one line like: 1-A, 2-C, 3-B, 4-D, 5-A\n"
        f"No explanations.\n"
    )


def pyq_fill_prompt(topic: str) -> str:
    return (
        f"{SYSTEM_RULES}\n"
        f"Task: PYQ exam-writing guidance for: {topic}\n"
        f"Return exactly:\n"
        f"- Structure (Intro/Body/Conclusion) in 3 bullets\n"
        f"- Key points to include (5 bullets)\n"
        f"- Common examiner expectations (3 bullets)\n"
        f"- 2 sample past-year style questions (numbered 1 and 2)\n"
    )


def summarize_context(messages) -> str:
    if not messages:
        return ""
    lines = []
    for m in messages[-6:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)
