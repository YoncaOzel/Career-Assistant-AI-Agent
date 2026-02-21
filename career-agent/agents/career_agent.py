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


def generate_response(employer_message: str) -> dict:
    """
    İşveren mesajına profesyonel e-posta yanıtı üretir.

    Args:
        employer_message: İşverenin gönderdiği mesaj (veya feedback ile birleştirilmiş retry mesajı)

    Returns:
        dict: {
            "response": str,        # Üretilen e-posta yanıtı
            "message_type": str,    # interview_invite | technical_question | job_offer | decline | clarification | other
            "requires_human": bool  # Evaluator bu değeri güncelleyebilir
        }
    """
    cv = load_cv()

    system_prompt = f"""
Sen bir kariyer asistanısın. Aşağıdaki kişinin adına iş başvurusu e-postalarına yanıt veriyorsun.

## Kişi Profili:
- İsim: {cv['name']}
- Unvan: {cv['title']}
- Deneyim: {cv['experience_years']} yıl
- Yetenekler: {', '.join(cv['skills'])}
- Eğitim: {cv['education']}
- Diller: {', '.join(cv['languages'])}
- Uzaktan çalışma: {'Evet' if cv['remote_ok'] else 'Hayır'}
- Taşınmaya açık: {'Evet' if cv['willing_to_relocate'] else 'Hayır'}
- Çalışmaya müsait: {'Evet' if cv['available_for_work'] else 'Hayır'}
- Tercih edilen stack: {cv['preferred_stack']}

## Uzmanlık Alanları:
{chr(10).join('- ' + d for d in cv['expertise_domains'])}

## Kurallar:
1. Her zaman profesyonel, nazik ve özlü ol
2. Yalan söyleme veya abartma — sadece profildeki gerçek bilgileri kullan
3. Bilmediğin teknik bir şey sorulduysa dürüstçe belirt ama ilgiyle takip edeceğini söyle
4. Yanıtı 150-250 kelime arasında tut
5. İngilizce yanıt ver

## Mesaj Tipi Tespiti:
Yanıtının ilk satırında şu formatta bir etiket ekle (yanıt metninden önce):
TYPE: [interview_invite | technical_question | job_offer | decline | clarification | other]

Etiketten sonra boş satır bırak, ardından gerçek e-posta yanıtını yaz.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"İşveren mesajı:\n{employer_message}"},
        ],
        temperature=0.7,
    )

    full_response = response.choices[0].message.content.strip()

    # TYPE: satırını ayıkla
    lines = full_response.split("\n")
    message_type = "other"
    actual_response = full_response

    if lines and lines[0].startswith("TYPE:"):
        message_type = lines[0].replace("TYPE:", "").strip().lower()
        actual_response = "\n".join(lines[1:]).strip()

    return {
        "response": actual_response,
        "message_type": message_type,
        "requires_human": False,
    }
