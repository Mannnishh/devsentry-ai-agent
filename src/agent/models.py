"""Domain models for agent actions, observations, and termination states."""

from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    """An action the agent decided to execute."""

    tool: str = Field(description="Name of the tool to execute, e.g. 'read_file'")
    tool_input: str = Field(description="Input argument passed to the tool, e.g. 'main.py'")
    thought: str = Field(description="The reasoning trace leading to this action")


class AgentFinish(BaseModel):
    """The final state when the agent has completed its task."""

    final_answer: str = Field(description="The complete response for the user")
    thought: str = Field(description="Final reasoning trace")


class AgentStep(BaseModel):
    """A completed execution step containing action and resulting observation."""

    action: AgentAction
    observation: str = Field(description="Tool output returned back to the agent")
