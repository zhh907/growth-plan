# 0015 — L3 cgroup v2 opens: tree shape read + subtree_control wall (experiment pending)

Date: 2026-11-17 (same day as 0014, short session).

## 1. Model: namespace vs cgroup

- namespace = walls (what you can SEE); cgroup = meters (how much you can USE). A container is both.
- k8s `limits` → cgroup knob files. Nothing magic.

## 2. /sys/fs/cgroup structure read (executed)

- Prediction quiz ("files or directories?"): answered "files" — half right. Knobs ARE files, but the TREE NODES are directories: one directory per group, subgroups = subdirectories, knobs live inside each node.
- `cat /proc/self/cgroup` → `0::/` — L1 fingerprint redeemed (0 = v2 unified hierarchy, path = position on tree).
- TWO-LEDGERS CALLBACK (learner spotted via mentor, unplanned): inside the container the path reads `/`, but on the host the same container lives at `/sys/fs/cgroup/docker/<id>/` — cgroup namespace redecorates your own room as the building front. Same pattern as L2 PID dual numbering.
- `ls /sys/fs/cgroup/` = all knobs of ONE node (own room's meters): pairs `pids.max/current`, `memory.max/current`, `cpu.max/cpu.stat`.

## 3. pids.max experiment → Permission denied (root-caused, fix queued)

Steps attempted: `mkdir /sys/fs/cgroup/test` (OK) → `echo 10 > test/pids.max` → **Permission denied** (sudo same).

Evidence gathered:
- `mount | grep cgroup` → `rw,nosuid,nodev,noexec,relatime,nsdelegate` — not read-only; `nsdelegate` = permissions decided by DELEGATION (ownership), not by root identity. Living in the room ≠ allowed to change the meters.
- `ls -la /sys/fs/cgroup/test` → **smoking gun**: no controller knob files at all, only `cgroup.*` + `cpu.stat` base files. Writing pids.max failed because the file does not exist and cgroupfs forbids creating files by hand — kernel manufactures them.
- Root cause: cgroup v2 **top-down controller enablement** — parent must `echo +pids > cgroup.subtree_control` before children grow pids.max. Root's `cgroup.controllers` shows `cpuset cpu io memory pids` available.
- Container identity loose end: `docker inspect ops-lab` → no such object; this container has another name (`docker ps` pending). Possibly not `--privileged`.

## 4. Resume point (updated 2026-11-17 eve)

Progress since first draft: fresh `--rm -it --privileged` container opened; `echo +pids > /sys/fs/cgroup/cgroup.subtree_control` SUCCEEDED → `pids.max/pids.current/pids.events` GREW in test/ (top-down enablement verified live; enabling on a process-occupied ns-root works because ns-root is exempt from no-internal-process).

NEW WALL (experiment parked by learner): `echo $$ > test/cgroup.procs` AND `echo <sleep-pid> >` both → **Operation not supported** (EOPNOTSUPP, not EACCES — permission passed). Hypothesis "PID 1 restricted" FALSIFIED by moving sleep (PID 13) instead — same error. Remaining suspects: (a) test/cgroup.type threaded, (b) no-internal-process corollary — processes in a group with enabled subtree_control are barred from migrating. Discriminating commands prepared (toggle -pids, retry write, re-enable) — NOT RUN.

1. Container: `cat /sys/fs/cgroup/test/cgroup.type`, then toggle experiment above.
2. Then pids.max hands-on: limit 10, move process in, watch fork EAGAIN.

## 5. Concept layer completed (same day, lab-free)

Three knobs, three death styles (paper quiz 1.5/2 — exit code 137 and "throttle recovers next period" filled in):

- **memory.max** = execution: OOM kill picks the fattest process in group, SIGKILL (137 = 128+9, uncatchable even by PID 1 — L1 callback); `memory.oom.group=1` → whole group dies (k8s Pod kill).
- **cpu.max** = throttle: `200000 100000` = 200ms CPU per 100ms period (2 cores); over quota → hung until next period, ALIVE, reversible; `cpu.stat nr_throttled` = evidence.
- **pids.max** = refused birth: fork returns EAGAIN; existing processes untouched; fork-bomb defense.

Soft/hard isomorphism (L1 rlimit debt PAID): memory.high = soft (frantic reclaim, slow, swap — misery not death) vs memory.max = hard (kill). cpu.weight (1–10000, default 100) = cake-share weight, no cap; cpu.max = cap.

k8s mapping: limits.memory→memory.max / limits.cpu→cpu.max / requests.cpu→cpu.weight.

L3 concept layer DONE. Remaining: hands-on (resume point §4) + capstone hand-built container.

## Re-quiz seeds

1. Why did test/ have no pids.max? (subtree_control top-down enablement — parent must hand the controller down)
2. What does nsdelegate mean for permissions? (delegation/ownership decides, not root)
3. Two ledgers in cgroup: what path does the container see vs the host? (`0::/` vs `/docker/<id>/`, cgroup namespace)
4. Knob pairs: pids.max/pids.current, memory.max/memory.current — which is the limit, which the reading?
