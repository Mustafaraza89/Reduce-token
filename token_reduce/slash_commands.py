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

    return [
        "/reduce",
        "/reducetoken",
        "/plan",
        "/review",
        "/security",
        "/qa",
        "/ship",
        "/debug",
        "/strategy",
    ]


def _write_claude_commands(cmd_dir: Path) -> None:
    cmd_dir.mkdir(parents=True, exist_ok=True)

    # Clean up obsolete commands
    for old_name in ("caveman.md", "gstack-reduce.md", "gstack-review.md", "gstack-plan.md"):
        old_file = cmd_dir / old_name
        if old_file.exists():
            try:
                old_file.unlink()
            except OSError:
                pass

    reduce_cmd = cmd_dir / "reduce.md"
    reduce_cmd.write_text(
        """---
description: /reduce - Universal ReduceToken context optimizer before broad code changes
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

    review_cmd = cmd_dir / "review.md"
    review_cmd.write_text(
        """---
description: /review - Staff Engineer code review: find race conditions & production bugs on blast radius
---
Execute Staff Engineer review:
1. Run `token-reduce review --copy --print` to generate blast radius for current changes.
2. Audit race conditions, edge-case regressions, and missing error handling strictly on impacted files.
3. Output direct code fixes and minimal diffs with zero conversational filler.
""".strip() + "\n",
        encoding="utf-8",
    )

    plan_cmd = cmd_dir / "plan.md"
    plan_cmd.write_text(
        """---
description: /plan - Engineering Manager architecture gate: lock call graph & failure modes
---
Execute Architecture & Planning gate:
1. Run `token-reduce plan --copy --print` to generate call-graph dependencies.
2. Lock data flow, error paths, state machines, and test matrix before modifying code.
3. Save maximum tokens by reviewing only caller-callee blast radius.
""".strip() + "\n",
        encoding="utf-8",
    )

    security_cmd = cmd_dir / "security.md"
    security_cmd.write_text(
        """---
description: /security - CSO threat model: OWASP + injection + auth audit on changed attack surface
---
Execute CSO Security audit:
1. Run `token-reduce security --copy --print` to inspect the modified attack surface.
2. Audit injection risks, privilege escalation, authentication checks, and secrets.
3. Provide concrete exploit scenarios and direct patch diffs.
""".strip() + "\n",
        encoding="utf-8",
    )

    qa_cmd = cmd_dir / "qa.md"
    qa_cmd.write_text(
        """---
description: /qa - QA Lead: generate regression tests and verify edge cases on modified symbols
---
Execute QA verification:
1. Run `token-reduce qa --copy --print`.
2. Write atomic regression tests for all modified symbols.
3. Verify edge cases and failure modes with minimal test code.
""".strip() + "\n",
        encoding="utf-8",
    )

    ship_cmd = cmd_dir / "ship.md"
    ship_cmd.write_text(
        """---
description: /ship - Release Engineer: pre-flight checks, test verification, and PR summary
---
Execute Release Engineer workflow:
1. Run `token-reduce ship --copy --print`.
2. Run all automated tests, verify test delta, and draft concise release PR notes.
""".strip() + "\n",
        encoding="utf-8",
    )

    debug_cmd = cmd_dir / "debug.md"
    debug_cmd.write_text(
        """---
description: /debug - Root Cause Debugger: trace data flow & callers through AST graph
---
Execute Root Cause debugging:
1. Run `token-reduce debug --copy --print`.
2. Trace caller-callee call paths through the AST graph. Zero speculative fixes without verified root cause.
""".strip() + "\n",
        encoding="utf-8",
    )

    strategy_cmd = cmd_dir / "strategy.md"
    strategy_cmd.write_text(
        """---
description: /strategy - Founder Strategy: 6 forcing questions to reframe scope before code
---
Execute Founder Strategy session:
1. Run `token-reduce strategy --copy --print`.
2. Challenge premises, reframe the product, and recommend the narrowest wedge to ship.
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