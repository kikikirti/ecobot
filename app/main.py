import os
import sys
from typing import Dict, List

from dotenv import load_dotenv

from .llm import load_client_from_env
from .prompts import BotConfig, build_prompt, summarize_context
from .utils import clamp_chat_history, now_iso, safe_strip, write_jsonl, strip_think_blocks


HELP_TEXT = """
Commands:
  help                         Show this help
  mode explain|numerical|notes|mcq|exam
  marks 2|5|10
  topic <text>                 Set topic context (e.g., "Inflation", "IS-LM")
  model <hf-model-id>          Switch HF model on the fly
  clear                        Clear chat history
  exit                         Quit

Tips:
- If the model gives irrelevant output, try:
    model google/flan-t5-base
- For numerical questions, use:
    mode numerical
    marks 5
"""


def parse_command(line: str):
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return None, None
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return cmd, arg


def main():
    load_dotenv()

    # Logging path
    log_path = os.getenv("ECON_BOT_LOG", "logs/chat.jsonl")

    try:
        client = load_client_from_env()
    except Exception as e:
        print(f"[Error] {e}")
        print("Create .env from .env.example and set HF_TOKEN.")
        sys.exit(1)

    cfg = BotConfig(mode="explain", marks=5, topic="")
    history: List[Dict[str, str]] = []

    print("📘 Economics Explainer Bot (CLI)")
    print(f"Model: {client.model}")
    print("Type 'help' for commands.\n")

    while True:
        try:
            user_in = input("You> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_in:
            continue

        cmd, arg = parse_command(user_in)

        # Handle commands
        if cmd in ("help", "?"):
            print(HELP_TEXT)
            continue
        if cmd == "exit":
            print("Bye!")
            break
        if cmd == "clear":
            history = []
            print("✅ Cleared chat history.")
            continue
        if cmd == "mode":
            val = arg.lower()
            if val in ("explain", "numerical", "notes", "mcq", "exam"):
                cfg.mode = val  # type: ignore
                print(f"✅ mode set to: {cfg.mode}")
            else:
                print("❌ Invalid mode. Use: explain|numerical|notes|mcq|exam")
            continue
        if cmd == "marks":
            try:
                m = int(arg)
                if m in (2, 5, 10):
                    cfg.marks = m
                    print(f"✅ marks set to: {cfg.marks}")
                else:
                    print("❌ marks must be 2, 5, or 10.")
            except ValueError:
                print("❌ marks must be a number: 2|5|10")
            continue
        if cmd == "topic":
            cfg.topic = arg
            print(f"✅ topic set to: {cfg.topic}")
            continue
        if cmd == "model":
            if not arg:
                print("❌ Provide model id, e.g. model google/flan-t5-base")
                continue
            client.set_model(arg)
            print(f"✅ model set to: {client.model}")
            continue

        # Otherwise treat as question
        question = user_in
        history.append({"role": "user", "content": question})
        history = clamp_chat_history(history, max_turns=6)

        chat_context = summarize_context(history[:-1])  # context excluding current user question
        prompt = build_prompt(question, cfg, chat_context=chat_context)

        # Token-ish control (rough)
        max_new = 256 if cfg.marks == 2 else 650 if cfg.marks == 5 else 900
        temperature = 0.2 if cfg.mode in ("explain", "exam", "notes") else 0.1

        try:
            result = client.generate(prompt, max_new_tokens=max_new, temperature=temperature)
            answer = safe_strip(strip_think_blocks(result.text))
        except Exception as e:
            print(f"\n[Error] {e}\n")
            print("Try: model google/flan-t5-base  (or wait and retry if rate-limited)\n")
            continue

        history.append({"role": "assistant", "content": answer})
        history = clamp_chat_history(history, max_turns=6)

        # Print answer
        print("\nBot> " + answer + "\n")

        # Log
        write_jsonl(log_path, {
            "ts": now_iso(),
            "model": result.used_model,
            "mode": cfg.mode,
            "marks": cfg.marks,
            "topic": cfg.topic,
            "question": question,
            "answer": answer
        })


if __name__ == "__main__":
    main()
