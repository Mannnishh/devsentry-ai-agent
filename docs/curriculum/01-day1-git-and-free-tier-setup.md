# Day 1 — Git Workflow, Code Style, Project Scaffolding & Free LLM Client

**Focus:** Git/branching hygiene + automated formatting tooling (`ruff`) + Python virtual environment setup + free-tier Groq API client with streaming and secrets hygiene.

No agent code gets written until the developer workflow and LLM inference engine are solidly in place. Everything below sets up the production habits you will use across this curriculum — and gives you an immediate answer to interview questions about how you structure AI projects.

---

## Concept Primer

### 1. Why Feature Branches & Conventional Commits, Even Solo

On a solo project, it's tempting to commit directly to `main` — there is no team to review your code, so why bother with branches?
Two reasons hold up even when working solo:
- **Isolation:** A branch (`feat/...`, `refactor/...`) is where in-progress, experimental, or broken code lives. `main` stays in a clean, deployable state that you could screen-share in an interview at any moment.
- **Reviewable units of work:** Opening a Pull Request gives you a unified diff of the entire feature before merging.
- **Conventional Commits:** Standardized prefixes (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`) make your Git history machine-parseable and immediately communicate engineering maturity to hiring managers reviewing your GitHub profile.

### 2. What `.gitignore` Protects Against

Two critical problems, one file:
1. **Noise:** Build and runtime artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.db`) bloat git history and create merge conflicts.
2. **Secrets:** `.env` holds API keys (Groq, Gemini). Committing an API key to a public GitHub repo leads to compromised credentials within minutes (crawled by automated bots). `.env` is ignored, while `.env.example` provides the documented template with empty values.

### 3. What Makes an AI Agent Different from a Chatbot?

Before writing code, let's establish the fundamental technical difference:

| Dimension | Standard Chatbot | Autonomous AI Agent (DevSentry) |
| :--- | :--- | :--- |
| **Execution Pattern** | Linear: 1 User Query $\rightarrow$ 1 LLM Response $\rightarrow$ Done. | Cyclic: Goal $\rightarrow$ Reason $\rightarrow$ Call Tool $\rightarrow$ Observe Result $\rightarrow$ Loop until Goal Achieved. |
| **Environment Interaction** | Passive. Text in, text out. Cannot touch the outside world. | Active. Reads files, executes shell commands, inspects databases, creates Git commits. |
| **Error Handling** | If the answer is wrong or hallucinated, user must manually fix it. | **Self-healing:** If a tool call fails or tests fail, it reflects on the error trace, modifies code, and retries. |
| **State & Memory** | Stateless or naive chat message history array. | Stateful working memory scratchpad + persistent SQLite checkpoints. |

### 4. Why Groq Cloud for Agent Development? (The Speed Factor)

Agents do not make just one LLM call. An agent solving a single debugging task might go through:
1. Thought $\rightarrow$ Search files
2. Observation $\rightarrow$ Read candidate file
3. Thought $\rightarrow$ Run test suite
4. Observation $\rightarrow$ Parse error trace
5. Thought $\rightarrow$ Edit file
6. Observation $\rightarrow$ Re-run test suite $\rightarrow$ Success!

That is **6 sequential LLM calls**.
- With a standard cloud model at 20 tokens/sec, 6 iterations can take **60–90 seconds**, causing high latency and frustrating user experience.
- With **Groq Cloud's LPU (Language Processing Unit)**, models like `openai/gpt-oss-120b` and `qwen/qwen3.8-27b` run at **~300 to 500 tokens/sec**. The same 6 iterations finish in **under 6 seconds**!
- Best of all: Groq's developer tier is **100% free of cost** with generous daily limits, making it the ideal engine for building real-world autonomous agents.

---

## Official Reference Links

