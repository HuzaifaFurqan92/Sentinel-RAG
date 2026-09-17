# routers/mock_chatbot.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class MockQuery(BaseModel):
    query: str

@router.post("/mock-chatbot")
def mock_chatbot(payload: MockQuery):
    # Deliberately imperfect responses to test judge behavior
    return {
        "response": f"Here's an answer to: {payload.query} (mock response, may be incomplete)",
        "context": "This is placeholder retrieved context for testing purposes."
    }