"""Self-healing and reflection loop for failing tool operations."""

from src.agent.models import AgentAction
from src.llm.client import LLMClient

REFLEXION_PROMPT = """You are analyzing a failed execution step.
Previous Action: {tool_name} with input: {tool_input}
Error Trace / Failure Output:
{error_trace}

Analyze what went wrong in 2 sentences, and output the EXACT corrected Action and Action Input.
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
        """Check if an observation contains common failure and error indicators."""
        obs_lower = observation.lower()

        # Filter out benign test-runner counts like "0 failed" or "0 errors"
        cleaned = obs_lower.replace("0 failed", "").replace("0 errors", "")

        failure_signals = [
            "error",
            "failed",
            "exception",
            "traceback",
            "permission denied",
            "not found",
        ]

        return any(sig in cleaned for sig in failure_signals)

    def diagnose_and_repair(self, action: AgentAction, failure_output: str) -> str:
        """Prompt the LLM to diagnose the failure and recommend a corrective action."""
        prompt = REFLEXION_PROMPT.format(
            tool_name=action.tool,
            tool_input=action.tool_input,
            error_trace=failure_output[:2000],  # Bound context length
        )
        messages = [{"role": "user", "content": prompt}]
        return self.llm.generate(messages, temperature=0.0)
