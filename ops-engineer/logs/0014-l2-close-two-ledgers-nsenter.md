# 0014 — L2 CLOSE: two-ledgers re-verified + nsenter/lsns executed; namespaces unit done

Date: 2026-11-17 (4-day gap since 0011).

## 1. Two-ledgers re-verification (paper, mandatory opener)

First attempt: 0.5/3 — model still wet after the gap (expected). Zero new material; re-derived in 4 plain sentences (building/floor analogy):

1. `unshare --pid --fork` = new building, residents renumbered from 1; the city ledger (host) still valid — same person, floor-101 vs city-record-34. BOTH ledgers true.
2. Answer depends on WHICH ledger you query: `$$` asks in-building → 1; `readlink /proc/self` walked the city archive (/proc not yet swapped) → 34.
3. ps crash = roster-reader carrying building numbers into the city archive.
4. `--mount-proc` = build an in-building archive branch. Mantra: `--pid` owns WHERE NUMBERS COME FROM, `/proc` owns WHERE RECORDS LIVE — must be paired.

New layer taught (the question learner couldn't answer): after `--mount-proc`, the city number (34) is INVISIBLE inside the building — pairing swaps ledgers completely; old ledger only queryable from OUTSIDE (host ps / docker top / nsenter from host side).

Acceptance: `ps aux` (container) = new ledger / `docker top` = old ledger, queried from outside — **3/3 correct. Ledger model CLOSED.**

## 2. nsenter/lsns experiments (executed, both terminals in same container)

- Learner first ran `unshare` on macOS host → `command not found` (boundary sense re-tested, corrected to lab container).
- Terminal A: `unshare --pid --fork --mount-proc bash` → `$$`=1, `sleep 600 &`.
- Terminal B: `ps aux | grep sleep` → global PID 20 (old ledger); `lsns -t pid` → TWO pid rooms (4026532614 container main, 4026533713 the new building, led by PID 16).
- Mentor bug: gave `nsenter --fork` (an `unshare` option — nsenter has `-F/--no-fork`). Corrected.
- `nsenter -t 16 --pid --mount ps aux` → **PID 1 bash / PID 5 sleep / PID 6 ps**: same process, number 20 outside vs 5 inside.

Key readings: the KEY uses the old ledger (-t 16 global) to locate the room; once inside, ps reads the in-building /proc (new ledger). Room shows only 3 processes — new ledger lists building residents only. **This command IS docker exec's true form** (host-side setns into container namespaces).

## 3. Acceptance

L2 CLOSED 2026-11-17: pid ✅ uts ✅ net ✅ mnt ✅ overlay ✅ two-ledgers ✅(paper 3/3 + live evidence) nsenter/lsns ✅. Next: L3 cgroup v2 (CPU / memory / pids limits), then the capstone hand-built container (unshare + chroot).

## Re-quiz seeds

1. nsenter key vs view: which ledger does `-t` use, which does ps show after entering?
2. After `--mount-proc`, why is the host PID invisible inside? Where must you query it?
3. What is docker exec, underneath? (setns into the container's namespaces)
4. nsenter vs unshare option confusion: which one has --fork and why (unshare CREATES a room and must fork the first resident; nsenter only visits)?
