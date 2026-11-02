# Day 3 — Function Calling, Dynamic Tool Registry & Secure Sandboxing

**Focus:** Building a typed `ToolRegistry` with automatic JSON schema generation and secure, sandboxed tools (Code Grep, Safe File I/O with directory jailing, and Sandboxed Test Runner).

An agent without tools is just a chatbot. But giving an LLM access to your computer's filesystem and shell without strict security boundaries is an extreme vulnerability. Today, you will build production-grade tool abstractions that safely ground the agent in reality.

---

## Concept Primer

### 1. Python Primer for Beginners: What You Need Today

#### A. Python Decorators (`@tool`)
In Python, a decorator is a function that wraps another function to add behavior or metadata without modifying its code. In Java, this is similar to custom annotations (`@Tool`) combined with Spring Bean reflection.
```python
def tool(name: str, description: str):
    def decorator(func):
        func.tool_name = name
        func.tool_description = description
        return func

    return decorator


@tool("read_file", "Reads the full content of a specified file")
def read_file(path: str) -> str:
    return open(path).read()
```

#### B. Safe Path Handling with `pathlib.Path`
Never use simple string concatenation like `base_dir + "/" + user_path`. Attackers (or hallucinating LLMs) can pass `../../etc/passwd` or `../../Windows/System32` (Path Traversal Attack).
Python's `pathlib.Path` allows you to enforce a **sandbox root**:
```python
from pathlib import Path

safe_root = Path("./workspace").resolve()
target = (safe_root / requested_path).resolve()

# Check if target is strictly inside safe_root
if not target.is_relative_to(safe_root):
    raise PermissionError("Access denied: path outside sandbox root!")
```

#### C. Safe Shell Execution with `subprocess.run`
Never use `os.system()` or `shell=True` because it opens a full shell susceptible to command injection (e.g. `test_runner.py; rm -rf /`).
Instead, pass a list of arguments and set an explicit timeout:
```python
import subprocess

result = subprocess.run(
    ["pytest", "tests/"],
    capture_output=True,
    text=True,
    timeout=30,  # Prevents hanging processes
    cwd=str(safe_root),
)
```

---

### 2. The Tool Calling Protocol

Modern LLMs require three pieces of metadata for every tool:
1. **Name:** A clean, machine-friendly identifier (e.g. `read_file`).
2. **Description:** Clear natural language telling the LLM *when* and *why* to use this tool.
3. **Parameter Schema:** Exact argument names and types.

---

## Official Reference Links

