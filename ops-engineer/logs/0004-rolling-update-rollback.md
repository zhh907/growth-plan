# 0004 · Rolling update & rollback (step 5, PASSED)

**Date: 2026-11-08 · Session 4 (same day, second half)**

## What I did
1. Finished step 4 verification: self-heal demo — deleted pod `.15`, replacement `.16` Running before I could even type `kubectl get pods -w` (reconcile is faster than typing); endpoints swapped `.14,.15 → .14,.16` automatically; browser opened localhost:30080 (nginx) — all 5 hops proven.
2. Step 5, Act 1 (rolling update): edited yaml `nginx:alpine → nginx:1.27-alpine`, watched `get pods -w` in a second terminal, then `get rs` (fossil layer) + `rollout history`.
3. Step 5, Act 2 (break & rollback): image → `nginx:broke-the-build`; rollout stuck 44s+ (Ctrl+C only stops the WATCHER, not the rollout); curl during the outage-risk window returned full HTML (old version still serving); `rollout undo` → back in seconds.
4. Spotted (myself, before mentor said it) that **undo does NOT revert the yaml file** → config drift → must fix the file too, or the next apply re-detonates the mine.

## Key insights

**1. Rolling update = two ReplicaSets trading places, never both empty.**
Watch output showed the safe ordering: new pod Pending→ContainerCreating→Running **1/1 Ready FIRST**, only then old pod Terminating. With defaults maxSurge/maxUnavailable=25% on 2 replicas (≈ +1/-1). Whole swap took ~3s. Terminating → Completed = graceful shutdown (SIGTERM, main process finishes).

**2. Deployment → ReplicaSet → Pod naming.**
`web-deploy-<rs-hash>-<random>`: editing the pod template creates a NEW ReplicaSet; the old one is scaled to 0, NOT deleted — that dormant RS is the rollback archive. `kubectl get rs` = the fossil layer (new DESIRED=2, old DESIRED=0).

**3. Failed rollout evidence from AGE columns.**
After the broken-image rollout + undo, the pod names (mwcvm, rhsnz) and AGE (6m, unbroken) were IDENTICAL to pre-incident: the surge pod never went Ready, so k8s never touched the old RS — zero pods sacrificed. The safe ordering protected the old version completely. Reading AGE/names as forensic evidence.

**4. undo rolls back the CLUSTER, not the file (config drift).**
`rollout undo` sets the previous revision's template as the NEW desired state (a forward rollout of an old version), but the yaml on disk still holds `nginx:broke-the-build`. Discipline: the file is the single source of truth; after undo, fix the file too. This exact pain is what GitOps/ArgoCD (roadmap Phase 2) industrializes — repo as truth, drift auto-corrected.

**5. Bonus closures from step-4 verification:**
- `.orbholder` mystery solved: cluster's built-in `kubernetes` Service ClusterIP = 192.168.194.129, sitting in the upper half of the same /25 (.128/25) — OrbStack's channel for Mac's kubectl to reach the API server.
- `v1 Endpoints is deprecated` warning → EndpointSlice (v1.33+): same concept, sliced for scale. Warnings are teaching material too.

## Gotchas
1. Run `kubectl get pods -w` BEFORE triggering, or the transition finishes before you watch it.
2. Ctrl+C on `rollout status` aborts nothing server-side — the rollout keeps going in the background.
3. After `rollout undo`, the yaml file is still wrong — fix it or the next apply re-breaks.

## Artifacts
- `projects/k8s-first-steps/0000-deploy-svc.yaml` — image now `nginx:1.27-alpine` (post-undo, file aligned).

## Next step
- Phase 0 remaining: Docker basics unit (newly added to roadmap; the running Tomcat container is the living textbook), then ConfigMap/Ingress + a multi-service app.
