import json
import datetime
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from agents.career_agent import generate_response
from agents.evaluator_agent import evaluate_response, SCORE_THRESHOLD
from tools.notification import (
    notify_new_message,
    notify_response_sent,
    notify_human_needed,
    notify_retry,
)
from tools.unknown_detector import detect_unknown
from rag.pdf_loader import get_vector_store

# ---------------------------------------------------------------------------
# Lifespan — startup'ta CV'yi indexle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Indexes the CV on startup and cleans up on shutdown."""
    print("🚀 Career Agent starting...")
    get_vector_store()  # First run reads the PDF; subsequent runs load from cache
    print("✅ CV indexed successfully, system ready.")
    yield

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Career Assistant AI Agent",
    description="Automatically generates professional replies to employer messages.",
    version="1.1",
    lifespan=lifespan,
)

# Serve static files (templates/ directory)
_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=_templates_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Logs all unhandled exceptions and returns a detailed 500 response."""
    tb = traceback.format_exc()
    print(f"\n❌ ERROR — {request.method} {request.url}\n{tb}", flush=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb},
    )

# ---------------------------------------------------------------------------
# Pydantic modeli
# ---------------------------------------------------------------------------


class EmployerMessage(BaseModel):
    sender_name: str
    message: str


class HumanResponse(BaseModel):
    sender_name: str
    message: str
    human_reply: str
    category: str = ""
    reason: str = ""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

LOGS_PATH = os.path.join(os.path.dirname(__file__), "data", "logs.json")


def log_interaction(data: dict) -> None:
    """Saves all interactions to data/logs.json."""
    try:
        with open(LOGS_PATH, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = []

    data["timestamp"] = datetime.datetime.now().isoformat()
    logs.append(data)

    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/process-message")
async def process_message(payload: EmployerMessage):
    """
    Main endpoint — runs the full agent pipeline.

    Pipeline:
        1. Telegram: new message notification
        2. Unknown Detector: is human intervention required?
        3. Career Agent: generate reply
        4. Evaluator Agent: score the reply (max 3 attempts)
        5. Telegram: result notification
        6. Log: save the interaction
    """

    # ------------------------------------------------------------------
    # 1. New message notification
    # ------------------------------------------------------------------
    notify_new_message(payload.sender_name, payload.message)

    # ------------------------------------------------------------------
    # 2. Unknown Detection — stop if high-confidence human required
    # ------------------------------------------------------------------
    detection = detect_unknown(payload.message)

    if detection["requires_human"] and detection["confidence_score"] >= 0.8:
        notify_human_needed(f"{detection['category']}: {detection['reason']}")
        log_interaction(
            {
                "sender": payload.sender_name,
                "message": payload.message,
                "action": "human_intervention_requested",
                "detection": detection,
            }
        )
        return {
            "status": "human_required",
            "reason": detection["reason"],
            "category": detection["category"],
        }

    # ------------------------------------------------------------------
    # 3. Career Agent — generate initial reply
    # ------------------------------------------------------------------
    agent_result = generate_response(payload.message)
    final_response = agent_result["response"]
    evaluation = None
    attempt = 0

    # ------------------------------------------------------------------
    # 4. Evaluator Agent — max 3 attempts
    # ------------------------------------------------------------------
    max_retries = 3

    for attempt in range(max_retries):
        evaluation = evaluate_response(payload.message, final_response)

        if evaluation["approved"]:
            break  # Good enough — exit loop

        if attempt < max_retries - 1:
            # Low score → send notification, then rewrite
            notify_retry(attempt + 1, evaluation["total_score"])

            improvement_prompt = (
                f"{payload.message}\n\n"
                f"[PREVIOUS REPLY WAS INSUFFICIENT]\n"
                f"Evaluator feedback: {evaluation['suggestions']}\n"
                f"Please write a better reply taking this feedback into account."
            )
            agent_result = generate_response(improvement_prompt)
            final_response = agent_result["response"]

    # ------------------------------------------------------------------
    # 5. Result notification
    # ------------------------------------------------------------------
    notify_response_sent(evaluation["total_score"])

    # ------------------------------------------------------------------
    # 6. Log
    # ------------------------------------------------------------------
    log_interaction(
        {
            "sender": payload.sender_name,
            "message": payload.message,
            "final_response": final_response,
            "evaluation": evaluation,
            "message_type": agent_result["message_type"],
            "attempts": attempt + 1,
            "detection": detection,
        }
    )

    return {
        "status": "sent",
        "response": final_response,
        "message_type": agent_result["message_type"],
        "evaluation": {
            "score": evaluation["total_score"],
            "approved": evaluation["approved"],
            "scores": evaluation["scores"],
            "feedback": evaluation["feedback"],
        },
        "attempts": attempt + 1,
    }


@app.post("/submit-human-response")
async def submit_human_response(payload: HumanResponse):
    """
    Human types their own reply after intervention was required.
    Logs the interaction and returns the submitted response.
    """
    log_interaction(
        {
            "sender": payload.sender_name,
            "message": payload.message,
            "final_response": payload.human_reply,
            "action": "human_response_submitted",
            "category": payload.category,
            "reason": payload.reason,
        }
    )
    return {
        "status": "sent",
        "response": payload.human_reply,
        "message_type": "human_response",
        "submitted_by": "human",
    }


@app.get("/logs")
async def get_logs():
    """Returns all interaction logs."""
    try:
        with open(LOGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.delete("/logs")
async def clear_logs():
    """Clears the log file."""
    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"status": "ok", "message": "Logs cleared."}


@app.get("/health")
async def health():
    """Server health check."""
    return {"status": "ok", "agent": "Career Assistant v1.1"}


@app.get("/dashboard")
async def dashboard():
    """Serves the confidence scoring dashboard."""
    dashboard_path = os.path.join(os.path.dirname(__file__), "templates", "dashboard.html")
    return FileResponse(dashboard_path)


# ---------------------------------------------------------------------------
# Main HTML UI
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serves the main UI."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html><body>
        <h2>Career Assistant AI Agent is running!</h2>
        <p>API Docs: <a href='/docs'>/docs</a></p>
        </body></html>
        """
