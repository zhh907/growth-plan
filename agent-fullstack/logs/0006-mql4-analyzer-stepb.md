# 0006 · MQL4 analyzer Step B — wiring the agent + a 7-bug debug saga + first real audit

**Date: 2026-11-09 (ran past midnight into 11-10) · Session 6**

## What I did
1. Formalized MY OWN MQL4 bug checklist (domain knowledge into prompt): lot size control / same-bar repeated entries / missing stop loss.
2. Wired Step B into `0005-mql4-analyzer.py`: SYSTEM_PROMPT (role + workflow + checklist + report rules), `execute_tool` dispatcher, `run_agent` loop with `system=`, `main` taking a .mq4 path.
3. Debugged SEVEN character/structure-level bugs in my own transcription — the deepest debugging session so far.
4. Ran the finished agent against my REAL production EA (悦鹤_均线逆势马丁_双边对冲_v2.mq4, 701 logical / 2475 physical lines). It delivered a correct audit: 2 of 3 checklist hits, ZERO false positives.

## Key insights

**1. Step B architecture (what got added):**
- SYSTEM_PROMPT three parts: workflow (recon → ordered patrol → report), bug checklist (THE domain payload — "domain knowledge into prompt, general capability from the model"), report rules (cite line numbers, say "does not apply" explicitly, **do NOT invent bugs beyond the checklist** — the anti-false-positive rein).
- `execute_tool` = dispatch layer; unknown tool names → error dict (open-world defense).
- Protocol direction: **assistant sends `tool_use` blocks; user replies `tool_result` blocks, matched by `tool_use_id`.** user-message content must be the LIST of result blocks, not a bare dict.

**2. The 7-bug debug saga (symptom → root cause → lesson):**

| # | Symptom | Root cause | Lesson |
|---|---|---|---|
| 1 | Zero output, clean exit | `if __name__ == "__main__": main()` guard missing | Defs without an entry point = Python reads the file as a dictionary |
| 2 | `stop=tool_use` but `tools=[]`, empty answer | filter line typo in my transcription (fixed after grep; suspected `!=`) | When assumption (filter) contradicts data (block types), dump the RAW response |
| 3 | `TypeError: 'list' object is not callable` | `resp.content()` — parens on an attribute | Parens = call; attributes are taken, not called |
| 4 | Only round 1 ran, then "round cap" | `return None` indented INSIDE the for loop | Indentation = membership; same disease as YAML/compose misplacement |
| 5 | Upstream Chinese error `[1213] 未正常接收到prompt参数` | result block type set to `"tool_use"` (assistant's type) inside a user message | Wrong-direction type: tool_call (nonexistent) → tool_use (wrong direction) → tool_result (correct) |
| 6 | 400: `messages.2.content` not string/list | appended `output` (bare dict) instead of `results` (list) | Error messages name the exact message index and expected types — read them |
| 7 | Empty FINAL REPORT, `stop=max_tokens` | thinking consumed the whole 2000-token budget before any text | Arithmetic proof: total out 4408 ≈ 400 + 2000 + 2000 — every round died exactly at the cap |

Meta-lesson: **partial fixes are a failure mode of their own** — each half-applied fix produced a NEW error on the next run. Fixes ship as a set.

**3. New phenomena observed (glm via relay):**
- **thinking blocks**: responses arrive as `[{thinking}, {tool_use}, ...]`; the model "thinks out loud" before every tool call. Harmless — we append `resp.content` wholesale, thinking rides along in history.
- **Hallucination + self-correction, live**: model asserted the file had 1200/1228 lines, requested out-of-range chunks, hit our error dicts ("start_line beyond end of file"), then corrected itself next round — its phrasing: "according to the user's correction" (tool results ride the user role). **Errors-as-data vindicated in production.**
- **UTF-16LE source file**: MetaEditor's default save format. Reading as UTF-8 interleaves null bytes and DOUBLES the physical line count (2475 vs 1228). The model adapted on its own; the proper fix (BOM sniffing in the tool layer) is queued as B1.
- **Cost bell: in=206,020 tokens for one audit.** Agent loops re-send the full accumulated history every round → input grows ~quadratically with rounds×file size. This is why tool granularity and prompt caching matter.

**4. The audit itself (acceptance PASSED):**
- Round 1 = get_file_info (workflow followed); rounds 2-8 = ordered, non-skipping chunks; final VERDICT + token usage printed.
- Found: [HIGH] missing SL everywhere (cited OrderSend line 1710 which — beyond the checklist — ignores the SL parameter entirely because `mSymbol==""`, and OrderModify line 1529 that keeps SL=0); [HIGH] lot control (NormalizeDouble(...,2) instead of MODE_LOTSTEP, zero MODE_MINLOT/MAXLOT queries in the whole file).
- **Item 2 correctly ruled "DOES NOT APPLY (protected)"** — my EA has a new-bar guard (line 443), empty-basket requirement, and pipstep distance gates. Zero false positives. Reporting "no bug here, here's the proof" is worth as much as a hit.

## Gotchas
1. `max_tokens` must budget thinking + text TOGETHER; 2000 starves the answer, 16000 sufficed (final out=7828).
2. Treat `stop_reason == "max_tokens"` as an ERROR (return None), or an empty answer sails through silently with exit code 0.
3. Empty output + exit 0 = no entry point; filter-returns-nothing + block-dump-contradicts = your filter is wrong, not the data.
4. .mq4 files from MetaEditor are UTF-16LE — BOM-sniff in the tool layer before trusting any line counts.

## Artifacts
- `projects/hello-agent/0005-mql4-analyzer.py` — complete Step B (tool layer + prompt + loop + CLI), audited a real EA end-to-end
- First real-agent deliverable: audit report of 悦鹤_均线逆势马丁_双边对冲_v2.mq4 (in this session's transcript)

## Next step
- **Unanswered quiz questions (opening recap seeds):** Q1 why "do not invent bugs beyond the checklist" is a risk-control rule for a reviewer agent; Q2 why input tokens grow to 206K over 8 rounds and what that implies for auditing large files.
- B1: UTF-16 BOM sniffing in read_file_chunk (≤10 lines).
- Step C: seeded-bug .mq4 samples in `evals/`, measure hit rate / false positives — Phase 0 closes on numbers.
- Prompt caching catch-up (only untouched Phase 0 item); observed live (repeat run showed in=28).
- SECURITY: relay key rotation still pending since 2026-11-07.
