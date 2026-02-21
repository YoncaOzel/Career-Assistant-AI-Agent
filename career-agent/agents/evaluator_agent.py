import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCORE_THRESHOLD = 7  # Eşiğin altındaysa yeniden yaz


def evaluate_response(employer_message: str, agent_response: str) -> dict:
    """
    Career Agent'ın ürettiği yanıtı 5 kriter üzerinden değerlendirir.

    Kriterler (her biri 0-2 puan):
        - professional_tone : Profesyonel, kibar dil
        - clarity           : Anlaşılır ve tutarlı içerik
        - completeness      : Soruyu tam olarak yanıtlıyor mu?
        - safety            : Yalan / hallüsinasyon yok mu?
        - relevance         : İşveren mesajıyla bağlantılı mı?

    Args:
        employer_message: Orijinal işveren mesajı
        agent_response  : Career Agent tarafından üretilen yanıt

    Returns:
        dict: {
            "total_score"  : int,   # 0-10
            "scores"       : dict,  # kriter bazlı puanlar
            "feedback"     : str,   # neden bu puan?
            "suggestions"  : str,   # nasıl iyileştirilebilir?
            "approved"     : bool   # SCORE_THRESHOLD'u geçti mi?
        }
    """
    eval_prompt = f"""
Aşağıdaki kariyer asistanı yanıtını DEĞERLENDİR.

## İşveren Mesajı:
{employer_message}

## Asistan Yanıtı:
{agent_response}

## Değerlendirme Kriterleri (her biri 0-2 puan):
- professional_tone : Dil profesyonel ve kibar mı?
- clarity           : İçerik anlaşılır ve tutarlı mı?
- completeness      : İşverenin sorusu tamamen yanıtlandı mı?
- safety            : Yanlış, uydurma veya tehlikeli bilgi yok mu?
- relevance         : Yanıt, gelen mesajla doğrudan ilgili mi?

Sadece JSON döndür, başka hiçbir şey yazma:
{{
    "professional_tone": <0-2>,
    "clarity": <0-2>,
    "completeness": <0-2>,
    "safety": <0-2>,
    "relevance": <0-2>,
    "feedback": "<neden bu toplam puanı verdiğini kısaca açıkla>",
    "suggestions": "<puan düşükse nasıl daha iyi yazılabilir, puan yüksekse 'No changes needed'>'"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": eval_prompt}],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    scores = {
        "professional_tone": int(result.get("professional_tone", 0)),
        "clarity": int(result.get("clarity", 0)),
        "completeness": int(result.get("completeness", 0)),
        "safety": int(result.get("safety", 0)),
        "relevance": int(result.get("relevance", 0)),
    }
    total = sum(scores.values())

    return {
        "total_score": total,
        "scores": scores,
        "feedback": str(result.get("feedback", "")),
        "suggestions": str(result.get("suggestions", "")),
        "approved": total >= SCORE_THRESHOLD,
    }
