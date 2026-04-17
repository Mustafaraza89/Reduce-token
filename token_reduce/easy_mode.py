from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer import Analyzer
from .config import AppConfig
from .context_pack import ContextPack, build_context_pack


ASSISTANT_CHOICES = ("generic", "codex", "claude", "gemini", "chatgpt", "antigravity")


@dataclass(slots=True)
class UseResult:
    assistant: str
    changed: list[str]
    graph_built: bool
    sync_summary: dict[str, int]
    context_json_path: str
    prompt_md_path: str


def run_use_flow(
    config: AppConfig,
    analyzer: Analyzer,
    assistant: str,
    changed_inputs: list[str],
    depth: int | None,
    max_files: int | None,
    out_dir: Path | None,
) -> UseResult:
    graph_built = False
    if _tracked_count(analyzer) == 0:
        analyzer.build_graph()
        graph_built = True

    changed = _resolve_changed(analyzer, changed_inputs)
    if not changed:
        raise ValueError(
            "No changed files found. Pass --changed <files> or make sure git worktree has changes before running `token-reduce use`."
        )

    sync_summary = analyzer.sync_files(changed)
    blast = analyzer.blast_radius(changed, max_depth=depth)
    changed_rel = _to_rel_paths(analyzer, changed)
    pack = build_context_pack(config, analyzer.store, blast, changed_rel, max_files=max_files)

    output_root = out_dir if out_dir is not None else (Path(config.project_root) / ".token-reduce" / "assistant")
    output_root.mkdir(parents=True, exist_ok=True)

    context_json_path = output_root / f"context-{assistant}.json"
    prompt_md_path = output_root / f"prompt-{assistant}.md"

    context_json_path.write_text(pack.to_json(), encoding="utf-8")
    prompt_md_path.write_text(pack.to_markdown(assistant=assistant), encoding="utf-8")

    return UseResult(
        assistant=assistant,
        changed=changed_rel,
        graph_built=graph_built,
        sync_summary=sync_summary,
        context_json_path=str(context_json_path),
        prompt_md_path=str(prompt_md_path),
    )


def _tracked_count(analyzer: Analyzer) -> int:
    row = analyzer.store.conn.execute("SELECT COUNT(*) AS count FROM files").fetchone()
    return int(row["count"]) if row else 0


def _resolve_changed(analyzer: Analyzer, changed_inputs: list[str]) -> list[Path]:
    if changed_inputs:
        return [Path(item) if Path(item).is_absolute() else analyzer.project_root / item for item in changed_inputs]

    candidates = analyzer.changed_files_from_worktree()
    if candidates:
        return candidates

    return analyzer.changed_files_from_head()


def _to_rel_paths(analyzer: Analyzer, changed: list[Path]) -> list[str]:
    rels: list[str] = []
    seen: set[str] = set()
    for item in changed:
        resolved = item.resolve()
        try:
            rel = str(resolved.relative_to(analyzer.project_root)).replace("\\", "/")
        except ValueError:
            continue
        if rel in seen:
            continue
        seen.add(rel)
        rels.append(rel)
    return rels
