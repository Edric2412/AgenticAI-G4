# 🛠️ DocuFlow AI: Autonomous Multi-Agent Document Workflow

<div align="center">

![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=for-the-badge&logo=next.js&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful-orange?style=for-the-badge&logo=langchain&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/Postgres-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4_CSS--First-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**An autonomous, stateful Multi-Agent document generation, self-correction, and audit workflow application.**  
*Developed as an internship project showcase demonstrating advanced agentic loop orchestration and human-in-the-loop controls.*

</div>

---

## 🏗️ System Architecture & Workflow DAG

DocuFlow AI is built as a stateful, cyclic state machine using a Directed Acyclic Graph (DAG) pattern rather than a linear pipeline. The central state is serialized and persisted in a database, allowing thread executions to pause, resume, and loop back dynamically.

```mermaid
graph TD
    %% Styling definitions
    classDef init fill:#1a1a2e,stroke:#adc6ff,stroke-width:2px;
    classDef agent fill:#201f20,stroke:#8c909f,stroke-width:2px;
    classDef check fill:#2a2a2b,stroke:#ffdcc6,stroke-width:2px;
    classDef hitl fill:#3a393a,stroke:#ffb786,stroke-dasharray: 5 5,stroke-width:2px;
    classDef endNode fill:#1c1b1c,stroke:#10B981,stroke-width:2px;

    %% Nodes
    A[Conception Hub: Raw Intake]:::init
    B[pgvector Semantic Style Guide Retrieval]:::check
    C["Writer Node (gemini-3.1-flash-lite)"]:::agent
    D["Critic Node (Llama 3.3 70B via Groq)"]:::agent
    E{Router Decision Edge}:::check
    F["Human-in-the-Loop Interrupt Gate"]:::hitl
    G["Deployment Node"]:::endNode

    %% Flow Paths
    A --> B
    B --> C
    C --> D
    D --> E
    
    %% Loops
    E -- "Score < 95 & Cycles < 3 (Loop back)" --> H[Increment Loop Count]
    H --> C
    
    E -- "Score >= 95" --> G
    E -- "Circuit Breaker: Cycles >= 3" --> F
    
    F -- "User Feedback (Resume Loop)" --> C
    F -- "User Approval (Final Deploy)" --> G
```

---

## 🌟 Key Technology Highlights

> [!NOTE]
> **Stateful Orchestration (LangGraph)**  
> Tracks the live document draft, validation scorecards, iteration log arrays, loop counters, and system statuses in a central Pydantic state model. State checkpoints are serialized at every node transition, ensuring re-entrancy safety.

> [!IMPORTANT]
> **Matryoshka Representation Learning (MRL)**  
> Generates context embeddings using `gemini-embedding-2`, explicitly truncated to **768 dimensions** using prefix-slicing. This maintains 98%+ retrieval accuracy while speeding up cosine-similarity searches inside `pgvector`.

> [!WARNING]
> **Circuit Breaker Loop Guard**  
> To contain API token budgets and prevent infinite semantic loops (e.g. Writer and Critic disputing constraints endlessly), execution is automatically interrupted and routed to the user's dashboard after 3 revision cycles.

> [!IMPORTANT]
> **pgvector Semantic Retrieval**  
> Style-guide embeddings are stored using PostgreSQL + pgvector `Vector(768)` columns, enabling high-performance cosine similarity retrieval for contextual drafting and reviewer alignment.

> [!TIP]
> **Groq Critic Orchestration**  
> The Critic Node uses Groq-hosted Llama 3.3 70B to generate deterministic structured JSON scorecards for multi-agent document critique and revision routing.

> [!TIP]
> **Semantic Enrichment & Conflict Detection Toggles**  
> Conception Hub toggles dynamically control downstream model behaviors. *Semantic Enrichment* pulls style context dynamically via `pgvector` to enrich drafts, while *Conflict Detection* appends a dedicated internal contradiction evaluation check (ID: `con`) to the Critic's prompt and checklist.

---

## 📂 Monorepo Structure

```
DocuFlow/
├── frontend/                # Next.js 16 (App Router)
│   ├── src/
│   │   ├── app/             # Routing segments (/dashboard, /conception, /canvas)
│   │   ├── components/      # UI Cards, Sidebars, and top navigation wrappers
│   │   ├── hooks/           # useAgentSession hook (SSE stream parser & simulator)
│   │   └── types/           # Pydantic schemas mapped to TypeScript interfaces
│   ├── public/              # Static assets and icons
│   └── .env.example         # Template for client environment variables
│
├── backend/                 # FastAPI Gateway + LangGraph API
│   ├── alembic/             # Database migrations for PostgreSQL + pgvector
│   ├── alembic.ini          # Alembic migration configuration
│   ├── docker-compose.yml   # PostgreSQL pgvector infrastructure
│   ├── app/
│   │   ├── config.py        # Settings and environment API key validations
│   │   ├── db.py            # SQLAlchemy database setup & pgvector lookup stubs
│   │   ├── graph.py         # LangGraph workflow, Groq critic orchestration & routing logic
│   │   ├── main.py          # FastAPI REST endpoints & Server-Sent Events stream
│   │   ├── schemas.py       # Pydantic schema declarations
│   │   └── state.py         # TypedDict graph state tracking definitions
│   ├── requirements.txt     # Python backend dependencies
│   └── .env.example         # Backend environment configuration template
│
└── .gitignore               # Unified monorepo git exclusions
```

---

## 🚀 Local Startup Guide

### 1. Frontend Setup (Next.js)

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```
2.  **Configure environment variables**:
    ```bash
    cp .env.example .env.local
    ```
3.  **Install packages and run**:
    ```bash
    npm install
    npm run dev
    ```
    *   Open [http://localhost:3000](http://localhost:3000) to view the client.

### 2. Backend Setup (FastAPI)

> [!IMPORTANT] 
> **Docker Desktop Required**  
> Docker Desktop is required for local pgvector PostgreSQL infrastructure.  
> The semantic retrieval pipeline depends on PostgreSQL vector extension support and cannot run on SQLite.

> [!NOTE]
> New infrastructure dependencies include `pgvector`, `asyncpg`, `alembic`, and Groq/OpenAI-compatible client integrations for semantic retrieval and structured AI critique orchestration.

1.  **Navigate to the backend directory**:
    ```bash
    cd backend
    ```
2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv .venv
    ```

    **Linux/macOS**
    ```bash
    source .venv/bin/activate
    ```

    **Windows**
    ```bash
    .venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create a `.env` file inside `backend/`**:

> [!TIP]
> Copy `.env.example` → `.env` before running the backend locally.

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5434/docuflow
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

### 3. PostgreSQL + pgvector Setup

1. **Start PostgreSQL with pgvector**

```bash
docker-compose up -d
```

2. **Verify container is running**

```bash
docker ps
```

Expected container:

```text
docuflow-postgres
```

3. **Enable pgvector extension**

```bash
docker exec -it docuflow-postgres psql -U postgres -d docuflow
```

Inside PostgreSQL shell:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Exit PostgreSQL:

```sql
\q
```

4. **Run Alembic migrations**

```bash
python -m alembic upgrade head
```

> [!WARNING]
> Backend startup may fail if migrations are not executed before running the FastAPI server.

5.  **Start FastAPI backend**:
    ```bash
    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ```

*   Interactive Swagger API docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
   
---

## Infrastructure Verification Checklist

### Verify Docker Container

```bash
docker ps
```

Expected:
```text
docuflow-postgres
```

### Verify pgvector Extension

```bash
docker exec -it docuflow-postgres psql -U postgres -d docuflow
```

Inside PostgreSQL:
```sql
SELECT extname FROM pg_extension;
```

Expected extension:
```text
vector
```

### Verify Alembic Migration

```bash
python -m alembic upgrade head
```

### Verify FastAPI Startup

```bash
uvicorn app.main:app --reload
```

Expected:
```text
Application startup complete
```

### Verify Swagger Docs

Open:
```text
http://127.0.0.1:8000/docs
```

---

## 🧪 End-to-End Archetype Testing

DocuFlow AI includes a robust Playwright E2E integration test suite that verifies the entire document generation, human revision loop, approval, and dashboard reporting flow. The test script has been parameterized to support testing any of the document archetypes.

### Running Archetype E2E Tests

Ensure both the Next.js frontend (port 3000) and the FastAPI backend (port 8000) are running, then run the test script specifying your desired archetype:

```bash
# Run tests using the backend virtual environment python
./backend/venv/bin/python e2e_test.py --archetype [Technical | Legal | Financial | Creative]
```

* Archetype-specific screenshots (e.g. `1_conception_legal.png`, `4_canvas_paused_legal.png`, etc.) will be archived in the workspace scratch directory: `/home/edricjsam/.gemini/antigravity-ide/scratch/`.

---

## 🔒 Database & Connection Resilience

The database connector incorporates production-grade resiliency controls to prevent transaction cancellations and pool contamination:

1. **Atomic DB Writes (`asyncio.shield`)**:
   Background session state persistence tasks are shielded from cancellation. If a client terminates their SSE stream connection or navigates away, the database write operation is guaranteed to finish atomically, preventing transaction truncation.

2. **Optimistic Disconnect Handling (`pool_pre_ping`)**:
   The SQLAlchemy engine uses `pool_pre_ping=True` and a connection recycle timeout of 30 minutes to verify connection health before checking them out of the pool. If a database session drops or gets disconnected, the pool automatically recycles the connection, eliminating `InterfaceError: connection is closed` exceptions.

3. **Transaction Rollback Safeguards**:
   The persistence layer explicitly catches `BaseException` (which captures `asyncio.CancelledError`) to execute a clean transaction rollback on cancellation before bubbling up, preventing session leaks.