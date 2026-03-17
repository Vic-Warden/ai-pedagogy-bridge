# AI Pedagogy Bridge 

A fully local AI-powered learning platform for high school. Students ask questions, get guided answers, revision sheets and targeted exercises. Teachers see class difficulties in real time, get AI reports and gamified teaching ideas. Runs 100% offline with Ollama — no data leaves the machine.

---

## Features

### Student Side

| Feature | What it does |
|---|---|
| **AI Tutor Chat** | Student asks questions about the course PDF. The AI answers only from the course content and guides without giving the answer directly. |
| **Revision Sheet** | The AI builds a personalized revision sheet from all questions asked during the session. Downloadable as `.md`. |
| **Exercise Suggestions** | The AI searches `exercices.pdf` and suggests the best exercises based on the student's weak points. |
| **Optional ID** | Students can enter their name at start or continue anonymously. Questions are logged accordingly. |
| **🟡 "J'ai du mal"** | One-click anonymous signal, always available. The teacher sees a live count of struggling students. |
| **🔴 "Besoin d'aide"** | Unlocked after 3 questions. Student can describe the problem and choose to stay anonymous or share their name. |

### Teacher Side

| Feature | What it does |
|---|---|
| **Dashboard** | KPIs (total questions, active students, top topic, repeated questions), interactive charts, filter by student, CSV/Markdown export. |
| **Class Thermometer** | Live count of 🟡 and 🔴 signals, progress bar, breakdown charts, filterable signal journal, CSV export. |
| **AI Synthesis** | The AI analyzes all student questions and generates a report: critical topics, per-student analysis, weak signals, actionable recommendations. |
| **Challenges** | The AI generates gamified teaching ideas (battles, sprints, escape games…) to engage students. |

---

## Tech Stack

| Component | Tool |
|---|---|
| Web UI | Streamlit |
| LLM (local) | Ollama — LLaMA 3.2 |
| Embeddings (local) | Ollama — nomic-embed-text |
| LLM Orchestration | LangChain |
| Vector Store | ChromaDB |
| PDF Parsing | PyPDF |
| Charts | Plotly |

---

## Installation

### 1. Install Ollama

```bash
brew install ollama
```

Or download from [ollama.com](https://ollama.com).

### 2. Pull the models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Add course PDFs

Place files in `course_materials/`:
- `chapitre1.pdf` — the course
- `exercices.pdf` — the exercise book

---

## Run

```bash
ollama serve
streamlit run app.py
```

> **macOS note**: if `python3` points to Homebrew, use `/usr/bin/python3 -m streamlit run app.py`.

Opens at `http://localhost:8501`.

---

## Project Structure

```
app.py                 # Entry point, sidebar navigation
student_space.py       # Student space (anonymous, chat, signals)
teacher_space.py       # Teacher space (dashboard, signals, synthesis, challenges)
rag_logic.py           # AI logic 
requirements.txt       # Python dependencies
course_materials/      # Course + exercise PDFs
questions_log.csv      # Student question log 
signals_log.csv        # Student help signals log
```

---

## How It Works

```
Student opens the platform
        │
        ▼
Optional: enter name or stay anonymous
        │
        ▼
Student asks a question
        │
        ▼
Course PDF → chunks → embeddings (nomic-embed-text)
        │
        ▼
Most relevant chunks retrieved (RAG)
        │
        ▼
LLaMA 3.2 generates a guided answer
        │
        ▼
Question logged to CSV for the teacher
        │
        ▼
🟡 "J'ai du mal" → 1 click, always available, anonymous
🔴 "Besoin d'aide" → after 3 questions, message + anonymous/named
        │
        ▼
Teacher sees live class thermometer (🟡 vs 🔴)
```
Signal appears in real time on the teacher dashboard
```