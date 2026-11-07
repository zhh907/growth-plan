# 0001 · Relay setup, protocol anatomy, first successful calls (0000-probe)

**Date: 2026-11-07 · Session 1**

## What I did
1. Set up project `projects/hello-agent/`: venv + `openai`/`anthropic`/`python-dotenv`, secrets in `.env` (`chmod 600`).
2. Probed a relay (`api.new13.top`) owned via an API-relay key, using a data-plane probe script (`0000-probe.py`) that fires 5-token test requests per candidate model.
3. Got both protocols working; identified which models respond on which protocol.

## What I learned — key insights

**1. A relay's `/v1/models` list is the CONFIG plane, not the CAPABILITY plane.**
new-api style relays return what the admin configured, not what actually works. Deep health check principle: only a real request proves availability. Probe with `max_tokens=5` to keep cost at fractions of a cent.

**2. Model availability is a property of (key → group → channel config), not of the model.**
Same relay, same key: `glm-5.3` via OpenAI protocol → 404 "not supported by any configured account in this group"; via Anthropic protocol → works. Relays route by MODEL NAME STRING per protocol endpoint; the name `claude-*` maps to a GLM backend. Requesting the "real" backend name fails if no channel exposes it.

**3. OpenAI protocol vs Anthropic protocol (the mental table).**

| Dimension | OpenAI | Anthropic |
|---|---|---|
| Endpoint | `/v1/chat/completions` | `/v1/messages` |
| SDK | `openai` | `anthropic` |
| Auth | `Authorization: Bearer` | `x-api-key` OR `auth_token` (Bearer) |
| Content | string (or mixed array) | typed block array: thinking / text / tool_use |
| Streaming | text chunks (you reassemble blind) | semantic events: content_block_start/delta/stop |
| Tool args | JSON **string** (double-encoded, can be invalid) | already-parsed **dict** |
| Why care | industry de-facto standard, swap models by changing base_url | better agent ergonomics (stream events, typed blocks, tool inputs) |

**4. Thinking models budget "draft + answer" from ONE `max_tokens` pool.**
With `max_tokens=5`, glm-5.3 spent it all on the ThinkingBlock — response contained NO text block at all. Fix: budget for thinking + answer (≥200).

**5. Anthropic response parsing must be type-aware and defensive.**
`r.content` is `[ThinkingBlock, TextBlock, ...]` — never assume `content[0].text`. Use:
```python
text = next((b.text for b in r.content if b.type == "text"), "(no text block)")
```

## Gotchas / errors hit (all real, all instructive)
1. **Empty Bearer header → API_KEY_REQUIRED.** Cause: header used `$OPENAI_API` but variable was `OPENAI_API_KEY`. Lesson: when an error says "missing key" but you set one, suspect variable name first. Verify without leaking: `echo ${OPENAI_API_KEY:+set}`.
2. **`NameError: Excepetion` while handling a 404.** Typo in `except` broke the safety net. Log signature: "During handling of the above exception, another exception occurred" → the except block itself is buggy.
3. **Plaintext key pasted into chat (a.txt incident).** Response: deleted file + rotate key. Doctrine: any secret that touches a chat window/screenshot/log/repo is compromised — rotate. Rotation checklist includes `~/.claude/settings.json` ANTHROPIC_AUTH_TOKEN. (Note to self: still pending as of 2026-11-07.)
4. **"No response" = silent hang.** SDK default timeout is 10 minutes with quiet retries. Bisection tool: raw `curl -m 30` + `-w "%{http_code} %{time_total}"` against the same endpoint — bypasses all code layers.
5. **`(no text block)` printed instead of failure.** Defensive parse default surfaced the truth: all 5 tokens went to thinking (see insight 4).

## Artifacts
- `projects/hello-agent/0000-probe.py` — data-plane model probe (retired, kept as reference)
- `.env` — `BASE_URL`, `API_KEY` (600, never committed)

## Next step
- `0001-streaming.py`: streaming events + thinking/text block discrimination in the stream + usage accounting (the bill).
