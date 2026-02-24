import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

# Proje kök dizinine göre yollar
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_PATH = os.path.join(_BASE_DIR, "data", "vector_store")
CV_PDF_PATH = os.path.join(_BASE_DIR, "data", "cv.pdf")


def build_vector_store() -> FAISS:
    """
    PDF CV'yi okur, parçalara böler ve FAISS vektör deposu oluşturur.
    Eğer vektör deposu zaten varsa disk'ten yükler.
    """
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small",  # Ucuz ve yeterince iyi
    )

    # Zaten indexlendiyse yeniden hesaplama
    if os.path.exists(VECTOR_STORE_PATH):
        print("✅ Mevcut vektör deposu yükleniyor...")
        return FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    print("📄 PDF okunuyor ve indexleniyor...")

    if not os.path.exists(CV_PDF_PATH):
        raise FileNotFoundError(
            f"CV bulunamadı: {CV_PDF_PATH}\n"
            "Lütfen PDF'ini data/cv.pdf konumuna koy."
        )

    # PDF'i yükle
    loader = PyPDFLoader(CV_PDF_PATH)
    pages = loader.load()

    # Metni parçalara böl
    # chunk_size: her parçanın max karakter sayısı
    # chunk_overlap: parçalar arasındaki örtüşme (bağlamı korur)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    print(f"   → {len(pages)} sayfa, {len(chunks)} parça oluşturuldu")

    # Vektör deposu oluştur ve diske kaydet
    vector_store = FAISS.from_documents(chunks, embeddings)

    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vector_store.save_local(VECTOR_STORE_PATH)

    print(f"✅ Vektör deposu kaydedildi: {VECTOR_STORE_PATH}")
    return vector_store


# Uygulama başlarken bir kez yükle — her istekte tekrar yükleme yapma
_vector_store: FAISS | None = None


def get_vector_store() -> FAISS:
    """Singleton — vektör deposunu döndürür, gerekirse oluşturur."""
    global _vector_store
    if _vector_store is None:
        _vector_store = build_vector_store()
    return _vector_store
