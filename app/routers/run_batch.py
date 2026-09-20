from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import KBInput, ChatbotConfig, VerdictRead
from ..agents.persona_agent import generate_test_queries, validate_grounding
from ..agents.judge_agent import judge_response
from ..caller import run_test_batch
from ..models import Verdict

router = APIRouter()

from ..run_utils import start_new_run

@router.post("/run-full-eval")
def run_full_eval(kb: KBInput, config: ChatbotConfig, db: Session = Depends(get_db)):
    run_id, run_label = start_new_run(db)

    raw_result = generate_test_queries(kb.kb_text, kb.n)
    clean_result = validate_grounding(raw_result, kb.kb_text)

    queries = [item.query for item in clean_result.items]
    expected_map = {item.query: item.response for item in clean_result.items}

    traces = run_test_batch(queries, config, db, run_id, run_label)

    verdicts = []
    failed_calls = []
    skipped_no_meta = []

    for position, trace in enumerate(traces, start=1):
        if trace.response is None:
            failed_calls.append({"position": position, "query": trace.query, "reason": "chatbot call failed or returned no response"})
            continue

        expected_response = expected_map.get(trace.query)
        if expected_response is None:
            skipped_no_meta.append({"position": position, "query": trace.query, "reason": "no matching expected_response found"})
            continue

        verdict_result = judge_response(
            query=trace.query,
            expected_response=expected_response,
            actual_response=trace.response,
            retrieved_context=trace.retrieved_context or "",
        )
        db_verdict = Verdict(
            trace_id=trace.id,
            actual_response=trace.response,
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

        verdict_out = VerdictRead.model_validate(db_verdict).model_dump()
        verdict_out["position_in_run"] = position  # friendly, not the raw id
        verdicts.append(verdict_out)

    return {
        "run_label": run_label,
        "total_tested": len(traces),
        "verdicts": verdicts,
        "failed_calls": failed_calls,
        "skipped_no_meta": skipped_no_meta,
    }