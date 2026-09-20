from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import KBInput, ChatbotConfig
from ..graph.build_graph import build_eval_graph
from ..run_utils import start_new_run

router = APIRouter()

@router.post("/run-full-eval-graph")
def run_full_eval_graph(kb: KBInput, config: ChatbotConfig, db: Session = Depends(get_db)):
    run_id, run_label = start_new_run(db)

    compiled_graph = build_eval_graph(db)

    initial_state = {
        "kb_text": kb.kb_text,
        "n": kb.n,
        "chatbot_config": config.model_dump(),
        "run_id": run_id,
        "run_label": run_label,
        "generated_queries": [],
        "traces": [],
        "verdicts": [],
        "flagged_for_kb_update": [],
    }

    final_state = compiled_graph.invoke(initial_state)

    return {
        "run_label": run_label,
        "verdicts": final_state["verdicts"],
        "flagged_for_kb_update": final_state["flagged_for_kb_update"],
    }