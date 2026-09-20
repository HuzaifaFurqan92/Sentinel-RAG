from sqlalchemy.orm import Session
from .eval_state import EvalState
from ..agents.persona_agent import generate_test_queries, validate_grounding
from ..agents.judge_agent import judge_response
from ..caller import run_test_batch
from ..models import Verdict
from ..schemas import ChatbotConfig, VerdictRead


def generate_node(state: EvalState) -> dict:
    kb_text = state["kb_text"]
    n = state["n"]
    queries = generate_test_queries(kb_text, n)
    validated_queries = validate_grounding(queries, kb_text)
    return {
        "generated_queries": [item.model_dump() for item in validated_queries.items]
    }


def make_call_chatbot_node(db: Session):
    def node(state: EvalState) -> dict:
        chatbot_config = ChatbotConfig(**state["chatbot_config"])
        queries = [item["query"] for item in state["generated_queries"]]

        traces = run_test_batch(
            queries,
            chatbot_config,
            db,
            state["run_id"],
            state["run_label"],
        )

        return {
            "traces": [
                {
                    "id": t.id,
                    "query": t.query,
                    "response": t.response,
                    "retrieved_context": t.retrieved_context,
                }
                for t in traces
            ]
        }
    return node


def make_judge_node(db: Session):
    def node(state: EvalState) -> dict:
        expected_map = {item["query"]: item["response"] for item in state["generated_queries"]}
        verdicts = []
        flagged = []

        for trace in state["traces"]:
            if trace["response"] is None:
                continue

            expected_response = expected_map.get(trace["query"])
            if expected_response is None:
                continue

            verdict_result = judge_response(
                query=trace["query"],
                expected_response=expected_response,
                actual_response=trace["response"],
                retrieved_context=trace["retrieved_context"] or "",
            )

            db_verdict = Verdict(
                trace_id=trace["id"],
                actual_response=trace["response"],
                expected_response=expected_response,
                retrieval_relevant=verdict_result.retrieval_relevant,
                faithful=verdict_result.faithful,
                correct=verdict_result.correct,
                primary_failure_mode=verdict_result.primary_failure_mode.value,
                reasoning=verdict_result.reasoning,
            )
            db.add(db_verdict)
            db.commit()
            db.refresh(db_verdict)

            verdict_dict = VerdictRead.model_validate(db_verdict).model_dump()
            verdicts.append(verdict_dict)

            if not verdict_result.retrieval_relevant:
                flagged.append({"trace_id": trace["id"], "query": trace["query"]})

        return {"verdicts": verdicts, "flagged_for_kb_update": flagged}
    return node
def flag_for_kb_update_node(state: EvalState) -> dict:
    """
    Runs only when there ARE flagged items (routed here conditionally).
    For now: just formats a clear, actionable summary. Later this could
    write to a separate 'kb_gaps' table, or trigger a notification.
    """
    flagged = state["flagged_for_kb_update"]
    summary = [
        f"Query '{item['query']}' failed retrieval — KB likely missing or poorly chunked content for this topic."
        for item in flagged
    ]
    return {"kb_gap_summary": summary}

def route_after_judge(state: EvalState) -> str:
    if state["flagged_for_kb_update"]:
        return "flag_for_kb_update"
    return "end"