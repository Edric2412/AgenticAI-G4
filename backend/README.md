# DocuFlow AI: Backend Server Documentation

The backend service is built using **FastAPI** for asynchronous routing and **LangGraph** for multi-agent cyclic flow execution. 

---

## 🛠️ Requirements & Setup

1.  **System Requirements**:
    *   Python 3.11+
    *   Pip package manager

2.  **Navigate to the backend folder**:
    ```bash
    cd backend
    ```

3.  **Create a virtual environment (Optional but Recommended)**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🚀 Execution Guide

Run the development API server using **Uvicorn**:

```bash
# From the backend directory
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API endpoints will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).
You can inspect the interactive OpenAPI Swagger docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

## 📂 File Architecture & Team Assignment References

*   **`app/db.py`**:
    *   *Assignee*: **Teammate A (Boilerplate)** & **Teammate C (Vector search)**.
    *   *Contents*: SQLAlchemy models, engine configuration, and stubs for embedding generation and pgvector lookup.
*   **`app/graph.py`**:
    *   *Assignee*: **Teammate B (Prompt/LLM logic)**.
    *   *Contents*: LangGraph workflow definition, node methods (Writer, Critic, Pauses), and edge conditional routing rules.
*   **`app/main.py`**:
    *   *Contents*: REST API routes, thread checks, and Server-Sent Events generator.
*   **`app/state.py`**:
    *   *Contents*: LangGraph Shared State dictionary schema.
