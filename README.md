# DocuFlow AI: Autonomous Multi-Agent Document Workflow

DocuFlow AI is an autonomous, stateful multi-agent document workflow application. It is designed to streamline corporate document drafting, self-correction, and compliance audits using a stateful Directed Acyclic Graph (DAG) pattern. This project is developed to showcase stateful agent orchestration, high-performance UI systems, and self-correction loops.

---

## 🏗️ Project Architecture

```
                    [ CONCEPTION HUB (Ingestion Payload) ]
                                     │
                                     ▼
                            [ VECTOR DATABASE ]
                       (pgvector exact keyword matching)
                                     │
                                     ▼
                           [ WRITER AGENT NODE ] <───────────┐
                         (gemini-3.1-flash-lite)             │
                                     │                       │
                                     ▼                       │ (If Score < Threshold &
                           [ CRITIC AGENT NODE ]             │  Loops < Circuit Breaker)
                           (Llama 3.3 70B via Groq)          │
                                     │                       │
                                     ▼                       │
                            [ CONDITION ROUTER ] ────────────┘
                                     │
                                     ├─► (Checks Pass OR Loop Limit Hit)
                                     ▼
                        [ HUMAN-IN-THE-LOOP PAUSE ]
                        (PostgresSaver thread lock)
                                     │
                                     ▼
                        [ USER APPROVAL & DEPLOY ]
```

### Key Components:
1.  **Stateful Orchestration**: Driven by LangGraph, tracking live document drafts, validation scorecards, loop counters, and execution history.
2.  **Writer Node**: Powered by `gemini-3.1-flash-lite` for dense markdown drafting and deep context assimilation.
3.  **Critic Node**: Powered by `Llama 3.3 70B` via Groq for high-speed, deterministic structured JSON validation scorecards.
4.  **Human-in-the-Loop (HITL)**: Uses LangGraph's `interrupt` protocol to pause state traversal in PostgreSQL and solicit final user validation.
5.  **Vector Store**: `pgvector` performing flat exact search with hybrid keyword matching (`tsvector`) for 100% semantic matching fidelity.

---

## 📂 Monorepo Structure

```
DocuFlow/
├── frontend/                # Next.js 16 (App Router + Tailwind CSS v4)
│   ├── src/
│   │   ├── app/             # Main layouts & routes (/dashboard, /conception, /canvas)
│   │   ├── components/      # Glassmorphism design elements (Sidebar, Topbar)
│   │   ├── hooks/           # useAgentSession hook (SSE + Simulation engine)
│   │   └── types/           # TS Types matching backend Pydantic schemas
│   ├── public/              # Static assets
│   └── .env.example         # Template for environment variables
│
├── backend/                 # FastAPI API Gateway + LangGraph (To be constructed)
│
├── .gitignore               # Unified monorepo ignore configuration
└── README.md                # Project documentation (This file)
```

---

## 🚀 Setup & Execution Guide

### 1. Frontend Setup (Next.js)

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Configure environment variables**:
    Copy the environment template:
    ```bash
    cp .env.example .env.local
    ```
    *(By default, this points `NEXT_PUBLIC_API_URL` to `http://127.0.0.1:8000`)*.

3.  **Install dependencies**:
    ```bash
    npm install
    ```

4.  **Run in development mode**:
    ```bash
    npm run dev
    ```
    Open [http://localhost:3000](http://localhost:3000) to view the application.

5.  **Build for production**:
    ```bash
    npm run build
    ```

### 2. Backend Setup (FastAPI + LangGraph)

*(Detailed setup instructions will be updated here during the backend construction phase)*.

*   Default Port: `8000`
*   Frameworks: Python 3.11+, FastAPI, LangGraph, Pydantic v2, PostgreSQL + pgvector
