from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import AppConfig
from .graph_store import GraphStore


@dataclass(slots=True)
class ContextFile:
    path: str
    distance: int
    snippets: list[str]


@dataclass(slots=True)
class ContextPack:
    changed: list[str]
    impacted: list[ContextFile]

    def to_json(self) -> str:
        return json.dumps(
            {
                "changed": self.changed,
                "impacted": [asdict(item) for item in self.impacted],
            },
            indent=2,
        )

    def to_markdown(self, assistant: str = "generic") -> str:
        header = _assistant_header(assistant)
        lines: list[str] = []
        lines.append(f"# Token Reduce Prompt ({assistant})")
        lines.append("")
        lines.append(header)
        lines.append("")
        lines.append("## Changed Files")
        if self.changed:
            for item in self.changed:
                lines.append(f"- `{item}`")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Impacted Context")
        if not self.impacted:
            lines.append("- (none)")
        for context_file in self.impacted:
            lines.append(f"### `{context_file.path}` (distance={context_file.distance})")
            for snippet in context_file.snippets:
                lines.append("```text")
                lines.append(snippet)
                lines.append("```")
        lines.append("")
        lines.append("## Task")
        lines.append(
            "Use only this impacted context first. If additional files are required, ask specifically for those files."
        )
        lines.append(
            "Provide: root cause, exact code changes, tests (or why not), and any migration/rollout risk."
        )
        return "\n".join(lines)


def _assistant_header(assistant: str) -> str:
    if assistant == "codex":
        return "Codex mode: prioritize minimal, behavior-safe patch with explicit verification commands."
    if assistant == "claude":
        return "Claude mode: reason briefly, then apply precise edits with no broad context scanning."
    if assistant == "gemini":
        return "Gemini mode: focus on deterministic code changes and impacted dependency paths only."
    if assistant == "chatgpt":
        return "ChatGPT mode: keep solution concise, code-first, and constrained to impacted files."
    if assistant == "antigravity":
        return "Antigravity mode: use targeted context and avoid exploratory full-repo reads."
    return "Generic mode: use targeted impacted context and avoid full repository re-reads."


def build_context_pack(
    config: AppConfig,
    store: GraphStore,
    blast: list[tuple[str, int]],
    changed: list[str],
    max_files: int | None = None,
) -> ContextPack:
    project_root = Path(config.project_root)
    max_output = max_files if max_files is not None else config.max_context_files

    by_file: dict[str, int] = {}
    symbol_hits: dict[str, list[str]] = {}

    for node_id, depth in blast:
        if node_id.startswith("file::"):
            path = node_id[len("file::") :]
            by_file[path] = min(depth, by_file.get(path, depth))
            continue
        if not node_id.startswith("sym::"):
            continue
        _, path, _kind, name, _line = node_id.split("::", 4)
        by_file[path] = min(depth, by_file.get(path, depth))
        symbol_hits.setdefault(path, []).append(name)

    impacted: list[ContextFile] = []
    for path, depth in sorted(by_file.items(), key=lambda item: (item[1], item[0]))[:max_output]:
        snippets = _snippets_for_file(project_root / path, symbol_hits.get(path, []))
        impacted.append(ContextFile(path=path, distance=depth, snippets=snippets))

    return ContextPack(changed=changed, impacted=impacted)


def _snippets_for_file(path: Path, symbol_names: list[str]) -> list[str]:
    if not path.exists() or not path.is_file():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    snippets: list[str] = []

    # Capture specific symbol lines first.
    for name in list(dict.fromkeys(symbol_names))[:8]:
        for idx, line in enumerate(lines, start=1):
            if name in line:
                start = max(1, idx - 4)
                end = min(len(lines), idx + 4)
                body = "\n".join(f"{n:>4} {lines[n - 1]}" for n in range(start, end + 1))
                snippets.append(f"# {name} @ {path}:{idx}\n{body}")
                break

    if not snippets:
        preview_lines = min(60, len(lines))
        body = "\n".join(f"{n:>4} {lines[n - 1]}" for n in range(1, preview_lines + 1))
        snippets.append(f"# {path} (head)\n{body}")

    return snippets[:8]
