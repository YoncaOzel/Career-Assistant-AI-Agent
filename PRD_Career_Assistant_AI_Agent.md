# 📋 PRD — Career Assistant AI Agent
### Product Requirements Document (Ödev Uygulama Rehberi)

**Versiyon:** 1.0  
**Tarih:** Şubat 2026  
**Hazırlayan:** Senior Full Stack Developer  
**Hedef Kitle:** Yazılım öğrencisi (sıfırdan başlayan)

---

## 📌 1. Proje Özeti

Bu proje, iş dünyasından gelen mesajlara (işe davet, teknik sorular, iş teklifleri vb.) **senin adına otomatik olarak profesyonel yanıtlar üreten** bir yapay zeka ajanı sistemidir.

Sistem 4 ana bileşenden oluşur:
1. **Career Agent** – Ana yanıt üretici ajan
2. **Evaluator Agent** – Yanıtı kalite açısından değerlendiren eleştirmen ajan
3. **Notification Tool** – Mobil bildirim gönderici araç
4. **Unknown Question Detector** – Bilgi dışı soruları tespit eden araç

---

## 🧠 2. Sistemi Anlamak: Büyük Resim

```
[İşveren Mesajı Gelir]
        ↓
[Career Agent mesajı okur, CV bilgilerini kullanarak yanıt üretir]
        ↓
[Evaluator Agent yanıtı puanlar (0-10)]
        ↓
    Puan ≥ 7?
   /         \
EVET          HAYIR
  ↓             ↓
[Yanıt      [Career Agent
 gönderilir]  yeniden yazar]
  ↓             ↓
[Kullanıcıya bildirim gönderilir]
```

---

## 🏗️ 3. Mimari & Teknoloji Stack

### 3.1 Seçilen Teknolojiler

| Katman | Teknoloji | Neden? |
|--------|-----------|--------|
| Backend dil | Python 3.11+ | Kolay, LLM kütüphaneleriyle uyumlu |
| LLM API | OpenAI GPT-4o-mini | Ucuz, güçlü |
| Web Framework | FastAPI | Hızlı, otomatik API dökümantasyonu |
| Bildirim | Telegram Bot API | Ücretsiz, kolay kurulum |
| Veri saklama | JSON dosyası (basit) | Karmaşıklık ekleme |
| Frontend | Basit HTML + JS | Opsiyonel, demo için yeterli |

### 3.2 Klasör Yapısı

```
career-agent/
├── main.py                  # FastAPI uygulaması, tüm endpoint'ler
├── agents/
│   ├── career_agent.py      # Ana yanıt üretici
│   └── evaluator_agent.py   # Kalite değerlendirici
├── tools/
│   ├── notification.py      # Telegram bildirim aracı
│   └── unknown_detector.py  # Bilgi dışı soru tespiti
├── data/
│   ├── cv_profile.json      # Senin CV/profil bilgilerin
│   └── logs.json            # Tüm etkileşim kayıtları
├── templates/
│   └── index.html           # Basit demo arayüzü (opsiyonel)
├── .env                     # API anahtarları (git'e ekleme!)
├── requirements.txt         # Python bağımlılıkları
└── README.md
```

---

## 📂 4. Detaylı Bileşen Tasarımı

### 4.1 CV Profil Verisi (`data/cv_profile.json`)

Bu dosya ajanın "beyni"dir. Seni tanımlayan bilgileri buraya koyarsın.

```json
{
  "name": "Adın Soyadın",
  "title": "Backend Developer",
  "experience_years": 2,
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
  "education": "Bilgisayar Mühendisliği, XYZ Üniversitesi, 2024",
  "languages": ["Türkçe (anadil)", "İngilizce (B2)"],
  "preferred_stack": "Python backend, REST API, cloud deployment",
  "available_for_work": true,
  "preferred_salary_range": "belirtilmedi",
  "willing_to_relocate": false,
  "remote_ok": true,
  "linkedin": "linkedin.com/in/...",
  "github": "github.com/...",
  "email": "email@example.com",
  "expertise_domains": [
    "REST API development",
    "Database design",
    "Python scripting",
    "Docker containerization"
  ],
  "non_expertise_domains": [
    "Mobile development",
    "Blockchain",
    "Hardware programming",
    "Salary negotiation details"
  ]
}
```

