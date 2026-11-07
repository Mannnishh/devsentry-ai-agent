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
        """Initialize database schema if tables do not exist."""
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
                    if INTEGER PRIMARY KEY AUTOINCREMENT,
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
        """Create a new session record or update existing."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, task, status) VALUES (?, ?, ?)",
                (session_id, task, status),
            )

    def save_step(self, session_id: str, step_index: int, step: AgentStep) -> None:
        """Save an individual step execution checkpoint."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                    INSERT INTO checkpoints (session_id, step_index, thought,
                    tool, tool_input, observation
                    )
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
        """Load and reconstruct all steps for a session ordered by step_index."""
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
                thought=thought or "", tool=tool or "", tool_input=tool_input or ""
            )
            steps.append(AgentStep(action=action, observation=obs or ""))
        return steps
