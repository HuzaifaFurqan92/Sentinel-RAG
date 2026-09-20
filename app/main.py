# main.py
from fastapi import FastAPI
from .db import engine, Base
from .routers import ingest, generate, evaluate, run_batch, run_redteam, mock_chatbot, real_mock_chatbot,report

app = FastAPI(title="SentinelRAG")

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(generate.router, tags=["generate"])
app.include_router(ingest.router, tags=["ingest"])
app.include_router(evaluate.router, tags=["evaluate"])
app.include_router(run_batch.router, tags=["run-full-eval"])
app.include_router(run_redteam.router, tags=["run-full-redteam"])
app.include_router(report.router, tags=["report"])
app.include_router(mock_chatbot.router, tags=["mock-chatbot"])
app.include_router(real_mock_chatbot.router, tags=["real-mock-chatbot"])

@app.get("/")
def root():
    return {"status": "SentinelRAG running"}