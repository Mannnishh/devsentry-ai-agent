"""Unit tests for retry backoff and self-healing reflexion."""

from unittest.mock import MagicMock

import pytest

from src.agent.models import AgentAction
from src.agent.reflection import SelfHealingCoordinator
from src.resilience.backoff import retry_with_jitter


def test_retry_with_jitter_success_after_failures() -> None:
    """Verify decorator retries on exceptions and returns when function succeeds."""
    call_count = 0

    @retry_with_jitter(max_retries=4, base_delay=0.01, max_delay=0.05)
    def flaky_operation() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Temporary network blip")
        return "SUCCESS"

    result = flaky_operation()
    assert result == "SUCCESS"
    assert call_count == 3


def test_retry_with_jitter_exhausts_retries() -> None:
    """Verify decorator re-raises exception once max_retries is reached."""
    call_count = 0

    @retry_with_jitter(max_retries=3, base_delay=0.01, max_delay=0.05)
    def always_failing() -> None:
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Service unavailable")

    with pytest.raises(TimeoutError, match="Service unavailable"):
        always_failing()

    assert call_count == 3


def test_self_healing_coordinator_is_failure() -> None:
    """Verify is_failure detects error indicators and ignores clean outputs."""
    mock_llm = MagicMock()
    coordinator = SelfHealingCoordinator(llm_client=mock_llm)

    assert coordinator.is_failure("Error: File not found: src/utils.py") is True
    assert coordinator.is_failure("FAILED: AssertionError in tests/test_tools.py") is True
    assert coordinator.is_failure("Traceback (most recent call last):") is True
    assert coordinator.is_failure("Permission denied: /root/secret") is True
    assert coordinator.is_failure("3 passed, 0 failed in 0.24s") is False


def test_self_healing_coordinator_diagnose_and_repair() -> None:
    """Verify diagnose_and_repair formats prompt and invokes LLM."""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "Analysis: File does not exist.\n"
        "Corrected Action: write_file\n"
        "Corrected Action Input: src/main.py:::print('hello')"
    )

    coordinator = SelfHealingCoordinator(llm_client=mock_llm)
    action = AgentAction(thought="Read main", tool="read_file", tool_input="src/main.py")
    diagnosis = coordinator.diagnose_and_repair(
        action=action, failure_output="FileNotFoundError: [Errno 2] No such file"
    )

    assert "Analysis: File does not exist." in diagnosis
    assert "Corrected Action: write_file" in diagnosis
    assert mock_llm.generate.call_count == 1
