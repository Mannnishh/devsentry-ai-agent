"""Working memory scratchpad with context compaction."""

from src.agent.models import AgentStep


class ScratchpadManager:
    """Manages agent working memory, enforcing length bounds and sliding window truncation."""

    def __init__(self, max_observation_chars: int = 1500, max_recent_steps: int = 5) -> None:
        self.max_obs_chars = max_observation_chars
        self.max_recent_steps = max_recent_steps

    def format_step(self, step: AgentStep, is_recent: bool = True) -> str:
        """Format a single step, truncating older or verbose observations."""
        obs = step.observation
        if not is_recent or len(obs) > self.max_obs_chars:
            omitted = len(step.observation) - self.max_obs_chars
            obs = obs[: self.max_obs_chars] + f"\n...[Truncated: {omitted} chars omitted] ..."
        return (
            f"Thought: {step.action.thought}\n"
            f"Action: {step.action.tool}\n"
            f"Action Input: {step.action.tool_input}\n"
            f"Observation: {obs}\n"
        )

    def build(self, steps: list[AgentStep]) -> str:
        """Build the complete scratchpad string with compaction applied."""
        if not steps:
            return ""

        formatted_steps: list[str] = []
        # Any step older than the last `max_recent_steps` is treated as non-recent
        split_idx = max(0, len(steps) - self.max_recent_steps)

        for i, step in enumerate(steps):
            is_recent = i >= split_idx
            formatted_steps.append(self.format_step(step, is_recent=is_recent))

        return "".join(formatted_steps)
