"""DevSentry CLI entrypoint for testing streaming LLM inference."""

import sys

from rich.console import Console
from rich.panel import Panel

from src.llm.client import LLMClient

console = Console()


def main() -> None:
    prompt = (
        sys.argv[1]
        if len(sys.argv) > 1
        else (
            "Explain what an autonomous AI agent is and "
            "how it differs from a chatbot in 2 sentences."
        )
    )

    console.print(
        Panel(f"[bold cyan]Prompt:[/bold cyan] {prompt}", title="DevSentry Day 1 Checkpoint")
    )
    console.print("\n[bold green]Streaming Response:[/bold green]")

    client = LLMClient()
    for token in client.stream([{"role": "user", "content": prompt}]):
        console.print(token, end="")
    console.print("\n")


if __name__ == "__main__":
    main()
