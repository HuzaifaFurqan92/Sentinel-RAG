import requests
from sqlalchemy.orm import Session
from .models import Trace
from .schemas import ChatbotConfig


def call_target_chatbot(query: str, config: ChatbotConfig) -> dict:
    """Sends a single test query to the client's chatbot and extracts response + context."""
    payload = {config.request_field: query}
    headers = {"Authorization": f"Bearer {config.api_key}"} if config.api_key else {}

    resp = requests.post(config.endpoint_url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return {
        "response": data.get(config.response_field),
        "retrieved_context": data.get(config.context_field) if config.context_field else None,
    }


def run_test_batch(queries: list[str], config: ChatbotConfig, db: Session, run_id: str, run_label: str) -> list[Trace]:
    traces = []
    for query in queries:
        try:
            result = call_target_chatbot(query, config)
        except requests.RequestException as e:
            result = {"response": None, "retrieved_context": None}
            print(f"⚠️ Failed to call chatbot for query '{query}': {e}")

        trace = Trace(
            query=query,
            response=result["response"],
            retrieved_context=result["retrieved_context"],
            run_id=run_id,
            run_label=run_label,
        )
        db.add(trace)
        db.commit()
        db.refresh(trace)
        traces.append(trace)

    return traces