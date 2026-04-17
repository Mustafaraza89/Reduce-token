from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Callable, Iterable

from .languages import ParseResult, Symbol


class GraphStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def close(self) -> None:
        self.conn.close()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                language TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS symbols (
                symbol_id TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                language TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                signature TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_symbols_path ON symbols(path);
            CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);

            CREATE TABLE IF NOT EXISTS refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                target_name TEXT NOT NULL,
                kind TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_refs_path ON refs(path);
            CREATE INDEX IF NOT EXISTS idx_refs_target ON refs(target_name);

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                src_id TEXT NOT NULL,
                dst_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                path TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id);
            CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id);
            CREATE INDEX IF NOT EXISTS idx_edges_path ON edges(path);
            """
        )
        self.conn.commit()

    def file_hash(self, path: str) -> str | None:
        row = self.conn.execute("SELECT content_hash FROM files WHERE path = ?", (path,)).fetchone()
        return row[0] if row else None

    def tracked_files(self) -> set[str]:
        rows = self.conn.execute("SELECT path FROM files").fetchall()
        return {row[0] for row in rows}

    def upsert_file(self, path: str, language: str, content_hash: str, unix_time: int) -> None:
        self.conn.execute(
            """
            INSERT INTO files(path, language, content_hash, updated_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                language = excluded.language,
                content_hash = excluded.content_hash,
                updated_at = excluded.updated_at
            """,
            (path, language, content_hash, unix_time),
        )

    def remove_file(self, path: str) -> None:
        self.conn.execute("DELETE FROM files WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM symbols WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM refs WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM edges WHERE path = ?", (path,))
        self.conn.commit()

    def replace_file_parse(self, parse_result: ParseResult) -> None:
        path = parse_result.path
        file_node_id = f"file::{path}"
        self.conn.execute("DELETE FROM symbols WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM refs WHERE path = ?", (path,))
        self.conn.execute("DELETE FROM edges WHERE path = ?", (path,))

        for symbol in parse_result.symbols:
            self.conn.execute(
                """
                INSERT INTO symbols(symbol_id, path, name, kind, language, start_line, end_line, signature)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol.symbol_id,
                    symbol.path,
                    symbol.name,
                    symbol.kind,
                    symbol.language,
                    symbol.start_line,
                    symbol.end_line,
                    symbol.signature,
                ),
            )
            self.conn.execute(
                "INSERT INTO edges(src_id, dst_id, kind, path) VALUES (?, ?, 'contains', ?)",
                (file_node_id, symbol.symbol_id, path),
            )

        for imp in parse_result.imports:
            self.conn.execute(
                "INSERT INTO refs(path, owner_id, target_name, kind) VALUES (?, ?, ?, 'imports')",
                (path, file_node_id, imp),
            )

        for ref in parse_result.refs:
            self.conn.execute(
                "INSERT INTO refs(path, owner_id, target_name, kind) VALUES (?, ?, ?, ?)",
                (path, ref.owner_id, ref.target_name, ref.kind),
            )

        self.conn.commit()

    def refresh_reference_edges(self, import_resolver: Callable[[str, str], str | None]) -> None:
        self.conn.execute("DELETE FROM edges WHERE kind != 'contains'")

        refs = self.conn.execute("SELECT path, owner_id, target_name, kind FROM refs").fetchall()
        for row in refs:
            path = row["path"]
            owner = row["owner_id"]
            target_name = row["target_name"]
            kind = row["kind"]
            if kind == "imports":
                resolved = import_resolver(path, target_name)
                if not resolved:
                    continue
                dst_id = f"file::{resolved}"
                self.conn.execute(
                    "INSERT INTO edges(src_id, dst_id, kind, path) VALUES (?, ?, 'imports', ?)",
                    (owner, dst_id, path),
                )
                continue

            matches = self.conn.execute(
                "SELECT symbol_id FROM symbols WHERE name = ?",
                (target_name,),
            ).fetchall()
            if not matches:
                continue
            for match in matches:
                self.conn.execute(
                    "INSERT INTO edges(src_id, dst_id, kind, path) VALUES (?, ?, ?, ?)",
                    (owner, match["symbol_id"], kind, path),
                )
        self.conn.commit()

    def blast_radius(self, start_node_ids: Iterable[str], max_depth: int) -> list[tuple[str, int]]:
        queue: list[tuple[str, int]] = [(node_id, 0) for node_id in start_node_ids]
        visited: dict[str, int] = {node_id: 0 for node_id in start_node_ids}

        while queue:
            node_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue
            rows = self.conn.execute(
                """
                SELECT src_id, dst_id FROM edges
                WHERE src_id = ? OR dst_id = ?
                """,
                (node_id, node_id),
            ).fetchall()
            for row in rows:
                for candidate in (row["src_id"], row["dst_id"]):
                    if candidate in visited and visited[candidate] <= depth + 1:
                        continue
                    visited[candidate] = depth + 1
                    queue.append((candidate, depth + 1))

        return sorted(visited.items(), key=lambda item: (item[1], item[0]))

    def symbols_in_file(self, path: str) -> list[Symbol]:
        rows = self.conn.execute(
            "SELECT symbol_id, path, name, kind, language, start_line, end_line, signature FROM symbols WHERE path = ?",
            (path,),
        ).fetchall()
        return [
            Symbol(
                symbol_id=row["symbol_id"],
                path=row["path"],
                name=row["name"],
                kind=row["kind"],
                language=row["language"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                signature=row["signature"],
            )
            for row in rows
        ]

    def commit(self) -> None:
        self.conn.commit()
