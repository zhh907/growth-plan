# 0003 · Node internals exposed + first Deployment/Service (0000-deploy-svc.yaml)

**Date: 2026-11-08 · Session 3**

## What I did
1. Answered the 3 recap questions from lesson 0002 (with heavy mentor correction — only partial answers unaided).
2. Tried to SSH into the k8s node: `orbctl ssh` prints usage; `ssh orb` says "no machines found" — OrbStack "machens" are user-created distro VMs; the k8s node is an internal system VM, deliberately not SSH-able.
3. Used `kubectl debug node/orbstack -it --image=busybox` (hostPID profile) to inspect the node from inside.
4. Read `kubectl get nodes -o wide`: node = control-plane+master single node, INTERNAL-IP 192.168.139.2, Linux kernel 7.2.12-orbstack, runtime docker://29.8.2.
5. Inside the debug pod: `ps aux` and `ip addr` — solved the kubelet mystery and mapped all networks.
6. Verified from Mac: curl to a Pod IP (192.168.194.13) TIMES OUT after 75s — Pod network unreachable from host. (Mentor's guess that OrbStack magic would allow it was WRONG — data wins.)
7. First artifact `projects/k8s-first-steps/0000-deploy-svc.yaml` (Deployment 2×nginx:alpine + Service NodePort 30080). Hit a YAML typing error on replicas, fixed, applied.
8. Directory convention aligned with agent-fullstack: `ops-engineer/projects/<project-name>/` (renamed empty `project/` → `projects/`, added convention line to agent.md). Artifact numbering: logs 1-indexed per session, artifacts 0-indexed independent sequence.

## Key insights

**1. The container host: OrbStack's internal Linux VM, which is k3s.**
`ps aux` inside the node debug pod showed PID 1 `simplevisor` (OrbStack's init), `dockerd`, `containerd`, and — solving the "where is kubelet" mystery — PID 930 `{k3s-server} k3s server`. OrbStack's k8s is **k3s**: one binary embedding kubelet + apiserver + scheduler + controller-manager. That's why no process is named "kubelet" and why one node = a full cluster. Knowledge transfers to standard kubeadm clusters.

**2. containerd-shim: one per container.**
Each running container has a `containerd-shim-runc-v2` parent process (7 shims = 7 containers). The shim is the container's "foster parent": reaps the container when it dies so containerd itself is never taken down. `-namespace moby` = Docker's OSS name → OrbStack's k8s creates containers through its Docker implementation.

**3. pause containers hold the Pod's network namespace.**
`/pause` processes (user 65534/65535) — near-zero-cost containers, one per Pod. The pause container obtains the Pod IP and owns the netns; app containers join it. This is WHY all containers in a Pod share localhost/IP. Seen with our own eyes via hostPID.

**4. Network map (from `ip addr` on the node).**
- `eth0` 192.168.139.2/24 — node IP
- `docker0` 192.168.215.1/24 + `br-*` ×4 (192.168.97/107/117/147.1) — Docker bridge networks (user's own containers live here; a Java-8 Tomcat container was found running, with `pstub` processes implementing its `-p 18081:8080` mapping)
- `cni0` 192.168.194.1/25 — the POD network bridge (CNI plugin); pods get 192.168.194.x
- `.orbholder` 192.168.194.128/25 — OrbStack's interface on the same /25's upper half
Three unrelated worlds on one VM; the Mac's home router knows none of them.

**5. Pod IP is cluster-internal: curl from Mac timed out (75s).**
Timeout ≠ refused: timeout = packets silently dropped (no route); refused = reached the host, port closed. Read the failure MODE, not just "it failed". Consequence: a stable entry point is mandatory → Service.

**6. Events = append-only timestamped event stream** — same pattern as backend logs. `kubectl describe` → read Events bottom-up for root cause, like tailing a service log.

**7. First k8s API error read line-by-line:**
`cannot unmarshal string into ... replicas of type int32` — YAML infers types: `2` int, `"2"` or `___` string. The k8s API objects are strongly-typed Go structs server-side; error messages name the field and expected type — read, don't guess.
Also observed: **apply is per-object, NOT transactional** (Service created while Deployment failed); re-apply is idempotent (`service/web-svc unchanged`).

**8. Deployment + Service (concept level, from lesson):**
- Deployment = declared desired state (replicas), controller reconciles reality→declaration (self-heal/scale/rollout).
- Service = stable virtual IP + DNS; kube-proxy implements it as iptables rules (DNAT to a pod IP); endpoints list maintained by the Endpoints Controller watching labels, gated on Ready.
- selector.matchLabels (what Deployment claims) vs template.labels (what it stamps on children) — API server rejects mismatch to prevent orphan pods; Service selects the same label = the glue.
- NodePort path: Mac →(OrbStack port map)→ node:30080 →(iptables DNAT)→ pod IP:80 →(cni0)→ pause netns → nginx = 5 hops.

## Gotchas
1. `orbctl ssh` ≠ enter the k8s VM; it prints usage. `ssh orb` only reaches user-created machines ("no machines found").
2. `kubectl debug node/` pods do NOT auto-delete — clean up (`kubectl get pods -A | grep debug`).
3. YAML placeholder `___` in a numeric field = string = 400 BadRequest naming the exact field.
4. `--profile=legacy is deprecated` warning on kubectl debug — prefer `--profile=general` later.

## Artifacts
- `projects/k8s-first-steps/0000-deploy-svc.yaml` — Deployment (2× nginx:alpine) + Service (NodePort 30080), applied 2026-11-08.

## Next step
- Finish step 4 verification: self-heal demo (`delete pod` + `-w` + endpoints diff) + browser `http://localhost:30080`.
- Then step 5: rolling update & rollback (`kubectl rollout`/`set image`/`undo`).
- NEW in roadmap (2026-11-08): Docker basics inserted into Phase 0 — use the existing Tomcat container as living material.
