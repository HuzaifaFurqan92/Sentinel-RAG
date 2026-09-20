import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from .models import Trace

def start_new_run(db: Session) -> tuple[str, str]:
    """Generates a new internal run_id (UUID) and a friendly run_label (Run #N)."""
    existing_run_count = db.query(func.count(distinct(Trace.run_id))).scalar() or 0
    run_id = str(uuid.uuid4())
    run_label = f"Run #{existing_run_count + 1}"
    return run_id, run_label