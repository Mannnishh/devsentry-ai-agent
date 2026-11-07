"""DevSentry CLI entrypoint equipped with real filesystem, test runner, and persistent memory."""

import sys
import uuid

from rich.console import Console
from rich.panel import Panel

from src.agent.engine import ReActEngine
from src.llm.client import LLMClient
from src.memory.scratchpad import ScratchpadManager
from src.memory.storage import SQLiteSessionStore
from src.tools.base import Tool, ToolRegistry
from src.tools.filesystem import SafeFileSystem
from src.tools.test_runner import TestRunnerTool

console = Console()


def build_tool_registry() -> ToolRegistry:
    """Register real engineering tools for DevSentry."""
    fs = SafeFileSystem(".")
    test_runner = TestRunnerTool(".")

    registry = ToolRegistry()
    registry.register(
        Tool(
            name="read_file",
            description="Reads the text content of a file within workspace. Input: file path.",
            func=fs.read_file,
        )
    )
    registry.register(
        Tool(
            name="write_file",
            description="Writes text content to a file. Input format MUST be 'path:::content'.",
            func=fs.write_file,
        )
    )
    registry.register(
        Tool(
            name="list_dir",
            description="Lists files in a directory. Input: directory path (e.g. '.' or 'src').",
            func=fs.list_dir,
        )
    )
    registry.register(
        Tool(
            name="run_tests",
            description=(
                "Runs pytest unit tests in the workspace. Input: test file path or '' for all."
            ),
            func=test_runner.run_tests,
        )
    )
    return registry


def main() -> None:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "List the files inside the 'src' directory and tell me what components exist."
    )
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    console.print(
        Panel(
            f"[bold cyan]Task:[/bold cyan] {prompt}\n"
            f"[bold magenta]Session ID:[/bold magenta] {session_id}",
            title="DevSentry Day 4 Checkpoint",
        )
    )

    registry = build_tool_registry()
    client = LLMClient()
    session_store = SQLiteSessionStore("data/devsentry.db")
    scratchpad_manager = ScratchpadManager(max_observation_chars=1200, max_recent_steps=4)

    engine = ReActEngine(
        llm_client=client,
        tools=registry.to_dict(),
        max_iterations=8,
        scratchpad_manager=scratchpad_manager,
        session_store=session_store,
    )

    console.print("\n[bold yellow]Agent Running (Inspecting Codebase via Tools)...[/bold yellow]")
    final_answer = engine.run(prompt, session_id=session_id)

    console.print(
        Panel(
            f"[bold green]Final Answer:[/bold green]\n{final_answer}",
            title="Result",
        )
    )
    console.print(
        f"[dim green]✓ Checkpoints persisted to data/devsentry.db "
        f"(Session: {session_id})[/dim green]"
    )


if __name__ == "__main__":
    main()
