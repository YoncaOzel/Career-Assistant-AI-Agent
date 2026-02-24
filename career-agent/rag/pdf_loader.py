import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

# Paths relative to the project root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_PATH = os.path.join(_BASE_DIR, "data", "vector_store")
CV_PDF_PATH = os.path.join(_BASE_DIR, "data", "cv.pdf")


def build_vector_store() -> FAISS:
    """
    Reads the PDF CV, splits it into chunks, and builds a FAISS vector store.
    If a vector store already exists on disk, loads it instead.
    """
    embeddings = OpenAIEmbeddings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="text-embedding-3-small",  # Cheap and good enough
    )

    # Already indexed — skip recomputation
    if os.path.exists(VECTOR_STORE_PATH):
        print("✅ Loading existing vector store...")
        return FAISS.load_local(
            VECTOR_STORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True,
        )

    print("📄 Reading and indexing PDF...")

    if not os.path.exists(CV_PDF_PATH):
        raise FileNotFoundError(
            f"CV not found: {CV_PDF_PATH}\n"
            "Please place your PDF at data/cv.pdf."
        )

    # Load the PDF
    loader = PyPDFLoader(CV_PDF_PATH)
    pages = loader.load()

    # Split text into chunks
    # chunk_size: max characters per chunk
    # chunk_overlap: overlap between chunks (preserves context)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", " ", ""],
    )
    chunks = splitter.split_documents(pages)

    print(f"   → {len(pages)} pages, {len(chunks)} chunks created")

    # Build the vector store and save to disk
    vector_store = FAISS.from_documents(chunks, embeddings)

    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vector_store.save_local(VECTOR_STORE_PATH)

    print(f"✅ Vector store saved: {VECTOR_STORE_PATH}")
    return vector_store


# Load once at startup — do not reload on every request
_vector_store: FAISS | None = None


def get_vector_store() -> FAISS:
    """Singleton — returns the vector store, building it if necessary."""
    global _vector_store
    if _vector_store is None:
        _vector_store = build_vector_store()
    return _vector_store
