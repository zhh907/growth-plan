# Learning Log Index — Agent Full-Stack

> INDEX ONLY (context economy). Full entries live in `logs/NNNN-slug.md`, one file per session.
> Startup: read this index; open a specific log file only when its detail is needed.
> Writing convention: end of session → write `logs/NNNN-slug.md` (full detail, English, stranger-relearnable) + add ONE line below.

| # | Date | Topic | Key takeaway | File |
|---|---|---|---|---|
| 0007 | 2026-11-11 | Step C: evals — Phase 0 closes on numbers | control group is non-negotiable (exposed calibration drift invisible otherwise); rubric ambiguity = FP root cause (objective normalization vs subjective sizing philosophy); 4/4 hits + 1 known FP; cost ∝ file size (77 lines in=2.2K vs 700 lines in=206K); error-input robustness passed twice | [logs/0007-evals-stepc.md](logs/0007-evals-stepc.md) |
| 0006 | 2026-11-10 | 0005 Step B: wiring + first real audit | domain knowledge → SYSTEM_PROMPT checklist; assistant=tool_use / user=tool_result direction; 7-bug debug saga (entry guard, filter typo, indent, max_tokens arithmetic); glm thinking blocks; hallucinated line count self-corrected via error dicts; UTF-16LE .mq4 doubles lines; cost: in=206K/audit; real-EA verdict 2 hits + 0 false positives | [logs/0006-mql4-analyzer-stepb.md](logs/0006-mql4-analyzer-stepb.md) |
| 0005 | 2026-11-08 | Script → CLI tool (0004) | deterministic shell wraps probabilistic core; return > print for composability; exit codes 0/1/2 = pipeline handshake; stderr keeps data channel clean; nargs="+" = graceful degradation | [logs/0005-cli-agent.md](logs/0005-cli-agent.md) |
| 0004 | 2026-11-08 | Tool use — empty-input saga (0003) | `input` vs `input_schema` typo = silent contract failure; dump RAW request before blaming infra; CWD vs script dir; parallel tool calls; hard cap | [logs/0004-tool-use-empty-input-saga.md](logs/0004-tool-use-empty-input-saga.md) |
| 0003 | 2026-11-08 | Structured output passed (0002) | schema-in-prompt works first try; extraction/validation = insurance; parsed output feeds downstream code | [logs/0003-structured-output.md](logs/0003-structured-output.md) |
| 0002 | 2026-11-07 | Streaming + structured briefing (0001) | ThinkingDelta vs SignatureDelta; allowlist > denylist parsing; streaming chain buffers at every hop | [logs/0002-streaming-and-structured-briefing.md](logs/0002-streaming-and-structured-briefing.md) |
| 0001 | 2026-11-07 | Relay setup, protocol anatomy (0000) | /models = config plane not capability; model availability = (key→group→channel); OpenAI vs Anthropic protocol table; thinking budget pool | [logs/0001-relay-setup-and-protocols.md](logs/0001-relay-setup-and-protocols.md) |

## Open items (not session-scoped)

- **SECURITY (urgent): rotate leaked relay key** — both `~/.claude/settings.json` ANTHROPIC_AUTH_TOKEN and `projects/hello-agent/.env`. Pending since 2026-11-07.
- ~~0003 final rerun from a different directory~~ CLOSED 2026-11-08: anchoring verified via 0004 run from `~` (tool returned absolute path).
