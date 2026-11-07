# 0003 · Structured output passed (0002)

**Date: 2026-11-08 · Session 3**

## What I did
Ran `0002-structured-output.py`: schema-prompted JSON risk assessment, parsed & validated end to end.

## What I learned
1. **Explicit schema in prompt works**: model returned clean JSON on the first try — the extraction/validation layers are INSURANCE, not expected path.
2. **Structured output costs more tokens than chat** (78 in / 188 out) — schema text + filled fields. Motivates prompt caching for repeated agent calls.
3. The whole point: parsed output is directly consumable by downstream code (e.g. auto-generate a deploy-block ticket).

## Gotchas
None — first green run.

## Next step
0003-tool-use.py: function calling — the heart of agents.
