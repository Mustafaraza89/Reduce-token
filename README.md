# ⚡ ReduceToken

> **Universal Token Optimization Framework for AI Coding Assistants**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 16 Passing](https://img.shields.io/badge/tests-16%20passing-brightgreen.svg)]()

**ReduceToken** dramatically reduces the tokens consumed by AI coding assistants. Works with **Claude Code, Cursor, Gemini, GitHub Copilot, VS Code, and any terminal** via a simple slash command.

- **Input Token Reduction: 80% – 95%** — via AST Knowledge Graph & Blast Radius Analysis
- **Output Token Reduction: 50% – 75%** — via ReduceToken Direct Engine (silences AI monologue & filler)

---

## ⚡ Install in One Command

No shell scripts. No manual steps. Just run:

```bash
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
```

Then run setup inside your project folder:

```bash
token-reduce setup
```

**Done.** You can now use `token-reduce /` in any project.

> **Windows users:** If `token-reduce` is not found after install, see the [Windows section](#windows) below.

---

## 🚀 Quick Start (3 Steps)

```bash
# Step 1: Install
pip install git+https://github.com/Mustafaraza89/Reduce-token.git

# Step 2: Go to your project and set up
cd your-project
token-reduce setup

# Step 3: Run ReduceToken — builds context and copies to clipboard
token-reduce /
```

Paste the clipboard output directly into Claude, Cursor, Gemini, or ChatGPT.

---

## 🤔 Why Do You Need This?

When you use AI for coding, two problems waste your tokens:

### Problem 1 — Input Token Bloat
The AI reads your entire repo or 10–15 large files:
- Wastes **10,000–50,000+ input tokens** per prompt
- Fills the context window → model gets confused → hallucinations

### Problem 2 — Output Token Waste (AI Monologue)
Models like Gemini Thinking, Claude 3.7, and OpenAI o1 generate long filler before answering:
- *"Sure! I would be happy to help. Let's analyze the problem carefully..."*
- This wastes output tokens and buries the actual code in noise.

---

## ⚡ Dual-Engine Solution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       REDUCETOKEN DUAL-ENGINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  [ENGINE 1: AST Knowledge Graph]       [ENGINE 2: ReduceToken Direct]       │
│  • SQLite Symbol & Call Graph          • Silences Reasoning / Monologue     │
│  • BFS Blast-Radius Calculation        • Zero conversational filler words   │
│  • Line-Range Deduplication            • Instant direct code / diffs        │
│  ⬇️                                    ⬇️                                   │
│  SAVINGS: 80% – 95% INPUT TOKENS       SAVINGS: 50% – 75% OUTPUT TOKENS     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Installation — All Options

### macOS / Linux

```bash
# Recommended — pip install (no shell scripts needed):
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
token-reduce setup

# Or with a virtual environment (isolated, recommended for projects):
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
token-reduce setup

# Or clone and install locally:
git clone https://github.com/Mustafaraza89/Reduce-token.git
cd Reduce-token
pip install -e .
token-reduce setup
```

---

### Windows

**Step 1:** Open PowerShell or Command Prompt.

**Step 2:** Install:

```powershell
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
```

**Step 3:** If `token-reduce` is not found, add Python Scripts to PATH:

```powershell
# Find your Scripts directory:
python -c "import sysconfig; print(sysconfig.get_path('scripts'))"

# Example output: C:\Users\YourName\AppData\Local\Programs\Python\Python312\Scripts
```

Add that path to your System PATH:
1. Search "Environment Variables" in Start Menu
2. Click "Edit the system environment variables"
3. Click "Environment Variables" → select "Path" → "Edit" → "New"
4. Paste the Scripts path → OK → restart PowerShell

**Step 4:** Run setup in your project:

```powershell
cd your-project
token-reduce setup
```

**Step 5:** Use it:

```powershell
token-reduce /
```

> **Tip for Windows:** Use `token-reduce use --print` if the clipboard copy doesn't work automatically.

---

## 🕹️ How to Use

### Main Command

```bash
# Builds blast radius context + injects Direct Engine override + copies to clipboard:
token-reduce /

# Equivalent full form:
token-reduce use --caveman full --copy --print

# With a specific query:
token-reduce use --query "fix the auth bug" --copy --print
```

### Editor Integrations

Run `token-reduce setup` once in your project to install all of these automatically:

| Editor | How It Works |
|---|---|
| **Claude Code** | `/reduce` and `/reducetoken` slash commands in `.claude/commands/` |
| **Cursor AI** | `.cursor/rules/reduce-token.mdc` auto-applied |
| **Gemini / Antigravity** | `GEMINI.md` workspace rule auto-loaded |
| **VS Code** | Command Palette → Run Task → "ReduceToken: Direct Context" |
| **GitHub Copilot** | `.github/copilot-instructions.md` auto-read by Copilot |

---

## 🥊 Direct Modes

| Mode | Output Savings | Behavior |
|---|---|---|
| `mild` | ~40% | Concise, code-first, no pleasantries |
| `full` *(default)* | ~65% | Direct code & diffs, monologue silenced |
| `raw` | ~75% | Pure code/diff only, zero English prose |
| `off` | 0% | Normal AI output |

```bash
token-reduce /                                    # full mode (default)
token-reduce use --caveman raw --copy --print     # raw mode, max savings
token-reduce use --max-tokens 2000 --copy --print # strict token budget
```

---

## 📊 Live Token Savings Report

Every run shows real-time savings in the terminal and at the top of the prompt:

```
mode=ReduceToken(AST+DirectEngine) assistant=generic
changed=src/auth.py,src/utils.py
tokens_input=~1,240  baseline=~11,480  saved=89.2%
reducetoken_mode=DIRECT (est_output_saved=~65% + thinking_overridden)
clipboard=copied ReduceToken prompt to system clipboard!
```

---

## 🛠️ Full CLI Reference

| Command | Description |
|---|---|
| `token-reduce /` | Main command — blast radius + Direct Engine prompt, copied to clipboard |
| `token-reduce setup` | One-time setup: build graph + install editor integrations + git hooks |
| `token-reduce use` | Same as `/` with full flag control (`--caveman`, `--max-tokens`, `--copy`, `--print`) |
| `token-reduce build` | Scan codebase and build/update AST graph index |
| `token-reduce sync` | Incrementally sync only changed files |
| `token-reduce blast` | Show raw blast radius for specific files |
| `token-reduce context` | Generate context pack as JSON or Markdown |
| `token-reduce status` | Show index stats — files, symbols, call edges, DB size |
| `token-reduce clean` | Clean graph DB and cache |
| `token-reduce watch` | Background daemon for real-time incremental indexing |

---

## 💻 Supported Languages

Python, TypeScript, JavaScript, Go, Rust, Java, C, C++, C#, Ruby, PHP, Swift, Kotlin

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -v
```

All 16 tests pass in under 0.1 seconds.

---

## 📁 Project Structure

```
Reduce-token/
├── install.sh                      # Optional shell installer (clone-and-run alternative)
├── GEMINI.md                       # Gemini / Antigravity workspace rule
├── pyproject.toml                  # pip package config
├── token_reduce/
│   ├── cli.py                      # CLI entry point (token-reduce command)
│   ├── context_pack.py             # Blast radius → context builder
│   ├── caveman.py                  # ReduceToken Direct Engine (output override)
│   ├── slash_commands.py           # Editor integration installer
│   └── ...                        # Language parsers, graph engine, DB layer
├── .claude/commands/               # Claude Code slash commands
├── .cursor/rules/                  # Cursor AI rule
├── .github/copilot-instructions.md # Copilot instructions
├── .vscode/tasks.json              # VS Code tasks
└── tests/test_token_reduce.py      # 16-test suite
```

---

## 🤝 Contributing

PRs welcome. Open an issue first to discuss your change.

---

## 📄 License

MIT — free for personal and commercial use.
