"""Secure filesystem tools with path traversal protection."""

from pathlib import Path


class SafeFileSystem:
    """Filesystem operations restricted to a specific root directory."""

    def __init__(self, root_dir: str | Path = ".") -> None:
        self.root = Path(root_dir).resolve()

    def _resolve_safe_path(self, relative_path: str) -> Path:
        """Resolve path and verify it says strictly inside self.root sandbox."""
        clean_path = relative_path.strip().lstrip("/\\")
        target = (self.root / clean_path).resolve()

        if not target.is_relative_to(self.root):
            raise PermissionError(
                f"Security violation: path '{relative_path}' escapes sandbox root '{self.root}'"
            )
        return target

    def read_file(self, path: str) -> str:
        """Read text from a file within the sandbox"""
        target = self._resolve_safe_path(path)
        if not target.exists():
            return f"Error: File '{path}' does not exist."
        if not target.is_file():
            return f"Error: '{path}' is a directory, not a file."
        return target.read_text(encoding="utf-8")

    def write_file(self, input_str: str) -> str:
        """Write content to a file. Expects format: 'path:::content'."""
        if ":::" not in input_str:
            return "Error: write_file expects format 'path:::content'"

        path_part, content = input_str.split(":::", 1)
        target = self._resolve_safe_path(path_part)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to '{path_part}'."

    def list_dir(self, path: str = ".") -> str:
        """List files and directories in path within the sandbox."""
        target = self._resolve_safe_path(path)
        if not target.exists():
            return f"Error: Directory '{path}' does not exist."

        entries = []
        for item in sorted(target.iterdir()):
            prefix = "[DIR] " if item.is_dir() else "[FILE]"
            entries.append(f"{prefix} {item.name}")
        return "\n".join(entries) if entries else "(Empty directory)"
