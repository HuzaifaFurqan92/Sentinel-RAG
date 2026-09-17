# agents/persona_agent.py
from groq import Groq
import instructor
from pydantic import BaseModel, Field
from typing import List
from ..config import settings
from ..schemas import TestQuerySet

client = instructor.from_groq(Groq(api_key=settings.GROQ_API_KEY), mode=instructor.Mode.JSON)


def generate_test_queries(kb_text: str, n: int ) -> TestQuerySet:
    prompt = f"""You are a QA test-case generator for a RAG chatbot.
You must respond in structured JSON matching the required schema — no free text outside the schema fields.

KNOWLEDGE BASE:
\"\"\"{kb_text}\"\"\"

Generate exactly {n} realistic user queries a customer might ask, based STRICTLY on the knowledge base above.

Rules:
- Every query must be answerable using ONLY the knowledge base text — do not invent facts, products, or details not present.
- "response" must be the correct answer, derived only from the knowledge base.
- "reference" must be a verbatim substring copied directly from the knowledge base that supports the response.
- If you cannot find enough distinct groundable queries, generate fewer rather than inventing content.
- Do not answer using outside/general knowledge, even if you know the real answer.

Here are two examples of the expected style (from a DIFFERENT knowledge base, for format reference only):

Example 1:
{{
  "id": 1,
  "query": "What is the refund window for orders?",
  "response": "Orders can be refunded within 30 days of purchase.",
  "reference": "refunds are accepted within 30 days of the original purchase date"
}}

Example 2:
{{
  "id": 2,
  "query": "Does the plan include priority support?",
  "response": "Yes, the Pro plan includes 24/7 priority support.",
  "reference": "Pro plan subscribers receive 24/7 priority customer support"
}}

Now generate {n} new items following this exact style, grounded ONLY in the knowledge base provided above.
"""
    result = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=TestQuerySet,
        messages=[{"role": "user", "content": prompt}],
    )
    return result

def validate_grounding(result: TestQuerySet, kb_text: str) -> TestQuerySet:
    """
    Post-check: instructor guarantees SHAPE (types/fields), not TRUTH.
    This filters out any item whose 'reference' isn't an actual substring
    of the knowledge base — i.e. the model made it up.
    """
    grounded_items = [
        item for item in result.items
        if item.reference.strip() in kb_text
    ]
    dropped = len(result.items) - len(grounded_items)
    if dropped > 0:
        print(f"⚠️ Dropped {dropped} ungrounded item(s) — reference not found verbatim in KB")
    return TestQuerySet(items=grounded_items)