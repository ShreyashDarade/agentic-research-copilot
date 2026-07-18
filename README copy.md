<!-- Daily update: 2026-07-18 -->
# DeepAgents Agentic-Research-Copilot

This is not a basic chatbot. It is AI engineering project that demonstrates:

- **Agentic workflow orchestration** with `LangGraph`.
- **RAG architecture** with chunking, embeddings, and vector retrieval.
- **Source-grounded research** from URLs and PDFs.
- **Claim verification** before report finalization.
- **Human-in-the-loop approval** for safer AI output.
- **DeepAgents harness integration** for planning, artifacts, subagents, context compression, and approval interrupts.
- **FastAPI production API design** with typed request/response schemas.
- **Minimal dashboard** for demos and recruiter walkthroughs.
- **Postgres-ready persistence model** with SQLAlchemy and Alembic.
- **Qdrant vector database integration** for semantic retrieval.
- **LangSmith-ready observability** for tracing, debugging, and evaluation.
- **CI-friendly engineering quality** with `pytest`, `ruff`, and `mypy`.

## High-Level Architecture

```mermaid
flowchart TD
    User[User] --> Dashboard[Minimal Dashboard]
    Dashboard --> API[FastAPI API]
    API --> ResearchService[Research Service]

    ResearchService --> Ingestion[Source Ingestion]
    Ingestion --> URLLoader[URL Loader]
    Ingestion --> PDFLoader[PDF Loader]
    Ingestion --> Chunker[Text Chunker]
    Chunker --> Embeddings[Embedding Model]
    Embeddings --> Qdrant[Qdrant Vector Store]

    ResearchService --> Graph[LangGraph Workflow]
    Graph --> Planner[Planner Node]
    Graph --> Retrieval[Retrieval Node]
    Graph --> Verifier[Claim Verifier Node]
    Graph --> DraftWriter[Draft Report Writer]
    Graph --> ApprovalGate[Human Approval Gate]
    ApprovalGate --> FinalWriter[Final Report Writer]

    API --> Postgres[Postgres Metadata Schema]
    Graph --> LangSmith[LangSmith Tracing]
```

## Core Workflow

1. User submits a research topic and optional source URLs.
2. Source ingestion extracts text from URLs or PDFs.
3. Text is normalized, chunked, embedded, and stored for retrieval.
4. LangGraph plans research questions.
5. Relevant evidence chunks are retrieved.
6. Claims are generated and checked against evidence.
7. A draft report is created with source citations.
8. The workflow pauses for human approval.
9. After approval, a final Markdown report is generated.

## Tech Stack

| Area                | Technology                    |
| ------------------- | ----------------------------- |
| Language            | Python 3.12+                  |
| API                 | FastAPI, Pydantic v2, Uvicorn |
| Agent Runtime       | LangGraph, DeepAgents         |
| LLM/RAG Framework   | LangChain                     |
| Vector Database     | Qdrant                        |
| Relational Database | Postgres                      |
| ORM/Migrations      | SQLAlchemy 2, Alembic         |
| Dashboard           | Jinja2 templates, CSS         |
| Observability       | LangSmith-ready tracing hooks |
| Testing             | pytest, pytest-asyncio, httpx |
| Quality             | ruff, mypy                    |
| Packaging           | uv                            |
| Local Infra         | Docker Compose                |

## Project Structure

```text
.
├── app/
│   ├── agents/          # LangGraph state, workflow nodes, prompts, DeepAgents harness
│   ├── api/             # FastAPI routes and API schemas
│   ├── core/            # Settings, logging, observability
│   ├── db/              # SQLAlchemy models, repositories, async sessions
│   ├── rag/             # Loaders, chunking, embeddings, ingestion, vector stores
│   ├── services/        # Research orchestration service
│   └── web/             # Dashboard templates and static assets
├── alembic/             # Database migrations
├── tests/               # Unit and integration tests
├── docker-compose.yml   # Postgres and Qdrant
├── Dockerfile           # Production API image
├── pyproject.toml       # uv project and tooling config
└── README.md
```

## Features

### Agentic Research Runs

Create a research run with:

- Topic
- Optional source URLs
- Optional research constraints
- Approval-gated final report generation

### Source Ingestion

The project supports:

- URL ingestion through `httpx` and `BeautifulSoup`
- PDF ingestion through `pypdf`
- Chunking with metadata and offsets
- Deterministic local embeddings for no-key demos
- Qdrant adapter for production vector search

### Claim Verification

The workflow extracts source-backed claims and assigns support labels:

- `supported`
- `weakly_supported`
- `unsupported`

Each claim is linked to evidence chunk IDs so reviewers can trace report statements back to source material.

### Human Approval Gate

Before final report generation, the graph pauses in:

```text
awaiting_approval
```

A human reviewer can approve or reject the draft from the dashboard or API.

### DeepAgents Harness

The project includes a concrete DeepAgents integration in `app/agents/deepagents_adapter.py`.

Every research run is prepared with:

- **Task planning**: a structured checklist for long-running research work.
- **Virtual filesystem artifacts**: per-run files under `storage/artifacts/<run_id>/`.
- **Subagent delegation**: specialist tasks for `source_analyst`, `claim_verifier`, and `report_writer`.
- **Context compression**: retained evidence summaries with chunk IDs and source metadata.
- **Human approval policy**: final report writing is configured as an interrupt-worthy action.
- **Live runtime factory**: `create_runtime_agent()` calls `deepagents.create_deep_agent(...)` when model credentials are configured.

