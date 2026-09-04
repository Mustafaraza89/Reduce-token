---
description: /review - Staff Engineer code review: find race conditions & production bugs on blast radius
---
Execute Staff Engineer review:
1. Run `token-reduce review --copy --print` to generate blast radius for the active change.
2. Audit race conditions, edge-case regressions, and missing error handling strictly on impacted files.
3. Output direct code fixes and minimal diffs with zero conversational filler.
