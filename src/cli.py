"""DevSentry CLI entrypoint for testing the ReAct reasoning loop."""

import sys

from rich.console import Console
from rich.panel import Panel

from src.agent.engine import ReActEngine
from src.llm.client import LLMClient

console = Console()


def reverse_text(text: str) -> str:
    """Reverses the given text string."""
    return text.strip()[::-1]


def calculate_math(expression: str) -> str:
    """Evaluates a basic arithmetic expression."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: Unsupported characters in math expression."
        return str(eval(expression, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Math error: {e}"


def main() -> None:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "What is the result of reversing the text 'DevSentry Agent'?"
    )

    console.print(
        Panel(
            f"[bold cyan]Task:[/bold cyan] {prompt}",
            title="DevSentry Day 2 Checkpoint",
        )
    )

    tools = {
        "reverse_text": reverse_text,
        "calculate_math": calculate_math,
    }

    client = LLMClient()
    engine = ReActEngine(llm_client=client, tools=tools, max_iterations=5)

    console.print("\n[bold yellow]Agent Running (ReAct Loop)...[/bold yellow]")
    final_answer = engine.run(prompt)

    console.print(
        Panel(
            f"[bold green]Final Answer:[/bold green]\n{final_answer}",
            title="Result",
        )
    )


if __name__ == "__main__":
    main()
