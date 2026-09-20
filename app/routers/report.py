from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from collections import Counter, defaultdict
from typing import Optional
from ..db import get_db
from ..models import Verdict, SafetyVerdictRecord, Trace
from ..schemas import FullReport, QualityReport, SafetyReport, FailureModeBreakdown, AttackTypeBreakdown

router = APIRouter()


@router.get("/report", response_model=FullReport)
def get_report(run_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    if run_id:
        relevant_trace_ids = {t.id for t in db.query(Trace.id).filter(Trace.run_id == run_id).all()}
        verdicts = db.query(Verdict).filter(Verdict.trace_id.in_(relevant_trace_ids)).all()
        safety_verdicts = db.query(SafetyVerdictRecord).filter(SafetyVerdictRecord.trace_id.in_(relevant_trace_ids)).all()
    else:
        verdicts = db.query(Verdict).all()
        safety_verdicts = db.query(SafetyVerdictRecord).all()

    # ---- Quality report ----
    total_quality = len(verdicts)
    failure_counter = Counter(v.primary_failure_mode for v in verdicts)
    passed_quality = failure_counter.get("none", 0)
    quality_pass_rate = (passed_quality / total_quality) if total_quality > 0 else 0.0

    failure_breakdown = [
        FailureModeBreakdown(mode=mode, count=count)
        for mode, count in failure_counter.items()
    ]

    quality_report = QualityReport(
        total_evaluated=total_quality,
        pass_rate=round(quality_pass_rate, 4),
        failure_breakdown=failure_breakdown,
    )

    # ---- Safety report ----
    total_safety = len(safety_verdicts)
    safety_passed = sum(1 for v in safety_verdicts if v.passed)
    safety_pass_rate = (safety_passed / total_safety) if total_safety > 0 else 0.0

    attack_groups = defaultdict(list)
    for v in safety_verdicts:
        attack_groups[v.attack_type].append(v.passed)

    attack_breakdown = []
    for attack_type, results in attack_groups.items():
        total = len(results)
        passed = sum(1 for r in results if r)
        rate = (passed / total) if total > 0 else 0.0
        attack_breakdown.append(
            AttackTypeBreakdown(
                attack_type=attack_type,
                total=total,
                passed=passed,
                pass_rate=round(rate, 4),
            )
        )

    safety_report = SafetyReport(
        total_evaluated=total_safety,
        pass_rate=round(safety_pass_rate, 4),
        breakdown_by_attack_type=attack_breakdown,
    )

    return FullReport(quality=quality_report, safety=safety_report)