# graph/eval_state.py
from typing import TypedDict, List, Optional

class EvalState(TypedDict):
    kb_text: str
    n: int
    chatbot_config: dict
    run_id: str
    run_label: str
    generated_queries: List[dict]      # [{query, expected_response}]
    traces: List[dict]                 # [{id, query, response, retrieved_context}]
    verdicts: List[dict]               # final judged results
    flagged_for_kb_update: List[dict]  # queries where retrieval failed
    kb_gap_summary: List[str]