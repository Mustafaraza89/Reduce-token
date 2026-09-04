# ⚡ ReduceToken

> **Universal Token Optimization Framework for AI Coding Assistants**

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 16 Passing](https://img.shields.io/badge/tests-16%20passing-brightgreen.svg)]()

**ReduceToken** is an open-source framework that dramatically reduces the number of tokens consumed by AI coding assistants. It works with **Claude Code, Cursor, Gemini, GitHub Copilot, VS Code, and any terminal CLI** — using a simple `/` slash command.

- **Input Token Reduction: 80% – 95%** — via AST Knowledge Graph & Blast Radius Analysis
- **Output Token Reduction: 50% – 75%** — via ReduceToken Direct Engine (silences AI monologue & filler)

---

## 🤔 Why Do You Need This?

When you use an AI assistant (Gemini, Claude, ChatGPT, Cursor, Copilot) for coding, two major problems cause token waste:

### Problem 1 — Input Token Bloat
The AI reads your entire repository or 10–15 large files at once:
- Wastes **10,000–50,000+ input tokens** per prompt
- Fills up the context window quickly
- Causes the model to get confused by irrelevant code → hallucinations

### Problem 2 — Output Token Waste (AI Monologue)
Modern reasoning models (Gemini Thinking, Claude 3.7, OpenAI o1/o3) generate long internal monologues and conversational filler before giving you the actual answer:
- *"Sure! I would be happy to help you with this task. Let's analyze the problem carefully..."*
- *"In summary, the changes we made today include..."*
- This wastes output tokens, slows generation speed, and forces you to scroll through noise to find the code.

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

**Engine 1** builds a static AST (Abstract Syntax Tree) graph of your codebase using SQLite. When you run ReduceToken, it computes only the "blast radius" — the minimal set of files and symbols actually impacted by your change — and feeds only those to the AI.

**Engine 2** injects a system-level override directive into the AI prompt that forces the model to skip reasoning monologues, skip filler phrases, and deliver direct code or diffs immediately.

---

## 🚀 Installation

### Requirements

- **Python 3.9 or higher** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/downloads))
- macOS / Linux / Windows (WSL recommended on Windows)

---

### Option A — 1-Click Installer (Recommended)

**Step 1: Clone the repository**

```bash
git clone https://github.com/Mustafaraza89/Reduce-token.git
cd Reduce-token
```

**Step 2: Run the installer**

```bash
chmod +x install.sh
./install.sh
```

The installer automatically:
1. Checks that Python 3.9+ is installed
2. Creates a Python virtual environment (`.venv`)
3. Installs the `token-reduce` package and all dependencies
4. Builds the AST knowledge graph index for your project
5. Installs Git hooks for real-time incremental sync
6. Registers `/reduce` and `/reducetoken` slash commands in Claude Code, Cursor, Gemini, Copilot, and VS Code
7. Prints alias setup instructions for `tr` and `tr/` shortcuts

**Step 3 (Optional): Add terminal aliases**

After the installer finishes, add these lines to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
alias tr='token-reduce'
alias 'tr/'='token-reduce /'
```

Then reload your shell:

```bash
source ~/.zshrc   # or source ~/.bashrc
```

---

### Option B — Manual Installation

**Step 1: Clone the repository**

```bash
git clone https://github.com/Mustafaraza89/Reduce-token.git
cd Reduce-token
```

**Step 2: Create and activate a virtual environment**

```bash
python3 -m venv .venv

# macOS / Linux:
source .venv/bin/activate

# Windows (WSL):
source .venv/bin/activate
```

**Step 3: Install the package**

```bash
pip install -e .
```

**Step 4: Build the AST graph index**

```bash
token-reduce build
```

**Step 5: Install slash commands for your editors**

```bash
token-reduce setup
```

This creates:
- `.claude/commands/reduce.md` and `.claude/commands/reducetoken.md` — Claude Code slash commands
- `.cursor/rules/reduce-token.mdc` — Cursor AI rule
- `GEMINI.md` — Gemini / Antigravity workspace rule
- `.vscode/tasks.json` — VS Code task
- `.github/copilot-instructions.md` — GitHub Copilot instructions

---

## 🕹️ How to Use

### Universal Slash Command (Terminal)

The fastest way to use ReduceToken — just run this in your terminal inside any project:

```bash
# Analyze blast radius, override AI thinking, copy prompt to clipboard:
token-reduce /

# With a specific query:
token-reduce / --query "fix token leak in parser"

