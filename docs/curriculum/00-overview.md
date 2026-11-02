# DevSentry: 7-Day Autonomous AI Agent Curriculum

## Goal

Over the next 7 days, you will build **DevSentry** from scratch: a production-grade, 100% free-of-cost **Autonomous Codebase & DevOps Troubleshooting Agent**.

Given a bug report, failing test suite, or software engineering task, DevSentry autonomously:
1. **Understands & Plans:** Breaks down the problem using the **ReAct (Reason + Act)** loop.
2. **Inspects & Searches:** Uses secure tools to search the filesystem, inspect code AST, and read files.
3. **Executes & Tests:** Runs unit tests and shell commands in a controlled execution sandbox.
4. **Self-Heals:** Catches tool execution errors and failing test stack traces, reflects on the failure, repairs the code, and re-verifies until tests pass.
5. **Maintains Human Safety (HITL):** Pauses and prompts the user before executing high-risk actions (modifying critical files, committing code).
6. **Remembers State:** Persists execution history and conversation sessions in SQLite with time-travel / rollback capability.
7. **Streams Real-Time Events:** Emits step-by-step thoughts and actions via Server-Sent Events (SSE) through a FastAPI service.

Along the way, every day reinforces senior-level engineering practices:
- **Feature branch Git hygiene** (`feat/...`), Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`), and PR reviews.
- **Automated formatting & linting** with `ruff` and deterministic testing with `pytest`.
- **Architectural patterns** (Finite State Machine, Strategy, Command, Observer, Decorator).
- **Senior-level Interview Angles** exploring trade-offs, gotcha questions, and failure modes.

---

## Prerequisites

- **Python 3.12+:** Installed and available on your PATH.
- **Git & GitHub:** Installed and authenticated via `gh` CLI.
- **Free LLM API Key:**
  - **Groq Cloud API Key:** 100% free with blazing inference speed (~500 tokens/sec). Get an API key from the [GroqCloud Console](https://console.groq.com/keys) (sign up takes 30 seconds; no credit card required).
  - *(Optional Backup)* **Google Gemini API Key:** Generous free tier from [Google AI Studio](https://aistudio.google.com/).
- **IDE:** VS Code or IntelliJ IDEA / PyCharm.

---

## How to Use This Curriculum

- **One file per day:** Located in `docs/curriculum/`. Work through them in sequence; each day builds directly on the working code of the previous day.
- **Structure of each day:**
  1. **Concept Primer:** The "Why" and "How" explained in plain, simple English before you write any code.
  2. **Official Reference Links:** Real documentation and research papers (e.g., ReAct paper, Pydantic, Groq API).
  3. **Hands-on Exercise:** Guided tasks with scaffolded code, TODOs, and architectural hints for you to write, test, and understand.
  4. **Checkpoint:** A concrete, runnable command or test suite verifying that your day's work is functional.
  5. **Interview Angle:** High-yield questions and discussion topics for senior engineering interviews.
- **Git Feature Branch Workflow:**
  - Every day's work is developed on a dedicated branch: `feat/dayX-...`
  - Commits follow [Conventional Commits](https://www.conventionalcommits.org/): e.g. `feat(llm): implement provider-agnostic Groq client`
  - At the end of the day, merge into `main` after all checkpoints pass.

---

## 7-Day Schedule

| Day | Focus | Checkpoint |
| :--- | :--- | :--- |
| **Day 1** | **Git Hygiene, Architecture Blueprint & Free-Tier LLM Client** | CLI script sends a prompt and streams a response from Groq Llama 3.3 70B with zero cost. |
| **Day 2** | **The ReAct Reasoning Engine from Scratch** | Core ReAct FSM loop parses `Thought:`, `Action:`, `Observation:`, and `Final Answer:` without third-party frameworks. |
| **Day 3** | **Function Calling & Secure Tool Sandbox** | Typed `ToolRegistry` with JSON Schema generation; File Read/Write, Code Search, and Sandboxed Test Runner. |
| **Day 4** | **Working Memory, Scratchpad Compaction & SQLite State** | Token-budget sliding window, message summarization, and SQLite durable session checkpointing. |
| **Day 5** | **Production Resilience, Rate Limiting & Self-Healing** | Exponential backoff with full jitter for free-tier APIs; Reflexion self-healing loop on tool failures. |
| **Day 6** | **Human-in-the-Loop (HITL) & Safety Guardrails** | Interactive pause/resume interrupts for dangerous actions; loop detection and token cost ceilings. |
| **Day 7** | **Streaming API, Dockerization & Mock Interview Defense** | FastAPI SSE streaming endpoint (`/agent/stream`), multi-stage Dockerfile, and complete interview defense. |

---

## Day Files

1. [Day 1 — Git Hygiene, Project Scaffolding & Free LLM Client](01-day1-git-and-free-tier-setup.md)
2. Day 2 — The ReAct Reasoning Engine from Scratch
3. Day 3 — Function Calling & Secure Tool Sandbox
4. Day 4 — Working Memory & SQLite State Persistence
5. Day 5 — Production Resilience & Self-Healing Loop
6. Day 6 — Human-in-the-Loop & Safety Guardrails
7. Day 7 — Streaming API, Docker & Interview Defense
