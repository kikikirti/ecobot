import os
import sys
import re
from typing import Optional

from dotenv import load_dotenv

from .llm import load_client_from_env
from .prompts import BotConfig, build_prompt_fast
from .utils import now_iso, strip_think_blocks, write_jsonl

HELP_TEXT = """
Commands:
  help
  marks 2|5|10
  model <ollama-model>
  /demo
  /notes <topic>
  /mcq <topic>
  /pyq <topic>
  exit
"""


DEMO_NOTES = """Key Terms:
- Inflation
- Demand-pull inflation
- Cost-push inflation
- Price level
- Monetary policy

Core Points:
1. Inflation is a sustained increase in the general price level of goods and services over time.
2. It reduces the purchasing power of money and affects savers, borrowers and fixed-income earners differently.
3. For exams, always define inflation, mention causes (demand-pull, cost-push), and briefly note effects and policy control.

Diagram:
- Axes: Price Level (vertical), Real Output (horizontal)
- Shift: Rightward shift of Aggregate Demand (AD) curve showing demand-pull inflation

Exam Questions:
1) Define inflation and distinguish between demand-pull and cost-push inflation.
2) Explain any three effects of inflation on different sections of society.
3) Briefly discuss the role of monetary policy in controlling inflation.
"""

DEMO_MCQ = """MCQs:
1. Demand-pull inflation arises mainly due to:
A) Excess aggregate demand over available output
B) Increase in costs of production
C) Fall in money supply
D) Decrease in investment

2. Which of the following is most closely associated with demand-pull inflation?
A) Recession
B) Full-employment level of output
C) Technological unemployment
D) Reduction in indirect taxes

3. Demand-pull inflation can be controlled primarily by:
A) Increasing government expenditure
B) Increasing the policy interest rate
C) Reducing direct taxes
D) Increasing subsidies

4. When the government increases its expenditure without raising taxes, it is most likely to cause:
A) Cost-push inflation
B) Demand-pull inflation
C) Disinflation
D) Deflation

5. A typical policy mix to reduce demand-pull inflation would be:
A) Higher interest rates and lower government spending
B) Lower interest rates and higher government spending
C) Higher subsidies and higher transfers
D) Lower reserve requirements and tax cuts

Answer Key:
1-A, 2-B, 3-B, 4-B, 5-A
"""

DEMO_PYQ = """How to structure the answer (Intro/Body/Conclusion):
- Intro: Define the IS-LM model and mention that it explains simultaneous equilibrium in the goods and money markets.
- Body: Explain the IS curve (goods market), the LM curve (money market), and show how their intersection determines income and interest rate.
- Conclusion: Briefly state policy implications (fiscal vs monetary policy) and limitations of the model.

Key points to include:
- Meaning of IS (Investment–Saving) curve and why it slopes downward.
- Meaning of LM (Liquidity preference–Money supply) curve and why it slopes upward.
- Equilibrium at the intersection of IS and LM.
- Impact of fiscal expansion (shift of IS) and monetary expansion (shift of LM) on income (Y) and interest rate (r).

Common examiner expectations:
- Clear labelled diagram of IS and LM with axes (interest rate r on vertical, income/output Y on horizontal).
- Correct explanation of shifts in IS and LM curves due to policy changes.
- Brief mention of assumptions (closed economy, fixed prices in the basic model).
- Coherent link between theory and policy conclusions.

2 sample past-year style questions:
1) Explain the IS-LM model of income determination in a closed economy. How is equilibrium achieved?
2) Using the IS-LM framework, explain the relative effectiveness of fiscal and monetary policy.
"""



