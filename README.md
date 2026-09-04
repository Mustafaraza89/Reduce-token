# ⚡ ReduceToken

> **Universal Token Optimization Framework for AI Coding Assistants**  
> **Input Token Reduction (80% - 95%)** via AST Knowledge Graph & Blast Radius  
> **Output Token Reduction (50% - 75%)** & **Thinking Monologue Override** via ReduceToken Direct Engine  
> **Universal Slash Commands (`/`)** across Claude Code, Cursor, Gemini, Antigravity, VS Code, and Terminal CLI.

---

## 🎯 Ye Framework Kis Kaam Ka Hai? (Why You Need This)

Jab aap kisi AI assistant (**Gemini, Claude, ChatGPT, Cursor, Antigravity, Copilot**) se coding karate hain, do badi problems aati hain:

### 1. Input Tokens Waste (Repo Bloat)
Assistant poori repository ya 10-15 lambi files read karta hai. Result:
- 10,000 se 50,000+ input tokens har prompt mein waste hote hain.
- Context window jaldi bhar jati hai.
- Model irrelevant code dekh kar confuse ho jata hai aur hallucinations create karta hai.

### 2. Output Tokens Waste (Thinking Monologue & Conversational Filler)
Modern reasoning models (**Gemini Thinking, Claude 3.7 Thinking, OpenAI o1/o3**) lambe lambe internal monologues aur conversational sentences likhte hain:
- *"Sure! I would be happy to help you with this task. Let's analyze the problem..."*
- *"In summary, the changes we made are..."*
- Result: Output tokens waste hote hain, generation speed bohot slow ho jati hai, aur developer ko code dhundne ke liye scroll karna padta hai.

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
│  SAVINGS: 80% - 95% INPUT TOKENS       SAVINGS: 50% - 75% OUTPUT TOKENS     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 1-Click Fast Installation (`install.sh`)

Is project mein poora automated **1-Click Installer** included hai jo Python check, `.venv` setup, package install, AST graph build, Git hooks aur sabhi AI slash commands ko 10 seconds mein configure kar deta hai:

```bash
# Clone & run 1-click installer:
./install.sh
```

Installer automatically:
1. Python 3.9+ verify karta hai.
2. Virtual environment (`.venv`) banata aur activate karta hai.
3. `token-reduce` ko install karta hai.
4. AST graph index karta hai aur Git hooks install karta hai.
5. Claude, Cursor, Gemini, Copilot aur VS Code ke liye `/` slash commands register karta hai.
6. Convenient terminal alias (`tr` aur `tr/`) set karne ke instructions deta hai.

---

## 🕹️ Universal Slash Command (`/`) System

Aap is framework ko apne favourite editor ya terminal mein direct `/` command se use kar sakte hain:

### 1. Terminal / CLI (`/` Shortcut)
Ek simple command se pura blast radius analyze hoga, thinking override apply hoga, prompt terminal me print hoga aur **seedhe clipboard me copy** ho jayega:

```bash
# Instant slash shortcut (auto-detects changes + copies prompt):
token-reduce /

# With query:
token-reduce / --query "fix token leak in parser"
```

*(Tip: Agar aapne alias banaya hai to sirf `tr /` type karein!)*

### 2. Claude Code CLI
Claude Code me slash commands automatically installed hain:
- `/reduce` : Graph AST analyze karke minimal blast context load karega.
- `/reducetoken` : Direct Mode enable karega (zero filler, instant code).

### 3. Cursor AI
Cursor open karte hi `.cursor/rules/reduce-token.mdc` automatically background me apply rehta hai. Model automatically concise code aur zero conversational fluff deliver karta hai.

### 4. Gemini / Google Antigravity
Workspace root par `GEMINI.md` configured hai jo Antigravity / Gemini model ko instructions deta hai ki direct blast radius context use kare aur reasoning monologue override kare.

### 5. VS Code
Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) -> **Run Task** -> **"ReduceToken: Direct Context"**.

