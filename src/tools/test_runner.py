"""Sandboxed test runner tool executing pytest within isolated boundaries."""

import subprocess
import sys
from pathlib import Path


class TestRunnerTool:
    """Executes pytest suites within an isolated workspace directory."""

    __test__ = False  # Tells pytest not to confuse this with a test suite

    def __init__(self, workspace_root: str | Path = ".", timeout_seconds: int = 30) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.timeout = timeout_seconds

    def run_tests(self, test_target: str = "") -> str:
        """Run pytest on the given target file or directory within workspace."""
        args = [sys.executable, "-m", "pytest", "-v"]

        if test_target.strip():
            # Ensure target stays strictly inside the workspace boundary
            target = (self.workspace_root / test_target.strip()).resolve()
            if not target.is_relative_to(self.workspace_root):
                return f"Error: Test target '{test_target}' outside workspace boundary."
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
            return f"Error: Test suite execution timed out after {self.timeout}s."
        except Exception as e:
            return f"Execution error: {type(e).__name__}: {e}"
