# 0002 · Streaming + structured output briefing (0001 run, 0002 briefed)

**Date: 2026-11-07 · Session 2**

## What I did
1. Ran `0001-streaming.py`; hit two real-world stream delta types beyond the basics.
2. Diagnosed "no char-by-char output" — conclusion: answer too short, streaming itself fine (would need longer output or timestamps to see).

## What I learned — key insights

**1. Thinking blocks stream as TWO delta types: `ThinkingDelta` (has `.thinking`) and `SignatureDelta` (has `.signature` only).**
The signature is an anti-tamper proof attached to thinking content (verified when thinking is re-submitted in multi-turn tool use). Crashed on `SignatureDelta.text` → AttributeError.

**2. Allowlist > denylist when parsing external input.**
Denylist (`if has thinking: skip`) breaks when a NEW unknown type arrives (SignatureDelta). Allowlist (`if has .text: print`) survives unknown types silently. External systems evolve — parse for what you WANT, not what you know to avoid.

**3. Streaming is a CHAIN; every hop can buffer: model → provider → relay → SDK → stdout → terminal.**
"Char-by-char" requires real-time pass-through at every layer. Relays commonly buffer SSE. Diagnostic technique: timestamp each event's arrival (`time.time() - t0`) — spread timestamps = healthy stream, clumped = buffering upstream. Bisect with data, not guesses.

**4. Structured output failure modes (briefed, hands-on in 0003 log):**
- chatter before JSON ("Sure! Here is...")
- markdown fences (```json ... ```)
- wrong field names (置信度 instead of confidence)
- invalid JSON (hallucinated comma)

Defense stack: explicit schema in prompt → robust extraction (slice first `{` to last `}`) → post-parse validation (required keys + enum check). Tool-use (next lesson) is the protocol-level guarantee.

## Gotchas
- `AttributeError: 'SignatureDelta' object has no attribute 'text'` — see insight 1/2.

## Artifacts
- `0001-streaming.py` — streaming + allowlist parsing + usage accounting (PASSED)

## Next step
- Run `0002-structured-output.py`; then 0003 tool use.