# If you set up the alias:
tr /
```

This command:
1. Scans your git-changed files
2. Computes the minimal blast radius (only impacted code)
3. Injects the ReduceToken Direct Engine override directive
4. Copies the final optimized prompt to your clipboard
5. Prints token savings stats in the terminal

---

### Editor Integrations

#### Claude Code

Slash commands are automatically available after `token-reduce setup`:

| Command | What It Does |
|---|---|
| `/reduce` | Loads minimal AST blast context for the current change |
| `/reducetoken` | Enables Direct Mode — zero filler, instant code output |

#### Cursor AI

The `.cursor/rules/reduce-token.mdc` rule is automatically applied when you open the project in Cursor. The model will deliver concise, direct code with no conversational noise.

#### Gemini / Google Antigravity

The `GEMINI.md` file in the project root configures Gemini and Antigravity to use blast radius context and override the reasoning monologue automatically.

#### VS Code

Open the Command Palette (`Cmd+Shift+P` on Mac / `Ctrl+Shift+P` on Windows):
→ **Run Task** → **"ReduceToken: Direct Context"**

#### GitHub Copilot

`.github/copilot-instructions.md` is automatically read by Copilot in VS Code to apply ReduceToken-style output instructions.

---

## 🥊 ReduceToken Direct Modes

Control how aggressively the AI output is compressed:

| Mode | Output Token Savings | AI Behavior |
|---|---|---|
| `mild` | ~40% savings | Concise senior engineer style — code-first, no pleasantries, short bullet points |
| `full` *(default)* | ~65% savings | Telegraphic style — minimal words, direct code & diffs, monologue silenced |
| `raw` | ~75% savings | Pure machine — only code/diff blocks, zero conversational English |
| `off` | 0% | Normal conversational AI output |

```bash
# Default (full mode):
token-reduce /

# Raw mode (pure code only, maximum savings):
token-reduce / --caveman raw

# Enforce a strict input token budget (e.g. max 2000 tokens):
token-reduce / --max-tokens 2000

# Mild mode:
token-reduce use --caveman mild --assistant gemini --copy --print
```

---

## 📊 Live Token Savings Report

Every prompt generated by ReduceToken includes a real-time savings badge at the top:

```
# ReduceToken Context Prompt (gemini)

> ⚡ ReduceToken Optimization Engine:
> - Input Tokens: ~1,240 tokens (saved 89.2% vs ~11,480 full candidate tokens)
> - Output Mode: REDUCETOKEN DIRECT (estimated ~65% output tokens saved & thinking monologue overridden)
```

---

## 🛠️ Full CLI Reference

| Command | Description |
|---|---|
| `./install.sh` | **1-Click Installer** — Full setup in ~10 seconds |
| `token-reduce /` | **Universal Slash Command** — Context + Direct prompt, copied to clipboard |
| `token-reduce use` | Daily use command with full options (`--assistant`, `--max-tokens`, `--copy`, `--print`, `--launch`) |
| `token-reduce build` | Scan codebase and build/update the AST graph index |
| `token-reduce sync` | Incrementally sync only changed files (`--files`, `--worktree`, `--git-head`) |
| `token-reduce blast` | Compute raw blast radius for specific files (`--changed <files> --depth 2`) |
| `token-reduce context` | Generate impacted context pack in JSON or Markdown |
| `token-reduce status` | Show indexed files, symbols by language, call edges, and DB size |
| `token-reduce setup` | Install slash commands for all supported editors |
| `token-reduce clean` | Clean graph database and assistant cache (`--all`) |
| `token-reduce watch` | Run background watcher daemon for real-time incremental indexing |

---

## 💻 Supported Languages

| Language | Extensions |
|---|---|
| Python | `.py`, `.ipynb` (Jupyter Notebooks) |
| TypeScript / JavaScript | `.ts`, `.tsx`, `.js`, `.jsx` |
| Go | `.go` |
| Rust | `.rs` |
| Java | `.java` |
| C / C++ | `.c`, `.cpp`, `.h` |
| C# | `.cs` |
| Ruby | `.rb` |
| PHP | `.php` |
| Swift | `.swift` |
| Kotlin | `.kt` |

---

## 🧪 Running Tests

The repository includes a full unit test suite covering blast radius calculation, language parsers, Direct Engine directives, slash command installation, and token estimation:

```bash
# Make sure your venv is active first:
source .venv/bin/activate

# Run all tests:
python -m unittest discover -s tests -v
```

**All 16 tests pass in under 0.1 seconds.**

---

## 📁 Project Structure

```
Reduce-token/
├── install.sh                      # 1-Click installer script
├── GEMINI.md                       # Gemini / Antigravity workspace rule
├── README.md                       # This file
├── setup.py / pyproject.toml       # Package config
├── token_reduce/
│   ├── cli.py                      # Main CLI entry point (token-reduce command)
│   ├── context_pack.py             # AST blast radius → markdown context builder
│   ├── easy_mode.py                # High-level use flow (UseResult dataclass)
│   ├── caveman.py                  # ReduceToken Direct Engine (output override)
│   ├── slash_commands.py           # Editor slash command installer
│   └── ...                        # Language parsers, graph engine, DB layer
├── .claude/commands/
│   ├── reduce.md                   # Claude Code /reduce command
│   └── reducetoken.md              # Claude Code /reducetoken command
├── .cursor/rules/
│   └── reduce-token.mdc            # Cursor AI rule
├── .github/
│   └── copilot-instructions.md     # GitHub Copilot instructions
├── .vscode/
│   └── tasks.json                  # VS Code tasks
└── tests/
    └── test_token_reduce.py        # 16-test unit test suite
```

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss what you would like to change.

---

## 📄 License

MIT License — free to use in personal and commercial projects.
