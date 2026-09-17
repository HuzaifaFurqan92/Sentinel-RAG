# routers/real_mock_chatbot.py
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
from ..config import settings

router = APIRouter()
client = Groq(api_key=settings.GROQ_API_KEY)

# Hardcoded "knowledge base" chunks for this fake client
KB_CHUNKS = [
    "Our refund policy allows returns within 30 days of purchase.",
    "Pro plan subscribers receive 24/7 priority customer support.",
    "Standard plan subscribers get email support with a 48-hour response time.",
    "Shipping is free for orders over $50 within the continental US.",
]

class MockQuery(BaseModel):
    query: str

def simple_retrieve(query: str, chunks: list[str], top_k: int = 1) -> list[str]:
    """Naive keyword-overlap retrieval — deliberately simple, not embeddings, so behavior is easy to reason about."""
    query_words = set(query.lower().split())
    scored = []
    for chunk in chunks:
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words & chunk_words)
        scored.append((overlap, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored[:top_k] if score > 0]

@router.post("/real-mock-chatbot")
def real_mock_chatbot(payload: MockQuery):
    retrieved = simple_retrieve(payload.query, KB_CHUNKS, top_k=2)
    context_text = " ".join(retrieved) if retrieved else "No relevant context found."

    prompt = f"""Answer the user's question using ONLY the context below. If the context doesn't contain the answer, say you don't have that information.

Context: {context_text}

Question: {payload.query}
"""
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
    )
    answer = completion.choices[0].message.content

    return {
        "response": answer,
        "context": context_text,
    }