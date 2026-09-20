from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db, create_trace
from ..schemas import TraceRead, TraceCreate

router = APIRouter(prefix="", tags=["Ingest"])


@router.post(
    "/ingest",
    response_model=TraceRead,
    status_code=status.HTTP_201_CREATED,  # Fixed: status_code parameter name
)
def ingest_trace(tracepayload: TraceCreate, db: Session = Depends(get_db)):
    try:
        # Fixed: calling standalone create_trace function instead of db.create_trace
        trace = create_trace(db=db, trace_data=tracepayload)
        return trace
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest trace: {str(e)}",
        )