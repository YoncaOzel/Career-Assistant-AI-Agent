from rag.pdf_loader import get_vector_store


def retrieve_cv_context(query: str, top_k: int = 3) -> str:
    """
    Kullanıcının sorusuna en ilgili CV bölümlerini döndürür.

    Args:
        query: İşverenin mesajı veya anahtar konu
        top_k: Kaç parça getirileceği (3 genellikle yeterli)

    Returns:
        str: Birleştirilmiş CV bölümleri (sayfa numarasıyla)
    """
    vector_store = get_vector_store()

    # Semantik arama — anlama dayalı, kelime eşleşmesi değil
    relevant_docs = vector_store.similarity_search(query, k=top_k)

    if not relevant_docs:
        return "CV bilgisi bulunamadı."

    # Parçaları birleştir
    context_parts = []
    for i, doc in enumerate(relevant_docs, 1):
        page_num = doc.metadata.get("page", 0) + 1
        context_parts.append(
            f"[CV Bölüm {i} — Sayfa {page_num}]\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)


def retrieve_identity_context() -> str:
    """
    Her zaman CV'deki kimlik bilgilerini çeker: isim, unvan, iletişim.
    career_agent'ın her yanıtta kişiyi tanıması için kullanılır.

    Returns:
        str: Kimlik ve iletişim bilgisi içeren CV parçaları
    """
    identity_queries = [
        "name full name contact email phone",
        "title position role summary",
    ]

    all_chunks: set[str] = set()
    vector_store = get_vector_store()

    for query in identity_queries:
        docs = vector_store.similarity_search(query, k=2)
        for doc in docs:
            all_chunks.add(doc.page_content)

    if not all_chunks:
        return ""

    return "\n\n".join(list(all_chunks)[:4])  # Max 4 parça


def retrieve_full_cv_summary() -> str:
    """
    Tüm CV'yi değil, genel bir özet almak için geniş kapsamlı sorgu çalıştırır.
    Evaluator agent ve Unknown Detector için kullanılır.

    Returns:
        str: CV'nin genel özetini oluşturan max 8 parça
    """
    broad_queries = [
        "skills experience education",
        "projects achievements work history",
        "contact information name title",
    ]

    all_chunks: set[str] = set()
    vector_store = get_vector_store()

    for query in broad_queries:
        docs = vector_store.similarity_search(query, k=2)
        for doc in docs:
            all_chunks.add(doc.page_content)

    return "\n\n".join(list(all_chunks)[:8])  # Max 8 parça