- [Python `pathlib` Documentation](https://docs.python.org/3/library/pathlib.html)
- [Python `subprocess` Management](https://docs.python.org/3/library/subprocess.html)
- [OWASP: Path Traversal Vulnerability](https://owasp.org/www-community/attacks/Path_Traversal)

---

## Hands-on Exercise

Today you will build 3 files:
1. `src/tools/base.py` — The `BaseTool` class and `@tool` decorator.
2. `src/tools/filesystem.py` — Safe File Reader, Writer, and Code Grepper jailed to a specific root directory.
3. `src/tools/test_runner.py` — Sandboxed pytest command executor with timeout protection.

---

### Step 1: Base Tool Architecture (`src/tools/base.py`)

Create `src/tools/base.py`:

```python
"""Base tool abstraction and registry."""

from collections.abc import Callable
from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Represents a callable tool exposed to the AI agent."""

    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Instructions for the LLM on when to call this tool")
    func: Callable[[str], str] = Field(description="The underlying Python function to execute")

    def execute(self, argument: str) -> str:
        """Execute the tool safely and catch any runtime exceptions."""
        try:
            return str(self.func(argument))
        except Exception as e:
            return f"Error executing tool '{self.name}': {type(e).__name__}: {e}"


class ToolRegistry:
    """Central registry of tools available to the agent."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def get_descriptions(self) -> str:
        """Generate formatted description string for the ReAct system prompt."""
        return "\n".join([f"- {t.name}: {t.description}" for t in self._tools.values()])

    def get_names(self) -> str:
        return ", ".join(self._tools.keys())
```

---

### Step 2: Safe Filesystem Tools (`src/tools/filesystem.py`)

Create `src/tools/filesystem.py` with this guided TODO:

```python
"""Secure filesystem tools with path traversal protection."""

from pathlib import Path


class SafeFileSystem:
    """Filesystem operations restricted to a specific root directory."""

    def __init__(self, root_dir: str | Path = ".") -> None:
        self.root = Path(root_dir).resolve()

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and verify it stays strictly inside self.root.

        # TODO: Implement safety check:
        # 1. target = (self.root / relative_path.strip()).resolve()
        # 2. Check if target.is_relative_to(self.root)
        # 3. If not, raise PermissionError(f"Path traversal detected: {relative_path}")
        # 4. Return target
        """
        raise NotImplementedError("Implement _resolve_safe_path")

    def read_file(self, path: str) -> str:
        """Read text from a file within the sandbox."""
        # TODO: Resolve safe path, check if it exists and is file, return content
        raise NotImplementedError("Implement read_file")

    def write_file(self, input_str: str) -> str:
        """Write content to a file. Expects format: 'path:::content'."""
        # TODO: Parse 'path:::content', resolve safe path, create parent directories, write text
        raise NotImplementedError("Implement write_file")

    def list_dir(self, path: str = ".") -> str:
        """List files and directories in path."""
        # TODO: List directory contents
        raise NotImplementedError("Implement list_dir")
```

<details>
<summary>👉 Click to reveal Answer Key for `src/tools/filesystem.py`</summary>

```python
"""Secure filesystem tools with path traversal protection."""

from pathlib import Path


class SafeFileSystem:
    """Filesystem operations restricted to a specific root directory."""

    def __init__(self, root_dir: str | Path = ".") -> None:
        self.root = Path(root_dir).resolve()

    def _resolve_safe_path(self, relative_path: str) -> Path:
        clean_path = relative_path.strip().lstrip("/\\")
        target = (self.root / clean_path).resolve()
        if not target.is_relative_to(self.root):
            raise PermissionError(
                f"Security violation: path '{relative_path}' escapes sandbox root '{self.root}'"
            )
        return target

    def read_file(self, path: str) -> str:
        target = self._resolve_safe_path(path)
        if not target.exists():
            return f"Error: File '{path}' does not exist."
        if not target.is_file():
            return f"Error: '{path}' is a directory, not a file."
        return target.read_text(encoding="utf-8")

    def write_file(self, input_str: str) -> str:
        if ":::" not in input_str:
            return "Error: write_file expects format 'path:::content'"
        path_part, content = input_str.split(":::", 1)
        target = self._resolve_safe_path(path_part)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to '{path_part}'."

    def list_dir(self, path: str = ".") -> str:
        target = self._resolve_safe_path(path)
        if not target.exists():
            return f"Error: Directory '{path}' does not exist."
        entries = []
        for item in sorted(target.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            entries.append(f"{prefix} {item.name}")
        return "\n".join(entries) if entries else "(Empty directory)"
```
</details>

---

### Step 3: Sandboxed Test Runner Tool (`src/tools/test_runner.py`)

Create `src/tools/test_runner.py`:

```python
"""Sandboxed test runner tool."""

import subprocess
from pathlib import Path


class TestRunnerTool:
    """Executes pytest suites within an isolated workspace directory."""

    def __init__(
        self, workspace_root: str | Path = ".", timeout_seconds: int = 30
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.timeout = timeout_seconds

    def run_tests(self, test_target: str = "") -> str:
        """Run pytest on the given target file or directory."""
        args = ["pytest", "-v"]
        if test_target.strip():
            # Ensure target stays within workspace
            target = (self.workspace_root / test_target.strip()).resolve()
            if not target.is_relative_to(self.workspace_root):
                return f"Error: Test target '{test_target}' outside workspace."
            args.append(str(target))

        try:
            result = subprocess.run(
                args,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = result.stdout or result.stderr
            status = "PASSED" if result.returncode == 0 else "FAILED"
            return f"Test Run [{status}] (Exit code: {result.returncode})\n\n{output}"
        except subprocess.TimeoutExpired:
            return (
                f"Error: Test suite execution timed out after {self.timeout}s."
            )
        except Exception as e:
            return f"Execution error: {type(e).__name__}: {e}"
```

---

## Checkpoint

Prove that Day 3 is complete:
1. Create `tests/test_tools.py` asserting that:
   - `SafeFileSystem` reads and writes files inside `./workspace`.
   - `SafeFileSystem` throws a `PermissionError` when trying to access `../../sensitive.txt`.
   - `TestRunnerTool` executes tests and captures stdout/stderr properly.
2. Run:
   ```powershell
   pytest -v tests/test_tools.py
   ruff check .
   ```

---

## Senior Interview Angle

### Q: "What security threat model do you consider when giving an LLM access to file and execution tools?"
**Senior Answer:**
> *"The threat model includes three major attack vectors:
> 1. **Path Traversal & Data Exfiltration:** Malicious prompts or hallucinated arguments can attempt directory escape (`../../etc/passwd` or SSH keys). We mitigate this by canonicalizing paths (`Path.resolve()`) and enforcing strict directory containment (`is_relative_to`).
> 2. **Arbitrary Code Execution & Shell Injection:** Invoking shell scripts with `shell=True` allows prompt injection payloads to chain commands (`test.py; curl evil.com`). We eliminate this by using direct parameter lists in `subprocess.run(shell=False)` with an allowlist of permitted commands.
> 3. **Denial of Service (DoS):** Infinite loops or blocking I/O can hang worker threads indefinitely. We enforce process timeouts (`timeout=30`), stdout truncation limits, and containerized memory limits."*

---

## Ready to Merge?

```powershell
git checkout -b feat/day3-tools-and-sandboxing
git add src/ tests/ docs/
git commit -m "feat(tools): implement safe filesystem and test runner tools with path jailing"
git push -u origin feat/day3-tools-and-sandboxing
```