---

### 4.2 Career Agent (`agents/career_agent.py`)

**Görevi:** Gelen işveren mesajını okumak, CV bilgilerini kullanarak uygun, profesyonel bir yanıt üretmek.

**Mantığı:**
1. Mesaj tipini belirle (davet mi? teknik soru mu? teklif mi?)
2. CV profilini sisteme dahil et
3. OpenAI'ya mesajı gönder
4. Yanıtı döndür

```python
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_cv():
    with open("data/cv_profile.json", "r") as f:
        return json.load(f)

def generate_response(employer_message: str) -> dict:
    """
    İşveren mesajına profesyonel yanıt üretir.
    
    Returns:
        dict: {
            "response": str,       # Üretilen yanıt
            "message_type": str,   # interview_invite | technical_question | job_offer | other
            "requires_human": bool # İnsan müdahalesi gerekiyor mu?
        }
    """
    cv = load_cv()
    
    system_prompt = f"""
    Sen bir kariyer asistanısın. Aşağıdaki kişinin adına iş başvurusu emaillerine yanıt veriyorsun.
    
    ## Kişi Profili:
    - İsim: {cv['name']}
    - Unvan: {cv['title']}
    - Deneyim: {cv['experience_years']} yıl
    - Yetenekler: {', '.join(cv['skills'])}
    - Eğitim: {cv['education']}
    - Uzaktan çalışma: {'Evet' if cv['remote_ok'] else 'Hayır'}
    - Taşınmaya açık: {'Evet' if cv['willing_to_relocate'] else 'Hayır'}
    
    ## Kurallar:
    1. Her zaman profesyonel, nazik ve özlü ol
    2. Yalan söyleme veya abartma — sadece profildeki gerçek bilgileri kullan
    3. Bilmediğin teknik bir şey sorulduysa dürüstçe belirt
    4. Yanıtı 150-250 kelime arasında tut
    5. İngilizce yanıt ver
    
    ## Mesaj Tipi Tespiti:
    Yanıtın başında şu formatta bir satır ekle:
    TYPE: [interview_invite | technical_question | job_offer | decline | clarification]
    
    Sonra gerçek email yanıtını yaz.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"İşveren mesajı:\n{employer_message}"}
        ],
        temperature=0.7
    )
    
    full_response = response.choices[0].message.content
    
    # Mesaj tipini ayıkla
    lines = full_response.split('\n')
    message_type = "other"
    actual_response = full_response
    
    if lines[0].startswith("TYPE:"):
        message_type = lines[0].replace("TYPE:", "").strip()
        actual_response = '\n'.join(lines[1:]).strip()
    
    return {
        "response": actual_response,
        "message_type": message_type,
        "requires_human": False  # Evaluator bunu güncelleyecek
    }
```

---

### 4.3 Evaluator Agent (`agents/evaluator_agent.py`)

**Görevi:** Career Agent'ın ürettiği yanıtı 5 kritere göre puanlamak. Puan düşükse yeniden yazmasını tetiklemek.

**Değerlendirme Kriterleri:**

| Kriter | Max Puan | Açıklama |
|--------|----------|----------|
| Profesyonel ton | 2 | Kibar, resmi dil |
| Netlik | 2 | Anlaşılır, tutarlı |
| Eksiksizlik | 2 | Soruyu tam yanıtlamış mı? |
| Güvenlik | 2 | Yalan/hallüsinasyon yok mu? |
| Alaka | 2 | İşveren mesajıyla ilgili mi? |
| **Toplam** | **10** | |

**Eşik değer:** 7/10 → Altındaysa yeniden yazılır.

