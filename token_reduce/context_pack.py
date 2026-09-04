from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from .caveman import estimate_output_savings_pct, format_caveman_directive
from .config import AppConfig
from .graph_store import GraphStore


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


@dataclass(slots=True)
class ContextFile:
    path: str
    distance: int
    snippets: list[str]


@dataclass(slots=True)
class ContextPack:
    changed: list[str]
    impacted: list[ContextFile]
    estimated_tokens: int = 0
    baseline_tokens: int = 0
    token_reduction_pct: float = 0.0
    caveman: str = "full"

    @property
    def caveman_savings_pct(self) -> float:
        return estimate_output_savings_pct(self.caveman)

    def to_json(self) -> str:
        return json.dumps(
            {
                "changed": self.changed,
                "impacted": [asdict(item) for item in self.impacted],
                "estimated_tokens": self.estimated_tokens,
                "baseline_tokens": self.baseline_tokens,
                "token_reduction_pct": self.token_reduction_pct,
                "caveman": self.caveman,
                "estimated_output_savings_pct": estimate_output_savings_pct(self.caveman),
            },
            indent=2,
        )

    def to_markdown(self, assistant: str = "generic") -> str:
        header = _assistant_header(assistant)
        caveman_block = format_caveman_directive(self.caveman, assistant=assistant)
        out_savings = estimate_output_savings_pct(self.caveman)

        lines: list[str] = []
        lines.append(f"# ReduceToken Context Prompt ({assistant})")
        lines.append("")
        savings_text = f"{self.token_reduction_pct:.1f}%" if self.token_reduction_pct > 0 else "0%"
        mode_label = "DIRECT" if self.caveman == "full" else self.caveman.upper()
        lines.append(
            f"> ⚡ **ReduceToken Optimization Engine**:\n"
            f"> - **Input Tokens**: ~{self.estimated_tokens:,} tokens (saved {savings_text} vs ~{self.baseline_tokens:,} full candidate tokens)\n"
            f"> - **Output Mode**: REDUCETOKEN {mode_label} (estimated ~{out_savings:.0f}% output tokens saved & thinking monologue overridden)"
        )
        lines.append("")
        if caveman_block:
            lines.append(caveman_block)
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
        lines.append("Below blocks are auto-extracted code snippets for AI context (reference only).")
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
    max_tokens: int | None = None,
    caveman: str = "full",
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

    # Compute baseline token count of candidate files in full
    baseline_tokens = 0
    for path in by_file:
        full_path = project_root / path
        if full_path.exists() and full_path.is_file():
            try:
                baseline_tokens += estimate_tokens(full_path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    impacted: list[ContextFile] = []
    current_tokens = 200  # Base boilerplate token allowance

    for path, depth in sorted(by_file.items(), key=lambda item: (item[1], item[0]))[:max_output]:
        snippets = _snippets_for_file(
            path=project_root / path,
            symbol_names=symbol_hits.get(path, []),
            rel_path=path,
            store=store,
        )
        if not snippets:
            continue

        file_tokens = sum(estimate_tokens(s) for s in snippets) + 50
        if max_tokens is not None and (current_tokens + file_tokens > max_tokens) and impacted:
            # Stop adding distant files once token budget is reached
            break

        impacted.append(ContextFile(path=path, distance=depth, snippets=snippets))
        current_tokens += file_tokens

    pack = ContextPack(
        changed=changed,
        impacted=impacted,
        baseline_tokens=baseline_tokens,
        caveman=caveman,
    )
    # Calculate estimated tokens of generated prompt
    pack.estimated_tokens = estimate_tokens(pack.to_markdown())
    if baseline_tokens > 0:
        reduction = (1.0 - (pack.estimated_tokens / baseline_tokens)) * 100
        pack.token_reduction_pct = max(0.0, round(reduction, 1))
    else:
        pack.token_reduction_pct = 0.0

    return pack


def _snippets_for_file(
    path: Path,
    symbol_names: list[str],
    rel_path: str = "",
    store: GraphStore | None = None,
) -> list[str]:
    if not path.exists() or not path.is_file():
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.splitlines()
    if not lines:
        return []

    # Known symbol positions from database
    known_symbols: dict[str, tuple[int, int]] = {}
    if store and rel_path:
        for sym in store.symbols_in_file(rel_path):
            known_symbols[sym.name] = (sym.start_line, sym.end_line)

    ranges: list[tuple[int, int, str]] = []

    for name in list(dict.fromkeys(symbol_names))[:8]:
        start_line = None
        end_line = None
        if name in known_symbols:
            s, e = known_symbols[name]
            start_line = s
            # Cap snippet length to at most 20 lines to prevent dumping entire large classes/files
            end_line = min(e, s + 18)
        else:
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            best_idx = None
            for idx, line in enumerate(lines, start=1):
                if pattern.search(line):
                    stripped = line.strip()
                    if any(
                        stripped.startswith(kw)
                        for kw in (
                            "def ",
                            "class ",
                            "function",
                            "func ",
                            "fn ",
                            "const ",
                            "let ",
                            "var ",
                            "export ",
                            "public ",
                            "type ",
                            "interface ",
                        )
                    ):
                        best_idx = idx
                        break
                    if best_idx is None:
                        best_idx = idx

            if best_idx is not None:
                start_line = best_idx
                end_line = min(len(lines), best_idx + 14)

        if start_line is not None and end_line is not None:
            s_clamp = max(1, start_line - 2)
            e_clamp = min(len(lines), end_line + 2)
            ranges.append((s_clamp, e_clamp, name))

    if not ranges:
        preview_lines = min(40, len(lines))
        body = "\n".join(f"{n:>4} {lines[n - 1]}" for n in range(1, preview_lines + 1))
        return [f"# {rel_path or path.name} (head)\n{body}"]

    # Sort and merge overlapping or adjacent ranges to eliminate code duplication
    ranges.sort(key=lambda r: (r[0], r[1]))
    merged: list[tuple[int, int, list[str]]] = []
    for s, e, lbl in ranges:
        if not merged:
            merged.append((s, e, [lbl]))
        else:
            last_s, last_e, last_lbls = merged[-1]
            if s <= last_e + 2:
                # Merge overlapping or touching ranges
                merged[-1] = (last_s, max(last_e, e), last_lbls + [lbl])
            else:
                merged.append((s, e, [lbl]))

    snippets: list[str] = []
    for s, e, lbls in merged[:6]:
        labels_str = ", ".join(dict.fromkeys(lbls))
        body = "\n".join(f"{n:>4} {lines[n - 1]}" for n in range(s, e + 1))
        snippets.append(f"# {labels_str} @ {rel_path or path.name}:{s}-{e}\n{body}")

    return snippets
