# DevSentry: Autonomous Codebase & DevOps Troubleshooting Agent

DevSentry is a production-grade, 100% free-of-cost autonomous AI software engineer and codebase diagnostic agent built from scratch in Python 3.12.

Given a bug report, failing test suite, or software task, DevSentry autonomously:
- Breaks down complex requirements using a custom **ReAct (Reason + Act)** loop.
- Executes codebase inspection, AST search, and safe file patching in a sandboxed execution boundary.
- Runs verification tests, self-reflects on errors, and autonomously fixes bugs.
- Requires **Human-in-the-Loop (HITL)** approval before executing high-risk file mutations or Git actions.
- Persists session memory and state snapshots in SQLite for pause-and-resume workflows.
- Emits real-time reasoning and tool events via Server-Sent Events (SSE).

Built over a structured 7-day engineering curriculum with zero third-party agent framework bloat (no hidden abstractions; core FSM implemented from first principles).

---

## Architecture Overview

```mermaid
flowchart TD
    User["Developer / Issue Webhook"] -->|Task prompt & file paths| Agent["DevSentry Agent (ReAct Loop)"]
    Agent -->|1. Thought: 'Locate failing test'| Tools
    subgraph Tools ["Secure Tool Registry"]
        T1["CodeSearch / AST Grep"]
        T2["File Reader & Chunk Inspector"]
        T3["File Editor (Patch/Diff)"]
        T4["Sandboxed Shell / Test Runner"]
        T5["Git Command Runner"]
    end
    Tools -->|2. Test failure output| Agent
    Agent -->|3. Thought: 'Fix logic bug'| T3
    T3 -->|Patch applied| Agent
    Agent -->|4. Thought: 'Verify with test runner'| T4
    T4 -->|Tests Pass (Exit 0)| Agent
    Agent -->|5. Require Approval if safe=false| HITL["Human-In-The-Loop Approval"]
    HITL -->|Approved| T5
    T5 -->|Commit to feat/fix branch| Final["Git PR Ready + Diagnostic Report"]
```

---

## Free-of-Cost Tech Stack

- **LLM Inference:** [Groq Cloud](https://console.groq.com/) (Llama 3.3 70B Versatile, Llama 3.1 8B Instant) — Free tier, ~500 tokens/sec.
- **Runtime:** Python 3.12, Pydantic V2, FastAPI, Uvicorn.
- **Persistence:** SQLite with JSON state checkpoints.
- **Testing & Quality:** Pytest, Ruff (linting and formatting).
- **Deployment:** Docker & Docker Compose.

---

## Curriculum & Progress

See [`docs/curriculum/00-overview.md`](docs/curriculum/00-overview.md) for the complete 7-day curriculum roadmap and daily guides.
