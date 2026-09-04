from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .analyzer import Analyzer
from .caveman import estimate_output_savings_pct, format_caveman_directive
from .config import AppConfig
from .context_pack import ContextPack, build_context_pack
from .easy_mode import _resolve_changed, _to_rel_paths, _tracked_count

SPECIALIST_ROLES = {
    "review": {
        "title": "Staff Engineer Code Reviewer",
        "command": "/review",
        "description": "Production bug hunter: audits race conditions, regressions, and incomplete error paths.",
        "directive": "Review ONLY the impacted code for race conditions, error handling, edge cases, and regressions. Output direct code fixes and minimal diffs.",
    },
    "plan": {
        "title": "Engineering Manager Architecture Gate",
        "command": "/plan",
        "description": "Lock data flow, call graphs, state machines, and edge cases with minimal token budget.",
        "directive": "Audit call graphs, failure modes, error paths, and test matrix on impacted files. Lock architecture before coding.",
    },
    "security": {
        "title": "Chief Security Officer (CSO)",
        "command": "/security",
        "description": "OWASP Top 10 + STRIDE threat modeling on the modified attack surface.",
        "directive": "Audit security vulnerabilities, injection risks, auth checks, and data leaks strictly on the modified blast radius.",
    },
    "qa": {
        "title": "QA Verification Lead",
        "command": "/qa",
        "description": "Targeted test verification and regression test suite generation for changed symbols.",
        "directive": "Write atomic regression tests for modified symbols. Verify edge cases and failure modes with minimal code.",
    },
    "ship": {
        "title": "Release Engineer",
        "command": "/ship",
        "description": "Pre-flight checks, test verification, and PR summary with minimal token footprint.",
        "directive": "Verify test suite, check coverage delta, and draft concise release PR with zero conversational filler.",
    },
    "debug": {
        "title": "Root Cause Debugger",
        "command": "/debug",
        "description": "Systematic root-cause debugging tracing callers and callee dependencies through AST.",
        "directive": "Trace data flow through caller-callee AST graph. Zero speculative fixes without verified root cause.",
    },
    "strategy": {
        "title": "Product & Founder Strategy",
        "command": "/strategy",
        "description": "Six forcing questions to reframe product before code; minimal context footprint.",
        "directive": "Challenge premises, ask the 6 forcing questions, recommend the narrowest wedge.",
    },
}


@dataclass(slots=True)
class SpecialistResult:
    role_key: str
    title: str
    command: str
    changed: list[str]
    impacted_count: int
    estimated_tokens: int
    baseline_tokens: int
    token_reduction_pct: float
    caveman: str
    caveman_savings_pct: float
    context_json_path: str
    prompt_md_path: str


