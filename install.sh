#!/usr/bin/env bash
# ==============================================================================
# ReduceToken Engine - 1-Click Installer
# Universal Token Optimization (AST Knowledge Graph + Direct Thinking Override)
# ==============================================================================

set -e

# ANSI Color Codes
BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
MAGENTA="\033[35m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
cat << "BANNER"
  _______    _                    _____           _                  
 |__   __|  | |                  |  __ \         | |                 
    | | ___ | | _____ _ __ ______| |__) |___   __| |_   _  ___ ___   
    | |/ _ \| |/ / _ \ '_ \______|  _  // _ \ / _` | | | |/ __/ _ \  
    | | (_) |   <  __/ | | |     | | \ \  __/| (_| | |_| | (_|  __/  
    |_|\___/|_|\_\___|_| |_|     |_|  \_\___| \__,_|\__,_|\___\___|  
                           REDUCETOKEN ENGINE
BANNER
echo -e "${RESET}"

echo -e "${BOLD}🚀 Starting 1-Click Installation & Setup...${RESET}\n"

# 1. Check Python installation
echo -e "${MAGENTA}▶ [1/5] Checking Python environment...${RESET}"
PYTHON_BIN=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        PY_VER=$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)
        PY_MAJOR=$("$cmd" -c 'import sys; print(sys.version_info.major)' 2>/dev/null || true)
        PY_MINOR=$("$cmd" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null || true)
        if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 9 ]; then
            PYTHON_BIN="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo -e "${RED}❌ Error: Python 3.9+ is required, but none was found.${RESET}"
    echo "Please install Python 3.9 or higher and try again."
    exit 1
fi
echo -e "${GREEN}✓ Found Python: $($PYTHON_BIN --version) (${PYTHON_BIN})${RESET}"

# 2. Setup Virtual Environment
echo -e "\n${MAGENTA}▶ [2/5] Setting up Virtual Environment (.venv)...${RESET}"
if [ ! -d ".venv" ]; then
    "$PYTHON_BIN" -m venv .venv
    echo -e "${GREEN}✓ Created new virtual environment in .venv${RESET}"
else
    echo -e "${GREEN}✓ Existing .venv found${RESET}"
fi

# Source virtualenv
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${RESET}"

# 3. Install Package
echo -e "\n${MAGENTA}▶ [3/5] Checking/installing token-reduce package...${RESET}"
if command -v token-reduce &> /dev/null; then
    echo -e "${GREEN}✓ Package token-reduce already installed in environment${RESET}"
else
    pip install --quiet --upgrade pip setuptools wheel 2>/dev/null || true
    pip install -e . 2>/dev/null || pip install --no-build-isolation -e .
    echo -e "${GREEN}✓ Package token-reduce installed successfully${RESET}"
fi

# 4. Run Setup & Indexing
echo -e "\n${MAGENTA}▶ [4/5] Initializing AST Knowledge Graph & Slash Commands...${RESET}"
token-reduce setup --no-watch

# 5. Shell Alias Recommendations
echo -e "\n${MAGENTA}▶ [5/5] Configuring Shell Integrations & Aliases...${RESET}"

SHELL_NAME=$(basename "${SHELL:-bash}")
RC_FILE=""
if [ "$SHELL_NAME" = "zsh" ]; then
    RC_FILE="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    if [ -f "$HOME/.bashrc" ]; then
        RC_FILE="$HOME/.bashrc"
    else
        RC_FILE="$HOME/.bash_profile"
    fi
fi

ALIAS_CMD="alias tr=\"$(pwd)/.venv/bin/token-reduce\""
SLASH_ALIAS="alias tr/=\"$(pwd)/.venv/bin/token-reduce /\""

# Summary
echo -e "\n${GREEN}${BOLD}═════════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  🎉 ReduceToken Setup Complete!                                     ${RESET}"
echo -e "${GREEN}${BOLD}═════════════════════════════════════════════════════════════════════${RESET}\n"

echo -e "${BOLD}⚡ Dual-Engine Token Optimization Active:${RESET}"
echo -e "  1. ${CYAN}AST Knowledge Graph Engine${RESET}  : Cuts 80-95% input tokens via blast-radius."
echo -e "  2. ${YELLOW}ReduceToken Direct Engine${RESET}   : Cuts 50-75% output tokens & silences thinking monologue."
echo -e "  3. ${MAGENTA}Live Token Savings Metrics${RESET} : Live report of exact tokens saved and reduction %.\n"

echo -e "${BOLD}🎯 Universal Slash Command Support (Ready out of the box):${RESET}"
echo -e "  • ${CYAN}Claude Code${RESET}       : Type ${BOLD}/reduce${RESET} or ${BOLD}/reducetoken${RESET} in Claude chat"
echo -e "  • ${CYAN}Cursor AI${RESET}         : Loaded via ${BOLD}.cursor/rules/reduce-token.mdc${RESET}"
echo -e "  • ${CYAN}Gemini / Antigravity${RESET} : Embedded in ${BOLD}GEMINI.md${RESET}"
echo -e "  • ${CYAN}Terminal / CLI${RESET}    : Run ${BOLD}token-reduce /${RESET} or ${BOLD}tr /${RESET}"
echo -e "  • ${CYAN}VS Code${RESET}           : Use Command Palette -> Run Task -> 'ReduceToken: Direct Context'\n"

echo -e "${BOLD}💡 Pro-Tip: Add convenient shell aliases:${RESET}"
if [ -n "$RC_FILE" ]; then
    echo -e "  Run the following commands to add 'tr' shortcuts to ${CYAN}${RC_FILE}${RESET}:"
    echo -e "    echo '${ALIAS_CMD}' >> ${RC_FILE}"
    echo -e "    echo '${SLASH_ALIAS}' >> ${RC_FILE}"
    echo -e "    source ${RC_FILE}\n"
else
    echo -e "    ${ALIAS_CMD}\n"
fi

echo -e "${BOLD}Try it right now:${RESET}"
echo -e "  ${CYAN}token-reduce / --query \"fix bug in parser\"${RESET}"
echo -e "  ${CYAN}token-reduce /${RESET}\n"