The local demo path is deterministic so tests and dashboard demos run without paid API keys. In production, this adapter is the boundary where you enable the live DeepAgents runtime.

## Run Locally

### 1. Install prerequisites

Install:

- Python 3.12+
- Docker Desktop
- uv

Install `uv` if needed:

```bash
pip install uv
```

### 2. Clone the GitHub repository

```bash
git clone https://github.com/<your-username>/evidencegraph-ai.git
cd evidencegraph-ai
```

### 3. Install dependencies

```bash
uv sync
```

### 4. Create environment file

On macOS/Linux:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The default config uses local demo mode:

```text
LLM_PROVIDER=mock
EMBEDDING_PROVIDER=hash
```

That means the project can run without an OpenAI key.

### 5. Start local infrastructure

```bash
docker compose up -d
```

This starts:

- Postgres on `localhost:5432`
- Qdrant on `localhost:6333`

### 6. Run database migrations

```bash
uv run alembic upgrade head
```

### 7. Start the app

```bash
uv run uvicorn app.main:create_app --factory --reload
```

Open:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

## Run In GitHub Codespaces

1. Push this project to GitHub.
2. Open the repository on GitHub.
3. Click **Code**.
4. Select **Codespaces**.
5. Click **Create codespace on main**.
6. In the Codespaces terminal, run:

```bash
uv sync
cp .env.example .env
docker compose up -d
uv run alembic upgrade head
uv run uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

1. When Codespaces shows port `8000`, open it in the browser.

If Docker services take a few seconds to become healthy, rerun:

```bash
docker compose ps
```

Then run migrations again if needed:

```bash
uv run alembic upgrade head
```

## Run Tests In GitHub

This repository includes a GitHub Actions workflow at:

```text
.github/workflows/ci.yml
```

After you push to GitHub, CI runs automatically on:

- Push to `main`
- Pull requests to `main`

The workflow runs:

```bash
uv run ruff check .
uv run mypy app tests
uv run pytest -q
```

You can see results in:

```text
GitHub repository -> Actions tab
```

## API Usage

### Health check

```bash
curl http://localhost:8000/api/health
```

### Create a research run

```bash
curl -X POST http://localhost:8000/api/research-runs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI agents in production software engineering",
    "source_urls": ["https://example.com/agent-report"],
    "constraints": "Focus on verification, governance, and observability."
  }'
```

Example response shape:

```json
{
  "run_id": "run_...",
  "topic": "AI agents in production software engineering",
  "status": "awaiting_approval",
  "draft_report": "...",
  "final_report": null,
  "approval_request": {
    "required_action": "approve_or_reject"
  },
  "claims": [],
  "sources": []
}
```

### Approve final report

```bash
curl -X POST http://localhost:8000/api/research-runs/<run_id>/approval \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "reviewer": "human"}'
```

### Reject draft report

```bash
curl -X POST http://localhost:8000/api/research-runs/<run_id>/approval \
  -H "Content-Type: application/json" \
  -d '{"approved": false, "reviewer": "human", "notes": "Needs stronger sources."}'
```

## Development Commands

Run tests:

```bash
uv run pytest -q
```

Run lint:

```bash
uv run ruff check .
```

Run type checks:

```bash
uv run mypy app tests
```

Format code:

```bash
uv run ruff format .
```

Run all checks:

```bash
uv run ruff check .
uv run mypy app tests
uv run pytest -q
```

## Environment Variables

| Variable             | Purpose                               | Default                                                          |
| -------------------- | ------------------------------------- | ---------------------------------------------------------------- |
| `DATABASE_URL`       | Async Postgres connection string      | `postgresql+asyncpg://research:research@localhost:5432/research` |
| `QDRANT_URL`         | Qdrant endpoint                       | `http://localhost:6333`                                          |
| `QDRANT_COLLECTION`  | Vector collection name                | `research_chunks`                                                |
| `ARTIFACT_DIR`       | Report/artifact directory             | `storage/artifacts`                                              |
| `LLM_PROVIDER`       | LLM mode                              | `mock`                                                           |
| `EMBEDDING_PROVIDER` | Embedding mode                        | `hash`                                                           |
| `OPENAI_API_KEY`     | OpenAI key for production model calls | empty                                                            |
| `LANGSMITH_TRACING`  | Enable LangSmith tracing              | `false`                                                          |
| `LANGSMITH_API_KEY`  | LangSmith API key                     | empty                                                            |
| `LANGSMITH_PROJECT`  | LangSmith project name                | `agentic-research-assistant`                                     |

## Production Upgrade Path

This project is intentionally built as a strong first production-style version. Recommended next upgrades:

- Persist live research runs through `ResearchRunRepository` instead of the in-memory service store.
- Move long-running ingestion and report generation into a worker queue.
- Add Redis or Postgres-backed job status events.
- Add real OpenAI/Anthropic model calls for planner, verifier, and writer nodes.
- Use managed Qdrant/Postgres for deployment.
- Add authentication for dashboard/API access.
- Add source quality scoring and citation confidence.
- Add evaluation datasets for hallucination, citation support, and report quality.
- Add OpenTelemetry traces and metrics for production monitoring.

## Resume Bullet

```text
Built EvidenceGraph AI, a production-style agentic research assistant using LangGraph,
FastAPI, Qdrant, Postgres, and LangSmith-ready observability to ingest web/PDF sources,
perform RAG, verify claims against evidence, and require human approval before final
report generation.
```

## License

MIT License. Use freely for learning, portfolio, and resume projects.
