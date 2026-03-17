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
| **Student ID** | Each student enters their name before starting. All questions are logged with their identity. |

### Teacher Side

| Feature | What it does |
|---|---|
| **Dashboard** | KPIs (total questions, active students, top topic, repeated questions), interactive charts, filter by student, CSV/Markdown export. |
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
student_space.py       # Student space 
teacher_space.py       # Teacher space 
rag_logic.py           # AI logic 
requirements.txt       # Python dependencies
course_materials/      # Course + exercise PDFs
questions_log.csv      # Student question log 
```

---

## How It Works

```
Student asks a question
        │
        ▼
Course PDF is split into chunks
        │
        ▼
Chunks are embedded locally (nomic-embed-text)
        │
        ▼
Most relevant chunks are retrieved (RAG)
        │
        ▼
LLaMA 3.2 generates a guided answer
        │
        ▼
Question is logged to CSV for the teacher
```