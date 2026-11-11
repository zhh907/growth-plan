# Eval Answer Key — Step C (ground truth)

> Seeded against the 0005 checklist: (1) lot size control (2) same-bar repeated entries (3) missing stop loss.
> Do NOT let the model see this file. Examiner (zhanghao) only.

## Sample A — buggy (3 seeds)

| # | Bug | Location | Evidence |
|---|-----|----------|----------|
| 1 | Lot control: `BaseLots * MathPow(Multiplier, existing)` — no NormalizeDouble, no LOTSTEP/MINLOT/MAXLOT | `OpenTrade()`, `double lots = ...` line (~line 31) | zero `MarketInfo` calls in file |
| 2 | Same-bar repeated entries: `OnTick` fires `OpenTrade` on EVERY tick while `fast > slow` — no `Time[0]` new-bar guard; MaxTrades=5 fills within one bar | `OnTick()` `if(fast > slow) OpenTrade(OP_BUY);` (~line 21) | no `datetime`/`Time[0]` anywhere |
| 3 | Missing SL: `OrderSend(..., 3, 0, tp, ...)` — SL param is 0 | `OrderSend` call (~line 38) | no `sl` variable, no StopLossPips input |

## Sample B — clean (0 seeds) ← control group

Expected verdict: all three checklist items "DOES NOT APPLY" with proof:
- Lot: `NormalizeLots()` with LOTSTEP/MINLOT/MAXLOT (~line 37-46)
- Same-bar: `static datetime lastBarTime` guard (~line 17-20)
- SL: `sl` computed from `StopLossPips` and passed to OrderSend (~line 55-62)

ANY bug reported on this paper = false positive.

## Sample C — partial (1 seed)

| # | Bug | Location | Evidence |
|---|-----|----------|----------|
| 1 | Missing SL only: OrderSend passes 0 for SL | `OrderSend` call (~line 64) | no sl variable |

Lot (NormalizeLots present) and same-bar (Time[0] guard present) are CLEAN here.
Reporting either of those two = false positive; missing the SL = miss.

## Scoring

- Hit rate = (bugs found) / (bugs seeded): A → x/3, C → x/1
- False positives = any bug reported that was not seeded (B especially)
- Note per-paper token usage (in/out) from the run footer.
