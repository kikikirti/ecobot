from dataclasses import dataclass
from typing import Dict, Literal

Mode = Literal["explain", "numerical", "notes", "mcq", "exam"]


@dataclass
class BotConfig:
    mode: Mode = "explain"
    marks: int = 5  # 2, 5, 10
    topic: str = ""


SYSTEM_RULES = """You are an Economics Explainer Bot for students.
Follow these rules:
- Be correct and clear. If the question is ambiguous, ask 1–2 clarifying questions.
- Do NOT invent official statistics, current GDP/inflation numbers, or policy details unless the user provides them.
- Prefer general theory + simple examples over made-up factual claims.
- Keep language exam-friendly, concise, and structured.
- If you are unsure, say so and provide what can be said confidently.
"""

FORMAT_EXPLAIN = """Return in this exact structure:
1) Definition (2–3 lines)
2) Intuition (simple explanation)
3) Example (realistic but generic; do not claim exact official numbers)
4) Common mistakes (2–4 bullets)
5) Quick recap (3 bullets)
6) 3 MCQs with answers (A/B/C/D)
"""

FORMAT_NUMERICAL = """Return in this exact structure:
1) What is asked
2) Given/Assumptions
3) Step-by-step solution with formulas
4) Final answer
5) Common pitfalls (2–3 bullets)
"""

FORMAT_NOTES = """Return in this exact structure:
- Key terms (bullets)
- Core points (6–10 bullets)
- Diagram/graph suggestion (describe axes + curve shift verbally)
- 3 likely exam questions
"""

FORMAT_MCQ = """Generate:
- 8 MCQs (A/B/C/D) + answer key
- 2 assertion-reason questions + answers
Questions must be conceptual and aligned with economics exam style.
"""

FORMAT_EXAM = """User wants an exam-ready answer.
Return:
- Intro (2–3 lines)
- Main body with headings
- One example
- Conclusion (1–2 lines)
Keep length suitable for marks asked.
"""


def marks_guidance(marks: int) -> str:
    if marks <= 2:
        return "Length guidance: very short (3–6 lines)."
    if marks <= 5:
        return "Length guidance: medium (10–14 lines)."
    return "Length guidance: long (3–6 short paragraphs)."


def mode_format(mode: Mode) -> str:
    return {
        "explain": FORMAT_EXPLAIN,
        "numerical": FORMAT_NUMERICAL,
        "notes": FORMAT_NOTES,
        "mcq": FORMAT_MCQ,
        "exam": FORMAT_EXAM,
    }[mode]


def build_prompt(user_question: str, cfg: BotConfig, chat_context: str = "") -> str:
    """
    For simple hosted models, we embed instructions into one prompt.
    """
    topic_line = f"Topic context: {cfg.topic}\n" if cfg.topic.strip() else ""
    context_block = f"Recent chat context:\n{chat_context}\n\n" if chat_context.strip() else ""

    prompt = (
        f"{SYSTEM_RULES}\n"
        f"{topic_line}"
        f"Mode: {cfg.mode}\n"
        f"Marks: {cfg.marks} ({marks_guidance(cfg.marks)})\n\n"
        f"{mode_format(cfg.mode)}\n\n"
        f"{context_block}"
        f"User question: {user_question}\n\n"
        f"Answer:"
    )
    return prompt


def summarize_context(messages) -> str:
    """
    Minimal context string from last few turns; helps keep continuity without heavy token usage.
    """
    if not messages:
        return ""
    lines = []
    for m in messages[-8:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)
