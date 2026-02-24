import os
from openai import OpenAI
from dotenv import load_dotenv
from rag.retriever import retrieve_cv_context, retrieve_identity_context

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_response(employer_message: str) -> dict:
    """
    Generates a professional email reply to an employer message using CV context.

    Args:
        employer_message: The employer's incoming message (or a retry message combined with feedback)

    Returns:
        dict: {
            "response": str,          # Generated email reply
            "message_type": str,      # interview_invite | technical_question | job_offer | decline | clarification | other
            "requires_human": bool,   # Evaluator may update this value
            "cv_context_used": str    # CV context retrieved from RAG (for debug/logging)
        }
    """
    # RAG: Fixed identity context (name, title) + message-specific CV sections
    identity_context = retrieve_identity_context()
    cv_context = retrieve_cv_context(employer_message)

    system_prompt = f"""
You are a career assistant. You reply to job-related emails on behalf of the person described below.

## Person Identity (Always Applicable):
{identity_context}

## CV Sections Relevant to This Message:
{cv_context}

## Rules:
1. Use only the CV information above — never invent or add extra details
2. The person's identity (name, title) is always provided above — never say "my information is limited"
3. For technical details genuinely not found in the CV, honestly say "my knowledge on this is limited"
4. Always be professional, polite, and concise
5. Keep the reply between 150-250 words
6. Reply in English

## Message Type Detection:
On the very first line of your reply, add a tag in this format (before the reply text):
TYPE: [interview_invite | technical_question | job_offer | decline | clarification | other]

Leave a blank line after the tag, then write the actual email reply.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Employer message:\n{employer_message}"},
        ],
        temperature=0.7,
    )

    full_response = response.choices[0].message.content.strip()

    # Extract the TYPE: line
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
