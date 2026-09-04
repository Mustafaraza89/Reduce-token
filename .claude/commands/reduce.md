---
description: /reduce - Run ReduceToken context optimizer before broad code changes
---
Execute `/reduce` workflow:
Run `token-reduce use --caveman full --copy --print` to generate blast-radius context.
Prioritize only the impacted files and apply ReduceToken direct rules (zero conversational filler, direct diffs).
