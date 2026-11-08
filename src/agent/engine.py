"""Core ReAct execution engine with working memory compaction and session persistence."""

from collections.abc import Callable

from src.agent.models import AgentAction, AgentFinish, AgentStep
from src.agent.parser import ReActParser
from src.agent.prompts import REACT_SYSTEM_PROMPT
from src.agent.reflection import SelfHealingCoordinator
from src.llm.client import LLMClient
from src.memory.scratchpad import ScratchpadManager
from src.memory.storage import SQLiteSessionStore


class ReActEngine:
    """Orchestrates the ReAct reasoning and execution loop."""

    def __init__(
        self,
        llm_client: LLMClient,
        tools: dict[str, Callable[[str], str]],
        max_iterations: int = 5,
        scratchpad_manager: ScratchpadManager | None = None,
        session_store: SQLiteSessionStore | None = None,
        self_healing: SelfHealingCoordinator | None = None,
    ):
        self.llm = llm_client
        self.tools = tools
        self.max_iterations = max_iterations
        self.parser = ReActParser()
        self.scratchpad_manager = scratchpad_manager or ScratchpadManager()
        self.session_store = session_store
        self.self_healing = self_healing

    def run(self, question: str, session_id: str | None = None) -> str:
        """Run the ReAct loop until completion or max iterations reached."""
        intermediate_steps: list[AgentStep] = []
        tool_names = ", ".join(self.tools.keys())
        tools_description = "\n".join([f"- {name}: callable function" for name in self.tools])

        if self.session_store and session_id:
            self.session_store.create_session(session_id, question, status="RUNNING")

        for iteration in range(self.max_iterations):
            # 1. Build the dynamic scratchpad from past steps with sliding-window compaction
            scratchpad = self.scratchpad_manager.build(intermediate_steps)

            # 2. Format the system prompt with available tools and current history
            formatted_system = REACT_SYSTEM_PROMPT.format(
                tools_description=tools_description,
                tool_names=tool_names,
            )
            prompt = f"{formatted_system}\n\nQuestion: {question}\n{scratchpad}"

            # 3. Call the LLM with the stop sequence
            messages = [{"role": "user", "content": prompt}]
            raw_response = self.llm.generate(messages, stop=["Observation:"])

            # 4. Parse the response into an Action or Finish
            parsed = self.parser.parse(raw_response)

            # 5. Check if the task is finished
            if isinstance(parsed, AgentFinish):
                print(f"[Step {iteration + 1}] Finished task!")
                if self.session_store and session_id:
                    self.session_store.create_session(session_id, question, status="COMPLETED")
                return parsed.final_answer

            # 6. Execute the requested tool
            if isinstance(parsed, AgentAction):
                print(f"[Step {iteration + 1}] Thought: {parsed.thought[:100]}")
                print(f"[Step {iteration + 1}] Action: {parsed.tool}('{parsed.tool_input}')")
                tool_func = self.tools.get(parsed.tool)
                if tool_func:
                    try:
                        observation = str(tool_func(parsed.tool_input))
                    except Exception as e:
                        observation = f"Error executing {parsed.tool}: {e}"
                else:
                    observation = f"Error: Tool '{parsed.tool}' not found in [{tool_names}]."

                # 7. Self-Healing Reflexion loop if an error or failure was returned
                if self.self_healing and self.self_healing.is_failure(observation):
                    print(f"[Step {iteration + 1}] ⚠️ Failure detected. Initiating Reflexion...")
                    try:
                        diagnosis = self.self_healing.diagnose_and_repair(parsed, observation)
                        observation += f"\n[Reflexion Self-Correction Plan]:\n{diagnosis}"
                    except Exception as e:
                        print(f"[Step {iteration + 1}] Reflexion failed: {e}")

            # 8. Record the completed step into working memory & persistent store
            step = AgentStep(action=parsed, observation=observation)
            intermediate_steps.append(step)

            if self.session_store and session_id:
                self.session_store.save_step(session_id, step_index=iteration + 1, step=step)

        if self.session_store and session_id:
            self.session_store.create_session(session_id, question, status="FAILED")

        return f"Agent failed to reach final answer within {self.max_iterations} iterations."