def format_specialist_prompt(pack: ContextPack, role_key: str = "review", assistant: str = "claude") -> str:
    """Generate a specialized ReduceToken prompt tailored for specific engineering roles."""
    role_info = SPECIALIST_ROLES.get(role_key, SPECIALIST_ROLES["review"])
    out_savings = estimate_output_savings_pct(pack.caveman)
    caveman_block = format_caveman_directive(pack.caveman, assistant=assistant)

    lines: list[str] = []
    lines.append(f"# ⚡ ReduceToken Specialist Prompt ({assistant.upper()})")
    lines.append("")
    lines.append("> ⚡ **ReduceToken Optimization Engine**:")
    lines.append(f"> - **Role**: `{role_info['title']}` (`{role_info['command']}`)")
    lines.append(
        f"> - **Input Tokens**: ~{pack.estimated_tokens:,} tokens "
        f"(saved {pack.token_reduction_pct:.1f}% vs ~{pack.baseline_tokens:,} full repository tokens)"
    )
    lines.append(
        f"> - **Output Mode**: REDUCETOKEN DIRECT (estimated ~{out_savings:.0f}% output tokens saved & thinking monologue overridden)"
    )
    lines.append("")
    lines.append(caveman_block)
    lines.append("")
    lines.append(f"## 🎯 ReduceToken Mission: {role_info['title']} (`{role_info['command']}`)")
    lines.append(f"**Directive**: {role_info['directive']}")
    lines.append("")
    lines.append("### Execution Rules:")
    lines.append("1. Focus your analysis STRICTLY on the impacted blast-radius files and symbols provided below.")
    lines.append("2. Do NOT request or read the entire repository.")
    lines.append("3. Provide direct code diffs, findings, or test fixes without conversational filler.")
    lines.append("4. Deliver maximum signal with minimum tokens.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📦 Impacted Codebase Context (AST Blast Radius)")
    lines.append("")
    lines.append(f"**Changed Root Files ({len(pack.changed)}):**")
    for f in pack.changed:
        lines.append(f"- `{f}`")
    lines.append("")

    for item in pack.impacted:
        lines.append(f"### File: `{item.path}` (Distance: {item.distance})")
        if item.snippets:
            lines.append("```")
            for snippet in item.snippets:
                lines.append(snippet)
            lines.append("```")
        else:
            lines.append("*(No symbol definitions found or file excluded)*")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def run_specialist_flow(
    config: AppConfig,
    analyzer: Analyzer,
    role: str = "review",
    assistant: str = "claude",
    changed_inputs: list[str] | None = None,
    depth: int | None = None,
    max_files: int | None = None,
    max_tokens: int | None = None,
    out_dir: Path | None = None,
    caveman: str = "full",
) -> SpecialistResult:
    """Execute the ReduceToken Specialist workflow."""
    if _tracked_count(analyzer) == 0:
        analyzer.build_graph()

    changed = _resolve_changed(analyzer, changed_inputs or [])
    if not changed:
        raise ValueError(
            "No source files found to generate context. Make sure the project has supported source files."
        )

    analyzer.sync_files(changed)
    blast = analyzer.blast_radius(changed, max_depth=depth)
    changed_rel = _to_rel_paths(analyzer, changed)

    pack = build_context_pack(
        config=config,
        store=analyzer.store,
        blast=blast,
        changed=changed_rel,
        max_files=max_files,
        max_tokens=max_tokens,
        caveman=caveman,
    )

    role_key = role.lower().lstrip("/")
    # Support common aliases
    if role_key in ("eng-review", "plan-eng-review", "architecture"):
        role_key = "plan"
    elif role_key in ("cso", "audit"):
        role_key = "security"
    elif role_key in ("investigate", "trace"):
        role_key = "debug"
    elif role_key in ("office-hours", "ceo", "scope"):
        role_key = "strategy"

    if role_key not in SPECIALIST_ROLES:
        role_key = "review"

    prompt_text = format_specialist_prompt(pack, role_key=role_key, assistant=assistant)

    target_dir = out_dir if out_dir is not None else (Path(config.project_root) / ".token-reduce" / "assistant")
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = target_dir / f"specialist_{role_key}_context.json"
    md_path = target_dir / f"specialist_{role_key}_prompt.md"

    json_path.write_text(pack.to_json(), encoding="utf-8")
    md_path.write_text(prompt_text, encoding="utf-8")

    role_info = SPECIALIST_ROLES[role_key]

    return SpecialistResult(
        role_key=role_key,
        title=role_info["title"],
        command=role_info["command"],
        changed=pack.changed,
        impacted_count=len(pack.impacted),
        estimated_tokens=pack.estimated_tokens,
        baseline_tokens=pack.baseline_tokens,
        token_reduction_pct=pack.token_reduction_pct,
        caveman=pack.caveman,
        caveman_savings_pct=pack.caveman_savings_pct,
        context_json_path=str(json_path),
        prompt_md_path=str(md_path),
    )


