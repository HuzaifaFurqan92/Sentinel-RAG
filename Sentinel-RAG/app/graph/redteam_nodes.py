from sqlalchemy.orm import Session
from .redteam_state import RedTeamState
from ..agents.red_team_agent import generate_redteam_queries, validate_redteam_grounding
from ..agents.safety_judge_agent import judge_safety
from ..caller import run_test_batch
from ..models import SafetyVerdictRecord
from ..schemas import ChatbotConfig, SafetyVerdictRead


def generate_redteam_node(state: RedTeamState) -> dict:
    kb_text = state["kb_text"]
    n = state["n"]
    raw_result = generate_redteam_queries(kb_text, n)
    clean_result = validate_redteam_grounding(raw_result, kb_text)
    return {
        "generated_queries": [item.model_dump() for item in clean_result.items]
    }


def make_call_chatbot_redteam_node(db: Session):
    def node(state: RedTeamState) -> dict:
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


def make_judge_safety_node(db: Session):
    def node(state: RedTeamState) -> dict:
        meta_map = {item["query"]: item for item in state["generated_queries"]}
        verdicts = []
        failed_checks = []

        for trace in state["traces"]:
            if trace["response"] is None:
                continue

            item = meta_map.get(trace["query"])
            if item is None:
                continue

            verdict_result = judge_safety(
                query=trace["query"],
                attack_type=item["attack_type"],
                expected_safe_behavior=item["expected_safe_behavior"],
                actual_response=trace["response"],
            )

            db_verdict = SafetyVerdictRecord(
                trace_id=trace["id"],
                query=trace["query"],
                attack_type=item["attack_type"],
                actual_response=trace["response"],
                expected_safe_behavior=item["expected_safe_behavior"],
                stayed_in_scope=verdict_result.stayed_in_scope,
                resisted_manipulation=verdict_result.resisted_manipulation,
                leaked_instructions=verdict_result.leaked_instructions,
                passed=verdict_result.passed,
                reasoning=verdict_result.reasoning,
            )
            db.add(db_verdict)
            db.commit()
            db.refresh(db_verdict)

            verdict_dict = SafetyVerdictRead.model_validate(db_verdict).model_dump()
            verdicts.append(verdict_dict)

            if not verdict_result.passed:
                failed_checks.append({"trace_id": trace["id"], "query": trace["query"], "attack_type": item["attack_type"]})

        return {"verdicts": verdicts, "failed_safety_checks": failed_checks}
    return node

def flag_safety_failures_node(state: RedTeamState) -> dict:
    failed = state["failed_safety_checks"]
    summary = [
        f"SECURITY ALERT: chatbot failed to resist '{item['attack_type']}' attack on query: '{item['query']}'"
        for item in failed
    ]
    return {"safety_alert_summary": summary}


def route_after_safety_judge(state: RedTeamState) -> str:
    if state["failed_safety_checks"]:
        return "flag_safety_failures"
    return "end"