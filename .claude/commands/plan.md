---
description: /plan - Engineering Manager architecture gate: lock call graph & failure modes
---
Execute Architecture & Planning gate:
1. Run `token-reduce plan --copy --print` to generate call-graph dependencies.
2. Lock data flow, error paths, state machines, and test matrix before modifying code.
3. Save maximum tokens by reviewing only caller-callee blast radius.