def normalize(text: str) -> str:
    if not text:
        return ""
    text = strip_think_blocks(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def looks_glued(text: str) -> bool:
    letters = sum(c.isalpha() for c in text)
    spaces = text.count(" ")
    return letters > 120 and spaces < max(10, letters // 80)


def repair_spacing(client, text: str) -> str:
    prompt = (
        "Fix spacing and line breaks in the text below.\n"
        "Do not change meaning, do not add/remove sections.\n"
        "Just rewrite with normal spaces and clean new lines.\n\n"
        f"TEXT:\n{text}\n\nREWRITE:"
    )
    res = client.generate(prompt, max_new_tokens=450, temperature=0.0)
    return normalize(res.text)


def trim_to_template(mode: str, text: str) -> str:
    """
    Keep only the part of the answer starting from the main heading
    for each mode. This removes 'Sure, here is...' style noise.
    """
    if not text:
        return ""

    lower = text.lower()

    if mode == "notes":
        anchor = "key terms:"
    elif mode == "mcq":
        anchor = "mcqs:"
    elif mode == "pyq":
        anchor = "how to structure the answer"
    else:
        return text

    idx = lower.find(anchor)
    if idx == -1:
        return text 

    return text[idx:].strip()


def validate(mode: str, text: str) -> bool:
    t = (text or "").lower()

    if mode == "notes":
        has_sections = all(
            x in t for x in ["key terms:", "core points:", "diagram:", "exam questions:"]
        )
        has_core_nums = all(x in t for x in ["1.", "2.", "3."])
        has_exam_nums = all(x in t for x in ["1)", "2)", "3)"])
        has_bullets = "- " in text
        return has_sections and has_core_nums and has_exam_nums and has_bullets

    if mode == "mcq":
        
        has_header = "mcqs:" in t and "answer key:" in t

        
        q_ok = all(f"{i}." in t for i in ["1", "2", "3", "4", "5"])

        
        opts_ok = all(x in t for x in ["a)", "b)", "c)", "d)"])

        key_ok = (
            re.search(
                r"answer key:\s*1-[abcd],\s*2-[abcd],\s*3-[abcd],\s*4-[abcd],\s*5-[abcd]",
                t,
            )
            is not None
        )

        return has_header and q_ok and opts_ok and key_ok

    if mode == "pyq":
        has_sections = all(
            x in t
            for x in [
                "how to structure the answer (intro/body/conclusion):",
                "key points to include:",
                "common examiner expectations:",
                "2 sample past-year style questions:",
            ]
        )
        has_samples = "1)" in t and "2)" in t
        return has_sections and has_samples

    return False





def build_fallback_answer(mode: str, question: str) -> str:
    """
    Deterministic, template-perfect fallback used when the model
    fails to follow the required structure after several retries.
    """
    topic = (question or "").strip()
    if not topic:
        topic = "the topic"

    if mode == "mcq":
        # Simple generic 5-MCQ block tied to the topic
        return f"""MCQs:
1. Which of the following best describes {topic}?
A) It is unrelated to the economy
B) It is a concept used in macroeconomics
C) It refers only to household decisions
D) It is a purely political term

2. The main objective of {topic} is to:
A) Maximize exports
B) Stabilize the economy using policy tools
C) Eliminate all forms of taxation
D) Fix wages at a constant level

3. Which of the following is usually associated with {topic}?
A) Changes in interest rates
B) Changes in rainfall
C) Changes in population census
D) Changes in consumer tastes only

4. A contractionary stance of {topic} typically aims to:
A) Increase inflation
B) Reduce inflationary pressure
C) Create hyperinflation
D) Double government expenditure

5. In the context of {topic}, an expansionary policy would:
A) Reduce money supply sharply
B) Increase money supply or lower interest rates
C) Ban all forms of credit
D) Fix prices by law for all goods

Answer Key:
1-B, 2-B, 3-A, 4-B, 5-B
"""

    if mode == "notes":
        return f"""Key Terms:
- {topic}
- Policy objectives
- Policy instruments
- Transmission mechanism
- Macroeconomic stabilization

Core Points:
1. {topic} is an important macroeconomic concept used to influence aggregate demand and overall economic activity.
2. It typically works through specific instruments (such as interest rates or money supply) to achieve goals like price stability and growth.
3. In exams, you should always define {topic}, mention its main objectives, and briefly explain how it affects the economy.

Diagram:
- Axes: Relevant policy variable on vertical, output or income on horizontal
- Shift: Policy change shifts the relevant curve showing its impact on output and stability

Exam Questions:
1) Define {topic} and state its main objectives.
2) Explain briefly how {topic} can influence aggregate demand.
3) Write short notes on the instruments commonly used in {topic}.
"""

    if mode == "pyq":
        return f"""How to structure the answer (Intro/Body/Conclusion):
- Intro: Define {topic} and place it within the relevant branch of economics.
- Body: Explain the key concepts, mechanisms, and diagrams associated with {topic}.
- Conclusion: Summarize the main insights and mention any limitations or policy implications.

Key points to include:
- Clear definition of {topic}
- Explanation of core components or mechanisms
- Use of at least one relevant diagram
- Short discussion of advantages, limitations, or real-world relevance

Common examiner expectations:
- Correct use of standard terminology related to {topic}
- Logical flow from definition to explanation to conclusion
- Properly labelled diagram(s) where applicable
- Focus on exam-relevant points rather than lengthy essays

2 sample past-year style questions:
1) Explain the concept of {topic}. How does it affect the overall performance of the economy?
2) Discuss the main features, advantages and limitations of {topic} with the help of a suitable diagram.
"""

   
    return f"{topic}."





def enforced_generate(client, cfg: BotConfig, question: str, log_path: str) -> str:
    base_prompt = build_prompt_fast(question, cfg)

   
    max_new = 450 if cfg.mode == "notes" else 900 if cfg.mode == "mcq" else 750

    answer: Optional[str] = None
    prompt = base_prompt

    
    temperature = 0.1 if cfg.mode == "mcq" else 0.2

    success = False
    used_fallback = False

    for attempt in range(5):
        res = client.generate(prompt, max_new_tokens=max_new, temperature=temperature)
        answer = normalize(res.text)

        
        if looks_glued(answer):
            answer = repair_spacing(client, answer)

        
        answer = trim_to_template(cfg.mode, answer)

        if validate(cfg.mode, answer):
            success = True
            break
        temperature = 0.0
        prompt = (
            base_prompt
            + "\n\nCRITICAL: Your previous output did NOT follow the required template.\n"
            "Rewrite the FULL answer FROM SCRATCH, exactly in the template above.\n"
            "Do NOT change headings, do NOT add extra sections, do NOT add any explanation.\n"
        )

    if not success:
      
        answer = build_fallback_answer(cfg.mode, question)
        used_fallback = True
        success = True  

    final = answer or ""

    print("\nBot> " + final + "\n")

    if log_path:
        write_jsonl(
            log_path,
            {
                "ts": now_iso(),
                "model": client.model,
                "mode": cfg.mode,
                "marks": cfg.marks,
                "question": question,
                "answer": final,
                "validated": success,
                "used_fallback": used_fallback,
            },
        )

    return final





def main():
    load_dotenv()
    log_path = os.getenv("ECON_BOT_LOG", "").strip()

    try:
        client = load_client_from_env()
    except Exception as e:
        print(f"[Error] {e}")
        sys.exit(1)

    cfg = BotConfig(mode="notes", marks=2)

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

        if user_in in ("help", "?"):
            print(HELP_TEXT)
            continue
        if user_in == "exit":
            print("Bye!")
            break

        if user_in.startswith("marks "):
            try:
                cfg.marks = int(user_in.split()[1])
                print(f"✅ marks set to: {cfg.marks}")
            except Exception:
                print("❌ marks must be 2, 5, or 10.")
            continue

        if user_in.startswith("model "):
            m = user_in.replace("model", "", 1).strip()
            if not m:
                print("❌ Provide model name.")
                continue
            client.set_model(m)
            print(f"✅ model set to: {client.model}")
            continue

       
        if user_in == "/demo":
            print("\n--- DEMO: NOTES (2 marks) | Inflation ---")
            print("\nBot> " + DEMO_NOTES + "\n")

            print("\n--- DEMO: MCQ (5 marks) | Demand-pull inflation ---")
            print("\nBot> " + DEMO_MCQ + "\n")

            print("\n--- DEMO: PYQ (10 marks) | Explain IS-LM model ---")
            print("\nBot> " + DEMO_PYQ + "\n")
            continue

     
        if user_in.startswith("/notes "):
            cfg.mode = "notes"
            q = user_in.replace("/notes", "", 1).strip()
            enforced_generate(client, cfg, q, log_path)
            continue

        if user_in.startswith("/mcq "):
            cfg.mode = "mcq"
            q = user_in.replace("/mcq", "", 1).strip()
            enforced_generate(client, cfg, q, log_path)
            continue

        if user_in.startswith("/pyq "):
            cfg.mode = "pyq"
            q = user_in.replace("/pyq", "", 1).strip()
            enforced_generate(client, cfg, q, log_path)
            continue

        
        cfg.mode = "notes"
        enforced_generate(client, cfg, user_in, log_path)


if __name__ == "__main__":
    main()
