import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from rag.retriever import retrieve_full_cv_summary

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def detect_unknown(employer_message: str) -> dict:
    """
    Determines whether a message requires human intervention.

    Args:
        employer_message: The employer's incoming message

    Returns:
        dict: {
            "requires_human": bool,
            "confidence_score": float,  # 0.0 - 1.0
            "reason": str,
            "category": str             # salary_negotiation | out_of_domain | legal | ambiguous | none
        }
    """
    # RAG: Retrieve full CV summary (skills, domains, experience)
    cv_summary = retrieve_full_cv_summary()

    detection_prompt = f"""
You are a career assistant. Analyze the following message.

## CV Summary (Retrieved from PDF):
{cv_summary}

## Employer Message:
{employer_message}

## Task:
Does this message contain any of the following situations?
- Salary negotiation (asking for specific numbers, bargaining)
- Deep technical question outside the profile's skills (unknown technology)
- Legal or contract details (non-compete, equity, legal clauses)
- Vague or manipulative offer (suspicious, insufficient information)

Return only JSON, nothing else:
{{
    "requires_human": true,
    "confidence_score": 0.0,
    "reason": "why human is required or not",
    "category": "salary_negotiation | out_of_domain | legal | ambiguous | none"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": detection_prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Type safety: ensure required fields exist
    return {
        "requires_human": bool(result.get("requires_human", False)),
        "confidence_score": float(result.get("confidence_score", 0.0)),
        "reason": str(result.get("reason", "")),
        "category": str(result.get("category", "none")),
    }
