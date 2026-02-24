import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_notification(message: str, notification_type: str = "info") -> bool:
    """
    Sends a notification via Telegram.

    Args:
        message: The text to send
        notification_type: "info" | "warning" | "success" | "alert"

    Returns:
        bool: Whether the send was successful
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram token or chat ID missing — check your .env file")
        return False

    emoji_map = {
        "info": "📨",
        "warning": "⚠️",
        "success": "✅",
        "alert": "🚨",
    }
    emoji = emoji_map.get(notification_type, "📌")

    full_message = f"{emoji} *Career Agent Notification*\n\n{message}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[Telegram] {emoji} Notification sent.")
            return True
        else:
            print(f"[Telegram] Error: {response.status_code} — {response.text}")
            return False
    except Exception as e:
        print(f"[Telegram] Connection error: {e}")
        return False


def notify_new_message(employer_name: str, preview: str) -> bool:
    """Sends a notification when a new employer message arrives."""
    return send_notification(
        f"New employer message!\n*From:* {employer_name}\n*Preview:* {preview[:100]}{'...' if len(preview) > 100 else ''}",
        "info",
    )


def notify_response_sent(score: int) -> bool:
    """Sends a notification when a reply is approved and sent."""
    return send_notification(
        f"Reply approved and sent.\n*Evaluation Score:* {score}/10",
        "success",
    )


def notify_human_needed(reason: str) -> bool:
    """Sends an urgent notification when human intervention is required."""
    return send_notification(
        f"HUMAN INTERVENTION REQUIRED!\n*Reason:* {reason}",
        "alert",
    )


def notify_retry(attempt: int, score: int) -> bool:
    """Sends a retry notification when the evaluator score is too low."""
    return send_notification(
        f"Reply was insufficient — rewriting.\n*Attempt:* {attempt}\n*Previous score:* {score}/10",
        "warning",
    )
