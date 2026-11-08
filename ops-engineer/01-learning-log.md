# Learning Log Index — Ops Engineer

> INDEX ONLY (context economy). Full entries live in `logs/NNNN-slug.md`, one file per session.
> Startup: read this index; open a specific log file only when its detail is needed.
> Writing convention: end of session → write `logs/NNNN-slug.md` (full detail, English, stranger-relearnable) + add ONE line below.

| # | Date | Topic | Key takeaway | File |
|---|---|---|---|---|
| 0004 | 2026-11-08 | Rolling update & rollback | two RS trade places, new-Ready-before-old-kill; failed rollout = zero pods sacrificed (AGE proof); `undo` reverts cluster NOT file → config drift; Ctrl+C on rollout status kills only the watcher | [logs/0004-rolling-update-rollback.md](logs/0004-rolling-update-rollback.md) |
| 0003 | 2026-11-08 | Node internals + first Deploy/Svc | k3s = OrbStack's k8s (kubelet hidden inside); pause container owns Pod netns; cni0 = Pod network, unreachable from Mac (curl timeout); YAML typing: `replicas: "2"` = 400; apply is per-object, not transactional | [logs/0003-node-internals-deploy-svc.md](logs/0003-node-internals-deploy-svc.md) |
| 0002 | 2026-11-08 | First Pod full lifecycle | Pod = smallest deployable unit; status state machine; deep health check = real request from inside; `--` separator; `-qO-` letter O | [logs/0002-first-pod-lifecycle.md](logs/0002-first-pod-lifecycle.md) |
| 0001 | 2026-11-07 | Env setup (OrbStack) | Local provider > building from scratch; single-node cluster in one VM; kubeconfig at `~/.orbstack/k8s/config.yml` | [logs/0001-env-setup-orbstack.md](logs/0001-env-setup-orbstack.md) |

## Open items (not session-scoped)

- ~~Finish step 4 verification~~ CLOSED 2026-11-08 (self-heal + browser verified).
- ~~Docker basics after step 5~~ NEXT UP: Docker basics unit (Phase 0 item 6) — Tomcat container as living textbook. Remaining after that: ConfigMap/Ingress + a multi-service app (Phase 0 closes).
