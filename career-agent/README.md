# 🤖 Career Assistant AI Agent

İşveren e-postalarına **PDF CV'den bilgi çekerek** otomatik, profesyonel yanıtlar üreten; yanıtları puanlayarak kaliteyi garanti altına alan AI ajan sistemi.

---

## 📋 Özellikler

### v1.0 — Temel Sistem
- **Career Agent** — GPT-4o-mini ile profesyonel e-posta yanıtı üretir
- **Evaluator Agent** — 5 kriter × 0-2 puan (toplam 10) üzerinden yanıt kalitesini ölçer; puan ≥ 7 olana kadar max 3 kez yeniden yazar
- **Unknown Detector** — Maaş müzakeresi, bilinmeyen teknoloji, hukuki detay veya şüpheli teklifleri tespit ederek insan yönlendirmesi yapar
- **Telegram Bildirimleri** — Her aşamada (yeni mesaj, yanıt gönderildi, retry, insan müdahalesi) anlık bildirim

### v1.1 — RAG + Confidence Dashboard
- **RAG Entegrasyonu** — `data/cv.pdf` PDF olarak yüklenir; LangChain + FAISS ile vektörize edilir; her yanıtta mesaja özel CV bölümleri semantik olarak çekilir
- **Confidence Scoring Dashboard** — Puan geçmişi, mesaj tipi dağılımı ve kriter barlarını gösteren gerçek zamanlı web arayüzü (Chart.js, otomatik 30 sn yenileme)

---

## 🗂 Klasör Yapısı

```
career-agent/
├── main.py                      # FastAPI uygulaması, tüm endpoint'ler
├── requirements.txt
├── .env                         # API anahtarları (git'e ekleme!)
│
├── agents/
│   ├── career_agent.py          # RAG destekli yanıt üretici
│   └── evaluator_agent.py       # 5 kriterli kalite değerlendirici
│
├── rag/
│   ├── __init__.py
│   ├── pdf_loader.py            # PDF → chunk → FAISS vektör deposu
│   └── retriever.py             # Semantik arama, CV özeti
│
├── tools/
│   ├── notification.py          # Telegram bildirimleri
│   └── unknown_detector.py      # İnsan müdahalesi tespiti (RAG destekli)
│
├── templates/
│   ├── index.html               # Ana demo arayüzü
│   └── dashboard.html           # Confidence scoring dashboard
│
└── data/
    ├── cv.pdf                   # ← Kendi CV'ni buraya koy
    ├── vector_store/            # Otomatik oluşturulur (FAISS index)
    ├── cv_profile.json          # Referans (artık aktif kullanılmıyor)
    └── logs.json                # Etkileşim logları
```

---

## ⚙️ Kurulum

### 1. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 2. `.env` dosyasını oluştur

```env
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC-...
TELEGRAM_CHAT_ID=123456789
```

### 3. CV'ni yerleştir

```bash
# Kendi PDF CV'ni bu konuma koy:
data/cv.pdf
```

---

## 🚀 Başlatma

```bash
uvicorn main:app --reload --port 8000
```

İlk başlatmada PDF okunup `data/vector_store/` oluşturulur:

```
🚀 Career Agent başlatılıyor...
📄 PDF okunuyor ve indexleniyor...
   → 3 sayfa, 24 parça oluşturuldu
✅ Vektör deposu kaydedildi: data/vector_store
✅ CV başarıyla indexlendi, sistem hazır.
```

Sonraki başlatmalarda diskten yüklenir (`📄` mesajı görünmez).

| URL | Açıklama |
|-----|----------|
| http://localhost:8000 | Ana demo arayüzü |
| http://localhost:8000/dashboard | Confidence scoring dashboard |
| http://localhost:8000/docs | Swagger API dokümantasyonu |
| http://localhost:8000/logs | Ham log verisi (JSON) |

---

## 🔄 Sistem Akışı

```
[İşveren Mesajı — POST /process-message]
              │
              ▼
  ┌─────────────────────┐
  │  Telegram Bildirimi  │  ← "Yeni mesaj geldi"
  └─────────────────────┘
              │
              ▼
  ┌─────────────────────┐
  │   Unknown Detector   │  ← RAG ile CV özetini çeker
  └─────────────────────┘
              │
    ┌─────────┴──────────┐
    │ confidence ≥ 0.8   │
    │ ve insan gerekli?  │
    └─────────┬──────────┘
         EVET │                   HAYIR
              ▼                     │
  ┌─────────────────────┐           │
  │  İnsan Yönlendirme   │           │
  │  (Telegram + log)    │           │
  └─────────────────────┘           │
                                    ▼
                        ┌─────────────────────┐
                        │    RAG Retriever     │  ← Mesaja özel CV bölümleri
                        └─────────────────────┘
                                    │
                                    ▼
                        ┌─────────────────────┐
                        │    Career Agent      │  ← GPT-4o-mini + CV bağlamı
                        └─────────────────────┘
                                    │
                              ┌─────▼─────┐
                              │ Evaluator │  ← 5 kriter × 0-2 = /10
                              └─────┬─────┘
                                    │
                          ┌─────────┴──────────┐
                          │    Puan ≥ 7?        │
                          └─────────┬──────────┘
                     EVET           │           HAYIR (max 3 deneme)
                       ◄────────────┘──────────────►
                       │                            │
                       ▼                            ▼
           ┌─────────────────────┐   ┌─────────────────────────┐
           │  Yanıt Gönderildi   │   │  Career Agent yeniden   │
           │  Telegram Bildirimi │   │  yazar (suggestions ile) │
           └─────────────────────┘   └─────────────────────────┘
                       │
                       ▼
           ┌─────────────────────┐
           │  Log kaydedildi     │  → data/logs.json
           └─────────────────────┘
                       │
                       ▼
           ┌─────────────────────┐
           │  Dashboard güncellenir │  ← /dashboard otomatik yenilenir
           └─────────────────────┘
```

---

## 📡 API Endpoint'leri

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/process-message` | Ana pipeline — işveren mesajını işler |
| `GET`  | `/logs` | Tüm etkileşim loglarını döndürür |
| `DELETE` | `/logs` | Log dosyasını temizler |
| `GET`  | `/dashboard` | Confidence scoring arayüzü |
| `GET`  | `/health` | Sunucu sağlık kontrolü |
| `GET`  | `/docs` | Swagger UI |

### Örnek İstek

```bash
curl -X POST http://localhost:8000/process-message \
  -H "Content-Type: application/json" \
  -d '{
    "sender_name": "ACME Corp",
    "message": "We would like to invite you for a technical interview next week."
  }'
```

### Örnek Yanıt

```json
{
  "status": "sent",
  "response": "Dear Hiring Team, Thank you for...",
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
    "feedback": "Strong professional tone..."
  },
  "attempts": 1
}
```

---

## 🔁 CV Güncelleme

CV'ni değiştirdikten sonra eski vektör deposunu sil, sistem otomatik yeniden indexler:

```bash
# Windows
Remove-Item -Recurse -Force data/vector_store

# Linux / macOS
rm -rf data/vector_store/

# Yeniden başlat
uvicorn main:app --reload --port 8000
```

---

## 🛠 Teknoloji Yığını

| Katman | Teknoloji |
|--------|-----------|
| API framework | FastAPI |
| LLM | OpenAI GPT-4o-mini |
| RAG pipeline | LangChain + FAISS |
| Embedding | text-embedding-3-small |
| PDF okuma | PyPDF |
| Bildirim | Telegram Bot API |
| Dashboard | Chart.js (CDN) |