```python
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SCORE_THRESHOLD = 7

def evaluate_response(employer_message: str, agent_response: str) -> dict:
    """
    Üretilen yanıtı değerlendirir.
    
    Returns:
        dict: {
            "total_score": int,       # 0-10
            "scores": dict,           # Kriter bazlı puanlar
            "feedback": str,          # Neden bu puan?
            "approved": bool,         # Eşiği geçti mi?
            "suggestions": str        # Nasıl düzeltilebilir?
        }
    """
    
    eval_prompt = f"""
    Aşağıdaki kariyer asistanı yanıtını DEĞERLENDİR.
    
    ## İşveren Mesajı:
    {employer_message}
    
    ## Asistan Yanıtı:
    {agent_response}
    
    ## Görevin:
    Her kriteri 0-2 arasında puan ver. Sadece JSON döndür, başka bir şey yazma.
    
    JSON formatı:
    {{
        "professional_tone": <0-2>,
        "clarity": <0-2>,
        "completeness": <0-2>,
        "safety": <0-2>,
        "relevance": <0-2>,
        "feedback": "<neden bu puanı verdiğini kısaca açıkla>",
        "suggestions": "<daha iyi olması için ne yapılmalı>"
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": eval_prompt}
        ],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    
    total = (
        result["professional_tone"] +
        result["clarity"] +
        result["completeness"] +
        result["safety"] +
        result["relevance"]
    )
    
    return {
        "total_score": total,
        "scores": {
            "professional_tone": result["professional_tone"],
            "clarity": result["clarity"],
            "completeness": result["completeness"],
            "safety": result["safety"],
            "relevance": result["relevance"]
        },
        "feedback": result["feedback"],
        "suggestions": result["suggestions"],
        "approved": total >= SCORE_THRESHOLD
    }
```

---

### 4.4 Notification Tool (`tools/notification.py`)

**Görev:** Şu durumlarda Telegram'dan sana bildirim gönder:
- Yeni işveren mesajı geldiğinde
- Yanıt onaylanıp gönderildiğinde
- İnsan müdahalesi gerektiğinde

**Telegram Bot Kurulum Adımları:**
1. Telegram'da `@BotFather`'a mesaj at
2. `/newbot` yaz, bir isim ver
3. Aldığın **token**'ı `.env`'e koy
4. Kendi Telegram hesabına `@userinfobot` ile chat ID'ni öğren

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_notification(message: str, notification_type: str = "info") -> bool:
    """
    Telegram bildirimi gönderir.
    
    notification_type: "info" | "warning" | "success" | "alert"
    """
    
    # Emoji ile görsel sınıflandırma
    emoji_map = {
        "info": "📨",
        "warning": "⚠️",
        "success": "✅",
        "alert": "🚨"
    }
    emoji = emoji_map.get(notification_type, "📌")
    
    full_message = f"{emoji} *Career Agent Bildirimi*\n\n{message}"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": full_message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Bildirim gönderilemedi: {e}")
        return False


# Kullanım örnekleri:
def notify_new_message(employer_name: str, preview: str):
    send_notification(
        f"Yeni işveren mesajı!\n*Gönderen:* {employer_name}\n*Önizleme:* {preview[:100]}...",
        "info"
    )

def notify_response_sent(score: int):
    send_notification(
        f"Yanıt onaylandı ve gönderildi.\n*Değerlendirme Puanı:* {score}/10",
        "success"
    )

def notify_human_needed(reason: str):
    send_notification(
        f"İNSAN MÜDAHALESİ GEREKLİ!\n*Sebep:* {reason}",
        "alert"
    )
```

---

### 4.5 Unknown Question Detector (`tools/unknown_detector.py`)

**Görev:** Ajanın yanıt veremeyeceği durumları tespit et ve seni uyar.

**Tetikleyici Durumlar:**
- Maaş müzakeresi (rakam verilmesi isteniyor)
- CV'de olmayan bir teknoloji hakkında derin teknik soru
- Hukuki sorular
- Belirsiz veya şüpheli teklifler

```python
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_cv():
    with open("data/cv_profile.json", "r") as f:
        return json.load(f)

