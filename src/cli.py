"""DevSentry CLI entrypoint equipped with real filesystem and test runner tools."""

import sys

from rich.console import Console
from rich.panel import Panel

from src.agent.engine import ReActEngine
from src.llm.client import LLMClient
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

    console.print(
        Panel(
            f"[bold cyan]Task:[/bold cyan] {prompt}",
            title="DevSentry Day 3 Checkpoint",
        )
    )

    registry = build_tool_registry()
    client = LLMClient()
    engine = ReActEngine(llm_client=client, tools=registry.to_dict(), max_iterations=8)

    console.print("\n[bold yellow]Agent Running (Inspecting Codebase via Tools)...[/bold yellow]")
    final_answer = engine.run(prompt)

    console.print(
        Panel(
            f"[bold green]Final Answer:[/bold green]\n{final_answer}",
            title="Result",
        )
    )


if __name__ == "__main__":
    main()
