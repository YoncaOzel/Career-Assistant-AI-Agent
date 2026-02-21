# Career Assistant AI Agent

An autonomous AI agent that monitors incoming employer messages and automatically drafts, evaluates, and logs professional email responses — powered by OpenAI GPT-4o-mini, orchestrated with FastAPI, and connected to Telegram for real-time notifications.

---

## What It Does

When a recruiter or employer sends a message, the agent:

1. **Detects** whether the message requires human involvement (salary negotiation, legal terms, out-of-domain questions)
2. **Generates** a professional, context-aware email reply using your CV profile
3. **Evaluates** the reply across 5 quality dimensions and rewrites it if the score is below the threshold
4. **Notifies** you in real time via Telegram at every stage
5. **Logs** every interaction to a local JSON file for audit and review

---

## System Architecture

```
career-agent/
├── main.py                  # FastAPI app & agent pipeline orchestrator
├── start.py                 # Server launcher
├── requirements.txt
├── .env                     # API keys (not committed)
├── agents/
│   ├── career_agent.py      # Generates professional email replies
│   └── evaluator_agent.py   # Scores and approves responses
├── tools/
│   ├── unknown_detector.py  # Identifies messages needing human review
│   └── notification.py      # Telegram notification helpers
├── data/
│   ├── cv_profile.json      # Your personal profile (skills, experience, etc.)
│   └── logs.json            # Interaction history
└── templates/
    └── index.html           # Browser-based demo UI
```

---

## System Flow

```mermaid
flowchart TD
    A([📨 Employer Message\nPOST /process-message]) --> B[Telegram Notification\nNew message alert]
    B --> C{Unknown Detector\nGPT-4o-mini analysis}

    C -->|requires_human = true\nconfidence ≥ 0.8| D[🚨 Telegram Alert\nHuman intervention needed]
    D --> E([⛔ Response: human_required\nCategory + Reason returned])

    C -->|Safe to automate| F[Career Agent\nGPT-4o-mini + CV Profile]
    F --> G[Draft Response\nProfessional email reply]

    G --> H{Evaluator Agent\nGPT-4o-mini — 5 criteria}
    H --> |Score ≥ 7 / 10\nApproved ✅| I[✅ Telegram Notification\nResponse sent + score]
    H --> |Score < 7 / 10\nAttempt < 3| J[⚠️ Telegram Warning\nRetrying...]
    J --> K[Career Agent\nRewrite with feedback]
    K --> H
    H --> |Score < 7 / 10\nAttempt = 3| I

    I --> L[(data/logs.json\nLog interaction)]
    L --> M([✅ Response: sent\nFinal email + evaluation])

    subgraph Evaluation Criteria
        N[professional_tone 0-2]
        O[clarity 0-2]
        P[completeness 0-2]
        Q[safety 0-2]
        R[relevance 0-2]
    end

    H -.-> Evaluation Criteria
```

---

## Core Components

### 1. Career Agent (`agents/career_agent.py`)

Generates a professional email reply to the employer's message using your full CV profile as context.

- Model: `gpt-4o-mini`
- Output length: 150–250 words
- Classifies message type: `interview_invite` · `job_offer` · `technical_question` · `decline` · `clarification` · `other`
- Strictly grounded in your real profile — no hallucinations or exaggerations

### 2. Evaluator Agent (`agents/evaluator_agent.py`)

Scores the generated response across 5 criteria (each 0–2 points, max 10):

| Criterion | Description |
|---|---|
| `professional_tone` | Polite, formal language |
| `clarity` | Clear and coherent content |
| `completeness` | Fully addresses the employer's question |
| `safety` | No false, fabricated, or harmful information |
| `relevance` | Directly related to the incoming message |

- **Approval threshold:** 7 / 10
- **Max retries:** 3 (each retry feeds evaluator feedback back to the Career Agent)

### 3. Unknown Detector (`tools/unknown_detector.py`)

Before generating any response, this tool analyzes the message to check whether it falls outside the agent's safe operating zone:

| Category | Trigger |
|---|---|
| `salary_negotiation` | Specific salary figures or bargaining expected |
| `out_of_domain` | Deep technical questions on unknown technologies |
| `legal` | Contract clauses, non-compete, equity, stock |
| `ambiguous` | Suspicious, vague, or manipulative offer |
| `none` | Safe to automate |

If `requires_human = true` AND `confidence_score ≥ 0.8`, the pipeline stops and sends an urgent Telegram alert.

### 4. Telegram Notifications (`tools/notification.py`)

You are notified at every key stage:

| Event | Type |
|---|---|
| New employer message received | 📨 Info |
| Human intervention required | 🚨 Alert |
| Response re-evaluated (score low) | ⚠️ Warning |
| Response approved and sent | ✅ Success |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/process-message` | Run the full agent pipeline |
| `GET` | `/logs` | Retrieve all interaction logs |
| `DELETE` | `/logs` | Clear all logs |
| `GET` | `/health` | Server health check |
| `GET` | `/` | Browser demo UI |
| `GET` | `/docs` | Interactive Swagger API docs |

### Request Body — `/process-message`

```json
{
  "sender_name": "Jane Smith (Acme Corp)",
  "message": "Hi, we'd like to invite you for a technical interview next week. Are you available?"
}
```

### Response — success

```json
{
  "status": "sent",
  "response": "Dear Jane, Thank you for reaching out...",
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
    "feedback": "Well-structured and professional reply."
  },
  "attempts": 1
}
```

### Response — human required

```json
{
  "status": "human_required",
  "reason": "Employer is requesting a specific salary figure",
  "category": "salary_negotiation"
}
```

---

## Setup

### Prerequisites

- Python 3.10+
- OpenAI API key
- Telegram bot token and chat ID

### Installation

```bash
git clone https://github.com/your-username/Career-Assistant-AI-Agent.git
cd Career-Assistant-AI-Agent/career-agent

python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file inside `career-agent/`:

```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456789:AAF...
TELEGRAM_CHAT_ID=987654321
```

### Configure Your Profile

Edit `data/cv_profile.json` with your real information:

```json
{
  "name": "Your Full Name",
  "title": "Backend Developer",
  "experience_years": 2,
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "education": "Computer Engineering, XYZ University, 2024",
  "languages": ["English (C1)", "Turkish (native)"],
  "remote_ok": true,
  "willing_to_relocate": false,
  "available_for_work": true,
  "expertise_domains": ["REST API development", "Database design"],
  "non_expertise_domains": ["Salary negotiation", "Legal contract terms"]
}
```

### Run

```bash
python start.py
```

The server starts at `http://localhost:8000`.  
Open `http://localhost:8000` in your browser for the demo UI, or `http://localhost:8000/docs` for the Swagger interface.

---

## How to Get a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts — you'll receive a **bot token**
3. Start a conversation with your new bot
4. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` to find your **chat ID**
5. Add both values to your `.env` file

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| AI Models | OpenAI GPT-4o-mini |
| Notifications | Telegram Bot API |
| Data Storage | JSON files (logs.json) |
| Runtime | Python 3.10+ / Uvicorn |
| Dependencies | openai · fastapi · uvicorn · python-dotenv · requests · pydantic |

---

## License

MIT
