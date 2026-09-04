# ⚡ ReduceToken

> **Universal Token Optimization Framework for AI Coding Assistants**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 16 Passing](https://img.shields.io/badge/tests-16%20passing-brightgreen.svg)]()

**ReduceToken** dramatically reduces the tokens consumed by AI coding assistants. Works with **Claude Code, Cursor, Gemini, GitHub Copilot, VS Code, and any terminal** via a simple `/` slash command.

- **Input Token Reduction: 80% – 95%** — via AST Knowledge Graph & Blast Radius Analysis
- **Output Token Reduction: 50% – 75%** — via ReduceToken Direct Engine (silences AI monologue & filler)

---

## ⚡ Install in One Command

No shell scripts. No manual steps. Just run this:

```bash
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
```

Then set up editor integrations (Claude, Cursor, Gemini, VS Code, Copilot):

```bash
token-reduce setup
```

**Done.** You can now use `token-reduce /` in any project.

---

## 🚀 Quick Start

```bash
# 1. Install
pip install git+https://github.com/Mustafaraza89/Reduce-token.git

# 2. Go to any project folder
cd your-project

# 3. Build the AST graph (first time only per project)
token-reduce build

# 4. Run ReduceToken — copies optimized prompt to clipboard
token-reduce /
```

> **Tip:** Paste the clipboard output directly into Claude, Cursor, Gemini, or ChatGPT.

---

## 🤔 Why Do You Need This?

When you use AI for coding, two problems waste your tokens:

### Problem 1 — Input Token Bloat
The AI reads your entire repo or 10–15 large files:
- Wastes **10,000–50,000+ input tokens** per prompt
- Fills the context window — model gets confused → hallucinations

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

**Engine 1** builds a static AST graph of your codebase in SQLite. On each run, it computes the "blast radius" — only the files and symbols actually impacted by your change — and sends only those to the AI.

**Engine 2** injects an override directive into the prompt that forces the model to skip monologues and deliver code directly.

---

## 🛠️ Installation — All Options

### Option 1 — pip (Recommended, no shell script needed)

```bash
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
token-reduce setup
```

### Option 2 — pip with virtual environment (isolated install)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install git+https://github.com/Mustafaraza89/Reduce-token.git
token-reduce setup
```

### Option 3 — Clone + install locally

```bash
git clone https://github.com/Mustafaraza89/Reduce-token.git
cd Reduce-token
pip install -e .
token-reduce setup
```

### Option 4 — 1-Click shell installer (after cloning)

```bash
git clone https://github.com/Mustafaraza89/Reduce-token.git
cd Reduce-token
chmod +x install.sh && ./install.sh
```

> **Requirements:** Python 3.9+ and Git. No other dependencies.

---

## 🕹️ How to Use

### Terminal (Universal)

```bash
# Analyze + override AI thinking + copy to clipboard:
token-reduce /

# With a query:
token-reduce / --query "fix the authentication bug"
```

### Optional Shell Aliases

Add to `~/.zshrc` or `~/.bashrc`:

```bash
alias tr='token-reduce'
```

Then: `tr /` — shortest possible command.

---

### Editor Integrations

Run `token-reduce setup` to install all of these automatically:

| Editor | How It Works |
|---|---|
| **Claude Code** | `/reduce` and `/reducetoken` slash commands |
| **Cursor AI** | `.cursor/rules/reduce-token.mdc` auto-applied |
| **Gemini / Antigravity** | `GEMINI.md` workspace rule |
| **VS Code** | Command Palette → Run Task → "ReduceToken: Direct Context" |
| **GitHub Copilot** | `.github/copilot-instructions.md` auto-read by Copilot |

---

## 🥊 Direct Modes

| Mode | Output Savings | Behavior |
|---|---|---|
| `mild` | ~40% | Concise senior-engineer style, no pleasantries |
| `full` *(default)* | ~65% | Telegraphic — direct code & diffs, monologue silenced |
| `raw` | ~75% | Pure code/diff only, zero English prose |
| `off` | 0% | Normal AI output |

```bash
token-reduce /                           # full mode (default)
token-reduce / --caveman raw             # raw mode, max savings
token-reduce / --max-tokens 2000         # strict token budget
```

---

## 📊 Live Token Savings Report

Every prompt shows real-time savings at the top:

```
# ReduceToken Context Prompt (gemini)

> ⚡ ReduceToken Optimization Engine:
> - Input Tokens: ~1,240 tokens (saved 89.2% vs ~11,480 full candidate tokens)
> - Output Mode: REDUCETOKEN DIRECT (estimated ~65% output tokens saved)
```

---

## 🛠️ Full CLI Reference

| Command | Description |
|---|---|
| `token-reduce /` | Universal slash command — builds context + copies to clipboard |
| `token-reduce setup` | Install editor integrations (Claude, Cursor, Gemini, VS Code, Copilot) |
| `token-reduce build` | Scan codebase and build/update AST graph index |
| `token-reduce use` | Full options: `--assistant`, `--max-tokens`, `--copy`, `--print` |
| `token-reduce sync` | Incrementally sync changed files only |
| `token-reduce blast` | Compute raw blast radius for specific files |
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
├── install.sh                      # Optional 1-click shell installer
├── GEMINI.md                       # Gemini / Antigravity workspace rule
├── pyproject.toml                  # pip package config
├── token_reduce/
│   ├── cli.py                      # CLI entry point
│   ├── context_pack.py             # Blast radius → context builder
│   ├── caveman.py                  # ReduceToken Direct Engine
│   ├── slash_commands.py           # Editor integration installer
│   └── ...                        # Parsers, graph engine, DB layer
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
