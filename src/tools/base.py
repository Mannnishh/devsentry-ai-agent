"""Base tool abstractions and registry for DevSentry."""

from collections.abc import Callable

from pydantic import BaseModel, Field

from src.safety.guardrails import ToolRisk


class Tool(BaseModel):
    """Represents a callable tool exposed to the AI agent."""

    name: str = Field(description="unique tool identifier, e.g. 'read_file'")
    description: str = Field("Instruction for the LLM on when and how to call this tool")
    func: Callable[[str], str] = Field(description="The underlying Python function to execute")
    risk: ToolRisk = Field(default=ToolRisk.SAFE, description="Safety tier: SAFE or HIGH")

    def execute(self, argument: str) -> str:
        """Safely execute the tool and catch any runtime exceptions."""
        try:
            return str(self.func(argument))
        except Exception as e:
            return f"Error executing tool '{self.name}': {type(e).__name__}: {e}"


class ToolRegistry:
    """Central registry of all tools available to the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a new tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Retrieve a tool by name."""
        return self._tools.get(name)

    def to_dict(self) -> dict[str, Callable[[str], str]]:
        """Export as a name-to-function dictionary for ReActEngine."""
        return {t.name: t.execute for t in self._tools.values()}

    def get_descriptions(self) -> str:
        """Generate formatted description string for the ReAct system prompt."""
        return "\n".join([f"- {t.name}: {t.description}" for t in self._tools.values()])

    def get_names(self) -> str:
        """Get comma-separated tool names for prompt formatting"""
        return ", ".join(self._tools.keys())

    def get_risk(self, name: str) -> ToolRisk:
        """Return the risk tier for a tool (defaults to HIGH if unknown)."""
        tool = self._tools.get(name)
        return tool.risk if tool else ToolRisk.HIGH
