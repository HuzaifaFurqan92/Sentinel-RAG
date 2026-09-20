# SentinelRAG

**An Autonomous Evaluation and Red-Teaming Platform for RAG / LLM Systems**

SentinelRAG is an evaluation and diagnosis platform for retrieval-augmented generation (RAG) chatbots. Given a knowledge base and a target chatbot's API, it autonomously generates realistic test queries and adversarial red-team attacks, executes them against the target system, judges the responses, and diagnoses the root cause of any failure — retrieval, generation, or safety — rather than reporting an isolated pass/fail score.

Most evaluation frameworks require test cases to be hand-written and metrics to be manually selected and interpreted. SentinelRAG generates its own test suite from a knowledge base, red-teams the target system for safety automatically, and produces a root-cause diagnosis rather than a set of disconnected metric scores.

---

## Motivation

Teams operating RAG chatbots in production frequently lack a reliable mechanism to detect hallucination, retrieval degradation, or susceptibility to prompt injection before end users are affected. Manual spot-checking does not scale, and existing evaluation libraries (DeepEval, Ragas, TruLens) are primarily developer-facing testing tools — effective, but they still require hand-written test cases and manual interpretation of multiple independent metric scores.

SentinelRAG addresses this by providing an autonomous evaluation layer: test generation, execution, judging, and root-cause diagnosis, end-to-end, through a single API call.

---

## Core capabilities

- **Autonomous test generation** — a persona agent generates realistic user queries grounded in the provided knowledge base, with automatic grounding validation to filter out ungrounded or hallucinated test cases.
- **Automated red-teaming** — a dedicated agent generates adversarial queries across four attack categories (prompt injection, jailbreak attempts, out-of-scope probing, and contradiction traps) and evaluates whether the target system resisted them safely.
- **Root-cause diagnosis** — rather than reporting independent metric scores, the quality judge assigns a single `primary_failure_mode` (`retrieval_failure`, `faithfulness_failure`, `correctness_failure`, `retrieval_and_generation_failure`, or `none`), identifying the actual point of failure.
- **LangGraph-orchestrated pipelines** — both the quality-evaluation and red-team flows are implemented as stateful graphs (generate → call target system → judge → conditional branch) rather than linear scripts, enabling dynamic routing based on runtime outcomes — for example, automatically flagging knowledge-base gaps when retrieval fails.
- **Aggregate reporting** — a `/report` endpoint summarizes pass rates and failure-mode distributions for a given run, scoped by `run_id`.

---

## Architecture

```
Knowledge Base + Chatbot API
        │
        ▼
 ┌─────────────────┐      ┌──────────────────┐
 │  Persona Agent    │      │  Red-Team Agent   │
 │  (realistic Qs)   │      │  (adversarial Qs) │
 └────────┬─────────┘      └─────────┬────────┘
          │                          │
          ▼                          ▼
   ┌──────────────────────────────────────┐
   │        Caller (hits target bot)        │
   └──────────────────┬───────────────────┘
                       ▼
             ┌───────────────────┐
             │   Quality Judge     │   ┌───────────────────┐
             │ (faithfulness,      │   │   Safety Judge      │
             │  correctness,       │   │ (scope, injection,  │
             │  retrieval)         │   │  jailbreak resist.) │
             └─────────┬──────────┘   └─────────┬──────────┘
                       ▼                        ▼
              Verdict + root-cause      SafetyVerdict + pass/fail
                       │                        │
                       └──────────┬─────────────┘
                                  ▼
                          Aggregate Report
```

Orchestrated via **LangGraph** with conditional edges: failed retrieval routes to a KB-gap flagging node; failed safety checks route to a security-alert node.

---

## Tech stack

- **Backend:** FastAPI, SQLAlchemy, SQLite (Postgres planned for production)
- **LLM inference:** Groq API (Llama / OpenAI OSS models)
- **Structured output:** `instructor` for schema-validated LLM responses
- **Orchestration:** LangGraph (stateful multi-agent graphs, conditional routing)
- **Validation:** Pydantic

---

## API overview

| Endpoint | Description |
|---|---|
| `POST /generate-tests` | Generate grounded test queries from a knowledge base |
| `POST /ingest` | Record a query/response/context trace from a chatbot |
| `POST /evaluate` | Judge a single recorded trace |
| `POST /run-full-eval` | End-to-end: generate → call target chatbot → judge → save |
| `POST /run-full-redteam` | End-to-end adversarial testing pipeline |
| `POST /run-full-eval-graph` | Same as above, orchestrated via LangGraph with conditional branching |
| `POST /run-full-redteam-graph` | Red-team pipeline via LangGraph |
| `GET /report` | Aggregate pass rates and failure-mode breakdown, optionally scoped by `run_id` |

---

## Status

Actively in development.
- [x] Core ingestion + generation + judging pipeline
- [x] Red-teaming (prompt injection, jailbreak, out-of-scope, contradiction traps)
- [x] Aggregate reporting
- [x] LangGraph orchestration with conditional branching
- [ ] Judge calibration against human-labeled ground truth (Cohen's kappa)
- [ ] Extended RAG metrics (contextual precision/recall, answer relevancy)
- [ ] Multi-turn conversation evaluation
- [ ] Self-hosted inference benchmarking (vLLM)
- [ ] Client dashboard
- [ ] Multi-tenant auth + billing

---

## Local setup

```bash
git clone https://github.com/HuzaifaFurqan92/Sentinel-RAG.git
cd Sentinel-RAG
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key
```

Run:
```bash
uvicorn app.main:app --reload
```

API docs available at `http://127.0.0.1:8000/docs`.

---

## Author

[Huzaifa Furqan](https://github.com/HuzaifaFurqan92)
