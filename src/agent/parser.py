"""Parser for extracting AgentAction or AgentFinish from raw model text."""

import re

from src.agent.models import AgentAction, AgentFinish


class ReActParsingError(Exception):
    """Raised when model response cannot be parsed into ReAct format."""

    pass


class ReActParser:
    """Parses raw LLM completion text into structured AgentAction or AgentFinish."""

    def parse(self, text: str) -> AgentAction | AgentFinish:
        """Parse raw model output into an action or terminal finish state."""

        # 1. Explicit Final Answer
        if "Final Answer:" in text:
            parts = text.split("Final Answer:", 1)
            thought = parts[0].replace("Thought:", "").strip()
            final_answer = parts[1].strip()
            return AgentFinish(final_answer=final_answer, thought=thought)

        # 2. Tool Action Call
        if "Action:" in text:
            pattern = r"Thought:\s*(.*?)\s*Action:\s*([a-zA-Z0-9_\-]+)\s*Action Input:\s*(.*)"
            match = re.search(pattern, text, re.DOTALL)
            if match:
                thought = match.group(1).strip()
                tool = match.group(2).strip()
                tool_input = match.group(3).strip()
                return AgentAction(tool=tool, tool_input=tool_input, thought=thought)

            fallback_pattern = r"Action:\s*([a-zA-Z0-9_\-]+)\s*Action Input:\s*(.*)"
            match_fallback = re.search(fallback_pattern, text, re.DOTALL)
            if match_fallback:
                tool = match_fallback.group(1).strip()
                tool_input = match_fallback.group(2).strip()
                return AgentAction(tool=tool, tool_input=tool_input, thought="")

            raise ReActParsingError(f"Malformed Action format in output:\n{text}")

        # 3. Direct Answer (Model provided answer without 'Final Answer:' prefix)
        if text.strip():
            clean_text = text.replace("Thought:", "").strip()
            return AgentFinish(final_answer=clean_text, thought=text.strip())

        raise ReActParsingError("Empty LLM output.")
