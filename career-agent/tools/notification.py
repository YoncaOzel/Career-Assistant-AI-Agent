import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_notification(message: str, notification_type: str = "info") -> bool:
    """
    Telegram üzerinden bildirim gönderir.

    Args:
        message: Gönderilecek metin
        notification_type: "info" | "warning" | "success" | "alert"

    Returns:
        bool: Gönderim başarılı mı?
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram token veya chat ID eksik — .env dosyasını kontrol et")
        return False

    emoji_map = {
        "info": "📨",
        "warning": "⚠️",
        "success": "✅",
        "alert": "🚨",
    }
    emoji = emoji_map.get(notification_type, "📌")

    full_message = f"{emoji} *Career Agent Bildirimi*\n\n{message}"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[Telegram] {emoji} Bildirim gönderildi.")
            return True
        else:
            print(f"[Telegram] Hata: {response.status_code} — {response.text}")
            return False
    except Exception as e:
        print(f"[Telegram] Bağlantı hatası: {e}")
        return False


def notify_new_message(employer_name: str, preview: str) -> bool:
    """Yeni işveren mesajı geldiğinde bildirim gönderir."""
    return send_notification(
        f"Yeni işveren mesajı!\n*Gönderen:* {employer_name}\n*Önizleme:* {preview[:100]}{'...' if len(preview) > 100 else ''}",
        "info",
    )


def notify_response_sent(score: int) -> bool:
    """Yanıt onaylanıp gönderildiğinde bildirim gönderir."""
    return send_notification(
        f"Yanıt onaylandı ve gönderildi.\n*Değerlendirme Puanı:* {score}/10",
        "success",
    )


def notify_human_needed(reason: str) -> bool:
    """İnsan müdahalesi gerektiğinde acil bildirim gönderir."""
    return send_notification(
        f"İNSAN MÜDAHALESİ GEREKLİ!\n*Sebep:* {reason}",
        "alert",
    )


def notify_retry(attempt: int, score: int) -> bool:
    """Evaluator skoru düşük olduğunda yeniden deneme bildirimi gönderir."""
    return send_notification(
        f"Yanıt yetersiz bulundu — yeniden yazılıyor.\n*Deneme:* {attempt}\n*Önceki puan:* {score}/10",
        "warning",
    )
