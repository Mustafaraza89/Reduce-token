# ⚡ ReduceToken

> **Universal Token Optimization Framework for AI Coding Assistants & gstack Workflows**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 18 Passing](https://img.shields.io/badge/tests-18%20passing-brightgreen.svg)]()
[![gstack Ready](https://img.shields.io/badge/gstack-integrated-purple.svg)](https://github.com/garrytan/gstack)

**ReduceToken** dramatically reduces the tokens consumed by AI coding assistants. Works out-of-the-box with **Claude Code, Cursor, Gemini, GitHub Copilot, VS Code, and Garry Tan's gstack framework** via simple slash commands.

- **Input Token Reduction: 80% – 95%** — via AST Knowledge Graph & Blast Radius Analysis
- **Output Token Reduction: 50% – 75%** — via ReduceToken Direct Engine (silences AI monologue & filler)
- **gstack Framework Synergy** — pre-flight token optimizer for `/plan-eng-review`, `/review`, `/cso`, `/qa`, and `/ship`

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

**Done.** All slash commands (`/reduce`, `/reducetoken`, `/gstack-reduce`) are installed **globally** in `~/.claude/commands/` and work across every project on your machine.

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

## 🤝 ReduceToken + gstack Integration

[gstack](https://github.com/garrytan/gstack) is Garry Tan's virtual software engineering team framework for Claude Code (23 specialists including CEO, Eng Manager, Staff Reviewer, CSO, and QA). 

Running gstack on mid-to-large repositories often burns **tens of thousands of tokens** because reviews inspect broad files and agents produce long reasoning monologues.

**ReduceToken supercharges gstack by solving both problems:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REDUCETOKEN + GSTACK SYNERGY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  gstack Specialist Personas          ReduceToken Dual-Engine                │
│  • /plan-eng-review (Architecture)  ──▶ AST Blast Radius (Only impacted)    │
│  • /review (Staff Bug Hunter)       ──▶ Call-graph caller/callee tracing    │
│  • /cso (Security Threat Model)     ──▶ Scoped attack surface analysis      │
│  • /ship (Release Engineer)         ──▶ Minimal diffs + direct brevity      │
│  ⬇️                                     ⬇️                                   │
│  Full Engineering Team Rigor        Cuts 80-95% Input + 50-75% Output Tokens│
└─────────────────────────────────────────────────────────────────────────────┘
```

### Using gstack with ReduceToken

```bash
# Run Staff Engineer review with minimal blast-radius:
token-reduce gstack --skill review

# Run Architecture Eng-Manager planning:
token-reduce gstack --skill plan-eng-review

# Run Security CSO audit on changed surface:
token-reduce gstack --skill cso

# Or use the slash command directly in Claude Code:
/gstack-reduce
```

Supported gstack personas: `office-hours`, `plan-ceo-review`, `plan-eng-review`, `review`, `investigate`, `cso`, `qa`, `ship`, `autoplan`.

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

---

## 🕹️ How to Use

### Main Commands

```bash
# Builds blast radius context + injects Direct Engine override + copies to clipboard:
token-reduce /

# Run gstack review with blast-radius optimization:
token-reduce gstack --skill review

# Full form with custom parameters:
token-reduce use --caveman full --copy --print
```

### Slash Commands in Claude Code

Run `token-reduce setup` once and these are globally available:

| Command | What It Does |
|---|---|
| `/reduce` | Runs ReduceToken context optimizer for current changes |
| `/reducetoken` | Activates Direct Mode — zero filler, instant code output |
| `/gstack-reduce` | Optimizes gstack sprint skills (`/review`, `/ship`, `/plan-eng-review`) |

### Editor Integrations

| Editor | How It Works |
|---|---|
| **Claude Code** | Global slash commands in `~/.claude/commands/` |
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
token-reduce gstack --skill review --caveman raw  # gstack in raw mode
token-reduce use --max-tokens 2000 --copy --print # strict token budget
```

---

## 📊 Live Token Savings Report

Every run shows real-time savings in the terminal and at the top of the prompt:

```
mode=gstack+ReduceToken skill=/review role="Staff Engineer / Production Bug Hunter"
changed=src/auth.py,src/utils.py
tokens_input=~1,240  baseline=~11,480  saved=89.2%
reducetoken_mode=DIRECT (est_output_saved=~65% + thinking_overridden)
clipboard=copied gstack+ReduceToken prompt to system clipboard!
```

---

## 🛠️ Full CLI Reference

| Command | Description |
|---|---|
| `token-reduce /` | Main command — blast radius + Direct Engine prompt, copied to clipboard |
| `token-reduce gstack` | Run gstack sprint review/planning with token reduction (`--skill <name>`) |
| `token-reduce setup` | One-time setup: build graph + install editor integrations + git hooks |
| `token-reduce use` | Daily command with full flag control (`--caveman`, `--max-tokens`, `--copy`, `--print`) |
| `token-reduce build` | Scan codebase and build/update AST graph index |
| `token-reduce sync` | Incrementally sync only changed files |
| `token-reduce blast` | Show raw blast radius for specific files |
| `token-reduce context` | Generate context pack as JSON or Markdown |
| `token-reduce status` | Show index stats — files, symbols, call edges, DB size |
| `token-reduce clean` | Clean graph DB and cache |
| `token-reduce watch` | Background daemon for real-time incremental indexing |

---

## 💻 Supported Languages

Python, TypeScript, JavaScript, Go, Rust, Java, C, C++, C#, Ruby, PHP, Swift, Kotlin, Jupyter Notebooks

---

## 🧪 Running Tests

```bash
python -m unittest discover -s tests -v
```

**All 18 tests pass in under 0.1 seconds.**

---

## 📁 Project Structure

```
Reduce-token/
├── install.sh                      # Optional shell installer
├── GEMINI.md                       # Gemini / Antigravity workspace rule
├── pyproject.toml                  # pip package config
├── token_reduce/
│   ├── cli.py                      # CLI entry point (token-reduce command)
│   ├── context_pack.py             # Blast radius → context builder
│   ├── caveman.py                  # ReduceToken Direct Engine (output override)
│   ├── gstack.py                   # gstack framework integration module
│   ├── slash_commands.py           # Editor integration installer
│   └── ...                        # Language parsers, graph engine, DB layer
├── .claude/commands/               # Claude Code slash commands (/reduce, /reducetoken, /gstack-reduce)
├── .cursor/rules/                  # Cursor AI rule
├── .github/copilot-instructions.md # Copilot instructions
├── .vscode/tasks.json              # VS Code tasks
└── tests/test_token_reduce.py      # 18-test suite
```

---

## 🤝 Contributing

PRs welcome. Open an issue first to discuss your change.

---

## 📄 License

MIT — free for personal and commercial use.
