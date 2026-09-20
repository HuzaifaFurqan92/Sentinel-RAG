from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Trace, Verdict
from ..schemas import EvaluateRequest, VerdictRead
from ..agents.judge_agent import judge_response

router = APIRouter()

@router.post("/evaluate", response_model=VerdictRead)
def evaluate_trace(payload: EvaluateRequest, db: Session = Depends(get_db)):
    trace = db.get(Trace, payload.trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    verdict_result = judge_response(
        query=trace.query,
        expected_response=payload.expected_response,
        actual_response=trace.response,
        retrieved_context=trace.retrieved_context,
    )

    db_verdict = Verdict(
        trace_id=trace.id,
        actual_response=trace.response,
        expected_response=payload.expected_response,
        retrieval_relevant=verdict_result.retrieval_relevant,
        faithful=verdict_result.faithful,
        correct=verdict_result.correct,
        primary_failure_mode=verdict_result.primary_failure_mode.value,
        reasoning=verdict_result.reasoning,
    )
    db.add(db_verdict)
    db.commit()
    db.refresh(db_verdict)
    return db_verdict