from __future__ import annotations

import fnmatch
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


DEFAULT_INCLUDE = [
    "**/*.py",
    "**/*.js",
    "**/*.jsx",
    "**/*.ts",
    "**/*.tsx",
    "**/*.java",
    "**/*.go",
    "**/*.rs",
    "**/*.c",
    "**/*.cc",
    "**/*.cpp",
    "**/*.h",
    "**/*.hpp",
    "**/*.cs",
    "**/*.rb",
    "**/*.php",
    "**/*.swift",
    "**/*.kt",
    "**/*.scala",
    "**/*.lua",
    "**/*.ipynb",
]

DEFAULT_EXCLUDE = [
    ".git/**",
    "**/.git/**",
    "**/.venv/**",
    "**/venv/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.next/**",
    "**/__pycache__/**",
    "**/*.min.js",
    "**/*.lock",
]


@dataclass(slots=True)
class AppConfig:
    project_root: str
    include_globs: list[str] = field(default_factory=lambda: list(DEFAULT_INCLUDE))
    exclude_globs: list[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE))
    max_blast_depth: int = 3
    max_context_files: int = 24
    watcher_interval_seconds: float = 1.5

    @property
    def state_dir(self) -> Path:
        return Path(self.project_root) / ".token-reduce"

    @property
    def graph_db_path(self) -> Path:
        return self.state_dir / "graph.db"

    @property
    def config_path(self) -> Path:
        return self.state_dir / "config.json"


def ensure_state_dir(config: AppConfig) -> None:
    config.state_dir.mkdir(parents=True, exist_ok=True)


def load_config(project_root: Path) -> AppConfig:
    state_dir = project_root / ".token-reduce"
    config_path = state_dir / "config.json"
    if not config_path.exists():
        cfg = AppConfig(project_root=str(project_root.resolve()))
        save_config(cfg)
        return cfg
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["project_root"] = str(project_root.resolve())
    return AppConfig(**payload)


def save_config(config: AppConfig) -> None:
    ensure_state_dir(config)
    config.config_path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def is_included(config: AppConfig, relative_path: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if any(_glob_matches(normalized, pattern) for pattern in config.exclude_globs):
        return False
    return any(_glob_matches(normalized, pattern) for pattern in config.include_globs)


def _glob_matches(path: str, pattern: str) -> bool:
    # `fnmatch` does not treat `**/*.ext` as matching top-level `file.ext`.
    if fnmatch.fnmatch(path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatch(path, pattern[3:])
    return False
