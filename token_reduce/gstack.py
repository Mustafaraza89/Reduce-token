from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .analyzer import Analyzer
from .caveman import estimate_output_savings_pct, format_caveman_directive
from .config import AppConfig
from .context_pack import ContextPack, build_context_pack
from .easy_mode import _resolve_changed, _to_rel_paths, _tracked_count

GSTACK_SKILLS = {
    "office-hours": {
        "role": "YC Office Hours / Founder Strategy",
        "description": "Six forcing questions to reframe product before code; minimal context footprint.",
        "directive": "Challenge premises, ask the 6 forcing questions, recommend narrowest wedge.",
    },
    "plan-ceo-review": {
        "role": "CEO / Product Scope Reviewer",
        "description": "Evaluate scope (expansion vs reduction) on the minimal impacted feature set.",
        "directive": "Evaluate product leverage and scope bounds on impacted components.",
    },
    "plan-eng-review": {
        "role": "Engineering Manager / Architecture Gate",
        "description": "Lock data flow, call graphs, state machines, and edge cases from AST blast radius.",
        "directive": "Audit call graphs, failure modes, error paths, and test matrix on impacted files.",
    },
    "review": {
        "role": "Staff Engineer / Production Bug Hunter",
        "description": "Find edge-case bugs, completeness gaps, and simplification opportunities on blast radius.",
        "directive": "Review only impacted code for race conditions, error handling, regressions. Output direct code fixes.",
    },
    "investigate": {
        "role": "Root Cause Debugger",
        "description": "Systematic root-cause debugging tracing callers and callee dependencies.",
        "directive": "Trace data flow through caller-callee AST graph. Zero fixes without verified root cause.",
    },
    "cso": {
        "role": "Chief Security Officer",
        "description": "OWASP Top 10 + STRIDE threat modeling on the modified attack surface.",
        "directive": "Audit security vulnerabilities and auth checks only on the modified blast radius.",
    },
    "qa": {
        "role": "QA Lead",
        "description": "Targeted test verification and regression test suite generation for changed symbols.",
        "directive": "Write regression tests for modified symbols. Verify atomic test cases.",
    },
    "ship": {
        "role": "Release Engineer",
        "description": "Pre-flight checks, test verification, and PR summary with minimal token footprint.",
        "directive": "Verify test suite, check coverage delta, and draft concise release PR.",
    },
    "autoplan": {
        "role": "Full Sprint Review Pipeline",
        "description": "Chained CEO -> Design -> DX -> Eng review powered by AST blast radius.",
        "directive": "Execute full review pipeline with strict token budgeting and zero conversational fluff.",
    },
}


@dataclass(slots=True)
class GstackResult:
    skill: str
    role: str
    changed: list[str]
    impacted_count: int
    estimated_tokens: int
    baseline_tokens: int
    token_reduction_pct: float
    caveman: str
    caveman_savings_pct: float
    context_json_path: str
    prompt_md_path: str


def format_gstack_prompt(pack: ContextPack, skill: str = "review", assistant: str = "claude") -> str:
    """Generate a combined gstack + ReduceToken prompt for Claude / Gemini / Cursor."""
    skill_info = GSTACK_SKILLS.get(skill, GSTACK_SKILLS["review"])
    out_savings = estimate_output_savings_pct(pack.caveman)
    caveman_block = format_caveman_directive(pack.caveman, assistant=assistant)

    lines: list[str] = []
    lines.append(f"# ⚡ ReduceToken + gstack Engine ({assistant.upper()})")
    lines.append("")
    lines.append("> ⚡ **ReduceToken Optimization Engine**:")
    lines.append(f"> - **gstack Specialist**: `{skill_info['role']}` (`/{skill}`)")
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
    lines.append(f"## 🎯 gstack Task: {skill_info['role']} (`/{skill}`)")
    lines.append(f"**Specialist Directive**: {skill_info['directive']}")
    lines.append("")
    lines.append("### Guidelines for this Review:")
    lines.append("1. Focus your analysis STRICTLY on the impacted blast-radius files and symbols provided below.")
    lines.append("2. Do NOT request or read the entire repository.")
    lines.append("3. Provide direct code diffs, findings, or test fixes without conversational filler.")
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


def run_gstack_flow(
    config: AppConfig,
    analyzer: Analyzer,
    skill: str = "review",
    assistant: str = "claude",
    changed_inputs: list[str] | None = None,
    depth: int | None = None,
    max_files: int | None = None,
    max_tokens: int | None = None,
    out_dir: Path | None = None,
    caveman: str = "full",
) -> GstackResult:
    """Execute the ReduceToken + gstack combined workflow."""
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

    skill_key = skill.lower().lstrip("/")
    if skill_key not in GSTACK_SKILLS:
        skill_key = "review"

    prompt_text = format_gstack_prompt(pack, skill=skill_key, assistant=assistant)

    target_dir = out_dir if out_dir is not None else (Path(config.project_root) / ".token-reduce" / "assistant")
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = target_dir / f"gstack_{skill_key}_context.json"
    md_path = target_dir / f"gstack_{skill_key}_prompt.md"

    json_path.write_text(pack.to_json(), encoding="utf-8")
    md_path.write_text(prompt_text, encoding="utf-8")

    skill_info = GSTACK_SKILLS[skill_key]

    return GstackResult(
        skill=skill_key,
        role=skill_info["role"],
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


def install_gstack_integrations(root: Path | str) -> list[str]:
    """Install gstack + ReduceToken bridge slash commands into project and globally."""
    root_path = Path(root)
    installed: list[str] = []

    commands = {
        "gstack-reduce.md": (
            "---\n"
            "description: /gstack-reduce - Optimize gstack sprint skills (/plan-eng-review, /review, /ship) with ReduceToken blast radius\n"
            "---\n"
            "Execute gstack sprint task with ReduceToken token reduction:\n"
            "1. Run `token-reduce gstack --skill review --copy --print` to generate blast radius for the active change.\n"
            "2. In gstack skills (/plan-eng-review, /review, /cso, /ship, /investigate), analyze ONLY the impacted context.\n"
            "3. Apply ReduceToken Direct rules: zero pleasantries, direct diffs, maximum tokens saved.\n"
        ),
        "gstack-review.md": (
            "---\n"
            "description: /gstack-review - Staff Engineer code review on exact blast-radius diffs\n"
            "---\n"
            "Execute Staff Engineer review:\n"
            "Run `token-reduce gstack --skill review --copy --print`.\n"
            "Audit race conditions, regressions, and incomplete error paths in the impacted files only.\n"
        ),
        "gstack-plan.md": (
            "---\n"
            "description: /gstack-plan - Lock architecture & failure modes with AST blast radius\n"
            "---\n"
            "Execute Eng Review planning:\n"
            "Run `token-reduce gstack --skill plan-eng-review --copy --print`.\n"
            "Lock call-graph data flow, state machines, and test matrix with minimal token budget.\n"
        ),
    }

    # Install locally
    local_dir = root_path / ".claude" / "commands"
    local_dir.mkdir(parents=True, exist_ok=True)
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
            for filename, content in commands.items():
                (global_dir / filename).write_text(content, encoding="utf-8")
        except (PermissionError, OSError):
            pass
    return installed

