"""Safety guardrails: risk classification, HITL gates, and cycle detection."""

import hashlib
from collections.abc import Callable
from enum import StrEnum

from src.agent.models import AgentAction


class ToolRisk(StrEnum):
    """Risk tier for tools."""

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
        """Hash the action and verify it hasn't exceeded the repeat threshold."""
        sig = f"{action.tool}::{action.tool_input}"
        h = hashlib.sha256(sig.encode("utf-8")).hexdigest()
        self.recent_hashes.append(h)

        if len(self.recent_hashes) >= self.max_repeats:
            last_n = self.recent_hashes[-self.max_repeats :]
            if all(item == last_n[0] for item in last_n):
                raise CycleDetectionError(
                    f"Infinite loop detected: tool '{action.tool}' called "
                    f"{self.max_repeats} times with identical input."
                )


class HITLApprovalGate:
    """Prompts human operator before executing high-risk actions."""

    def __init__(self, prompt_func: Callable[[str], bool] | None = None) -> None:
        self.prompt_func = prompt_func or self._default_cli_prompt

    def _default_cli_prompt(self, message: str) -> bool:
        """Default interactive CLI prompt."""
        choice = (
            input(f"\n[HITL SAFETY WARNING] {message}\nApprove execution? [y/N]: ").strip().lower()
        )
        return choice in ("y", "yes")

    def approve(self, action: AgentAction, risk: ToolRisk) -> bool:
        """Check if action is permitted to execute."""
        if risk == ToolRisk.SAFE:
            return True

        msg = (
            f"Agent requests to execute HIGH-RISK tool '{action.tool}' "
            f"with input: '{action.tool_input}'"
        )
        return self.prompt_func(msg)
