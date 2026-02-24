# 🤖 Career Assistant AI Agent

An AI agent system that automatically generates professional replies to employer emails by retrieving information from a PDF CV, scoring each reply to guarantee quality.

---

## 📋 Features

### v1.0 — Core System
- **Career Agent** — Generates professional email replies using GPT-4o-mini
- **Evaluator Agent** — Scores replies across 5 criteria × 0-2 points (total 10); rewrites up to 3 times until score ≥ 7
- **Unknown Detector** — Detects salary negotiation, unknown technology, legal details, or suspicious offers and routes to human intervention
- **Telegram Notifications** — Instant notifications at every stage (new message, reply sent, retry, human intervention)

### v1.1 — RAG + Confidence Dashboard
- **RAG Integration** — `data/cv.pdf` is loaded as a PDF; vectorized with LangChain + FAISS; message-specific CV sections are semantically retrieved for each reply
- **Confidence Scoring Dashboard** — Real-time web UI showing score history, message type distribution, and criteria bars (Chart.js, auto-refreshes every 30 s)

---

## 🗂 Folder Structure

```
career-agent/
├── main.py                      # FastAPI application, all endpoints
├── requirements.txt
├── .env                         # API keys (do NOT commit to git!)
│
├── agents/
│   ├── career_agent.py          # RAG-powered reply generator
│   └── evaluator_agent.py       # 5-criteria quality evaluator
│
├── rag/
│   ├── __init__.py
│   ├── pdf_loader.py            # PDF → chunk → FAISS vector store
│   └── retriever.py             # Semantic search, CV summary
│
├── tools/
│   ├── notification.py          # Telegram notifications
│   └── unknown_detector.py      # Human intervention detection (RAG-powered)
│
├── templates/
│   ├── index.html               # Main UI
│   └── dashboard.html           # Confidence scoring dashboard
│
└── data/
    ├── cv.pdf                   # ← Place your CV here
    ├── vector_store/            # Auto-generated (FAISS index)
    ├── cv_profile.json          # Reference (no longer actively used)
    └── logs.json                # Interaction logs
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Create the `.env` file

```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC-...
TELEGRAM_CHAT_ID=123456789
```

### 3. Place your CV

```bash
# Put your PDF CV at this location:
data/cv.pdf
```

---

## 🚀 Launch

```bash
uvicorn main:app --reload --port 8000
```

On first launch, the PDF is read and `data/vector_store/` is created:

```
🚀 Career Agent starting...
📄 Reading and indexing PDF...
   → 3 pages, 24 chunks created
✅ Vector store saved: data/vector_store
✅ CV indexed successfully, system ready.
```

Subsequent launches load from disk (the `📄` message won't appear).

| URL | Description |
|-----|----------|
| http://localhost:8000 | Main UI |
| http://localhost:8000/dashboard | Confidence scoring dashboard |
| http://localhost:8000/docs | Swagger API docs |
| http://localhost:8000/logs | Ham log verisi (JSON) |

---

## 🔄 System Flow

```
[Employer Message — POST /process-message]
              │
              ▼
  ┌─────────────────────┐
  │  Telegram Notification  │  ← "New message received"
  └─────────────────────┘
              │
              ▼
  ┌─────────────────────┐
  │   Unknown Detector   │  ← Retrieves CV summary via RAG
  └─────────────────────┘
              │
    ┌─────────┴──────────┐
    │ confidence ≥ 0.8   │
    │ and human needed?  │
    └─────────┬──────────┘
         YES │                   NO
              ▼                     │
  ┌─────────────────────┐           │
  │  Human Intervention  │           │
  │  (Telegram + log)    │           │
  └─────────────────────┘           │
                                    ▼
                        ┌─────────────────────┐
                        │    RAG Retriever     │  ← Message-specific CV sections
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │    Career Agent      │  ← GPT-4o-mini + CV context
                        └─────────────────────┘
                                    │
                              ┌─────▼─────┐
                              │ Evaluator │  ← 5 criteria × 0-2 = /10
                              └─────┬─────┘
                                    │
                          ┌─────────┴──────────┐
                          │    Score ≥ 7?        │
                          └─────────┬──────────┘
                     YES           │           NO (max 3 attempts)
                       ◄────────────┘──────────────►
                       │                            │
                       ▼                            ▼
           ┌─────────────────────┐   ┌─────────────────────────┐
           │  Reply Sent          │   │  Career Agent rewrites  │
           │  Telegram Notification│   │  (with suggestions)     │
           └─────────────────────┘   └─────────────────────────┘
                       │
                       ▼
           ┌─────────────────────┐
           │  Interaction logged  │  → data/logs.json
           └─────────────────────┘
                       │
                       ▼
           ┌─────────────────────┐
           │  Dashboard updated   │  ← /dashboard auto-refreshes
           └─────────────────────┘
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|----------|
| `POST` | `/process-message` | Main pipeline — processes an employer message |
| `GET`  | `/logs` | Returns all interaction logs |
| `DELETE` | `/logs` | Clears the log file |
| `GET`  | `/dashboard` | Confidence scoring UI |
| `GET`  | `/health` | Server health check |
| `GET`  | `/docs` | Swagger UI |

### Example Request

```bash
curl -X POST http://localhost:8000/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "sender_name": "ACME Corp",
    "message": "We would like to invite you for a technical interview next week."
  }'
```

### Example Response

```json
{
  "status": "sent",
  "response": "Dear Hiring Team, Thank you for...",
  "message_type": "interview_invite",
  "evaluation": {
    "score": 9,
    "approved": true,
    "scores": {
      "professional_tone": 2,
      "clarity": 2,
      "completeness": 2,
      "safety": 2,
      "relevance": 1
    },
    "feedback": "Strong professional tone..."
  },
  "attempts": 1
}
```

---

## 🔁 Updating the CV

After replacing your CV, delete the old vector store and the system will re-index automatically:

```bash
# Windows
Remove-Item -Recurse -Force data/vector_store

# Linux / macOS
rm -rf data/vector_store/

# Restart
uvicorn main:app --reload --port 8000
```

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|------------|
| API framework | FastAPI |
| LLM | OpenAI GPT-4o-mini |
| RAG pipeline | LangChain + FAISS |
| Embedding | text-embedding-3-small |
| PDF reading | PyPDF |
| Notifications | Telegram Bot API |
| Dashboard | Chart.js (CDN) |
