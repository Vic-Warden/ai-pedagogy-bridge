# AI Pedagogy Bridge 

AI-powered teaching assistant built on RAG (Retrieval-Augmented Generation) that helps students understand their course material while giving teachers analytics on common misunderstandings.

## Features

- Student Space — AI chat that answers strictly from the course content (PDF).
- Teacher Dashboard — Visualisation of frequent questions to help adapt future lectures.

## Tech Stack

| Component | Tool |
|-----------|------|
| Web UI | Streamlit |
| LLM Orchestration | LangChain |
| AI Model | Google Gemini |
| Vector Store | ChromaDB |
| PDF Parsing | PyPDF |

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

## Project Structure

```
app.py                 # Entry point & routing
student_space.py       # Student interface (PDF + chat)
teacher_space.py       # Teacher dashboard (analytics)
rag_logic.py           # RAG pipeline (embedding, retrieval, generation)
course_materials/      # Course PDFs
database/              # Question logs (CSV)
```

## Configuration

Set your Google Gemini API key in `rag_logic.py`:

```python
os.environ["GOOGLE_API_KEY"] = "your-key-here"
```