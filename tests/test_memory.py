"""Unit tests for working memory compaction and SQLite session persistence."""

from pathlib import Path

from src.agent.models import AgentAction, AgentStep
from src.memory.scratchpad import ScratchpadManager
from src.memory.storage import SQLiteSessionStore


def test_scratchpad_empty() -> None:
    """Verify empty step list produces an empty scratchpad."""
    manager = ScratchpadManager()
    assert manager.build([]) == ""


def test_scratchpad_sliding_window_compaction() -> None:
    """Verify older steps are truncated while recent steps retain full content."""
    # Keep only 2 most recent steps in full resolution, truncate earlier ones
    manager = ScratchpadManager(max_observation_chars=20, max_recent_steps=2)

    steps: list[AgentStep] = []
    for i in range(5):
        step = AgentStep(
            action=AgentAction(
                thought=f"Thinking about step {i}",
                tool="run_command",
                tool_input=f"cmd_{i}",
            ),
            observation="A" * 50,  # 50 chars (longer than max_observation_chars)
        )
        steps.append(step)

    scratchpad = manager.build(steps)

    # Older steps (0, 1, 2) must be truncated
    assert scratchpad.count("[Truncated:") >= 3

    # The scratchpad should still include thoughts and tools from all steps
    for i in range(5):
        assert f"Thinking about step {i}" in scratchpad
        assert f"cmd_{i}" in scratchpad


def test_scratchpad_single_oversized_observation() -> None:
    """Verify even a recent step is truncated if its observation exceeds max_obs_chars."""
    manager = ScratchpadManager(max_observation_chars=30, max_recent_steps=5)

    step = AgentStep(
        action=AgentAction(thought="Reviewing logs", tool="read_file", tool_input="large.log"),
        observation="X" * 100,
    )
    formatted = manager.format_step(step, is_recent=True)

    assert "X" * 30 in formatted
    assert "[Truncated: 70 chars omitted]" in formatted


def test_sqlite_session_store_persistence(tmp_path: Path) -> None:
    """Verify sessions and step checkpoints are saved and reloaded from disk."""
    db_file = tmp_path / "test_agent.db"

    # 1. First connection: write session and steps
    store_writer = SQLiteSessionStore(db_path=db_file)
    session_id = "test-session-42"
    store_writer.create_session(session_id=session_id, task="Investigate test failure")

    step1 = AgentStep(
        action=AgentAction(thought="Check files", tool="list_dir", tool_input="src/"),
        observation="agent/ llm/ tools/",
    )
    step2 = AgentStep(
        action=AgentAction(thought="Run tests", tool="run_tests", tool_input=""),
        observation="4 passed in 0.2s",
    )

    store_writer.save_step(session_id, step_index=1, step=step1)
    store_writer.save_step(session_id, step_index=2, step=step2)

    # 2. Simulate process restart: read from a new instance pointing to same DB
    store_reader = SQLiteSessionStore(db_path=db_file)
    recovered_steps = store_reader.load_steps(session_id)

    assert len(recovered_steps) == 2
    assert recovered_steps[0].action.tool == "list_dir"
    assert recovered_steps[0].observation == "agent/ llm/ tools/"
    assert recovered_steps[1].action.thought == "Run tests"
    assert recovered_steps[1].observation == "4 passed in 0.2s"


def test_sqlite_session_store_empty_session(tmp_path: Path) -> None:
    """Verify loading a non-existent session returns an empty list."""
    db_file = tmp_path / "empty.db"
    store = SQLiteSessionStore(db_path=db_file)
    assert store.load_steps("non-existent-session-id") == []