---

## 🥊 ReduceToken Direct Modes

Aap `--caveman` (direct mode) flag se output brevity customize kar sakte hain:

| Mode | Output Token Savings | AI Output Behaviour |
|---|---|---|
| `mild` | **~40% Savings** | **Concise Senior Engineer**: Code-first, zero pleasantries, 1-3 crisp bullet points. |
| `full` *(default)* | **~65% Savings** | **ReduceToken Direct**: Telegraphic style, minimal words, direct code & diffs immediately. Monologue silenced. |
| `raw` | **~75% Savings** | **Raw Machine**: Pure code/diff blocks only. 0% conversational English. |
| `off` | 0% | Normal conversational output. |

### Example CLI Usage:
```bash
# Run with full direct mode (default):
token-reduce /

# Run with Raw Machine (pure code only):
token-reduce / --caveman raw

# Enforce a strict input token budget (e.g. max 2000 tokens):
token-reduce / --max-tokens 2000
```

---

## 📊 Live Token Savings Badge

Har prompt ke top par real-time token reduction metrics generate hote hain jisse aapko live dikhta hai ki kitne tokens bache:

```markdown
# ReduceToken Context Prompt (gemini)

> ⚡ **ReduceToken Optimization Engine**:
> - **Input Tokens**: ~1,240 tokens (saved 89.2% vs ~11,480 full candidate tokens)
> - **Output Mode**: REDUCETOKEN DIRECT (estimated ~65% output tokens saved & thinking monologue overridden)

## ⚡ ReduceToken Direct Engine
[CRITICAL SYSTEM OVERRIDE - ZERO CONVERSATIONAL FILLER]
1. DO NOT think out loud, monologue, or provide conversational preambles.
2. DO NOT say "Sure!", "Certainly!", "I would be happy to help", "Here is the code", or "In summary".
3. Jump DIRECTLY to the solution/code/diff with zero conversational padding.
4. If code is needed, output ONLY the exact code changes or minimal diff.
5. Save every output token possible: Deliver maximum signal with minimum tokens.
```

---

## 🛠️ Complete CLI Command Reference

| Command | Description |
|---|---|
| `./install.sh` | **1-Click Installer**: Full setup in 10 seconds. |
| `token-reduce /` | **Universal Slash Command**: Context + Direct prompt copied to clipboard. |
| `token-reduce use` | Daily command with options: `--assistant`, `--max-tokens`, `--copy`, `--print`, `--launch`. |
| `token-reduce status` | Shows indexed files, symbols by language, call edges, and DB size. |
| `token-reduce build` | Scans codebase and builds/updates graph cache. |
| `token-reduce sync` | Incrementally syncs changed files (`--files`, `--worktree`, `--git-head`). |
| `token-reduce blast` | Computes raw blast radius for files (`--changed <files> --depth 2`). |
| `token-reduce context` | Generates impacted context pack in JSON or markdown. |
| `token-reduce clean` | Cleans graph database and assistant cache (`--all`). |
| `token-reduce watch` | Runs background watcher daemon for real-time indexing. |

---

## 💻 Supported Languages

- **Python** (`.py`, `.ipynb` Jupyter Notebooks)
- **TypeScript / JavaScript** (`.ts`, `.tsx`, `.js`, `.jsx` with relative import and `index` resolution)
- **Go** (`.go`)
- **Rust** (`.rs`)
- **Java** (`.java`)
- **C / C++** (`.c`, `.cpp`, `.h`)
- **C#** (`.cs`), **Ruby** (`.rb`), **PHP** (`.php`), **Swift** (`.swift`), **Kotlin** (`.kt`)

---

## 🧪 Verification & Testing

Is repo mein comprehensive unit test suite included hai jo blast radius, language parser, direct thinking overrides, slash commands aur token estimation verify karta hai:

```bash
python -m unittest discover -s tests -v
```

16/16 tests pass seamlessly in < 0.1s!



