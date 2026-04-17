# token-reduce

`token-reduce` AI coding assistants ke liye context optimizer hai. Ye full repo dubara-dubara read karne ke bajay sirf impacted files/snippets deta hai.

## Super quick start (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

# One-time setup
token-reduce setup

# Daily single command (auto-detect changed files)
token-reduce use --assistant claude
```

Bas. `use` command automatically:

- changed files detect karta hai
- graph sync karta hai
- blast radius nikalta hai
- 2 files generate karta hai:
  - `.token-reduce/assistant/context-<assistant>.json`
  - `.token-reduce/assistant/prompt-<assistant>.md`

`prompt-<assistant>.md` ka content copy karke apne AI tool me paste karo.

## Works with

- Codex
- Claude Code
- Gemini
- ChatGPT
- Antigravity
- Any IDE + terminal workflow

Use assistant-specific prompt style:

```bash
token-reduce use --assistant codex
token-reduce use --assistant claude
token-reduce use --assistant gemini
token-reduce use --assistant chatgpt
token-reduce use --assistant antigravity
```

## IDE workflow (direct)

1. Terminal open karo (IDE ke andar ya external)
2. Run:

```bash
token-reduce use --assistant claude
```

3. Open file:

- `.token-reduce/assistant/prompt-claude.md`

4. Iska content copy-paste into assistant chat.

Same steps Codex/Gemini/ChatGPT ke liye, sirf `--assistant` change karo.

## CLI commands

### Easy mode (recommended)

- `token-reduce setup` -> one-time init + build + install integrations
- `token-reduce use --assistant <name>` -> daily one-command context generation

### Advanced mode (optional)

- `token-reduce init`
- `token-reduce build`
- `token-reduce sync --worktree`
- `token-reduce blast --changed <files>`
- `token-reduce context --changed <files>`
- `token-reduce install`
- `token-reduce watch`
- `token-reduce status`

## When no changed files are detected

Agar git worktree clean ho, to explicit files pass karo:

```bash
token-reduce use --assistant claude --changed src/api/user.ts src/lib/auth.ts
```

## Installation notes

Homebrew Python me direct global install par `externally-managed-environment` error aa sakta hai. Isliye always virtualenv use karo (quick start jaisa).

## Test

```bash
python -m unittest discover -s tests -v
```
