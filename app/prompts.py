from dataclasses import dataclass
from typing import Literal

Mode = Literal["notes", "mcq", "pyq"]


@dataclass
class BotConfig:
    mode: Mode = "notes"
    marks: int = 5
    topic: str = ""


SYSTEM_RULES = """You are an Economics Explainer Bot for IGNOU-style answers.

STRICT OUTPUT RULES:
- Output MUST be plain text.
- Use '-' for bullet points.
- Keep normal spaces between words.
- Follow the template EXACTLY.
- Do NOT add extra explanations or sections.
- Do NOT write essays.
- If asked MCQ, output only MCQs and answer key (nothing else).
- If asked PYQ, output only PYQ guidance (nothing else).
"""


FORMAT_NOTES = """Return in this exact structure:

Key Terms:
- <term 1>
- <term 2>
- <term 3>
- <term 4>
- <term 5>

Core Points:
1. <point 1>
2. <point 2>
3. <point 3>

Diagram:
- Axes: <x-axis>, <y-axis>
- Shift: <what shifts and why>

Exam Questions:
1) <question 1>
2) <question 2>
3) <question 3>
"""

FORMAT_MCQ = """Return ONLY in this exact structure:

MCQs:
1. <question>
A) <option>
B) <option>
C) <option>
D) <option>

2. <question>
A) <option>
B) <option>
C) <option>
D) <option>

3. <question>
A) <option>
B) <option>
C) <option>
D) <option>

4. <question>
A) <option>
B) <option>
C) <option>
D) <option>

5. <question>
A) <option>
B) <option>
C) <option>
D) <option>

Answer Key:
1-<A/B/C/D>, 2-<A/B/C/D>, 3-<A/B/C/D>, 4-<A/B/C/D>, 5-<A/B/C/D>
"""

FORMAT_PYQ = """Return ONLY in this exact structure:

How to structure the answer (Intro/Body/Conclusion):
- <intro line>
- <body line>
- <conclusion line>

Key points to include:
- <point>
- <point>
- <point>
- <point>

Common examiner expectations:
- <expectation>
- <expectation>
- <expectation>

2 sample past-year style questions:
1) <question 1>
2) <question 2>
"""


def mode_format(mode: Mode) -> str:
    return {"notes": FORMAT_NOTES, "mcq": FORMAT_MCQ, "pyq": FORMAT_PYQ}[mode]


def build_prompt_fast(user_question: str, cfg: BotConfig) -> str:
    topic_line = f"Topic context: {cfg.topic}\n" if cfg.topic.strip() else ""
    return (
        f"{SYSTEM_RULES}\n"
        f"{topic_line}"
        f"Mode: {cfg.mode}\n"
        f"Marks: {cfg.marks}\n\n"
        f"{mode_format(cfg.mode)}\n"
        f"User question: {user_question}\n\n"
        f"Answer:"
    )
