"""Tests for the ReAct parser and execution engine."""

from unittest.mock import MagicMock

import pytest

from src.agent.engine import ReActEngine
from src.agent.models import AgentAction, AgentFinish
from src.agent.parser import ReActParser, ReActParsingError


def test_parser_extracts_final_answer():
    """Verify parser extracts AgentFinish when Final Answer is present."""
    parser = ReActParser()
    raw = (
        "Thought = I have finished investigating.\n"
        "Final Answer: The bug is caused by a missing null check on line 12."
    )
    result = parser.parse(raw)

    assert isinstance(result, AgentFinish)
    assert result.final_answer == "The bug is caused by a missing null check on line 12."
    assert "finished investigating" in result.thought


def test_parser_extracts_action():
    """Verify parser extracts tool name, tool input, and thought."""
    parser = ReActParser()
    raw = (
        "Thought: I should read the auth configuration file.\n"
        "Action: read_file\n"
        "Action Input: src/config.py"
    )
    result = parser.parse(raw)
    assert isinstance(result, AgentAction)
    assert result.tool == "read_file"
    assert result.tool_input == "src/config.py"
    assert "read the auth configuration" in result.thought


def test_parser_raises_on_invalid_format():
    """Verify parser raises ReActParsingError on unstructured text."""
    parser = ReActParser()
    raw = "Action: read_file_without_action_input"

    with pytest.raises(ReActParsingError):
        parser.parse(raw)


def test_react_engine_executes_tool_and_terminates():
    """Verify ReActEngine executes tools and feeds observations into the next iteration."""
    mock_llm = MagicMock()

    # Simulate 2 sequential LLM calls:
    # 1. Model asks to call 'reverse_string'
    # 2. Model receives observation and outputs 'Final Answer:'
    mock_llm.generate.side_effect = [
        "Thought: I need to reverse the word.\nAction: reverse_string\nAction Input: hello",
        "Thought: I now have the reversed string.\nFinal Answer: The reversed word is olleh.",
    ]

    # A simple tool function (in Python, s[::-1] reverses a string)
    tools = {"reverse_string": lambda s: s[::-1]}

    engine = ReActEngine(llm_client=mock_llm, tools=tools, max_iterations=3)
    final_result = engine.run("What is 'hello' reversed?")

    assert final_result == "The reversed word is olleh."
    assert mock_llm.generate.call_count == 2
