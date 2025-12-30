# 📘 Economics Explainer Bot (CLI)

A lightweight offline CLI tool that generates **IGNOU-style economics answers** in three formats — **Notes, MCQs, and PYQ guidance** — with strict exam-oriented templates. Runs on **Ollama (CPU-friendly, no API required)** and supports marks-based responses (2/5/10).

---

## 🎯 Features

- 📝 Notes mode (Key Terms, Core Points, Diagram, Exam Questions)  
- 🧠 MCQ mode (5 Questions + Answer Key)  
- 🏛 PYQ mode (Answer-structure guidance)  
- 🎚 Marks-aware output (2/5/10)  
- 🛡 Template validation + fallback reliability  
- 💾 JSONL logging for all responses  
- ⚡ Fully offline, CLI-based, fast

---

## 📂 Project Structure

```
app/
  main.py
  llm.py
  prompts.py
  utils.py
logs/
  chat.jsonl   
```
---

## ⚙️ Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull llama3.2:1b
```

Optional `.env`:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
ECON_BOT_LOG=logs/chat.jsonl
```

Run:

```bash
python -m app.main
```

---

## 🧩 Commands

```
/notes <topic>
/mcq <topic>
/pyq <topic>
marks 2|5|10
/demo
exit
```

---

## 🎬 Demo 

```powershell
@"
/demo
exit
"@ | python -m app.main
```

---

## 🧪 Test Execution

```powershell
@"
/mcq monetary policy
/pyq monetary policy
/notes monetary policy
exit
"@ | python -m app.main
```

---

## 📜 Logs (JSONL)

View last entries:

```powershell
Get-Content logs/chat.jsonl -Tail 5
```

Example record:

```json
{
  "mode": "mcq",
  "question": "monetary policy",
  "validated": true,
  "used_fallback": true
}
```

---

## 🧠 Purpose

Designed for **exam-disciplined learning**, structured formatting, and reliable offline generation using strict templates and validation safeguards.

---

## 🧾 License

MIT — free to use and extend.
