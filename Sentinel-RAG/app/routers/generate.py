from fastapi import APIRouter, HTTPException, status

from ..schemas import KBInput, TestQuerySet
from ..agents.persona_agent import generate_test_queries, validate_grounding

router = APIRouter(prefix="", tags=["Generate"])


@router.post(
    "/generate",
    response_model=TestQuerySet,
    status_code=status.HTTP_200_OK
)
def generate_test_set(payload: KBInput):
  
    try:
        raw_test_set = generate_test_queries(payload.kb_text, payload.n)
        clean_test_set = validate_grounding(raw_test_set, payload.kb_text)
        return clean_test_set
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate test set: {str(e)}"
        )