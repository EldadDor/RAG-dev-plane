"""Best-effort Git provenance for indexed workplace repositories."""

from __future__ import annotations

from pathlib import Path
import subprocess


def get_repository_metadata(source_path: str) -> dict:
    path = Path(source_path).resolve()
    cwd = path.parent if path.is_file() else path

    def git(*args: str) -> str | None:
        try:
            result = subprocess.run(
                ["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=2, check=True
            )
            return result.stdout.strip() or None
        except (FileNotFoundError, subprocess.SubprocessError):
            return None

    root_text = git("rev-parse", "--show-toplevel")
    if not root_text:
        return {}
    root = Path(root_text)
    try:
        relative_path = str(path.relative_to(root))
    except ValueError:
        relative_path = path.name
    return {
        "repository": root.name,
        "repository_path": str(root),
        "repository_relative_path": relative_path,
        "git_branch": git("branch", "--show-current"),
        "git_commit": git("rev-parse", "HEAD"),
    }
