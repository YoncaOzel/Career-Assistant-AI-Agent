import json
import datetime
import traceback
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
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

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Career Assistant AI Agent",
    description="İşveren mesajlarına otomatik profesyonel yanıt üretir.",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Tüm yakalanmamış hataları loglar ve detaylı 500 döner."""
    tb = traceback.format_exc()
    print(f"\n❌ HATA — {request.method} {request.url}\n{tb}", flush=True)
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


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

LOGS_PATH = os.path.join(os.path.dirname(__file__), "data", "logs.json")


def log_interaction(data: dict) -> None:
    """Tüm etkileşimleri data/logs.json dosyasına kaydeder."""
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
    Ana endpoint — tam agent pipeline'ını çalıştırır.

    Pipeline:
        1. Telegram: yeni mesaj bildirimi
        2. Unknown Detector: insan müdahalesi gerekiyor mu?
        3. Career Agent: yanıt üret
        4. Evaluator Agent: yanıtı puanla (max 3 deneme)
        5. Telegram: sonuç bildirimi
        6. Log: etkileşimi kaydet
    """

    # ------------------------------------------------------------------
    # 1. Yeni mesaj bildirimi
    # ------------------------------------------------------------------
    notify_new_message(payload.sender_name, payload.message)

    # ------------------------------------------------------------------
    # 2. Unknown Detection — eğer yüksek güvenle insan gerekiyorsa dur
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
    # 3. Career Agent — ilk yanıtı üret
    # ------------------------------------------------------------------
    agent_result = generate_response(payload.message)
    final_response = agent_result["response"]
    evaluation = None
    attempt = 0

    # ------------------------------------------------------------------
    # 4. Evaluator Agent — max 3 deneme
    # ------------------------------------------------------------------
    max_retries = 3

    for attempt in range(max_retries):
        evaluation = evaluate_response(payload.message, final_response)

        if evaluation["approved"]:
            break  # Yeterince iyi — döngüden çık

        if attempt < max_retries - 1:
            # Puan düşük → bildirim gönder, ardından yeniden yaz
            notify_retry(attempt + 1, evaluation["total_score"])

            improvement_prompt = (
                f"{payload.message}\n\n"
                f"[ÖNCEKİ YANIT YETERSİZ BULUNDU]\n"
                f"Değerlendirici geri bildirimi: {evaluation['suggestions']}\n"
                f"Lütfen bu geri bildirimi dikkate alarak daha iyi bir yanıt yaz."
            )
            agent_result = generate_response(improvement_prompt)
            final_response = agent_result["response"]

    # ------------------------------------------------------------------
    # 5. Sonuç bildirim
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


@app.get("/logs")
async def get_logs():
    """Tüm etkileşim loglarını döndürür."""
    try:
        with open(LOGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


@app.delete("/logs")
async def clear_logs():
    """Log dosyasını temizler."""
    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"status": "ok", "message": "Loglar temizlendi."}


@app.get("/health")
async def health():
    """Sunucu sağlık kontrolü."""
    return {"status": "ok", "agent": "Career Assistant v1.0"}


# ---------------------------------------------------------------------------
# Basit HTML demo arayüzü
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def root():
    """Demo arayüzünü döndürür."""
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
