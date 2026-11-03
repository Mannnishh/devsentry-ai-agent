# Day 4 — Working Memory, Scratchpad Compaction & SQLite Persistence

**Focus:** Building dynamic short-term working memory with token compaction and persistent session checkpointing in SQLite.

Production agents cannot rely solely on in-memory Python variables. If a server restarts, the network drops, or a task requires 20 tool iterations, naive agents crash or blow through context limits. Today, you will build state persistence and intelligent context management.

---

## Concept Primer

### 1. Python Primer for Beginners: What You Need Today

#### A. SQLite in Python (`sqlite3`)
Python has built-in support for SQLite — zero installation, zero Docker containers required:
```python
import sqlite3

# Connect to a local database file (created automatically if missing)
conn = sqlite3.connect("devsentry.db")
cursor = conn.cursor()

# Execute SQL with parameterized queries (never format strings!)
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        task TEXT NOT NULL,
        status TEXT NOT NULL
    )
"""
)
conn.commit()
conn.close()
```

#### B. Context Managers (`with`)
In Python, using `with` guarantees that resources (files, database connections) are cleanly closed and committed even if an exception occurs:
```python
with sqlite3.connect("devsentry.db") as conn:
    conn.execute(
        "INSERT INTO sessions (session_id, task, status) VALUES (?, ?, ?)",
        ("sess_123", "fix bug", "IN_PROGRESS"),
    )
# Automatically committed and closed here!
```

---

### 2. The Context Window Problem & "Lost in the Middle"

Every LLM has a finite context window (e.g. 8k, 32k, 128k tokens). More importantly:
- **Cost & Latency:** The more tokens in the prompt, the slower and more expensive each subsequent reasoning step becomes.
- **The "Lost in the Middle" Effect:** Research (Liu et al., 2023) demonstrates that LLM retrieval accuracy degrades sharply when relevant details are buried in the middle of long prompts.

#### The Solution: Working Memory Scratchpad Compaction
Instead of blindly appending every raw tool output (which could include 500 lines of test logs), our `ScratchpadManager`:
1. Keeps the original **Task Goal** pinned at the top.
2. Truncates or summarizes earlier tool outputs once they exceed a token budget.
3. Keeps the most recent $K$ steps in high-resolution detail.

---

## Official Reference Links

