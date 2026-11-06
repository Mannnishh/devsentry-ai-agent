"""Tests for tool registry, safe filesystem sandbox, and test runner."""

from pathlib import Path

import pytest

from src.tools.base import Tool, ToolRegistry
from src.tools.filesystem import SafeFileSystem
from src.tools.test_runner import TestRunnerTool


def test_tool_registry():
    """Verify tool registration and description generation."""
    registry = ToolRegistry()
    dummy_tool = Tool(
        name="dummy",
        description="A dummy test tool",
        func=lambda x: f"result: {x}",
    )
    registry.register(dummy_tool)

    assert registry.get("dummy") is not None
    assert "dummy: A dummy test tool" in registry.get_descriptions()
    assert "dummy" in registry.get_names()

    # Test execution via to_dict()
    tools_dict = registry.to_dict()
    assert tools_dict["dummy"]("hello") == "result: hello"


def test_safe_filesystem_crud(tmp_path: Path):
    """Verify safe file write, read, and list operations within sandbox."""
    fs = SafeFileSystem(root_dir=tmp_path)

    # 1. Write file
    write_res = fs.write_file("sub/hello.txt:::Hello DevSentry!")
    assert "Successfully wrote" in write_res

    # 2. Read file
    content = fs.read_file("sub/hello.txt")
    assert content == "Hello DevSentry!"

    # 3. List directory
    listing = fs.list_dir("sub")
    assert "[FILE] hello.txt" in listing


def test_safe_filesystem_blocks_path_traversal(tmp_path: Path):
    """Verify path traversal attacks (../../) are strictly blocked with PermissionError."""
    # Create an isolated sandbox subdirectory
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    fs = SafeFileSystem(root_dir=sandbox_dir)

    # Attempt to escape sandbox using relative path traversal
    with pytest.raises(PermissionError) as exc_info:
        fs.read_file("../../secret.txt")

    assert "Security violation" in str(exc_info.value)

    # Attempt path traversal on write
    with pytest.raises(PermissionError) as exc_info:
        fs.write_file("../../hacked.txt:::malicious content")

    assert "Security violation" in str(exc_info.value)


def test_test_runner_outside_boundary(tmp_path: Path):
    """Verify test runner rejects targets outside the workspace root."""
    runner = TestRunnerTool(workspace_root=tmp_path)
    runner.run_tests("../../outside_test.py")
