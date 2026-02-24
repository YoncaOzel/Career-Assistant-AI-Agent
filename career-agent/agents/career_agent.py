import os
from openai import OpenAI
from dotenv import load_dotenv
from rag.retriever import retrieve_cv_context, retrieve_identity_context

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_response(employer_message: str) -> dict:
    """
    İşveren mesajına CV'den bilgi çekerek profesyonel e-posta yanıtı üretir.

    Args:
        employer_message: İşverenin gönderdiği mesaj (veya feedback ile birleştirilmiş retry mesajı)

    Returns:
        dict: {
            "response": str,          # Üretilen e-posta yanıtı
            "message_type": str,      # interview_invite | technical_question | job_offer | decline | clarification | other
            "requires_human": bool,   # Evaluator bu değeri güncelleyebilir
            "cv_context_used": str    # RAG'dan çekilen CV bağlamı (debug/log için)
        }
    """
    # RAG: Sabit kimlik bağlamı (isim, unvan) + mesaja özel CV bölümleri
    identity_context = retrieve_identity_context()
    cv_context = retrieve_cv_context(employer_message)

    system_prompt = f"""
Sen bir kariyer asistanısın. Aşağıdaki kişinin adına iş başvurusu e-postalarına yanıt veriyorsun.

## Kişi Kimliği (Her Zaman Geçerli):
{identity_context}

## Bu Mesajla İlgili CV Bölümleri:
{cv_context}

## Kurallar:
1. Yukarıdaki CV bilgilerini kullan — asla icat etme veya ekstra bilgi ekleme
2. Kişinin kimliği (isim, unvan) her zaman yukarıda verilmiştir — "bilgim sınırlı" deme
3. CV'de gerçekten bulunmayan teknik detaylar için dürüstçe "bu konuda bilgim sınırlı" de
4. Her zaman profesyonel, nazik ve özlü ol
5. Yanıtı 150-250 kelime arasında tut
6. İngilizce yanıt ver

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
        "cv_context_used": f"[IDENTITY]\n{identity_context}\n\n[QUERY-SPECIFIC]\n{cv_context}",
    }
