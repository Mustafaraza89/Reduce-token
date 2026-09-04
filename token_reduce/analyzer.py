from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from .config import AppConfig, is_included
from .graph_store import GraphStore
from .hash_utils import file_sha1
from .languages import ParseResult, parse_source


EXTENSION_INDEX = {
    ".py",
    ".ipynb",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".lua",
}


class Analyzer:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.project_root = Path(config.project_root).resolve()
        self.store = GraphStore(config.graph_db_path)

    def close(self) -> None:
        self.store.close()

    def collect_source_files(self) -> list[Path]:
        files: list[Path] = []
        for path in self.project_root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in EXTENSION_INDEX:
                continue
            rel = str(path.relative_to(self.project_root)).replace("\\", "/")
            if not is_included(self.config, rel):
                continue
            files.append(path)
        return files

    def build_graph(self) -> dict[str, int]:
        processed = 0
        unchanged = 0

        existing = self.store.tracked_files()
        current: set[str] = set()

        for path in self.collect_source_files():
            rel = str(path.relative_to(self.project_root)).replace("\\", "/")
            current.add(rel)
            if self._upsert_if_changed(path):
                processed += 1
            else:
                unchanged += 1

        removed = existing - current
        for rel in removed:
            self.store.remove_file(rel)

        self.store.refresh_reference_edges(self.resolve_import)
        return {
            "processed": processed,
            "unchanged": unchanged,
            "removed": len(removed),
            "tracked": len(current),
        }

    def sync_files(self, files: list[Path]) -> dict[str, int]:
        parsed = 0
        skipped = 0
        removed = 0

        for path in files:
            resolved = (path if path.is_absolute() else self.project_root / path).resolve()
            rel = self._to_rel_or_none(resolved)
            if rel is None:
                skipped += 1
                continue
            if not resolved.exists():
                self.store.remove_file(rel)
                removed += 1
                continue
            if not is_included(self.config, rel):
                skipped += 1
                continue
            if self._upsert_if_changed(resolved):
                parsed += 1
            else:
                skipped += 1

        self.store.refresh_reference_edges(self.resolve_import)
        return {"parsed": parsed, "skipped": skipped, "removed": removed}

    def blast_radius(self, changed: list[Path], max_depth: int | None = None) -> list[tuple[str, int]]:
        node_ids: list[str] = []
        for path in changed:
            rel = self._to_rel_or_none(path if path.is_absolute() else self.project_root / path)
            if rel is None:
                continue
            node_ids.append(f"file::{rel}")
            for symbol in self.store.symbols_in_file(rel):
                node_ids.append(symbol.symbol_id)

        depth = max_depth if max_depth is not None else self.config.max_blast_depth
        return self.store.blast_radius(node_ids, depth)

    def resolve_import(self, source_path: str, import_token: str) -> str | None:
        token = import_token.strip()
        if not token:
            return None

        source = Path(source_path)
        root = self.project_root

        if token.startswith("."):
            return self._resolve_relative_import(source, token)

        token_path = token.replace(".", "/")
        source_roots = [root, root / "src", root / "lib", root / "app"]
        for sroot in source_roots:
            if not sroot.exists():
                continue
            for ext in ("", ".py", ".ts", ".tsx", ".js", ".jsx", "/__init__.py", "/index.ts", "/index.js"):
                if ext.startswith("/"):
                    candidate = sroot / token_path / ext.lstrip("/")
                else:
                    candidate = sroot / f"{token_path}{ext}"
                if candidate.exists() and candidate.is_file() and candidate.is_relative_to(root):
                    return str(candidate.relative_to(root)).replace("\\", "/")

        # fallback by basename for non-python module syntax
        if "/" in token or token.endswith(tuple(EXTENSION_INDEX)):
            candidate = (root / source.parent / token).resolve()
            if candidate.exists() and candidate.is_file() and candidate.is_relative_to(root):
                return str(candidate.relative_to(root)).replace("\\", "/")

        basename = Path(token).name
        row = self.store.conn.execute(
            "SELECT path FROM files WHERE path LIKE ? OR path LIKE ? LIMIT 1",
            (f"%/{basename}", f"%/{basename}.%"),
        ).fetchone()
        return row["path"] if row else None

    def _safe_git_env(self) -> dict[str, str]:
        env = dict(os.environ)
        if "HOME" not in env or not os.access(env.get("HOME", ""), os.R_OK):
            env["HOME"] = "/tmp"
        return env

    def changed_files_from_head(self) -> list[Path]:
        command = ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"]
        proc = subprocess.run(
            command, cwd=self.project_root, capture_output=True, text=True, check=False, env=self._safe_git_env()
        )
        if proc.returncode != 0:
            return []
        files: list[Path] = []
        for line in proc.stdout.splitlines():
            raw_path = line.strip()
            if not raw_path:
                continue
            if raw_path.startswith('"') and raw_path.endswith('"'):
                raw_path = raw_path[1:-1]
            files.append(self.project_root / raw_path)
        return files

    def changed_files_from_worktree(self) -> list[Path]:
        command = ["git", "status", "--porcelain"]
        proc = subprocess.run(
            command, cwd=self.project_root, capture_output=True, text=True, check=False, env=self._safe_git_env()
        )
        if proc.returncode != 0:
            return []
        changed: list[Path] = []
        for line in proc.stdout.splitlines():
            if len(line) < 4:
                continue
            raw_path = line[3:].strip()
            if not raw_path:
                continue
            # Handle renamed files: "R  old -> new"
            if " -> " in raw_path:
                raw_path = raw_path.split(" -> ", 1)[1].strip()
            # Handle quoted paths
            if raw_path.startswith('"') and raw_path.endswith('"'):
                raw_path = raw_path[1:-1]
            changed.append(self.project_root / raw_path)
        return changed

    def _upsert_if_changed(self, path: Path) -> bool:
        rel = self._to_rel(path)
        digest = file_sha1(path)
        if self.store.file_hash(rel) == digest:
            return False
        parse_result = parse_source(path, self.project_root)
        self._store_parsed_file(parse_result, digest)
        return True

    def _store_parsed_file(self, parse_result: ParseResult, content_hash: str) -> None:
        self.store.upsert_file(
            path=parse_result.path,
            language=parse_result.language,
            content_hash=content_hash,
            unix_time=int(time.time()),
        )
        self.store.replace_file_parse(parse_result)

    def _resolve_relative_import(self, source_rel: Path, import_token: str) -> str | None:
        root = self.project_root
        source_parent = source_rel.parent
        token_str = import_token.replace("\\", "/")

        if "/" in token_str:
            parts = token_str.split("/")
            up_count = 0
            clean_parts = []
            for p in parts:
                if p == "..":
                    up_count += 1
                elif p == "." or not p:
                    continue
                else:
                    clean_parts.append(p)
            rel_path_str = "/".join(clean_parts)
        else:
            leading_dots = len(token_str) - len(token_str.lstrip("."))
            up_count = max(0, leading_dots - 1)
            remainder = token_str.lstrip(".")
            rel_path_str = remainder.replace(".", "/")

        cursor = source_parent
        for _ in range(up_count):
            cursor = cursor.parent

        base = root / cursor / rel_path_str if rel_path_str else root / cursor

        candidate_exts = (
            "",
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".go",
            ".rs",
            ".java",
            "/__init__.py",
            "/index.ts",
            "/index.tsx",
            "/index.js",
            "/index.jsx",
        )
        for ext in candidate_exts:
            if ext.startswith("/"):
                candidate = base / ext.lstrip("/")
            elif ext:
                candidate = base.with_name(f"{base.name}{ext}")
            else:
                candidate = base
            if candidate.exists() and candidate.is_file() and candidate.is_relative_to(root):
                return str(candidate.relative_to(root)).replace("\\", "/")
        return None

    def _to_rel(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.project_root)).replace("\\", "/")

    def _to_rel_or_none(self, path: Path) -> str | None:
        try:
            return self._to_rel(path)
        except ValueError:
            return None
