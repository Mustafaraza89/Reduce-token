## ⚡ ReduceToken Mode
Before editing broad codebase areas:
1. Run `token-reduce / --assistant gemini`
2. Follow ReduceToken rules:
   - Override conversational monologues and thinking intros.
   - Zero filler (no "Sure!", "Certainly!").
   - Output direct code changes and commands immediately.
   - Save maximum tokens.

## ReduceToken Context Workflow
Before broad repository modifications, use ReduceToken context:
- `token-reduce / --assistant gemini`
Prioritize impacted context instead of reading full repository files.

## Token Reduce Context Workflow
Before broad repository modifications, use Token Reduce context:
- `token-reduce use --assistant gemini`
Prioritize impacted context instead of reading full repository files.
