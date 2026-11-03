# Day 6 — Human-in-the-Loop (HITL) & Safety Guardrails

**Focus:** Implementing Human-in-the-Loop (HITL) approval gates for high-risk actions, semantic cycle detection, and hard token budget ceilings.

An autonomous agent with the power to modify code, delete files, or execute commands cannot be left completely unsupervised in enterprise environments. Today, you will build the safety guardrails that prevent catastrophic mistakes and infinite loops.

---

## Concept Primer

### 1. Python Primer for Beginners: What You Need Today

#### A. Enums for Risk Categorization
In Python, the `enum` module provides strongly-typed enumerations:
```python
from enum import Enum


class ToolRisk(str, Enum):
    SAFE = "SAFE"  # Read-only operations (list_dir, read_file)
    MODERATE = "MODERATE"  # Safe test runner execution
    HIGH = "HIGH"  # Modifying files, git commits, destructive commands
```

#### B. Hashing for Cycle Detection (`hashlib`)
To detect if an agent is stuck in an infinite loop repeating the exact same action, we hash each action signature `tool_name + tool_input`:
```python
import hashlib


def hash_action(tool: str, tool_input: str) -> str:
    signature = f"{tool}:{tool_input}"
    return hashlib.sha256(signature.encode("utf-8")).hexdigest()
```

---

### 2. Human-in-the-Loop (HITL) Architecture

```mermaid
flowchart TD
    ActionProposed["Agent Emits Action: write_file('app.py')"] --> RiskCheck{"Is Action Risk HIGH?"}
    RiskCheck -->|No (Read-Only)| AutoExecute["Execute Automatically"]
    RiskCheck -->|Yes| PromptUser["Prompt Operator: Approve [Y/N]?"]
    PromptUser -->|User Inputs 'Y'| AutoExecute
    PromptUser -->|User Inputs 'N'| Reject["Return Observation: 'User rejected action'"]
    Reject --> FeedBack["Feed Back to ReAct Loop (Model adapts)"]
```

1. **Classification:** Every tool registers its risk level (`SAFE`, `MODERATE`, `HIGH`).
2. **Interception:** When the ReAct engine receives an `AgentAction`, it queries the `HITLApprovalGate`.
3. **Graceful Adaptation:** If the operator rejects an action, the agent doesn't crash — it receives an observation stating `Action rejected by user` and attempts an alternative strategy!

---

## Official Reference Links

