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

## 4. Resume point (next session)

1. Mac: `docker ps` → real container name; `docker inspect <name> --format '{{.HostConfig.Privileged}}'`.
2. Container: `echo +pids > /sys/fs/cgroup/cgroup.subtree_control` → `ls test/` → expect pids.max to appear.
3. If subtree_control write denied → re-open a fresh `--rm --privileged` container and redo (cgroup state dies with container — same lesson as tmpfs).
4. Then the pids.max hands-on: limit 10, move self in (`echo $$ > cgroup.procs`), watch fork get refused (EAGAIN).

## Re-quiz seeds

1. Why did test/ have no pids.max? (subtree_control top-down enablement — parent must hand the controller down)
2. What does nsdelegate mean for permissions? (delegation/ownership decides, not root)
3. Two ledgers in cgroup: what path does the container see vs the host? (`0::/` vs `/docker/<id>/`, cgroup namespace)
4. Knob pairs: pids.max/pids.current, memory.max/memory.current — which is the limit, which the reading?
