# Learning Log Index — Agent Full-Stack

> INDEX ONLY (context economy). Full entries live in `logs/NNNN-slug.md`, one file per session.
> Startup: read this index; open a specific log file only when its detail is needed.
> Writing convention: end of session → write `logs/NNNN-slug.md` (full detail, English, stranger-relearnable) + add ONE line below.

| # | Date | Topic | Key takeaway | File |
|---|---|---|---|---|
| 0004 | 2026-11-08 | Tool use — empty-input saga (0003) | `input` vs `input_schema` typo = silent contract failure; dump RAW request before blaming infra; CWD vs script dir; parallel tool calls; hard cap | [logs/0004-tool-use-empty-input-saga.md](logs/0004-tool-use-empty-input-saga.md) |
| 0003 | 2026-11-08 | Structured output passed (0002) | schema-in-prompt works first try; extraction/validation = insurance; parsed output feeds downstream code | [logs/0003-structured-output.md](logs/0003-structured-output.md) |
| 0002 | 2026-11-07 | Streaming + structured briefing (0001) | ThinkingDelta vs SignatureDelta; allowlist > denylist parsing; streaming chain buffers at every hop | [logs/0002-streaming-and-structured-briefing.md](logs/0002-streaming-and-structured-briefing.md) |
| 0001 | 2026-11-07 | Relay setup, protocol anatomy (0000) | /models = config plane not capability; model availability = (key→group→channel); OpenAI vs Anthropic protocol table; thinking budget pool | [logs/0001-relay-setup-and-protocols.md](logs/0001-relay-setup-and-protocols.md) |

## Open items (not session-scoped)

- **SECURITY (urgent): rotate leaked relay key** — both `~/.claude/settings.json` ANTHROPIC_AUTH_TOKEN and `projects/hello-agent/.env`. Pending since 2026-11-07.
- 0003 final rerun from a different directory (verify CWD anchoring + break).
