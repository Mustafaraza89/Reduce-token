# token-reduce

`token-reduce` ek Python CLI hai jo project ka incremental knowledge graph banata hai, blast radius nikalta hai, aur AI coding assistants (Claude/Cursor) ko sirf impacted context dene me help karta hai.

## Key features

- One-time graph build: files, symbols, imports, calls, inheritance links
- Blast radius analysis: changed file se related affected nodes/files
- Minimal context pack JSON generation for assistant prompts
- Incremental updates:
  - save-time watcher (`watch`)
  - git hook sync (`post-commit`, `post-merge`)
- Multi-language support:
  - Python AST parser
  - Jupyter `.ipynb` code-cell parsing
  - Heuristic parsing for JS/TS/Java/Go/Rust/C/C++/C#/Ruby/PHP/Swift/Kotlin/Scala/Lua

## Installation (recommended)

> Mac/Homebrew Python me `pip install -e .` direct run karne par PEP 668 error aa sakta hai. Isliye virtualenv recommended hai.

1. Clone repo

```bash
git clone <your-repo-url>
cd token-reduce
```

2. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install package in editable mode

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

4. Verify CLI

```bash
token-reduce --help
# fallback
python -m token_reduce --help
```

## Quick start

```bash
token-reduce init
token-reduce build
token-reduce status
```

### Incremental sync + context

```bash
# Sync only changed files from working tree
token-reduce sync --worktree

# Compute blast radius from changed file(s)
token-reduce blast --changed src/foo.py --depth 3

# Generate compact AI context payload
token-reduce context --changed src/foo.py --out .token-reduce/context.json
```

Then AI assistant ko poora repo dene ke badle `.token-reduce/context.json` + impacted files do.

## Install integrations (Claude/Cursor + hooks + watcher)

```bash
token-reduce install --json
```

`install` command:

- `.token-reduce/` state ensure karta hai
- Cursor detect hone par `.cursor/rules/token-reduce-context.mdc` banata hai
- Claude detect hone par `CLAUDE.md` me workflow section add karta hai
- Git hooks install karne try karta hai:
  - `.git/hooks/post-commit` -> `sync --git-head`
  - `.git/hooks/post-merge` -> `sync --worktree`
- Background watcher start karta hai (default)

### If you do not want background watcher

```bash
token-reduce install --no-watch
```

## CLI reference

- `token-reduce init`
- `token-reduce build [--json]`
- `token-reduce sync [--files ...] [--git-head] [--worktree] [--json]`
- `token-reduce blast --changed <file...> [--depth N] [--json]`
- `token-reduce context --changed <file...> [--depth N] [--max-files N] [--out FILE]`
- `token-reduce watch [--interval 1.5]`
- `token-reduce install [--no-watch] [--json]`
- `token-reduce status [--json]`

## Recommended daily workflow

1. Start of day / fresh branch:

```bash
token-reduce build
```

2. Before AI query on changed code:

```bash
token-reduce sync --worktree
token-reduce context --changed <changed-files> --out .token-reduce/context.json
```

3. After commit:

- `post-commit` hook auto-sync karega (agar hooks installed hain)

## Troubleshooting

### 1) `externally-managed-environment` during pip install

Use venv (recommended section above). Avoid global `pip install -e .` on Homebrew Python.

### 2) `install` me hook permission error

Agar output me `Permission denied writing git hook` aaye, to manually permissions check karo:

```bash
ls -ld .git .git/hooks
chmod u+w .git/hooks
```

Phir rerun:

```bash
token-reduce install --no-watch --json
```

### 3) `token-reduce` command not found

Venv activate karo ya module mode use karo:

```bash
python -m token_reduce <command>
```

### 4) Watcher already running

`install --json` notes me `Watcher already running.` aayega; ye normal hai.

## Development checks

```bash
python -m unittest discover -s tests -v
```