- [Python `enum` Documentation](https://docs.python.org/3/library/enum.html)
- [Python `hashlib` Documentation](https://docs.python.org/3/library/hashlib.html)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

---

## Hands-on Exercise

Today you will build `src/safety/guardrails.py`:
- `ToolRisk` enum
- `HITLApprovalGate` for user confirmation
- `CycleDetector` to abort infinite loops

---

### Step 1: Implement Safety Guardrails (`src/safety/guardrails.py`)

Create `src/tools/guardrails.py` with this guided TODO:

```python
"""Safety guardrails: risk classification, HITL gates, and loop detection."""

import hashlib
from collections.abc import Callable
from enum import Enum
from src.agent.models import AgentAction


class ToolRisk(str, Enum):
    SAFE = "SAFE"
    HIGH = "HIGH"


class CycleDetectionError(Exception):
    """Raised when an agent repeats identical actions consecutively."""

    pass


class CycleDetector:
    """Tracks action signatures to prevent infinite repeating loops."""

    def __init__(self, max_consecutive_repeats: int = 2) -> None:
        self.max_repeats = max_consecutive_repeats
        self.recent_hashes: list[str] = []

    def check(self, action: AgentAction) -> None:
        """# TODO:
        # 1. Compute sha256 hash of action.tool + '::' + action.tool_input
        # 2. Append to self.recent_hashes
        # 3. If the last N hashes are identical, raise CycleDetectionError
        """
        raise NotImplementedError("Implement CycleDetector.check")


class HITLApprovalGate:
    """Prompts human operator before executing high-risk actions."""

    def __init__(self, prompt_func: Callable[[str], bool] | None = None) -> None:
        # Default to standard interactive CLI input
        self.prompt_func = prompt_func or self._default_cli_prompt

    def _default_cli_prompt(self, message: str) -> bool:
        choice = (
            input(f"\n[HITL SAFETY WARNING] {message}\nApprove execution? [y/N]: ").strip().lower()
        )
        return choice in ("y", "yes")

    def approve(self, action: AgentAction, risk: ToolRisk) -> bool:
        if risk == ToolRisk.SAFE:
            return True
        msg = f"Agent requests to execute HIGH-RISK tool: '{action.tool}' with input: '{action.tool_input}'"
        return self.prompt_func(msg)
```

<details>
<summary>👉 Click to reveal Answer Key for `src/safety/guardrails.py`</summary>

```python
"""Safety guardrails: risk classification, HITL gates, and loop detection."""

import hashlib
from collections.abc import Callable
from enum import Enum
from src.agent.models import AgentAction


class ToolRisk(str, Enum):
    SAFE = "SAFE"
    HIGH = "HIGH"


class CycleDetectionError(Exception):
    """Raised when an agent repeats identical actions consecutively."""

    pass


class CycleDetector:
    """Tracks action signatures to prevent infinite repeating loops."""

    def __init__(self, max_consecutive_repeats: int = 2) -> None:
        self.max_repeats = max_consecutive_repeats
        self.recent_hashes: list[str] = []

    def check(self, action: AgentAction) -> None:
        sig = f"{action.tool}::{action.tool_input}"
        h = hashlib.sha256(sig.encode("utf-8")).hexdigest()
        self.recent_hashes.append(h)

        if len(self.recent_hashes) >= self.max_repeats:
            last_n = self.recent_hashes[-self.max_repeats :]
            if all(item == last_n[0] for item in last_n):
                raise CycleDetectionError(
                    f"Infinite loop detected: tool '{action.tool}' called {self.max_repeats} times with identical input."
                )


class HITLApprovalGate:
    """Prompts human operator before executing high-risk actions."""

    def __init__(self, prompt_func: Callable[[str], bool] | None = None) -> None:
        self.prompt_func = prompt_func or self._default_cli_prompt

    def _default_cli_prompt(self, message: str) -> bool:
        choice = (
            input(f"\n[HITL SAFETY WARNING] {message}\nApprove execution? [y/N]: ").strip().lower()
        )
        return choice in ("y", "yes")

    def approve(self, action: AgentAction, risk: ToolRisk) -> bool:
        if risk == ToolRisk.SAFE:
            return True
        msg = f"Agent requests to execute HIGH-RISK tool: '{action.tool}' with input: '{action.tool_input}'"
        return self.prompt_func(msg)
```
</details>

---

## Checkpoint

Prove Day 6 is complete:
1. Write a test in `tests/test_guardrails.py` that verifies:
   - `CycleDetector` allows 1 call, but raises `CycleDetectionError` when the same action repeats.
   - `HITLApprovalGate` allows `SAFE` tools without prompting, but intercepts `HIGH` risk tools.
2. Run:
   ```powershell
   pytest -v tests/test_guardrails.py
   ruff check .
   ```

---

## Senior Interview Angle

### Q: "How do you architect Human-in-the-Loop approval for asynchronous background tasks in production?"
**Senior Answer:**
> *"In a production API or background worker (e.g. Celery, Temporal, or AWS Step Functions), we cannot use a blocking `input()` call. Instead, we use the **Asynchronous Pause-and-Resume Pattern**:
> 1. When the agent reaches a high-risk tool, the state machine transitions to `STATUS: AWAITING_APPROVAL`.
> 2. The agent snapshots its current execution checkpoint into the database and generates an approval event (sent to Slack, email, or a dashboard via webhook).
> 3. The worker process frees up its thread/container.
> 4. When the human approves via an API endpoint (`POST /sessions/{id}/approve`), the orchestrator re-hydrates the agent from its database checkpoint and resumes execution."*

---

## Ready to Merge?

```powershell
git checkout -b feat/day6-human-in-the-loop-safety
git add src/ tests/ docs/
git commit -m "feat(safety): implement HITL approval gates and cycle detection guardrails"
git push -u origin feat/day6-human-in-the-loop-safety
```
