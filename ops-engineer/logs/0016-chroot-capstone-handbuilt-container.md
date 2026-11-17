# 0016 — chroot capstone: hand-built container (walls + ledger + floor all aligned)

Date: 2026-11-17 eve. Same lab container (privileged ubuntu:24.04) as log 0015.

## 1. Third pillar: chroot = swap the floor

Container = three pillars, all now built by hand:

| Pillar | Mechanism | Controls | Prior evidence |
|---|---|---|---|
| Walls | namespace (unshare) | what you SEE | L2 two ledgers |
| Meters | cgroup knobs | how much you USE | L3 death styles |
| Floor | chroot / pivot_root | where you STAND | L2 overlayfs cake |

## 2. Furnishing the bare floor (debug saga, three hits)

1. `chroot /myroot bash` on empty dir → "failed to run command 'bash'" = floor exists, no furniture. Lesson: after chroot, EVERYTHING (binaries + libs) must exist on the new floor — that's why images pack a whole tree.
2. Copied bash + `ldd` deps; STILL "No such file or directory" despite bash existing → **missing ELF interpreter**: kernel returns ENOENT for the loader, not the program. Classic Linux trap, now personally hit. Mentor bug: gave x86-64 loader path; lab is aarch64 (OrbStack) — correct = `/lib/ld-linux-aarch64.so.1`, must match ldd's path exactly.
3. `chroot /myroot /bin/bash` → prompt `bash-5.2#` (no PS1: /etc not copied).

Inside bare chroot: `$$ = 54` (ledger UNCHANGED — chroot swaps floor, not walls), `ls`/`ps` = command not found. Prediction quiz answered: chroot does NOT isolate processes; visibility depends on walls (pidns) + ledger (/proc mount), never the floor.

## 3. Capstone assembly — and the trap that taught most

One-liner attempt: `unshare --pid --fork --mount-proc chroot /myroot /bin/bash` → `$$ = 1` ✓ but `/proc` EMPTY (glob unexpanded, /proc/self missing).

**Diagnosis (L2 mount-ledger model callback):** --mount-proc records its ledger entry on the OLD tree's /proc path BEFORE chroot swaps the floor. Visibility binds at RECORDING time to a PATH — floor swap leaves the entry behind on the old tree. Exactly log 0011's law, rediscovered live.

Correct order — record onto the NEW floor's path, THEN swap:

```
unshare --pid --fork --mount bash
mkdir -p /myroot/proc            # (mount point must pre-exist — hit this error too)
mount -t proc proc /myroot/proc
chroot /myroot /bin/bash
```

Result: `read s < /proc/self/stat` → **7**, `echo $$` → **7. TWO LEDGERS FULLY ALIGNED.**

Why 7 not 1: the room's PID 1 is the OUTER room-holder bash (unshare --fork's child); the chroot'd bash is its descendant (forked for the chroot exec) and drew number 7. `read` is a builtin — no fork — so /proc/self = bash itself. Contrast 0010: $$=1 vs /proc/self=34 disagreed because the ledger wasn't swapped; now both query the same new ledger.

## 4. What docker run really is

unshare (walls) + mount/pivot_root (ledger + floor swap) + cgroup (meters) + automation. Hand-built 3 of 4 tonight; meter wiring parked with log 0015's EOPNOTSUPP mystery. Hardening note: production uses pivot_root (mount-tree move, old root unreachable) not chroot (double-chroot escape possible with root).

## Re-quiz seeds

1. bash exists on new floor but chroot says "No such file or directory" — what's actually missing? (ELF interpreter, kernel ENOET/ENOENT misdirection)
2. Why did `--mount-proc ... chroot` leave /proc empty? (entry recorded on old tree's path before floor swap)
3. In the final container, why is the chroot'd bash PID 7 and not 1? (PID 1 = room-holder outer bash; inner bash is a descendant)
4. $$ = /proc/self = 7 — why do they agree now but disagreed in 0010? (ledger actually swapped this time)
