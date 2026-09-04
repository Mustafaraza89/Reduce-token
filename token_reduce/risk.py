from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .graph_store import GraphStore

SENSITIVE_PATTERNS = [
    re.compile(r"(auth|login|password|token|jwt|session|oauth|permission|role|rbac)", re.IGNORECASE),
    re.compile(r"(secret|credential|key|crypto|cipher|signature|cert|private)", re.IGNORECASE),
    re.compile(r"(payment|billing|stripe|invoice|wallet|checkout|subscription)", re.IGNORECASE),
    re.compile(r"(migration|schema|database|db|sql|alembic|prisma)", re.IGNORECASE),
]

TEST_FILE_PATTERNS = [
    re.compile(r"(^test_|_test\.py$|\.test\.[a-z]+$|\.spec\.[a-z]+$|tests?/)", re.IGNORECASE),
]


def is_test_file(path: str) -> bool:
    return any(p.search(path) for p in TEST_FILE_PATTERNS)


def is_sensitive_file(path: str) -> bool:
    if is_test_file(path):
        return False
    cleaned = re.sub(r"token[-_]reduce[/\\]?", "", path, flags=re.IGNORECASE)
    return any(p.search(cleaned) for p in SENSITIVE_PATTERNS)


@dataclass(slots=True)
class RiskReport:
    score: int
    level: str
    fan_in_count: int
    impacted_file_count: int
    test_gap_files: list[str]
    sensitive_files: list[str]
    factors: list[str]

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "level": self.level,
            "fan_in_count": self.fan_in_count,
            "impacted_file_count": self.impacted_file_count,
            "test_gap_files": self.test_gap_files,
            "sensitive_files": self.sensitive_files,
            "factors": self.factors,
        }


def calculate_risk_score(
    store: GraphStore,
    changed_files: Sequence[str],
    blast_nodes: Sequence[tuple[str, int]],
) -> RiskReport:
    """Calculate an objective risk score (0-100) based on blast radius, fan-in, test gaps, and sensitivity."""
    score = 10
    factors: list[str] = []

    changed_set = set(changed_files)
    sensitive = [f for f in changed_files if is_sensitive_file(f)]
    if sensitive:
        score += min(30, 15 * len(sensitive))
        factors.append(f"Touches sensitive components ({', '.join(sensitive[:3])})")

    # Impacted files count
    impacted_files = {
        node_id.replace("file::", "")
        for node_id, _ in blast_nodes
        if node_id.startswith("file::") and node_id.replace("file::", "") not in changed_set
    }

    if len(impacted_files) > 10:
        score += 25
        factors.append(f"Large blast radius: {len(impacted_files)} dependent files affected")
    elif len(impacted_files) > 3:
        score += 15
        factors.append(f"Moderate blast radius: {len(impacted_files)} dependent files affected")

    # Fan-in calculation: how many distinct files call or import symbols in changed files
    fan_in_files: set[str] = set()
    for f in changed_files:
        rows = store.conn.execute(
            """
            SELECT DISTINCT path FROM edges
            WHERE dst_id IN (
                SELECT symbol_id FROM symbols WHERE path = ?
                UNION
                SELECT ?
            ) AND path != ?
            """,
            (f, f"file::{f}", f),
        ).fetchall()
        for r in rows:
            fan_in_files.add(r["path"])

    fan_in_count = len(fan_in_files)
    if fan_in_count > 8:
        score += 25
        factors.append(f"High caller fan-in: {fan_in_count} external files call modified symbols")
    elif fan_in_count > 2:
        score += 15
        factors.append(f"Moderate caller fan-in: {fan_in_count} external files call modified symbols")

    # Test Gap Detection
    test_gap_files: list[str] = []
    for f in changed_files:
        if is_test_file(f):
            continue
        # Check if any test file calls or imports this file
        test_edge = store.conn.execute(
            """
            SELECT path FROM edges
            WHERE (dst_id = ? OR dst_id IN (SELECT symbol_id FROM symbols WHERE path = ?))
            AND (path LIKE '%test%' OR path LIKE '%spec%')
            LIMIT 1
            """,
            (f"file::{f}", f),
        ).fetchone()
        if not test_edge:
            test_gap_files.append(f)

    if test_gap_files:
        score += min(25, 10 + 5 * len(test_gap_files))
        factors.append(f"Test gaps detected: {len(test_gap_files)} modified file(s) lack test coverage")

    # Final normalization
    score = min(100, max(5, score))

    if score >= 75:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    if not factors:
        factors.append("Isolated change with low propagation risk")

    return RiskReport(
        score=score,
        level=level,
        fan_in_count=fan_in_count,
        impacted_file_count=len(impacted_files),
        test_gap_files=test_gap_files,
        sensitive_files=sensitive,
        factors=factors,
    )
