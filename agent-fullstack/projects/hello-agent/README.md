# MQL4 Code Analyzer — 0005

An agent CLI that audits `.mq4` Expert Advisor source code against a fixed
bug checklist and reports findings with line citations.

## What it checks (the checklist)

1. **Lot size control** — lot not normalized to `MODE_LOTSTEP` / not clamped to `MODE_MINLOT..MODE_MAXLOT`
2. **Same-bar repeated entries** — no new-bar guard before entry logic
3. **Missing stop loss** — `OrderSend` called with SL = 0 and no later `OrderModify` adds one

By design it does NOT report bugs beyond this checklist (anti-false-positive
rule: a review report's credibility is its only asset).

## Requirements

- Python 3.10+
- An Anthropic-protocol relay endpoint + API key in `.env` (see `.env.example`)
- Dependencies: `anthropic` SDK

## Usage

```bash
python 0005-mql4-analyzer.py <path-to-file.mq4> [--max-rounds 15]
```

Exit codes:

- `0` — analysis completed, no checklist bugs found
- `1` — analysis completed, bugs found
- `2` — tool/usage error (bad args, unreadable file, round cap, output budget exhausted)

Data (final report) goes to stdout; diagnostics go to stderr — safe to pipe.

## Cost

Input tokens scale with file size × rounds (full history is re-sent each
round). Observed (glm via relay):

| File | Rounds | input tokens | output tokens |
|---|---|---|---|
| 77-line eval paper | 2 | ~2,300 | ~2,600 |
| 700-line production EA | 8 | ~206,000 | ~7,800 |

Budget `max_tokens` for thinking + text together (16,000 works for glm).

## Eval results (2026-11-11, evals/)

| Paper | Seeded | Hits | False positives |
|---|---|---|---|
| A buggy (3 bugs) | 3 | 3 | 0 |
| B clean (control) | 0 | — | 0 |
| C partial (1 bug) | 1 | 1 | 1 (known issue) |
| nonexistent file ×2 | — | — | 0 (refused to fabricate) |

**Hit rate 4/4 = 100%. Known issue (1 FP on C):** the lot-control checklist
term is ambiguous — objective normalization vs subjective risk-based sizing
philosophy. Same code pattern ruled clean on B, flagged MED on C (calibration
instability). Fix queued: tighten the rubric in SYSTEM_PROMPT, regression
re-run B & C.

## Known limitations

- UTF-16LE files (MetaEditor default save) double the physical line count —
  BOM sniffing in `read_file_chunk` is queued (B1)
- No prompt caching yet — large-file audits pay full price every round
- Checklist is fixed; extending it means editing SYSTEM_PROMPT and re-running
  the eval suite (evals/answer-key.md is the regression baseline)

## Files

- `0005-mql4-analyzer.py` — the tool (tools + prompt + agent loop + CLI)
- `evals/sample-{a-buggy,b-clean,c-partial}.mq4` — eval papers
- `evals/answer-key.md` — ground truth (do not feed to the model)
