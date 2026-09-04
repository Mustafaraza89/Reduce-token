# ⚡ ReduceToken

> **Universal Token Optimization Framework & Specialist Squad for AI Coding Assistants**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 21 Passing](https://img.shields.io/badge/tests-21%20passing-brightgreen.svg)]()

**ReduceToken** dramatically cuts the tokens consumed by AI coding assistants while turning your AI into a full virtual engineering team. Works out-of-the-box with **Claude Code, Cursor, Gemini, GitHub Copilot, VS Code, and any terminal** via universal slash commands and native Model Context Protocol (MCP).

- **Input Token Reduction: 80% – 95%** — via AST Knowledge Graph & Blast Radius Analysis
- **Output Token Reduction: 50% – 75%** — via ReduceToken Direct Engine (silences AI monologue & filler)
- **Objective Risk Scoring & Test Gap Analysis** — fan-in analysis, sensitive file flags, and test gap detector (0–100 score)
- **Native stdio Model Context Protocol (MCP) Server** — directly exposes tools to Claude Desktop, Cursor, and VS Code
- **Role-Based Engineering Squad** — dedicated slash commands for Review, Planning, Security, QA, and Shipping

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

**Done.** All slash commands are installed **globally** in `~/.claude/commands/` and work in every project across your machine.

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

## 👥 ReduceToken Specialist Squad (Role-Based Slash Commands)

ReduceToken equips your AI assistant with specialized engineering roles that each run on the exact blast radius of your code change:

| Slash Command | Role | What It Does |
|---|---|---|
| **`/review`** | **Staff Engineer** | Audits race conditions, regressions, and incomplete error paths. Direct code diffs. |
| **`/plan`** | **Engineering Manager** | Locks call-graph data flow, state machines, and test matrix before coding. |
| **`/security`** | **Chief Security Officer (CSO)** | OWASP Top 10 + STRIDE threat model on the modified attack surface. |
| **`/qa`** | **QA Lead** | Generates atomic regression tests and verifies edge cases on modified symbols. |
| **`/ship`** | **Release Engineer** | Runs pre-flight checks, verifies test coverage delta, and drafts concise PR notes. |
| **`/debug`** | **Root Cause Debugger** | Traces caller-callee call paths through the AST graph. Zero speculative fixes. |
| **`/strategy`** | **Founder Strategy** | 6 forcing questions to challenge premises and scope the narrowest wedge to ship. |
| **`/reduce`** | **Context Optimizer** | Universal blast-radius context builder for any task. |
| **`/reducetoken`** | **Direct Mode** | Instant code/diffs, zero conversational filler, suppresses thinking preambles. |

### CLI Equivalents

You can run any specialist workflow directly from the terminal:

```bash
token-reduce review       # Staff Engineer review on changed files
token-reduce plan         # Architecture planning gate
token-reduce security     # CSO security audit on attack surface
token-reduce qa           # QA regression test generator
token-reduce ship         # Release PR preparation
token-reduce debug        # Root cause AST tracer
token-reduce strategy     # Product strategy session
token-reduce risk         # Objective change risk scoring & test gap detector
```

---

## 🤔 Why Do You Need This?

When you use AI for coding, two critical problems burn your token budget:

### Problem 1 — Input Token Bloat
The AI reads your entire repo or 10–15 large files:
- Wastes **10,000–50,000+ input tokens** per prompt
- Fills the context window → model loses focus → hallucinations

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

## 🕹️ Daily Workflow

### Main Commands

```bash
# Builds blast radius context + injects Direct Engine override + copies to clipboard:
token-reduce /

# Staff Engineer review on current changes:
token-reduce review

# Eng Manager architecture gate:
token-reduce plan

# Full form with custom parameters:
token-reduce use --caveman full --copy --print
```

### Editor Integrations

| Editor | How It Works |
|---|---|
| **Claude Code** | Global slash commands in `~/.claude/commands/` (`/review`, `/plan`, `/reduce`, etc.) |
| **Cursor AI** | `.cursor/rules/reduce-token.mdc` auto-applied & `.cursor/mcp.json` |
| **Gemini / Antigravity** | `GEMINI.md` workspace rule auto-loaded |
| **VS Code** | Command Palette tasks & `.vscode/mcp.json` native MCP server |
| **GitHub Copilot** | `.github/copilot-instructions.md` auto-read by Copilot |
| **MCP (Model Context Protocol)** | stdio MCP server for Claude Desktop, Cursor, and VS Code |

---

## 🛡️ Objective Risk Scoring & Test Gap Detector

ReduceToken calculates an objective 0–100 risk score based on AST call graph fan-in, blast radius magnitude, sensitive components modified (auth, crypto, billing, migrations), and automated test gap detection:

```bash
token-reduce risk
```

**Live Output:**
```
Risk Assessment: 🟠 HIGH (Score: 70/100)
Fan-in Count: 5
Impacted Files: 11
Test Gaps (2 modified file(s) lack tests):
  ❌ token_reduce/mcp.py
  ❌ token_reduce/risk.py
Risk Factors:
  • Large blast radius: 11 dependent files affected
  • Moderate caller fan-in: 5 external files call modified symbols
  • Test gaps detected: 2 modified file(s) lack test coverage
```

---

## 🔌 Native Model Context Protocol (MCP) Server

ReduceToken includes a native, zero-dependency stdio Model Context Protocol (MCP) server. When you run `token-reduce setup`, configuration files are auto-generated for **Cursor** (`.cursor/mcp.json`) and **VS Code** (`.vscode/mcp.json`).

### Exposed MCP Tools
1. **`reducetoken_get_context`**: Provides token-reduced blast-radius context directly to your agent.
2. **`reducetoken_blast_radius`**: Exposes impacted nodes and call graph dependencies.
3. **`reducetoken_risk_score`**: Returns objective risk score, fan-in count, sensitive flags, and test gaps.
4. **`reducetoken_specialist`**: Triggers role-based analysis (review, plan, security, qa, ship, debug, strategy).

To run manually:
```bash
token-reduce mcp
```

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
token-reduce review --caveman raw                 # review in raw mode
token-reduce use --max-tokens 2000 --copy --print # strict token budget
```

---

## 📊 Live Token Savings Report

Every run shows real-time savings in the terminal and at the top of the prompt:

```
mode=ReduceToken role="Staff Engineer Code Reviewer" command=/review
changed=src/auth.py,src/utils.py
tokens_input=~1,240  baseline=~11,480  saved=89.2%
reducetoken_mode=DIRECT (est_output_saved=~65% + thinking_overridden)
clipboard=copied /review prompt to system clipboard!
```

---

## 🛠️ Full CLI Reference

| Command | Description |
|---|---|
| `token-reduce /` | Main command — blast radius + Direct Engine prompt, copied to clipboard |
| `token-reduce review` | Staff Engineer code review on blast radius |
| `token-reduce plan` | Engineering Manager architecture & call-graph planning gate |
| `token-reduce security` | CSO threat model & auth audit on changed attack surface |
| `token-reduce qa` | QA Lead regression tests & edge case verification |
| `token-reduce ship` | Release Engineer pre-flight checks and PR notes |
| `token-reduce debug` | Root cause debugger tracing AST callers |
| `token-reduce strategy` | Founder Strategy session with 6 forcing questions |
| `token-reduce risk` | Objective risk scoring (0-100), fan-in, and test gap detector |
| `token-reduce mcp` | Run native stdio Model Context Protocol (MCP) server |
| `token-reduce setup` | One-time setup: build graph + install editor integrations + git hooks + MCP configs |
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

**All 21 tests pass in under 0.15 seconds.**

---

## 📁 Project Structure

```
Reduce-token/
├── install.sh                      # Optional shell installer
├── GEMINI.md                       # Gemini / Antigravity workspace rule
├── pyproject.toml                  # pip package config
├── token_reduce/
│   ├── cli.py                      # CLI entry point (token-reduce command)
│   ├── risk.py                     # Objective Risk Engine & Test Gap Detector
│   ├── mcp.py                      # Native stdio Model Context Protocol Server
│   ├── context_pack.py             # Blast radius → context builder
│   ├── caveman.py                  # ReduceToken Direct Engine (output override)
│   ├── specialists.py              # Specialist squad roles (Review, Plan, CSO, QA, Ship)
│   ├── slash_commands.py           # Editor integration installer
│   └── ...                        # Language parsers, graph engine, DB layer
├── .claude/commands/               # Global Claude slash commands (/review, /plan, /security, /qa, /ship, /debug, /strategy, /reduce, /reducetoken)
├── .cursor/rules/                  # Cursor AI rule
├── .cursor/mcp.json                # Cursor native MCP config
├── .github/copilot-instructions.md # Copilot instructions
├── .vscode/tasks.json              # VS Code tasks
├── .vscode/mcp.json                # VS Code native MCP config
└── tests/test_token_reduce.py      # 21-test suite
```

---

## 🤝 Contributing

PRs welcome. Open an issue first to discuss your change.

---

## 📄 License

MIT — free for personal and commercial use.
