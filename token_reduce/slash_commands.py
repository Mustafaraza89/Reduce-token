from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SlashCommandInstallResult:
    claude_commands: list[str]
    cursor_rules: list[str]
    gemini_configured: bool
    vscode_configured: bool
    copilot_configured: bool
    notes: list[str]


def install_all_slash_commands(root: Path) -> SlashCommandInstallResult:
    claude_cmds = _install_claude_commands(root)
    cursor_rules = _install_cursor_rules(root)
    gemini_ok = _install_gemini_rules(root)
    vscode_ok = _install_vscode_tasks(root)
    copilot_ok = _install_copilot_instructions(root)

    notes = []
    if claude_cmds:
        notes.append(f"Claude Code slash commands: {', '.join(claude_cmds)}")
    if cursor_rules:
        notes.append(f"Cursor rules: {', '.join(cursor_rules)}")
    if gemini_ok:
        notes.append("Gemini / Antigravity GEMINI.md configured.")
    if vscode_ok:
        notes.append("VS Code tasks.json configured.")
    if copilot_ok:
        notes.append("GitHub Copilot instructions configured.")

    return SlashCommandInstallResult(
        claude_commands=claude_cmds,
        cursor_rules=cursor_rules,
        gemini_configured=gemini_ok,
        vscode_configured=vscode_ok,
        copilot_configured=copilot_ok,
        notes=notes,
    )


def _install_claude_commands(root: Path) -> list[str]:
    """Install Claude slash commands into both project-local AND global ~/.claude/commands/.

    Global install makes /reduce and /reducetoken available in ALL projects on the machine.
    Local install is a fallback for environments that only look in the project dir.
    """
    # Always install locally in the project dir
    local_cmd_dir = root / ".claude" / "commands"
    _write_claude_commands(local_cmd_dir)

    # Try global install into ~/.claude/commands/ (works in every project)
    global_cmd_dir = Path.home() / ".claude" / "commands"
    if global_cmd_dir != local_cmd_dir:
        try:
            _write_claude_commands(global_cmd_dir)
        except (PermissionError, OSError):
            # Graceful fallback: global install failed (sandbox / no home dir access)
            pass

    return ["/reduce", "/reducetoken", "/gstack-reduce"]


def _write_claude_commands(cmd_dir: Path) -> None:
    cmd_dir.mkdir(parents=True, exist_ok=True)

    # Remove old caveman.md if present
    old_caveman = cmd_dir / "caveman.md"
    if old_caveman.exists():
        try:
            old_caveman.unlink()
        except OSError:
            pass

    reduce_cmd = cmd_dir / "reduce.md"
    reduce_cmd.write_text(
        """---
description: /reduce - Run ReduceToken context optimizer before broad code changes
---
Execute `/reduce` workflow:
Run `token-reduce use --caveman full --copy --print` to generate blast-radius context.
Prioritize only the impacted files and apply ReduceToken direct rules (zero conversational filler, direct diffs).
""".strip() + "\n",
        encoding="utf-8",
    )

    reducetoken_cmd = cmd_dir / "reducetoken.md"
    reducetoken_cmd.write_text(
        """---
description: /reducetoken - Activate ReduceToken Direct Mode: zero filler, override thinking, instant code
---
Execute `/reducetoken` mode:
1. Zero conversational filler (no "Sure!", no "Certainly!", no "I would be happy to help").
2. Jump directly to code changes / diffs.
3. Speak in brief direct fragments: Deliver maximum signal with minimum tokens.
""".strip() + "\n",
        encoding="utf-8",
    )

    gstack_cmd = cmd_dir / "gstack-reduce.md"
    gstack_cmd.write_text(
        """---
description: /gstack-reduce - Optimize gstack sprint skills (/plan-eng-review, /review, /ship) with ReduceToken blast radius
---
Execute gstack workflow with ReduceToken optimization:
1. Run `token-reduce gstack --skill review --copy --print` to generate blast radius for the active change.
2. In gstack skills (/plan-eng-review, /review, /cso, /ship, /investigate), analyze ONLY the impacted context.
3. Apply ReduceToken Direct rules: zero pleasantries, direct diffs, maximum tokens saved.
""".strip() + "\n",
        encoding="utf-8",
    )




def _install_cursor_rules(root: Path) -> list[str]:
    rules_dir = root / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    old_rule = rules_dir / "token-reduce-caveman.mdc"
    if old_rule.exists():
        try:
            old_rule.unlink()
        except OSError:
            pass

    rule_path = rules_dir / "reduce-token.mdc"
    rule_path.write_text(
        """---
description: ReduceToken: Blast-radius context and direct code-first answers
globs:
alwaysApply: true
---
# ReduceToken Optimization

## 1. Input Context
Before broad edits across the codebase, run:
- `token-reduce /`
- `token-reduce context --changed <paths> --max-tokens 2000`
Use only the impacted context set instead of reading full repository files.

## 2. Output Direct Directive
- Override conversational monologues and thinking preambles.
- Zero pleasantries (never say "Sure!", "Certainly!", "I can help with that").
- Code-first: output the exact diff or implementation immediately.
- Deliver maximum signal with minimum tokens.
""".strip() + "\n",
        encoding="utf-8",
    )

    return ["reduce-token.mdc"]


def _install_gemini_rules(root: Path) -> bool:
    gemini_md = root / "GEMINI.md"
    section = """
## ⚡ ReduceToken Mode
Before editing broad codebase areas:
1. Run `token-reduce / --assistant gemini`
2. Follow ReduceToken rules:
   - Override conversational monologues and thinking intros.
   - Zero filler (no "Sure!", "Certainly!").
   - Output direct code changes and commands immediately.
   - Save maximum tokens.
""".strip()

    if gemini_md.exists():
        text = gemini_md.read_text(encoding="utf-8", errors="replace")
        if "Token Reduce & Caveman Mode" in text:
            text = text.replace("Token Reduce & Caveman Mode", "ReduceToken Mode")
            text = text.replace("Follow Caveman rules:", "Follow ReduceToken rules:")
            text = text.replace("token-reduce use --assistant gemini --caveman full", "token-reduce / --assistant gemini")
            gemini_md.write_text(text, encoding="utf-8")
        elif "ReduceToken Mode" not in text:
            gemini_md.write_text(f"{text.rstrip()}\n\n{section}\n", encoding="utf-8")
    else:
        gemini_md.write_text(f"{section}\n", encoding="utf-8")
    return True


def _install_vscode_tasks(root: Path) -> bool:
    vscode_dir = root / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    tasks_path = vscode_dir / "tasks.json"
    tasks_content = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "ReduceToken: Direct Context (/reduce)",
                "type": "shell",
                "command": "token-reduce / --assistant generic",
                "problemMatcher": [],
            },
            {
                "label": "ReduceToken: Build Graph",
                "type": "shell",
                "command": "token-reduce build",
                "problemMatcher": [],
            },
            {
                "label": "ReduceToken: Status",
                "type": "shell",
                "command": "token-reduce status",
                "problemMatcher": [],
            },
        ],
    }
    tasks_path.write_text(json.dumps(tasks_content, indent=2), encoding="utf-8")
    return True


def _install_copilot_instructions(root: Path) -> bool:
    github_dir = root / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)
    copilot_path = github_dir / "copilot-instructions.md"

    content = """# ReduceToken Optimization Instructions
- **ReduceToken Direct Active**: Be ultra-concise, direct, and code-first.
- Do not output polite filler ("Certainly!", "I can help with that").
- When modifying code, use the minimal impacted context set.
""".strip() + "\n"

    copilot_path.write_text(content, encoding="utf-8")
    return True