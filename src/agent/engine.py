"""Core ReAct execution engine."""

from collections.abc import Callable

from src.agent.models import AgentAction, AgentFinish, AgentStep
from src.agent.parser import ReActParser
from src.agent.prompts import REACT_SYSTEM_PROMPT, build_scratchpad
from src.llm.client import LLMClient


class ReActEngine:
    """Orchestrates the ReAct reasoning and execution loop."""

    def __init__(
        self,
        llm_client: LLMClient,
        tools: dict[str, Callable[[str], str]],
        max_iterations: int = 5,
    ):
        self.llm = llm_client
        self.tools = tools
        self.max_iterations = max_iterations
        self.parser = ReActParser()

    def run(self, question: str) -> str:
        """Run the ReAct loop until completion or max iterations reached."""
        intermediate_steps: list[AgentStep] = []
        tool_names = ", ".join(self.tools.keys())
        tools_description = "\n".join([f"- {name}: callable function" for name in self.tools])

        for _ in range(self.max_iterations):
            # 1. Build the dynamic scratchpad from past steps
            scratchpad = build_scratchpad(intermediate_steps)

            # 2. Format the system prompt with available tools and current history
            prompt = (
                f"{REACT_SYSTEM_PROMPT.format(tools_description=tools_description, tool_names=tool_names)}\n\n"
                f"Question: {question}\n"
                f"{scratchpad}"
            )
            # 3. Call the LLM with the stop sequence
            messages = [{"role": "user", "content": prompt}]
            raw_response = self.llm.generate(messages, stop=["Observation:"])

            # 4. Parse the response into an Action or Finish
            parsed = self.parser.parse(raw_response)

            # 5. Check if the task is finished
            if isinstance(parsed, AgentFinish):
                return parsed.final_answer

            # 6. Execute the requested tool
            if isinstance(parsed, AgentAction):
                tool_func = self.tools.get(parsed.tool)
                if tool_func:
                    try:
                        observation = str(tool_func(parsed.tool_input))
                    except Exception as e:
                        observation = f"Error executing {parsed.tool}: {e}"
                else:
                    observation = f"Error: Tool '{parsed.tool}' not found in [{tool_names}]."

            # 7. Record the completed step into working memory
            intermediate_steps.append(AgentStep(action=parsed, observation=observation))

        return f"Agent failed to reach final answer within {self.max_iterations} iterations."
