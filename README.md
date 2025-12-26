# 📘 Economics Explainer Bot (CLI)

An **exam-oriented Economics chatbot** designed for **IGNOU / university exams**, built as a **CLI application** using **Ollama (local LLMs)**.

The bot generates **structured, exam-ready answers** with strict formatting and mark-wise length control.

---

## ✨ Features

### 🔹 Core Capabilities
- Exam-friendly explanations
- Structured outputs (no free-form chat)
- Mark-wise answers: **2 / 5 / 10 marks**
- Runs **fully offline** using Ollama

### 🔹 IGNOU-Style Slash Commands (Milestone 3)
- `/notes <topic>` → Short exam notes  
- `/mcq <topic>` → 5 MCQs + Answer Key  
- `/pyq <topic>` → How to answer in exam (structure + expectations)

### 🔹 Output Discipline
- Guaranteed section completion (no truncation)
- Auto-retries and formatting guards
- Suitable for **written exam preparation**

---

## 🧠 Supported Modes

| Mode | Purpose |
|-----|--------|
| `notes` | Exam notes (Key terms, core points, diagram, questions) |
| `mcq` | Multiple-choice questions with answer key |
| `pyq` | Exam writing guidance |
| `explain` | Concept explanation (structured) |
| `numerical` | Step-by-step numerical answers |
| `exam` | Full descriptive answers |

---

## ⚙️ Setup Instructions

### 1️⃣ Install Ollama
Download and install Ollama from:  
👉 https://ollama.com

Pull a lightweight model (recommended for CPU):
```bash
ollama pull llama3.2:1b
```