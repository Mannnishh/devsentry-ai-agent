# Day 5 — Production Resilience, Free-Tier Rate Limiting & Self-Healing

**Focus:** Implementing token-bucket rate limiting with exponential backoff + jitter, and the **Reflexion** self-healing loop for automatic error recovery.

Free-tier LLM APIs (Groq, Gemini) have strict Requests-Per-Minute (RPM) and Tokens-Per-Minute (TPM) caps. If your agent hammers the API across a multi-step loop, you will encounter `HTTP 429 Too Many Requests`. Simultaneously, agents frequently write buggy code or execute failing tests on their first attempt. Today, you will make DevSentry bulletproof against rate limits and self-correcting on bugs.

---

## Concept Primer

### 1. Python Primer for Beginners: What You Need Today

#### A. Decorator Pattern for Retries
A retry decorator intercepts a function call. If a transient error occurs, it catches the exception, sleeps for an calculated duration, and retries:
```python
import functools
import time


def retry_on_exception(max_retries: int = 3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(2**attempt)

        return wrapper

    return decorator
```

#### B. The Mathematics of Exponential Backoff with Full Jitter
If 10 concurrent requests fail and all retry at exactly `2.0s`, `4.0s`, `8.0s`, they collide simultaneously at the upstream server (the **Thundering Herd Problem**).
Amazon AWS architecture research showed that **Full Jitter** eliminates spikes:
$$\text{Sleep Time} = \text{random}(0, \; \min(\text{cap}, \; \text{base} \times 2^{\text{attempt}}))$$

---

### 2. The Reflexion Pattern (Shinn et al., 2023)

When a human developer's unit test fails, they don't give up and crash. They read the stack trace, formulate a hypothesis, edit the code, and re-run.

The **Reflexion** loop automates this cognitive process:
1. **Action:** Agent modifies a function.
2. **Observation:** Test runner returns `FAILED: AssertionError: expected 42 but got 0`.
3. **Reflection Step:** Instead of proceeding blindly, we inject a reflection prompt:
   *"The previous action failed with: [Error Output]. Analyze why this failed and plan a specific corrective action."*
4. **Correction:** The model identifies its off-by-one bug or syntax mistake and generates a corrected patch.

---

## Official Reference Links

- [AWS Architecture: Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Reflexion: Language Agents with Verbal Reinforcement Learning (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366)
- [Groq Cloud Rate Limits Guide](https://console.groq.com/docs/rate-limits)

---

## Hands-on Exercise

Today you will build:
1. `src/resilience/backoff.py` — Production retry decorator with exponential backoff and full jitter.
2. `src/agent/reflection.py` — The Reflexion prompt and self-healing interceptor.

---

### Step 1: Implement Exponential Backoff with Jitter (`src/resilience/backoff.py`)

Create `src/resilience/backoff.py`:

```python
"""Resilience utilities: exponential backoff with full jitter."""

import functools
import random
import time
from collections.abc import Callable
from typing import Any


def retry_with_jitter(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator that retries a function using exponential backoff with full jitter."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    if attempt == max_retries - 1:
                        raise e

                    # Exponential backoff: base * 2^attempt
                    calculated_delay = min(max_delay, base_delay * (2**attempt))
                    # Full jitter: random between 0 and calculated_delay
                    sleep_time = random.uniform(0, calculated_delay)
                    time.sleep(sleep_time)

        return wrapper

    return decorator
```

---

### Step 2: Implement Self-Healing Reflexion (`src/agent/reflection.py`)

Create `src/agent/reflection.py` with this guided TODO:

```python
"""Self-healing and reflection loop for failing tool operations."""

from src.agent.models import AgentAction, AgentStep
from src.llm.client import LLMClient

REFLEXION_PROMPT = """You are analyzing a failed execution step.
Previous Action: {tool_name} with input {tool_input}
Error Trace / Failure Output:
{error_trace}

Analyze what went wrong in 2 sentences, and output the EXACT corrected Action and Action Input to fix it.
Format:
Analysis: your diagnosis
Corrected Action: tool_name
Corrected Action Input: corrected input
"""


class SelfHealingCoordinator:
    """Detects failing tool observations and prompts the LLM for self-correction."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    def is_failure(self, observation: str) -> bool:
        """Check if observation contains error indicators."""
        failure_signals = [
            "error",
            "failed",
            "exception",
            "traceback",
            "permission denied",
        ]
        obs_lower = observation.lower()
        return any(sig in obs_lower for sig in failure_signals)

    def diagnose_and_repair(
        self, action: AgentAction, failure_output: str
    ) -> str:
        """# TODO: Generate a diagnosis prompt and call self.llm.generate to produce an actionable diagnosis."""
        raise NotImplementedError("Implement diagnose_and_repair")
```

<details>
<summary>👉 Click to reveal Answer Key for `src/agent/reflection.py`</summary>

```python
"""Self-healing and reflection loop for failing tool operations."""

from src.agent.models import AgentAction
from src.llm.client import LLMClient

REFLEXION_PROMPT = """You are analyzing a failed execution step.
Previous Action: {tool_name} with input {tool_input}
Error Trace / Failure Output:
{error_trace}

Analyze what went wrong in 2 sentences, and output the EXACT corrected Action and Action Input to fix it.
Format:
Analysis: your diagnosis
Corrected Action: tool_name
Corrected Action Input: corrected input
"""


class SelfHealingCoordinator:
    """Detects failing tool observations and prompts the LLM for self-correction."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    def is_failure(self, observation: str) -> bool:
        failure_signals = [
            "error",
            "failed",
            "exception",
            "traceback",
            "permission denied",
        ]
        obs_lower = observation.lower()
        return any(sig in obs_lower for sig in failure_signals)

    def diagnose_and_repair(
        self, action: AgentAction, failure_output: str
    ) -> str:
        prompt = REFLEXION_PROMPT.format(
            tool_name=action.tool,
            tool_input=action.tool_input,
            error_trace=failure_output[:2000],  # Bound context length
        )
        messages = [{"role": "user", "content": prompt}]
        return self.llm.generate(messages, temperature=0.0)
```
</details>

---

## Checkpoint

Prove Day 5 is complete:
1. Write a test in `tests/test_resilience.py` verifying that:
   - `retry_with_jitter` retries a mock failing function 3 times before succeeding.
   - `SelfHealingCoordinator.is_failure` correctly flags test failure strings.
2. Run:
   ```powershell
   pytest -v tests/test_resilience.py
   ruff check .
   ```

---

## Senior Interview Angle

### Q: "How does the Reflexion pattern compare to standard Try-Catch retry blocks?"
**Senior Answer:**
> *"A standard Try-Catch retry block executes the exact same operation with the exact same arguments repeatedly. In deterministic failures (e.g. invalid syntax, failing unit test, missing file), repeating identical code will always fail identically (wasted cycles).
> 
> Reflexion introduces semantic self-correction:
> 1. It treats error traces as **new information** fed back into the LLM's working memory.
> 2. The agent inspects the stack trace (e.g. `FileNotFoundError: config.json`), updates its internal hypothesis, and generates a *different* action (e.g. creating `config.json` or searching for its correct path).
> 3. This transforms static code execution into an adaptive, self-healing system."*

---

## Ready to Merge?

```powershell
git checkout -b feat/day5-resilience-and-self-healing
git add src/ tests/ docs/
git commit -m "feat(resilience): implement exponential backoff with jitter and Reflexion loop"
git push -u origin feat/day5-resilience-and-self-healing
```
