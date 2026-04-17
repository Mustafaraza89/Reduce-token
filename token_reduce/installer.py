from __future__ import annotations

import os
import subprocess
import sys
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

    hook_names, hook_notes = _install_git_hooks(root)
    hooks_installed.extend(hook_names)
    notes.extend(hook_notes)

    watcher_started = False
    if start_watcher:
        watcher_started, watcher_note = _start_watcher(root)
        if watcher_note:
            notes.append(watcher_note)
        if not watcher_started and not watcher_note:
            notes.append("Watcher was not started.")

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


def _install_git_hooks(root: Path) -> tuple[list[str], list[str]]:
    git_dir = root / ".git"
    hooks: list[str] = []
    notes: list[str] = []
    if not git_dir.exists():
        return hooks, notes

    hooks_dir = git_dir / "hooks"
    try:
        hooks_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return hooks, [f"Permission denied creating hooks dir: {hooks_dir}"]

    post_commit = hooks_dir / "post-commit"
    post_merge = hooks_dir / "post-merge"

    for hook_path, mode in ((post_commit, "head"), (post_merge, "worktree")):
        script = _hook_script(mode)
        try:
            hook_path.write_text(script, encoding="utf-8")
            os.chmod(hook_path, 0o755)
            hooks.append(hook_path.name)
        except PermissionError:
            notes.append(f"Permission denied writing git hook: {hook_path}")
        except OSError as err:
            notes.append(f"Failed to install git hook {hook_path.name}: {err}")

    return hooks, notes


def _hook_script(mode: str) -> str:
    sync_flag = "--git-head" if mode == "head" else "--worktree"
    return f"""#!/bin/sh
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "$REPO_ROOT" ]; then
  if command -v token-reduce >/dev/null 2>&1; then
    token-reduce sync --project-root "$REPO_ROOT" {sync_flag} >/dev/null 2>&1
  elif command -v python3 >/dev/null 2>&1; then
    python3 -m token_reduce sync --project-root "$REPO_ROOT" {sync_flag} >/dev/null 2>&1
  fi
fi
"""


def _start_watcher(root: Path) -> tuple[bool, str | None]:
    state = root / ".token-reduce"
    pid_path = state / "watch.pid"
    log_path = state / "watch.log"

    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            return False, "Watcher already running."
        except (ValueError, ProcessLookupError, PermissionError):
            pid_path.unlink(missing_ok=True)

    command = [
        sys.executable,
        "-m",
        "token_reduce",
        "watch",
        "--project-root",
        str(root),
    ]

    try:
        with log_path.open("ab") as out:
            proc = subprocess.Popen(command, cwd=root, stdout=out, stderr=out, start_new_session=True)
        pid_path.write_text(str(proc.pid), encoding="utf-8")
        return True, None
    except FileNotFoundError:
        return False, "Python executable not found while starting watcher."
    except PermissionError:
        return False, f"Permission denied starting watcher/logging under: {state}"
    except OSError as err:
        return False, f"Failed to start watcher: {err}"
