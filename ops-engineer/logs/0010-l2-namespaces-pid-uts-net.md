# 0010 — L2 Namespaces (part 1): pid / uts / net + the two-ledgers lesson

Date: 2026-11-13 (afternoon session 2, follows 0009 same day). Lab: `docker run --rm -it --privileged ubuntu:24.04 bash`.

## Global map

Unit 1 trio: L1 processes (what it IS) → **L2 namespaces (what it SEES)** → L3 cgroups (what it MAY USE). Core mental model: **namespace = giving a process its own private room in a shared building**. Every process holds pointers to one room per resource type; fork with `CLONE_NEW*` = child points to fresh rooms. `unshare` = the manual room-creation tool — hand-doing what docker/runc automate with one clone call.

## 1. The 8 rooms (7 classic + time newcomer)

| namespace | isolates | evidence seen / k8s mapping |
|---|---|---|
| pid | PID numbering (restart from 1) | exp 0009 PID 1; container can't see neighbors |
| net | own network stack (links/routes/iptables/ports) | Pod network = netns held by pause container |
| mnt | mount table | overlayfs layers, volume mounts (filesystem lesson) |
| uts | hostname | container hostname = container ID |
| ipc | SysV IPC / POSIX queues | know it exists |
| user | UID mapping (in-room root ≠ building root) | CKS security topic |
| cgroup | cgroup path view | pairs with L3 |
| time | boot/monotonic clocks | newcomer, skipped |

`ls -l /proc/self/ns/` shows 10 symlinks but only 8 distinct rooms (compare inode numbers): `pid` and `pid_for_children` share one inode, so do `time`/`time_for_children`. Same inode = same room.

## 2. Gems found in /proc/self/ns

- **`pid_for_children` exists because** `unshare(CLONE_NEWPID)` can only affect FUTURE children — your own number is tattooed at birth. So each process carries two pointers: which pid-room I'm in, which one my children will be in. docker avoids the trick via `clone(CLONE_NEWPID)` at birth.
- **`--mount-proc` side effect**: mnt inode was also fresh (4026533380) — remounting /proc requires a private copy of the mount table, so one flag pulled TWO namespaces. Isolation is entangled.
- `user:[4026531837]` = low inode = still the host VM's initial user room → "root inside = root outside" root cause.

## 3. Command dissection (the one that matters)

```
unshare --pid --fork --mount-proc bash
```
- `unshare` = stop sharing, carve a new room
- `--pid` = new PID-numbering room
- `--fork` = MUST fork: own PID is immutable, only a newborn child can enroll in the new room
- `--mount-proc` = swap the roster (/proc) to the new room's edition
- `bash` = the tenant

Inside: `echo $$` → 1; `sleep 300 &` → `$!` = 4; `ps -ef` shows 1,4,5 only.

## 4. The two-ledgers lesson (key concept of this session)

`--pid` changes the NUMBERING RULE; `ps` reads the ROSTER (/proc). Rule without roster swap = two mismatched ledgers.

**Crash observed** — without `--mount-proc`:

```
unshare --pid --fork bash
ps -ef
# fatal library error, lookup self
```

Mechanism: ps asks the kernel "what number am I" (answer in NEW numbering, e.g. 8), opens `/proc/8` (OLD roster) — that entry belongs to someone else / doesn't exist → procps library aborts ("I know who I am but the roster disagrees"). Stronger proof than any output: mismatched ledgers BREAK tools. This is why runtimes ALWAYS remount /proc with the pidns. Half-configured namespaces are a trap, not isolation ("production-safe?" lens, live demo).

**Two numbers, one process** — the clean evidence:

```
unshare --pid --fork bash
echo $$                  # 1    (new room's ledger)
readlink /proc/self      # 34   (old building's ledger)
```

Same bash: #1 in its room, #34 in the building. Direct origin of "container PID 1 = just another process to the host".

## 5. uts and net quick wins

- uts: `unshare --uts bash -c 'hostname l2demo && hostname'` → prints l2demo; after exit `hostname` → 8dc9847f1e38 (restored). Hostname is per-uts-room, dies with the room.
- net: `unshare --net bash -c 'cat /proc/net/dev'` → ONLY `lo`, all-zero counters (bare, unpowered wire). Outside view (default container, shared docker stack): `lo` + `eth0` with real traffic. New net room = unfinished apartment with one dead lo cable. First-principles of Pod networking: pause container holds the (furnished) netns, sibling containers move in.
- Gotcha: `ip` not in ubuntu:24.04 base → fell back to /proc/net/dev (correct error-read-then-pivot). But `2>/dev/null` also buried a `lnke` typo — don't discard stderr while debugging.

## 6. PID-gap mystery: partially solved

Hand-rolled pidns also skips numbers (1 → 4,5; docker container 1 → 6/8). So gaps are NOT docker-specific: the kernel's cyclic allocator never guarantees dense numbering; docker/runc just burns MORE invisible short-lived helpers at startup. Engineering rule: never assume PIDs are contiguous or predictable. Residual: exactly who burns 2-3 in the bare unshare case (transient setup processes, invisible after exit).

## 7. Learner checkpoint

Mid-session feedback: "following the commands but not sure what they mean" → paused, re-derived everything in plain language (room/building analogy, word-by-word command dissection), then learner correctly predicted the with/without --mount-proc fork (initially misread the question, model was right). Verified by the two-numbers experiment. Lesson for mentor: keep plain-language re-derivation short and early when many new commands stack up.

## Acceptance status

L2 part 1 done: pid ✅ uts ✅ net ✅ /proc-self/ns anatomy ✅ two-ledgers ✅. L2 part 2 next: mnt namespace (tie to overlayfs), user/cgroup rooms brief, `lsns`/`nsenter` (setns) — then L3 cgroups. Re-quiz seeds: room model one-liner; why --fork is mandatory; lookup-self crash mechanism; $$ vs readlink /proc/self; --mount-proc dual namespace side effect.
