from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import AppConfig


@dataclass(slots=True)
class InstallResult:
    configured_tools: list[str]
    hooks_installed: list[str]
    watcher_started: bool
    notes: list[str]


def install_integrations(config: AppConfig, start_watcher: bool = True) -> InstallResult:
    root = Path(config.project_root)
    configured_tools: list[str] = []
    hooks_installed: list[str] = []
    notes: list[str] = []

    _ensure_state(root)

    if _configure_cursor(root):
        configured_tools.append("cursor")
    if _configure_claude(root):
        configured_tools.append("claude")

    hook_names = _install_git_hooks(root)
    hooks_installed.extend(hook_names)

    watcher_started = False
    if start_watcher:
        watcher_started = _start_watcher(root)
        if not watcher_started:
            notes.append("Watcher already running or could not be started.")

    if not configured_tools:
        notes.append("No known assistant config found; fallback setup still installed (hooks + graph state).")

    return InstallResult(
        configured_tools=configured_tools,
        hooks_installed=hooks_installed,
        watcher_started=watcher_started,
        notes=notes,
    )


def _ensure_state(root: Path) -> None:
    (root / ".token-reduce").mkdir(parents=True, exist_ok=True)


def _configure_cursor(root: Path) -> bool:
    cursor_dir = root / ".cursor"
    vscode_dir = root / ".vscode"
    if not cursor_dir.exists() and not vscode_dir.exists():
        return False

    rules_dir = cursor_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    rule_path = rules_dir / "token-reduce-context.mdc"
    content = """---
description: Use Token Reduce context workflow before large codebase tasks
globs:
alwaysApply: false
---
Before deep edits, run:
- token-reduce sync --worktree
- token-reduce context --changed <paths>
Then prioritize only the impacted files in context.
"""
    rule_path.write_text(content, encoding="utf-8")
    return True


def _configure_claude(root: Path) -> bool:
    claude_md = root / "CLAUDE.md"
    claude_dir = root / ".claude"
    if not claude_md.exists() and not claude_dir.exists():
        return False

    section = """
## Token Reduce context workflow
Before editing broad areas, run:
- `token-reduce sync --worktree`
- `token-reduce context --changed <paths>`
Use the impacted set instead of loading the full repository.
""".strip()

    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8", errors="replace")
        if "## Token Reduce context workflow" not in text:
            claude_md.write_text(f"{text.rstrip()}\n\n{section}\n", encoding="utf-8")
    else:
        claude_md.write_text(f"{section}\n", encoding="utf-8")
    return True


def _install_git_hooks(root: Path) -> list[str]:
    git_dir = root / ".git"
    hooks: list[str] = []
    if not git_dir.exists():
        return hooks

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    post_commit = hooks_dir / "post-commit"
    post_merge = hooks_dir / "post-merge"

    for hook_path, mode in ((post_commit, "head"), (post_merge, "worktree")):
        script = _hook_script(mode)
        hook_path.write_text(script, encoding="utf-8")
        os.chmod(hook_path, 0o755)
        hooks.append(hook_path.name)

    return hooks


def _hook_script(mode: str) -> str:
    sync_flag = "--git-head" if mode == "head" else "--worktree"
    return f"""#!/bin/sh
if command -v token-reduce >/dev/null 2>&1; then
  REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
  if [ -n "$REPO_ROOT" ]; then
    token-reduce sync --project-root "$REPO_ROOT" {sync_flag} >/dev/null 2>&1
  fi
fi
"""


def _start_watcher(root: Path) -> bool:
    state = root / ".token-reduce"
    pid_path = state / "watch.pid"
    log_path = state / "watch.log"

    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return False
        except (ValueError, ProcessLookupError, PermissionError):
            pid_path.unlink(missing_ok=True)

    command = [
        "nohup",
        "token-reduce",
        "watch",
        "--project-root",
        str(root),
    ]

    with log_path.open("ab") as out:
        proc = subprocess.Popen(command, cwd=root, stdout=out, stderr=out)

    pid_path.write_text(str(proc.pid), encoding="utf-8")
    return True