def detect_unknown(employer_message: str) -> dict:
    """
    Mesajın insan müdahalesi gerektirip gerektirmediğini tespit eder.
    
    Returns:
        dict: {
            "requires_human": bool,
            "confidence_score": float,  # 0.0 - 1.0 (1.0 = kesinlikle insan gerekli)
            "reason": str,
            "category": str
        }
    """
    cv = load_cv()
    
    detection_prompt = f"""
    Bir kariyer asistanı olarak şu mesajı analiz et.
    
    ## Kullanıcı Profili - Bildiği Teknolojiler:
    {', '.join(cv['skills'])}
    
    ## Kullanıcı Profili - BİLMEDİĞİ alanlar:
    {', '.join(cv['non_expertise_domains'])}
    
    ## İşveren Mesajı:
    {employer_message}
    
    ## Görev:
    Bu mesaj aşağıdaki durumlardan birini içeriyor mu?
    - Maaş rakamı müzakeresi
    - Profildeki beceriler dışında derin teknik soru
    - Hukuki veya sözleşme detayları
    - Belirsiz veya manipülatif teklif
    
    Sadece JSON döndür:
    {{
        "requires_human": true/false,
        "confidence_score": 0.0-1.0,
        "reason": "<neden insan gerekli veya değil>",
        "category": "salary_negotiation | out_of_domain | legal | ambiguous | none"
    }}
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": detection_prompt}],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
```

---

### 4.6 Ana Uygulama (`main.py`)

Tüm bileşenleri birbirine bağlayan orchestrator katmanı:

```python
import json
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.career_agent import generate_response
from agents.evaluator_agent import evaluate_response, SCORE_THRESHOLD
from tools.notification import notify_new_message, notify_response_sent, notify_human_needed
from tools.unknown_detector import detect_unknown

app = FastAPI(title="Career Assistant AI Agent", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class EmployerMessage(BaseModel):
    sender_name: str
    message: str

def log_interaction(data: dict):
    """Tüm etkileşimleri loglar."""
    try:
        with open("data/logs.json", "r") as f:
            logs = json.load(f)
    except FileNotFoundError:
        logs = []
    
    data["timestamp"] = datetime.datetime.now().isoformat()
    logs.append(data)
    
    with open("data/logs.json", "w") as f:
        json.dump(logs, f, indent=2, ensure_ascii=False)

@app.post("/process-message")
async def process_message(payload: EmployerMessage):
    """
    Ana endpoint. Tüm agent döngüsünü çalıştırır.
    """
    
    # 1. Bildirim: Yeni mesaj geldi
    notify_new_message(payload.sender_name, payload.message)
    
    # 2. Unknown detection — önce kontrol et
    detection = detect_unknown(payload.message)
    
    if detection["requires_human"] and detection["confidence_score"] >= 0.8:
        notify_human_needed(f"{detection['category']}: {detection['reason']}")
        log_interaction({
            "sender": payload.sender_name,
            "message": payload.message,
            "action": "human_intervention_requested",
            "detection": detection
        })
        return {
            "status": "human_required",
            "reason": detection["reason"],
            "category": detection["category"]
        }
    
    # 3. Career Agent — yanıt üret
    agent_result = generate_response(payload.message)
    
    # 4. Evaluator Agent — değerlendir (max 3 deneme)
    max_retries = 3
    final_response = agent_result["response"]
    evaluation = None
    
    for attempt in range(max_retries):
        evaluation = evaluate_response(payload.message, final_response)
        
        if evaluation["approved"]:
            break
        
        # Puanı düşükse yeniden yaz
        if attempt < max_retries - 1:
            improvement_message = (
                f"{payload.message}\n\n"
                f"[Önceki yanıt yetersizdi. Feedback: {evaluation['suggestions']}. "
                f"Lütfen daha iyi bir yanıt yaz.]"
            )
            agent_result = generate_response(improvement_message)
            final_response = agent_result["response"]
    
    # 5. Bildirim: Yanıt gönderildi
    notify_response_sent(evaluation["total_score"])
    
    # 6. Log
    log_interaction({
        "sender": payload.sender_name,
        "message": payload.message,
        "final_response": final_response,
        "evaluation": evaluation,
        "message_type": agent_result["message_type"],
        "attempts": attempt + 1
    })
    
    return {
        "status": "sent",
        "response": final_response,
        "message_type": agent_result["message_type"],
        "evaluation": {
            "score": evaluation["total_score"],
            "approved": evaluation["approved"],
            "scores": evaluation["scores"]
        }
    }

@app.get("/logs")
async def get_logs():
    """Tüm etkileşim loglarını döndürür."""
    try:
        with open("data/logs.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "Career Assistant v1.0"}
```

---

## ⚙️ 5. Kurulum Adımları (Sıfırdan)

### Adım 1: Python Ortamı Kur

```bash
# Python 3.11+ kurulu olmalı
python --version

# Proje klasörü oluştur
mkdir career-agent
cd career-agent

# Virtual environment oluştur
python -m venv venv

# Aktive et (Mac/Linux)
source venv/bin/activate

# Aktive et (Windows)
venv\Scripts\activate
```

### Adım 2: Bağımlılıkları Yükle

`requirements.txt` dosyası:

```
fastapi==0.115.0
uvicorn==0.30.0
openai==1.40.0
python-dotenv==1.0.1
requests==2.32.3
pydantic==2.8.0
```

```bash
pip install -r requirements.txt
```

### Adım 3: API Anahtarlarını Ayarla

`.env` dosyası oluştur (**bu dosyayı git'e kesinlikle ekleme!**):

```env
OPENAI_API_KEY=sk-...buraya_openai_anahtarını_yaz...
TELEGRAM_BOT_TOKEN=123456:ABC-...buraya_telegram_token_yaz...
TELEGRAM_CHAT_ID=123456789
```

### Adım 4: Data Klasörlerini Oluştur

```bash
mkdir -p data agents tools
touch data/logs.json
echo "[]" > data/logs.json
```

### Adım 5: Uygulamayı Başlat

```bash
uvicorn main:app --reload --port 8000
```

Tarayıcıda `http://localhost:8000/docs` adresine git — otomatik API dökümantasyonunu göreceksin.

---

## 🧪 6. Test Senaryoları

### Test 1: Standart Mülakat Daveti

**Input:**
```json
{
  "sender_name": "TechCorp HR",
  "message": "Hello! We came across your profile and would like to invite you for a technical interview for our Backend Developer position. Are you available next week?"
}
```

**Beklenen Çıktı:**
- `message_type`: `interview_invite`
- Yanıt: Nazik kabul, uygun zaman dilimi sorar
- Evaluator puanı: ≥ 7/10
- Telegram bildirimi gelir

---

### Test 2: Teknik Soru

**Input:**
```json
{
  "sender_name": "StartupXYZ CTO",
  "message": "Can you explain how you would design a REST API for a multi-tenant SaaS application? What authentication strategy would you use?"
}
```

**Beklenen Çıktı:**
- `message_type`: `technical_question`
- Yanıt: JWT + API key auth, tenant isolation stratejisi açıklanır
- Bilinen alan olduğu için `requires_human: false`

---

### Test 3: Bilinmeyen / İnsan Müdahalesi Gerektiren Soru

**Input:**
```json
{
  "sender_name": "BigCorp Recruiter",
  "message": "We're offering a position but need to discuss equity vesting schedules, stock options, and the specific legal terms of your non-compete clause. What are your expectations?"
}
```

**Beklenen Çıktı:**
- `status`: `human_required`
- `category`: `legal`
- Telegram'a 🚨 alert bildirimi gelir
- Yanıt gönderilmez, log'a kaydedilir

---

## 📊 7. Flow Diyagramı

```
┌─────────────────────────────────────────────────────┐
│                  CAREER AGENT SYSTEM                │
└─────────────────────────────────────────────────────┘

┌──────────────┐
│  İşveren     │  →  POST /process-message
│  Mesajı      │
└──────────────┘
        │
        ▼
┌──────────────────────┐
│  Unknown Detector    │  ← CV profili kullanılır
│  (Güven skoru)       │
└──────────────────────┘
        │
   conf ≥ 0.8?
   /          \
 EVET          HAYIR
   │              │
   ▼              ▼
[🚨 Alert    ┌────────────────┐
 Telegram]   │  Career Agent  │  ← CV + LLM prompt
             │  (Yanıt üret)  │
             └────────────────┘
                     │
                     ▼
             ┌────────────────┐
             │  Evaluator     │  (Puan: 0-10)
             │  Agent         │
             └────────────────┘
                     │
               Puan ≥ 7?
              /          \
           EVET           HAYIR (max 3 deneme)
             │                │
             ▼                ▼
      [✅ Yanıt         [Yeniden yaz]
       Onaylandı]            │
             │          [Tekrar değerlendir]
             ▼
      [📨 Telegram
       Bildirimi]
             │
             ▼
      [Log kaydet]
             │
             ▼
      [Response dön]
```

---

## 📝 8. Prompt Tasarımı

### Career Agent System Prompt Stratejisi

**Kullanılan teknik: Role + Context + Constraints + Output Format**

```
[ROL]        → "Sen bir kariyer asistanısın"
[BAĞLAM]     → CV profili enjeksiyonu (isim, yetenekler, deneyim...)
[KISITLAR]   → "Yalan söyleme", "150-250 kelime", "sadece gerçek bilgi"
[FORMAT]     → "TYPE: satırıyla başla, sonra email yaz"
```

### Evaluator Prompt Stratejisi

**Teknik: Structured JSON output with rubric**

```
[RUBRIK]     → Her kriter için 0-2 puan açıklaması
[FORMAT]     → Zorunlu JSON çıktısı (response_format: json_object)
[SICAKLIK]   → temperature=0.3 (tutarlı puanlama için düşük)
```

---

## 🎁 9. Bonus: Opsiyonel Geliştirmeler

### 9.1 Konuşma Hafızası (Memory)

Her kullanıcı için geçmiş mesajları saklayarak bağlamsal yanıtlar üret:

```python
# data/conversations/{sender_name}.json
def get_conversation_history(sender_name: str) -> list:
    path = f"data/conversations/{sender_name}.json"
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
```

### 9.2 Güven Skoru Görselleştirmesi

FastAPI endpoint'ine ek olarak basit bir HTML dashboard:

```html
<!-- templates/dashboard.html -->
<!-- Her yanıtın evaluator puanlarını bar chart olarak göster -->
```

### 9.3 Cloud Deploy (Render.com — Ücretsiz)

```bash
# requirements.txt hazır
# Render.com > New Web Service > GitHub repo bağla
# Environment variables'a .env içeriklerini ekle
# Build command: pip install -r requirements.txt
# Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## ✅ 10. Teslim Kontrol Listesi

- [ ] `career_agent.py` çalışıyor, yanıt üretiyor
- [ ] `evaluator_agent.py` 0-10 arasında puanlıyor
- [ ] Puan < 7 ise otomatik yeniden yazıyor (max 3 deneme)
- [ ] Telegram bildirimi çalışıyor (en az 1 canlı demo)
- [ ] Unknown detector hukuki/belirsiz soruları yakalıyor
- [ ] 3 test senaryosu çalışıyor (interview, teknik, bilinmeyen)
- [ ] Tüm etkileşimler `logs.json`'a kaydediliyor
- [ ] GitHub'da kaynak kod
- [ ] Mimari diyagram (yukarıdaki ASCII kullanılabilir)
- [ ] 3-5 sayfa rapor (tasarım kararları, değerlendirme stratejisi, başarısızlık durumları)

---

## ⚠️ 11. Yaygın Hatalar ve Çözümleri

| Hata | Sebep | Çözüm |
|------|-------|--------|
| `openai.AuthenticationError` | API key yanlış | `.env` dosyasını kontrol et |
| Telegram bildirimi gelmiyor | Chat ID yanlış | `@userinfobot`'a mesaj at |
| Evaluator hep 10 veriyor | Prompt yetersiz | Kriterleri daha net tanımla |
| `ModuleNotFoundError` | Venv aktif değil | `source venv/bin/activate` |
| Sonsuz retry döngüsü | SCORE_THRESHOLD çok yüksek | 7'den düşür veya max_retries azalt |

---

## 📚 12. Kaynak & Referanslar

- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

*Bu PRD, projenin sıfırdan canlıya alınması için gereken tüm teknik detayları içermektedir. Her bölümü sırasıyla takip ederek projeyi tamamlayabilirsin.*
