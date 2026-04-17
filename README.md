# token-reduce

`token-reduce` AI coding assistants ke liye context optimizer hai. Ye full repo dubara read karne ke bajay sirf impacted context deta hai.

## 1-minute setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .

token-reduce setup --no-watch
```

## Daily use (simplest)

### Gemini

```bash
token-reduce use --assistant gemini --launch
```

Ye command:

- changed files auto-detect karega
- context generate karega
- Gemini CLI ko prompt stdin se bhejne ki koshish karega
- first run par Gemini auth/login prompt aa sakta hai (expected behavior)

Agar Gemini binary PATH me nahi hai, to fallback:

```bash
token-reduce use --assistant gemini --print
```

Then printed prompt ko Gemini me paste karo.

### Any assistant

```bash
token-reduce use --assistant codex --launch
token-reduce use --assistant claude --launch
token-reduce use --assistant gemini --launch
token-reduce use --assistant chatgpt --launch
token-reduce use --assistant antigravity --launch
```

## If changed files auto-detect nahi ho

```bash
token-reduce use --assistant gemini --changed src/a.py src/b.ts --launch
```

## Useful output files

`use` command yahan files banata hai:

- `.token-reduce/assistant/context-<assistant>.json`
- `.token-reduce/assistant/prompt-<assistant>.md`

## Custom CLI command (if needed)

Agar aapke system me assistant ka command alag hai, `--cmd` use karo:

```bash
token-reduce use --assistant gemini --launch --cmd "gemini"
```

Example custom:

```bash
token-reduce use --assistant gemini --launch --cmd "my-gemini-cli"
```

## Easy mode commands

- `token-reduce setup` -> one-time init + build + install
- `token-reduce use --assistant <name>` -> daily context + prompt generation

## Advanced commands

- `token-reduce init`
- `token-reduce build`
- `token-reduce sync --worktree`
- `token-reduce blast --changed <files>`
- `token-reduce context --changed <files>`
- `token-reduce install`
- `token-reduce watch`
- `token-reduce status`

## Test

```bash
python -m unittest discover -s tests -v
```