- [Python `sqlite3` Standard Library](https://docs.python.org/3/library/sqlite3.html)
- [Lost in the Middle: How Language Models Use Long Contexts (Liu et al., 2023)](https://arxiv.org/abs/2307.03172)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

---

## Hands-on Exercise

Today you will build:
1. `src/memory/scratchpad.py` — Dynamic scratchpad formatter with sliding window compaction.
2. `src/memory/storage.py` — SQLite session manager storing checkpoints and execution history.

---

### Step 1: Implement Scratchpad Compaction (`src/memory/scratchpad.py`)

Create `src/memory/scratchpad.py`:

```python
"""Working memory scratchpad with context compaction."""

from src.agent.models import AgentStep


class ScratchpadManager:
    """Manages agent working memory, enforcing length bounds and truncation."""

    def __init__(self, max_observation_chars: int = 1500, max_recent_steps: int = 5) -> None:
        self.max_obs_chars = max_observation_chars
        self.max_recent_steps = max_recent_steps

    def format_step(self, step: AgentStep, is_recent: bool = True) -> str:
        """Format a single step, truncating older or verbose observations."""
        obs = step.observation
        if not is_recent or len(obs) > self.max_obs_chars:
            obs = (
                obs[: self.max_obs_chars]
                + f"\n... [Truncated: {len(step.observation) - self.max_obs_chars} chars omitted] ..."
            )

        return (
            f"Thought: {step.action.thought}\n"
            f"Action: {step.action.tool}\n"
            f"Action Input: {step.action.tool_input}\n"
            f"Observation: {obs}\n"
        )

    def build(self, steps: list[AgentStep]) -> str:
        """Build the complete scratchpad string with compaction."""
        if not steps:
            return ""

        formatted_steps: list[str] = []
        split_idx = max(0, len(steps) - self.max_recent_steps)

        for i, step in enumerate(steps):
            is_recent = i >= split_idx
            formatted_steps.append(self.format_step(step, is_recent=is_recent))

        return "".join(formatted_steps)
```

---

### Step 2: Implement SQLite State Persistence (`src/memory/storage.py`)

Create `src/memory/storage.py` with this guided TODO:

```python
"""SQLite persistence for agent sessions and execution checkpoints."""

import json
import sqlite3
from pathlib import Path
from src.agent.models import AgentAction, AgentStep


class SQLiteSessionStore:
    """Stores agent conversation sessions and step-by-step checkpoints in SQLite."""

    def __init__(self, db_path: str | Path = "data/devsentry.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist: sessions and checkpoints."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    thought TEXT,
                    tool TEXT,
                    tool_input TEXT,
                    observation TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

    def save_step(self, session_id: str, step_index: int, step: AgentStep) -> None:
        """# TODO: Insert a checkpoint record into the checkpoints table."""
        raise NotImplementedError("Implement save_step")

    def load_steps(self, session_id: str) -> list[AgentStep]:
        """# TODO: Query checkpoints for session_id ordered by step_index and reconstruct list[AgentStep]."""
        raise NotImplementedError("Implement load_steps")
```

<details>
<summary>👉 Click to reveal Answer Key for `src/memory/storage.py`</summary>

```python
"""SQLite persistence for agent sessions and execution checkpoints."""

import sqlite3
from pathlib import Path
from src.agent.models import AgentAction, AgentStep


class SQLiteSessionStore:
    """Stores agent conversation sessions and step-by-step checkpoints in SQLite."""

    def __init__(self, db_path: str | Path = "data/devsentry.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    thought TEXT,
                    tool TEXT,
                    tool_input TEXT,
                    observation TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                )
            """)

    def create_session(self, session_id: str, task: str, status: str = "RUNNING") -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, task, status) VALUES (?, ?, ?)",
                (session_id, task, status),
            )

    def save_step(self, session_id: str, step_index: int, step: AgentStep) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (session_id, step_index, thought, tool, tool_input, observation)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    step_index,
                    step.action.thought,
                    step.action.tool,
                    step.action.tool_input,
                    step.observation,
                ),
            )

    def load_steps(self, session_id: str) -> list[AgentStep]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT thought, tool, tool_input, observation
                FROM checkpoints
                WHERE session_id = ?
                ORDER BY step_index ASC
            """,
                (session_id,),
            )
            rows = cursor.fetchall()

        steps: list[AgentStep] = []
        for thought, tool, tool_input, obs in rows:
            action = AgentAction(
                thought=thought or "",
                tool=tool or "",
                tool_input=tool_input or "",
            )
            steps.append(AgentStep(action=action, observation=obs or ""))
        return steps
```
</details>

---

## Checkpoint

Prove Day 4 is complete:
1. Write a test in `tests/test_memory.py` that:
   - Populates 10 steps into `ScratchpadManager` and verifies older steps are cleanly truncated.
   - Saves 3 steps into `SQLiteSessionStore`, creates a new store instance, and asserts all 3 steps are recovered accurately.
2. Run:
   ```powershell
   pytest -v tests/test_memory.py
   ruff check .
   ```

---

## Senior Interview Angle

### Q: "Why use checkpoint-based persistence in agent systems instead of simply saving the final output?"
**Senior Answer:**
> *"Agent workflows are multi-step, I/O-heavy, and non-deterministic. A single task can involve multiple minutes of tool executions and LLM calls. If we only persist the final answer, any transient failure (network hiccup, API rate limit, power restart) results in total loss of progress, wasted token spend, and poor UX.
> 
> Checkpoint-based persistence provides three critical distributed systems capabilities:
> 1. **Resumability:** An agent can pick up directly from step $N$ without repeating steps $1$ to $N-1$.
> 2. **Auditability & Compliance:** Every intermediate thought and executed command is logged with an immutable audit trail.
> 3. **Time-Travel Debugging:** If an agent takes a wrong turn at step 4, we can roll back state to step 3, alter the prompt or tool parameters, and re-branch the trajectory."*

---

## Ready to Merge?

```powershell
git checkout -b feat/day4-memory-and-persistence
git add src/ tests/ docs/
git commit -m "feat(memory): implement scratchpad compaction and SQLite session persistence"
git push -u origin feat/day4-memory-and-persistence
```
