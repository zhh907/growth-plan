# Learning Log Index — Ops Engineer

> INDEX ONLY (context economy). Full entries live in `logs/NNNN-slug.md`, one file per session.
> Startup: read this index; open a specific log file only when its detail is needed.
> Writing convention: end of session → write `logs/NNNN-slug.md` (full detail, English, stranger-relearnable) + add ONE line below.

| # | Date | Topic | Key takeaway | File |
|---|---|---|---|---|
| 0006 | 2026-11-09 | Docker L2: network + volume + Compose | bridge=vswitch, OrbStack main process holds all -p ports; container IP reachable (L2 neighbor) but Pod IP blackholed by VPN broad route; volume survives cremation, bind mount=alias not copy; compose auto network + name DNS; depends_on=order NOT readiness | [logs/0006-docker-network-volume-compose.md](logs/0006-docker-network-volume-compose.md) |
| 0005 | 2026-11-09 | Docker L1: image layers + container=process | image=read-only layer cake (shared+cached), container=process+writable clay; smartpeak 581MB with 72% in two fat layers; same java = PID 381 (node view) vs PID 1 (container view); k8s pods visible in `docker ps` | [logs/0005-docker-image-and-container.md](logs/0005-docker-image-and-container.md) |
| 0004 | 2026-11-08 | Rolling update & rollback | two RS trade places, new-Ready-before-old-kill; failed rollout = zero pods sacrificed (AGE proof); `undo` reverts cluster NOT file → config drift; Ctrl+C on rollout status kills only the watcher | [logs/0004-rolling-update-rollback.md](logs/0004-rolling-update-rollback.md) |
| 0003 | 2026-11-08 | Node internals + first Deploy/Svc | k3s = OrbStack's k8s (kubelet hidden inside); pause container owns Pod netns; cni0 = Pod network, unreachable from Mac (curl timeout); YAML typing: `replicas: "2"` = 400; apply is per-object, not transactional | [logs/0003-node-internals-deploy-svc.md](logs/0003-node-internals-deploy-svc.md) |
| 0002 | 2026-11-08 | First Pod full lifecycle | Pod = smallest deployable unit; status state machine; deep health check = real request from inside; `--` separator; `-qO-` letter O | [logs/0002-first-pod-lifecycle.md](logs/0002-first-pod-lifecycle.md) |
| 0001 | 2026-11-07 | Env setup (OrbStack) | Local provider > building from scratch; single-node cluster in one VM; kubeconfig at `~/.orbstack/k8s/config.yml` | [logs/0001-env-setup-orbstack.md](logs/0001-env-setup-orbstack.md) |

## Open items (not session-scoped)

- ~~Finish step 4 verification~~ CLOSED 2026-11-08 (self-heal + browser verified).
- ~~Docker basics after step 5~~ CLOSED 2026-11-09 (L1 + L2 done, log 0005/0006). NEXT UP: ConfigMap/Ingress + a multi-service app → Phase 0 closes. Re-quiz pending: cache prefix invalidation / PID 1 duties / sidecar / errors-as-data. Lab leftovers to decide: compose stack (18095) + l2-web (18080) + l2-data volume.
