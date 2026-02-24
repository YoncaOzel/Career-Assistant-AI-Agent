from rag.pdf_loader import get_vector_store


def retrieve_cv_context(query: str, top_k: int = 3) -> str:
    """
    Returns the most relevant CV sections for the given query.

    Args:
        query: The employer's message or a key topic
        top_k: Number of chunks to retrieve (3 is usually sufficient)

    Returns:
        str: Concatenated CV sections (with page numbers)
    """
    vector_store = get_vector_store()

    # Semantic search — meaning-based, not keyword matching
    relevant_docs = vector_store.similarity_search(query, k=top_k)

    if not relevant_docs:
        return "No CV content found."

    # Concatenate chunks
    context_parts = []
    for i, doc in enumerate(relevant_docs, 1):
        page_num = doc.metadata.get("page", 0) + 1
        context_parts.append(
            f"[CV Section {i} — Page {page_num}]\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(context_parts)


def retrieve_identity_context() -> str:
    """
    Always retrieves identity information from the CV: name, title, contact.
    Used so the career_agent can identify the person in every reply.

    Returns:
        str: CV chunks containing identity and contact information
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

    return "\n\n".join(list(all_chunks)[:4])  # Max 4 chunks


def retrieve_full_cv_summary() -> str:
    """
    Runs broad queries to obtain a general CV summary (not the full CV).
    Used by the Evaluator Agent and Unknown Detector.

    Returns:
        str: Up to 8 chunks representing a general CV summary
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

    return "\n\n".join(list(all_chunks)[:8])  # Max 8 chunks