def install_all_specialist_slash_commands(root: Path | str) -> list[str]:
    """Install all ReduceToken role-based slash commands into project and globally."""
    root_path = Path(root)
    installed: list[str] = []

    commands = {
        "review.md": (
            "---\n"
            "description: /review - Staff Engineer code review: find race conditions & production bugs on blast radius\n"
            "---\n"
            "Execute Staff Engineer review:\n"
            "1. Run `token-reduce review --copy --print` to generate blast radius for the active change.\n"
            "2. Audit race conditions, edge-case regressions, and missing error handling strictly on impacted files.\n"
            "3. Output direct code fixes and minimal diffs with zero conversational filler.\n"
        ),
        "plan.md": (
            "---\n"
            "description: /plan - Engineering Manager architecture gate: lock call graph & failure modes\n"
            "---\n"
            "Execute Architecture & Planning gate:\n"
            "1. Run `token-reduce plan --copy --print` to generate call-graph dependencies.\n"
            "2. Lock data flow, error paths, state machines, and test matrix before modifying code.\n"
            "3. Save maximum tokens by reviewing only caller-callee blast radius.\n"
        ),
        "security.md": (
            "---\n"
            "description: /security - CSO threat model: OWASP + injection + auth audit on changed attack surface\n"
            "---\n"
            "Execute CSO Security audit:\n"
            "1. Run `token-reduce security --copy --print` to inspect the modified attack surface.\n"
            "2. Audit injection risks, privilege escalation, authentication checks, and secrets.\n"
            "3. Provide concrete exploit scenarios and direct patch diffs.\n"
        ),
        "qa.md": (
            "---\n"
            "description: /qa - QA Lead: generate regression tests and verify edge cases on modified symbols\n"
            "---\n"
            "Execute QA verification:\n"
            "1. Run `token-reduce qa --copy --print`.\n"
            "2. Write atomic regression tests for all modified symbols.\n"
            "3. Verify edge cases and failure modes with minimal test code.\n"
        ),
        "ship.md": (
            "---\n"
            "description: /ship - Release Engineer: pre-flight checks, test verification, and PR summary\n"
            "---\n"
            "Execute Release Engineer workflow:\n"
            "1. Run `token-reduce ship --copy --print`.\n"
            "2. Run all automated tests, verify test delta, and draft concise release PR notes.\n"
        ),
        "debug.md": (
            "---\n"
            "description: /debug - Root Cause Debugger: trace data flow & callers through AST graph\n"
            "---\n"
            "Execute Root Cause debugging:\n"
            "1. Run `token-reduce debug --copy --print`.\n"
            "2. Trace caller-callee call paths through the AST graph. Zero speculative fixes without verified root cause.\n"
        ),
        "strategy.md": (
            "---\n"
            "description: /strategy - Founder Strategy: 6 forcing questions to reframe scope before code\n"
            "---\n"
            "Execute Founder Strategy session:\n"
            "1. Run `token-reduce strategy --copy --print`.\n"
            "2. Challenge premises, reframe the product, and recommend the narrowest wedge to ship.\n"
        ),
    }

    # Remove any old gstack-*.md commands
    local_dir = root_path / ".claude" / "commands"
    local_dir.mkdir(parents=True, exist_ok=True)
    for old_file in local_dir.glob("gstack-*.md"):
        try:
            old_file.unlink()
        except OSError:
            pass

    for filename, content in commands.items():
        (local_dir / filename).write_text(content, encoding="utf-8")
        cmd_name = "/" + filename.replace(".md", "")
        if cmd_name not in installed:
            installed.append(cmd_name)

    # Try install globally
    global_dir = Path.home() / ".claude" / "commands"
    if global_dir != local_dir:
        try:
            global_dir.mkdir(parents=True, exist_ok=True)
            for old_file in global_dir.glob("gstack-*.md"):
                try:
                    old_file.unlink()
                except OSError:
                    pass
            for filename, content in commands.items():
                (global_dir / filename).write_text(content, encoding="utf-8")
        except (PermissionError, OSError):
            pass

    return installed
