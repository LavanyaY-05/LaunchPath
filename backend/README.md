# LaunchPath — AI Advisor for Early-Stage Entrepreneurship

LaunchPath is an AI advisor monorepo application designed for early-stage entrepreneurs, freelancers, startup founders, and small business owners. It provides strictly grounded, actionable insights based on curated domain knowledge without requiring user login or financial transactions.

---

## Project Structure

```
launchpath/
├── backend/
│   ├── data/                 # Curated seed domain knowledge documents
│   ├── db/
│   │   └── schema.sql        # Supabase Postgres pgvector & RRF hybrid search function
│   ├── .env.example          # Environment variables template
│   ├── requirements.txt      # Python dependencies (FastAPI, LangGraph, Supabase, Groq, etc.)
│   ├── ingest.py             # Script to chunk, embed, and ingest seed docs into Supabase
│   ├── retrieval.py          # Hybrid search engine (pgvector + Postgres FTS via RRF with local fallback)
│   ├── prompts.py            # Strictly grounded prompt templates & tone enforcement
│   ├── llm.py                # Swappable OpenAI / Groq LLM model wrapper with fallback
│   ├── graph.py              # 6-Node LangGraph StateGraph workflow
│   ├── main.py               # FastAPI REST endpoints (/chat, /explore/{domain}, /upload)
│   └── test_app.py           # Pytest test suite for intent, retrieval, endpoints, uploads
└── frontend/                 # Next.js modern user interface (Chat & Explore tabs)
```

---

## 6-Node LangGraph Agent Graph Diagram

LaunchPath uses a multi-node agent state graph where each node operates as a specialized agent task:

```
                  +--------------------------+
                  |   Incoming Chat State    |
                  +------------+-------------+
                               |
                               v
                  +--------------------------+
                  | 1. classify_intent       |  (Specialized Intent Classifier)
                  +------------+-------------+
                               |
                               v
                  +--------------------------+
                  | 2. retrieve              |  (Hybrid Retrieval Agent)
                  +------------+-------------+
                               |
                               v
                  +--------------------------+
                  | 3. relevance_check       |  (Strict Scope Evaluator)
                  +------+------------+------+
                         |            |
         Strong Match    |            | Weak / No Match
         (score >= 0.5)  v            v
           +---------------+  +--------------------------+
           | 4. generate   |  | out_of_scope_response    |
           +-------+-------+  +------------+-------------+
                   |                       |
                   v                       |
           +---------------+               |
           | 5. self_reflect|               |  (ReAct Grounding Auditor)
           +-------+-------+               |
                   |                       |
                   v                       |
           +---------------+               |
           | 6. finalize   |               |  (Citation & Follow-Up Synthesizer)
           +-------+-------+               |
                   |                       |
                   v                       v
           +---------------------------------+
           |        Final Output Object      |
           +---------------------------------+
```

### Specialized Node Roles:
1. **`classify_intent`**: Specialized Classifier Agent. Categorizes inputs into `idea_comparison`, `form_helper`, `general_qa`, or `document_review` (triggered when text files or pitch decks are uploaded for review).
2. **`retrieve`**: Search Agent. Executes hybrid search combining vector cosine similarity and full-text PostgreSQL search using Reciprocal Rank Fusion (RRF), with optional domain filtering.
3. **`relevance_check`**: Strict Gatekeeper Agent. Evaluates search relevance. If below `MIN_RELEVANCE_THRESHOLD = 0.5`, routes directly to `out_of_scope_response` without invoking the LLM, preventing ungrounded answers.
4. **`generate`**: Generation Agent. Fills the domain prompt template and invokes the LLM (Groq or OpenAI) under strict context constraints.
5. **`self_reflect`**: ReAct Quality Auditor Agent. Scans the generated output against retrieved context for any ungrounded statements. Triggers a stricter re-generation if claims lack context support.
6. **`finalize`**: Formatter Agent. Synthesizes natural text citations, separates `sources` for UI badge display, and generates 2-3 actionable `follow_ups` chips.

---

## Grounding & Tone Rules

1. **Strict Grounding**: Only answer using retrieved context. Unrelated queries return: `"I don't have relevant information on that right now."`
2. **Optimistic Opening**: Always open with positive validation tied to market demand or solvable problems.
3. **Market Framing**: Frame competitors as proof of an active space rather than a warning.
4. **Actionable Bullets**: Deliver 3-5 concrete, grounded suggestions as a bullet list.
5. **Natural Citations**: Weave source titles naturally into prose (no bracketed footnotes like `[1]`).

---

## How to Run Backend

1. **Install Dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and adjust API keys:
   - `GROQ_API_KEY`: Groq API key (`gsk_...`)
   - `LANGCHAIN_API_KEY`: LangSmith API key (`lsv2_pt_...`)
   - `LLM_PROVIDER`: `groq` or `openai`

3. **Run Seed Data Ingestion**:
   ```bash
   python ingest.py
   ```

4. **Run Tests**:
   ```bash
   pytest test_app.py -v
   ```

5. **Start FastAPI Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will run at `http://localhost:8000`.