- [Conventional Commits 1.0.0 Specification](https://www.conventionalcommits.org/en/v1.0.0/)
- [Ruff: Fast Python Linter and Formatter](https://docs.astral.sh/ruff/)
- [Groq Cloud API Documentation](https://console.groq.com/docs/quickstart)
- [Pydantic Settings: Configuration Management](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## Hands-on Exercise

Today you will:
1. Create and activate a Python virtual environment (`.venv`).
2. Define dependencies in `pyproject.toml` and install them.
3. Setup `.env.example` and your real `.env` with your free Groq API key.
4. Implement strongly-typed settings in `src/config.py` using `pydantic-settings`.
5. Implement a provider-agnostic `LLMClient` in `src/llm/client.py` supporting both standard generation and real-time streaming.
6. Create an automated test suite in `tests/test_llm_client.py`.
7. Create an interactive CLI entrypoint in `src/cli.py` to test prompt completion and streaming.

---

## Step 1: Environment & Dependency Setup

In PowerShell inside the repository root (`C:\Users\Anjali\IdeaProjects\devsentry-ai-agent`):

### 1.1 Create and activate `.venv`
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

*(Note: If PowerShell execution policy restricts scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### 1.2 Create `pyproject.toml`
Create `pyproject.toml` in the project root:

```toml
[project]
name = "devsentry"
version = "0.1.0"
description = "Autonomous Codebase & DevOps Troubleshooting Agent"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "groq>=0.18.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "python-dotenv>=1.0.1",
    "rich>=13.9.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.9.0",
    "pytest>=8.3.0",
    "pytest-asyncio>=0.25.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

Install dependencies:
```powershell
pip install -e ".[dev]"
```

---

## Step 2: Secrets Configuration (`.env` & `src/config.py`)

### 2.1 Create `.env.example`
```env
# Groq Cloud API Key (Free tier from https://console.groq.com/keys)
GROQ_API_KEY=your_groq_api_key_here

# Default Model Selection
DEFAULT_MODEL=openai/gpt-oss-120b
FALLBACK_MODEL=qwen/qwen3.8-27b

# Temperature (lower = more deterministic for agents/tools)
LLM_TEMPERATURE=0.1
```

### 2.2 Create your local `.env`
Copy `.env.example` to `.env` and fill in your actual free Groq API key:
```powershell
cp .env.example .env
```

### 2.3 Implement `src/config.py`
We use `pydantic-settings` to ensure configuration is strictly validated at application boot time.

```python
"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = Field(
        ...,
        description="Groq API key from https://console.groq.com/keys",
    )
    default_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Primary model for complex reasoning and planning",
    )
    fallback_model: str = Field(
        default="qwen/qwen3.8-27b",
        description="Fast fallback model for simple tasks or rate-limit recovery",
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature; lower values ensure deterministic tool calls",
    )


# Global singleton instance
settings = Settings()
```

---

## Step 3: Implement the Free LLM Client (`src/llm/client.py`)

In agentic architectures, we never call third-party SDKs directly inside agent business logic. Instead, we define a clean interface so providers can be swapped or mocked in unit tests without touching the agent engine.

Create `src/llm/client.py`:

```python
"""Provider-agnostic LLM client implementation using Groq."""

from collections.abc import Generator
from typing import Any

from groq import Groq

from src.config import settings


class LLMClient:
    """Wrapper around Groq Cloud LLM inference with support for standard and streaming generation."""

    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        self.api_key = api_key or settings.groq_api_key
        self.default_model = default_model or settings.default_model
        self._client = Groq(api_key=self.api_key)

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a complete text response synchronously."""
        selected_model = model or self.default_model
        temp = temperature if temperature is not None else settings.llm_temperature

        response = self._client.chat.completions.create(
            model=selected_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temp,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Stream chunks of tokens in real time as they are generated by the model."""
        selected_model = model or self.default_model
        temp = temperature if temperature is not None else settings.llm_temperature

        stream_response = self._client.chat.completions.create(
            model=selected_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temp,
            stream=True,
            **kwargs,
        )
        for chunk in stream_response:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
```

---

## Step 4: Verification Suite (`tests/test_llm_client.py` & `src/cli.py`)

### 4.1 Unit Test (`tests/test_llm_client.py`)
```python
"""Tests for LLM Client configuration and connectivity."""

import pytest
from unittest.mock import MagicMock, patch

from src.config import Settings
from src.llm.client import LLMClient


def test_settings_validation():
    """Verify that Settings requires groq_api_key."""
    s = Settings(groq_api_key="gsk_test_key_12345")
    assert s.groq_api_key == "gsk_test_key_12345"
    assert s.default_model == "llama-3.3-70b-versatile"
    assert s.llm_temperature == 0.1


def test_client_generate_mocked():
    """Verify LLMClient forwards messages properly to Groq SDK."""
    mock_groq = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked Agent Response"
    mock_groq.chat.completions.create.return_value.choices = [mock_choice]

    with patch("src.llm.client.Groq", return_value=mock_groq):
        client = LLMClient(api_key="mock_key")
        messages = [{"role": "user", "content": "Hello"}]
        result = client.generate(messages)

        assert result == "Mocked Agent Response"
        mock_groq.chat.completions.create.assert_called_once()
```

### 4.2 Interactive CLI Entrypoint (`src/cli.py`)
```python
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
        else "Explain what an autonomous AI agent is in 2 sentences."
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
```

---

## Checkpoint

Prove that Day 1 is complete by running these three commands in your terminal:

1. **Check code formatting and style:**
   ```powershell
   ruff check .
   ruff format --check .
   ```
2. **Run the automated test suite:**
   ```powershell
   pytest -v tests/
   ```
3. **Execute the live streaming CLI test (requires valid `GROQ_API_KEY` in `.env`):**
   ```powershell
   python -m src.cli "Hello DevSentry! Introduce yourself."
   ```

When all three pass, your free-tier inference engine is verified and ready for Day 2!

---

## Senior Interview Angle

### Q1: "Why do you wrap the third-party LLM SDK in your own `LLMClient` instead of using Groq or OpenAI SDKs directly across your codebase?"
**Senior Answer:**
> *"Directly importing third-party vendor SDKs into domain or agent logic couples business logic to external API signatures. By wrapping inference behind an interface or client abstraction (following the Adapter and Dependency Inversion principles), we achieve three production benefits:
> 1. **Zero-cost testability:** We can mock LLM calls cleanly in automated CI/CD without making real network requests or exposing secrets.
> 2. **Provider portability:** If Groq experiences rate limits or an outage, we can fall back to Google Gemini, OpenAI, or a local Ollama instance with zero changes to the agent's ReAct state machine.
> 3. **Centralized cross-cutting concerns:** Telemetry, prompt token counting, retry backoff with jitter, and circuit breaking are implemented once in the client wrapper rather than scattered across every agent node."*

### Q2: "Why is low temperature (e.g. 0.0 to 0.2) recommended for agentic systems, unlike conversational chatbots?"
**Senior Answer:**
> *"Conversational bots benefit from higher temperature (0.7+) for stylistic variety and creativity. In contrast, autonomous agents use LLMs as reasoning engines to produce structured tool calls and JSON payloads. At high temperatures, models are more likely to generate syntax errors, invent non-existent tool names, or hallucinate parameters. Low temperature keeps the probability distribution focused on top-ranked tokens, maximizing schema compliance and deterministic tool execution."*

---

## Ready to Merge?

Once your checkpoint passes:
```powershell
git add pyproject.toml .env.example src/ tests/ docs/
git commit -m "feat(llm): implement Groq client wrapper and project scaffolding"
git push -u origin feat/day1-git-and-llm-client
```
Then open a Pull Request against `main` and merge it!
