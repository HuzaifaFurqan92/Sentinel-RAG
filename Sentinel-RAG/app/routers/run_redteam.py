from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import KBInput, ChatbotConfig, SafetyVerdictRead
from ..agents.red_team_agent import generate_redteam_queries, validate_redteam_grounding
from ..agents.safety_judge_agent import judge_safety
from ..caller import run_test_batch
from ..models import SafetyVerdictRecord
from ..run_utils import start_new_run

router = APIRouter()


@router.post("/run-full-redteam")
def run_full_redteam(kb: KBInput, config: ChatbotConfig, db: Session = Depends(get_db)):
    run_id, run_label = start_new_run(db)

    raw_result = generate_redteam_queries(kb.kb_text, kb.n)
    clean_result = validate_redteam_grounding(raw_result, kb.kb_text)

    queries = [item.query for item in clean_result.items]
    meta_map = {item.query: item for item in clean_result.items}

    traces = run_test_batch(queries, config, db, run_id, run_label)

    verdicts = []
    failed_calls = []
    skipped_no_meta = []

    for position, trace in enumerate(traces, start=1):
        if trace.response is None:
            failed_calls.append({
                "position": position,
                "query": trace.query,
                "reason": "chatbot call failed or returned no response"
            })
            continue

        item = meta_map.get(trace.query)
        if item is None:
            skipped_no_meta.append({
                "position": position,
                "query": trace.query,
                "reason": "no matching red-team metadata found"
            })
            continue

        verdict_result = judge_safety(
            query=trace.query,
            attack_type=item.attack_type.value,
            expected_safe_behavior=item.expected_safe_behavior,
            actual_response=trace.response,
        )
        db_verdict = SafetyVerdictRecord(
            trace_id=trace.id,
            query=trace.query,
            attack_type=item.attack_type.value,
            actual_response=trace.response,
            expected_safe_behavior=item.expected_safe_behavior,
            stayed_in_scope=verdict_result.stayed_in_scope,
            resisted_manipulation=verdict_result.resisted_manipulation,
            leaked_instructions=verdict_result.leaked_instructions,
            passed=verdict_result.passed,
            reasoning=verdict_result.reasoning,
        )
        db.add(db_verdict)
        db.commit()
        db.refresh(db_verdict)

        verdict_out = SafetyVerdictRead.model_validate(db_verdict).model_dump()
        verdict_out["position_in_run"] = position
        verdicts.append(verdict_out)

    return {
        "run_label": run_label,
        "total_tested": len(traces),
        "verdicts": verdicts,
        "failed_calls": failed_calls,
        "skipped_no_meta": skipped_no_meta,
    }