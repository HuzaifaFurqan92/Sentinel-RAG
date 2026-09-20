from typing import TypedDict, List

class RedTeamState(TypedDict):
    kb_text: str
    n: int
    chatbot_config: dict
    run_id: str
    run_label: str
    generated_queries: List[dict]   # from redteam agent: query, attack_type, expected_safe_behavior
    traces: List[dict]
    verdicts: List[dict]
    failed_safety_checks: List[dict]  # attacks the chatbot did NOT resist