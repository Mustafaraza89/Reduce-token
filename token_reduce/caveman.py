from __future__ import annotations

CAVEMAN_CHOICES = ("off", "mild", "full", "raw")

# Directive to override reasoning/thinking models (Gemini Thinking, Claude 3.7 Thinking, o1/o3)
# and conversational filler across all LLMs.
THINKING_OVERRIDE_DIRECTIVE = """
[CRITICAL SYSTEM OVERRIDE - ZERO CONVERSATIONAL FILLER]
1. DO NOT think out loud, monologue, or provide conversational preambles.
2. DO NOT say "Sure!", "Certainly!", "I would be happy to help", "Here is the code", or "In summary".
3. Jump DIRECTLY to the solution/code/diff with zero conversational padding.
4. If code is needed, output ONLY the exact code changes or minimal diff.
5. Save every output token possible: Deliver maximum signal with minimum tokens.
""".strip()

CAVEMAN_LEVELS = {
    "mild": """
### Mode: Concise Senior Engineer (Direct)
- Be extremely brief and direct.
- Code-first: output the solution immediately.
- Explanations in 1-3 crisp bullet points maximum.
- No pleasantries, no fluff, no re-explaining what the user already knows.
""".strip(),
    "full": """
### Mode: ReduceToken Direct (Maximum Signal)
- Direct telegraphic engineering mode: minimal words, maximum signal.
- No filler words, no grammar padding, no conversational framing.
- Output exact code changes / diffs first.
- Brief rationale in short fragments: "<cause>. <fix>. <verify>."
- Save maximum output tokens.
""".strip(),
    "raw": """
### Mode: ReduceToken Raw Machine (Zero Natural Language)
- ZERO natural language explanation.
- Output ONLY code blocks, file edits, or executable commands.
- If explanation absolutely needed, use single inline code comment.
""".strip(),
}


def format_caveman_directive(level: str = "full", assistant: str = "generic") -> str:
    level = level.lower().strip()
    if level not in CAVEMAN_LEVELS:
        return ""

    body = CAVEMAN_LEVELS[level]
    lines = [
        "## ⚡ ReduceToken Direct Engine",
        "",
        THINKING_OVERRIDE_DIRECTIVE,
        "",
        body,
    ]
    return "\n".join(lines)


def estimate_output_savings_pct(level: str) -> float:
    level = level.lower().strip()
    if level == "raw":
        return 75.0
    if level == "full":
        return 65.0
    if level == "mild":
        return 40.0
    return 0.0
