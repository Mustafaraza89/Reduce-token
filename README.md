# token-reduce

`token-reduce` is a Python CLI that builds and incrementally maintains a codebase knowledge graph so AI coding assistants can use only impacted context instead of re-reading whole repositories.

## What it does

- Scans your repository once and builds a graph of files, symbols, imports, inheritance, and call references.
- Computes blast radius for changed files through graph traversal.
- Produces compact context packs (JSON) for assistant prompts.
- Updates incrementally:
  - on file save via built-in watcher
  - on commits/merges via installed git hooks
- Supports multiple languages via mixed parsing strategies:
  - AST-backed: Python
  - Notebook-aware: Jupyter `.ipynb` (code cells)
  - Heuristic parsing: JS/TS/Java/Go/Rust/C/C++/C#/Ruby/PHP/Swift/Kotlin/Scala/Lua

## Install

```bash
pip install -e .
```

## Quick start

```bash
token-reduce init
token-reduce build
token-reduce install
token-reduce sync --worktree
token-reduce blast --changed src/foo.py
token-reduce context --changed src/foo.py --out .token-reduce/context.json
```

## CLI

- `token-reduce init`
- `token-reduce build [--json]`
- `token-reduce sync [--files ...] [--git-head] [--worktree] [--json]`
- `token-reduce blast --changed <file...> [--depth N] [--json]`
- `token-reduce context --changed <file...> [--depth N] [--max-files N] [--out FILE]`
- `token-reduce watch [--interval 1.5]`
- `token-reduce install [--no-watch] [--json]`
- `token-reduce status [--json]`

## Installer behavior

`token-reduce install` automatically:

- Creates project state in `.token-reduce/`
- Detects and configures known assistants when found:
  - Cursor (`.cursor/rules/token-reduce-context.mdc`)
  - Claude (`CLAUDE.md` workflow section)
- Installs git hooks:
  - `.git/hooks/post-commit` (sync changed HEAD files)
  - `.git/hooks/post-merge` (sync worktree changes)
- Starts watcher background process (unless `--no-watch`)

## Output integration pattern for assistants

Call:

```bash
token-reduce sync --worktree
token-reduce context --changed <changed files> --out .token-reduce/context.json
```

Then provide only `.token-reduce/context.json` and impacted files to your assistant.
# Reduce-token
