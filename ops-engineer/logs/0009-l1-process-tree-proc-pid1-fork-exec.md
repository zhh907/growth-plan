# 0009 — L1 Processes: tree, /proc, PID 1 signals, fork/exec (Phase 1 Unit 1)

Date: 2026-11-13 (morning part: process tree + /proc; afternoon part: PID 1 signal experiment + fork/exec). Lab: `docker run --rm -it --privileged ubuntu:24.04 bash` on OrbStack. macOS host has no Linux namespaces/cgroups — that boundary was established in lesson.

## Global map (why this unit exists)

Unit 1 = Linux isolation trio (process → namespace → cgroup), the goal is to hand-build a "container" from the host's view. L1 (processes) is the foundation: containers ARE processes, so you must first understand how processes are born (fork/exec), who their parent is (process tree), how to X-ray them (/proc), and what makes PID 1 special (signals + zombie reaping). L2 namespaces and L3 cgroups build directly on this.

## 1. Process tree + /proc (morning)

- Every process is born from `fork()`; the tree root is PID 1. Inside a container, the container's CMD is PID 1; on the Linux host it's systemd, on macOS it's `launchd` (verified: `root 1 ... /sbin/launchd` in host `ps aux`).
- `/proc/<pid>/` four fingerprint entries (how to tell "this process runs in a container" from outside):

| Entry | Host normal process | Container process |
|---|---|---|
| `status` → `CapEff:` | long ffffff... hex (full caps) | `00000000a80425fb` (docker dropped a batch) |
| `status` → `Seccomp:` | `0` (off) | `2` (filter mode — syscall firewall) |
| `status` → `NSpid:` | one number | two numbers (host PID + namespace PID) |
| `cgroup` | `0::/user.slice/...` | `0::/` under a docker-created subpath |

- `cgroup` line anatomy: `0::` = hierarchy ID, `0` = unified hierarchy = **cgroup v2** (v1 had one tree per resource like `9:blkio:`; v2 merges into one tree). The path after `::` = where the process sits in the tree; limits attach to tree nodes, position decides whose quota applies.
- `limits` (soft/hard): soft = currently enforced, the process may raise it itself up to the hard limit (`ulimit -n 5000` succeeds if 5000 < hard). Hard = ceiling; raising it needs privilege (CAP_SYS_RESOURCE); a normal process can only lower it (irreversible). First check point for "too many open files" inside containers.

## 2. Experiment 3 — PID 1 signal immunity (afternoon)

Concept first: the kernel does NOT apply default signal dispositions to PID 1. A normal process dies on SIGTERM by default; PID 1 without an installed handler simply IGNORES SIGTERM. `docker stop` = send SIGTERM to PID 1, wait 10s, then SIGKILL.

Commands + real outputs:

```bash
docker run -d --name t1 ubuntu:24.04 sleep 1000
time docker stop t1     # 0.01s user 0.02s system 0% cpu 10.231 total

docker run -d --name t2 --init ubuntu:24.04 sleep 1000
time docker stop t2     # 0.01s user 0.01s system 12% cpu 0.193 total
```

53× difference. `--init` injects `/sbin/docker-init` (tini) as PID 1; sleep demoted to a child:

```
root  1  /sbin/docker-init -- sleep 1000
root  6  sleep 1000
```

tini's TWO jobs: (1) install signal handlers and FORWARD signals to children → sleep receives SIGTERM and dies immediately (as a non-PID-1 process it gets normal default disposition); (2) REAP ZOMBIES — orphans inside the container are re-parented to PID 1, and a bare `sleep`/Java/Python as PID 1 never calls wait(), so zombies accumulate. Classic production pitfall.

Death causes: t1's sleep died of **SIGKILL** (kernel executes after the 10s grace expires); t3's sleep died of **SIGTERM** (received notice, exited by default disposition).

Gotcha (self-parsed by learner): `docker exec t2 ps aux` after `docker stop t2` → `Error response ... is not running`. Root cause: stop already tore the container down; exec needs a running container. Fix: inspect BEFORE stopping.

## 3. fork/exec + orphan re-parenting

Concept: fork() = photocopy yourself (copy-on-write), returns twice (parent gets child PID, child gets 0). exec() = replace your memory image with a new program, PID unchanged. "Running a command" = fork + exec combo. Shell layer avatars: `$$` = own PID, `$!` = last background child PID.

Demo (inside fresh `docker run --rm -it ubuntu:24.04 bash`):

```bash
bash -c 'echo i am pid $$; sleep 300 & echo my child is $!; ps -ef'
# i am pid 8
# my child is 9
# PID 8 ps -ef   <-- same PID as bash -c!
# PID 9 sleep 300  PPID=8
```

Hidden gem: bash optimizes the LAST command of a `-c` script by exec'ing it IN PLACE (no fork) — so bash -c (PID 8) became ps (still PID 8). Live proof of exec: PID unchanged, program swapped. This also explains `/sbin/docker-init -- sleep 1000`: sleep is its forked child.

Orphan re-parenting, verified:

```bash
ps -ef   # after the ps (PID 8, sleep's parent) exited
# PID 9 sleep 300  PPID=1   <-- re-parented to PID 1
```

Zombie connection: a dead child that the parent never wait()s stays as `STAT=Z <defunct>` (21 of them found on the macOS host, harmless there — launchd eventually adopts/reaps). This is exactly why containers need a reaping PID 1.

## 4. Open observations (to resolve in L2)

- PID numbering gaps inside fresh containers: first child got PID 6 (t3), then 8/9 in another container — PIDs 2-7 burned by something invisible. Hypothesis: related to how runc/the runtime sets up the PID namespace (kernel threads or early setup forks are not visible). Revisit with `/proc/sys/kernel/ns_last_pid` in L2.
- Shell gotcha hit: `ps -ef |` + Enter → bash shows `>` continuation prompt waiting for the right side; stray `d` → `command not found`.

## 5. k8s/production connections

- Container = process with extra isolation; PID 1 duties (signal handling + reaping) are why base images / `shareProcessNamespace` / tini exist.
- k8s Pod: pause container holds namespaces; app containers are its siblings — L2 will map this precisely.
- "Permission denied" / weird syscall failures inside containers → check CapEff + Seccomp in /proc status FIRST.

## 6. Quiz record (2026-11-13 opening)

Scored 0.5/3 on morning content: CapEff/Seccomp fingerprints (answered "pid number", partial NSpid credit), cgroup `0::` meaning (blank), soft/hard limits (blank). All three become standing re-quiz items. Older debts still pending: Service three ports (port/targetPort/nodePort), describe parentheses value (Pod IP + container port), YAML law "parent = first shallower key above".

## Acceptance status

L1 complete: process tree ✅ /proc four entries ✅ PID 1 signals ✅ fork/exec ✅. Next: L2 namespaces (7 isolation dimensions, focus pid/net/mnt).
