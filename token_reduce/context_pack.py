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
