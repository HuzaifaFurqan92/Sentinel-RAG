from groq import Groq
import instructor
from ..config import settings
from ..schemas import JudgeVerdict

client = instructor.from_groq(Groq(api_key=settings.GROQ_API_KEY), mode=instructor.Mode.JSON)


def judge_response(
    query: str,
    expected_response: str,
    actual_response: str,
    retrieved_context: str,
) -> JudgeVerdict:
    prompt = f"""You are a strict QA judge diagnosing failures in a RAG chatbot.
Respond in structured JSON matching the required schema — no free text outside the schema fields.

USER QUERY:
\"\"\"{query}\"\"\"

RETRIEVED CONTEXT (what the retrieval system fetched for the chatbot):
\"\"\"{retrieved_context}\"\"\"

EXPECTED RESPONSE (ground truth / ideal answer):
\"\"\"{expected_response}\"\"\"

ACTUAL RESPONSE (what the chatbot actually said):
\"\"\"{actual_response}\"\"\"

Diagnose in this order:

1. RETRIEVAL: Does the retrieved context actually contain the information needed to
   answer the query correctly? If the context is irrelevant, incomplete, or missing
   the key fact entirely, retrieval_relevant = false. This must be judged independently
   of what the chatbot's response actually said.

2. FAITHFULNESS: Given the retrieved context (regardless of whether it was the RIGHT
   context), does the actual response only state things supported by it? If the
   response includes facts not present in the retrieved context, faithful = false.

3. CORRECTNESS: Does the actual response match the expected response's meaning?
   Paraphrasing is fine; wrong or missing key facts are not.

4. PRIMARY FAILURE MODE: Choose exactly one root cause:
   - If retrieval_relevant is false, the root cause is almost always "retrieval_failure"
     or "retrieval_and_generation_failure" (if the response ALSO hallucinated on top of bad context) — 
     don't blame faithfulness/correctness for a retrieval problem.
   - If retrieval was fine but the response invented facts beyond it, use "faithfulness_failure".
   - If retrieval and faithfulness were both fine but the answer still contradicts or misses
     the expected answer, use "correctness_failure".
   - If everything is fine, use "none".

Explain your reasoning briefly, specifically naming what was missing or wrong.
"""
    verdict = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        response_model=JudgeVerdict,
        messages=[{"role": "user", "content": prompt}],
    )
    return verdict