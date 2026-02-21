import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_cv() -> dict:
    """CV profil verisini yükler."""
    cv_path = os.path.join(os.path.dirname(__file__), "..", "data", "cv_profile.json")
    with open(cv_path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_unknown(employer_message: str) -> dict:
    """
    Mesajın insan müdahalesi gerektirip gerektirmediğini tespit eder.

    Args:
        employer_message: İşverenin gönderdiği mesaj

    Returns:
        dict: {
            "requires_human": bool,
            "confidence_score": float,  # 0.0 - 1.0
            "reason": str,
            "category": str             # salary_negotiation | out_of_domain | legal | ambiguous | none
        }
    """
    cv = load_cv()

    detection_prompt = f"""
Bir kariyer asistanı olarak şu mesajı analiz et.

## Kullanıcı Profili - Bildiği Teknolojiler:
{', '.join(cv['skills'])}

## Uzmanlık Alanları:
{', '.join(cv['expertise_domains'])}

## Kullanıcı Profili - BİLMEDİĞİ / Ele Alamayacağı Alanlar:
{', '.join(cv['non_expertise_domains'])}

## İşveren Mesajı:
{employer_message}

## Görev:
Bu mesaj aşağıdaki durumlardan birini içeriyor mu?
- Maaş rakamı müzakeresi (rakam verilmesi, pazarlık yapılması isteniyor)
- Profildeki beceriler dışında derin teknik soru (bilinmeyen teknoloji)
- Hukuki veya sözleşme detayları (non-compete, equity, hukuki maddeler)
- Belirsiz veya manipülatif teklif (şüpheli, yetersiz bilgi içeren)

Sadece JSON döndür, başka hiçbir şey yazma:
{{
    "requires_human": true,
    "confidence_score": 0.0,
    "reason": "neden insan gerekli veya değil",
    "category": "salary_negotiation | out_of_domain | legal | ambiguous | none"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": detection_prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Tip güvencesi: gerekli field'ların var olduğundan emin ol
    return {
        "requires_human": bool(result.get("requires_human", False)),
        "confidence_score": float(result.get("confidence_score", 0.0)),
        "reason": str(result.get("reason", "")),
        "category": str(result.get("category", "none")),
    }
