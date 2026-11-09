"""Unit tests for safety guardrails: CycleDetector and HITLApprovalGate."""

import pytest

from src.agent.models import AgentAction
from src.safety.guardrails import (
    CycleDetectionError,
    CycleDetector,
    HITLApprovalGate,
    ToolRisk,
)
from src.tools.base import Tool, ToolRegistry


def test_cycle_detector_allows_distinct_actions() -> None:
    """Verify distinct actions do not trigger cycle detection."""
    detector = CycleDetector(max_consecutive_repeats=2)

    # Calling different files should never raise an error
    detector.check(AgentAction(thought="step 1", tool="read_file", tool_input="a.txt"))
    detector.check(AgentAction(thought="step 2", tool="read_file", tool_input="b.txt"))
    detector.check(AgentAction(thought="step 3", tool="read_file", tool_input="c.txt"))


def test_cycle_detector_catches_infinite_loop() -> None:
    """Verify repeating identical actions consecutively raises CycleDetectionError."""
    detector = CycleDetector(max_consecutive_repeats=2)
    repeated_action = AgentAction(thought="read", tool="read_file", tool_input="missing.txt")

    # First attempt: allowed
    detector.check(repeated_action)

    # Second identical attempt: infinite loop caught!
    with pytest.raises(CycleDetectionError, match="Infinite loop detected"):
        detector.check(repeated_action)


def test_hitl_approval_gate_safe_tools_auto_approved() -> None:
    """Verify SAFE tools are approved automatically without prompting the user."""

    def mock_prompt(_: str) -> bool:
        raise AssertionError("Prompt should NOT be called for SAFE tools!")

    gate = HITLApprovalGate(prompt_func=mock_prompt)
    action = AgentAction(thought="list", tool="list_dir", tool_input="src")

    assert gate.approve(action, ToolRisk.SAFE) is True


def test_hitl_approval_gate_high_risk_user_approves() -> None:
    """Verify HIGH risk tools execute when operator inputs Yes."""
    prompt_called = False

    def mock_approve(_: str) -> bool:
        nonlocal prompt_called
        prompt_called = True
        return True

    gate = HITLApprovalGate(prompt_func=mock_approve)
    action = AgentAction(thought="write", tool="write_file", tool_input="app.py:::x=1")

    assert gate.approve(action, ToolRisk.HIGH) is True
    assert prompt_called is True


def test_hitl_approval_gate_high_risk_user_rejects() -> None:
    """Verify HIGH risk tools are blocked when operator inputs No."""
    gate = HITLApprovalGate(prompt_func=lambda _: False)
    action = AgentAction(thought="delete", tool="delete_file", tool_input="app.py")

    assert gate.approve(action, ToolRisk.HIGH) is False


def test_tool_registry_risk_tier() -> None:
    """Verify ToolRegistry stores and returns correct risk tiers."""
    registry = ToolRegistry()

    safe_tool = Tool(
        name="read_file",
        description="read",
        func=lambda s: s,
        risk=ToolRisk.SAFE,
    )
    high_tool = Tool(
        name="write_file",
        description="write",
        func=lambda s: s,
        risk=ToolRisk.HIGH,
    )

    registry.register(safe_tool)
    registry.register(high_tool)

    assert registry.get_risk("read_file") == ToolRisk.SAFE
    assert registry.get_risk("write_file") == ToolRisk.HIGH
    # Unknown tools must default to HIGH risk for safety
    assert registry.get_risk("unknown_tool") == ToolRisk.HIGH
