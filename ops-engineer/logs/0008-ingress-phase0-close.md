# 0008 · Ingress — the last brick of Phase 0 · Phase 0 CLOSED

**Date: 2026-11-12 · Session 8 (ops track)**

## What I did
1. Final acceptance for the multi-service unit (deferred from 2026-11-10): `curl localhost:30081/` → `web frontend OK`, `curl localhost:30081/api` → `hello from api v1`. The 6-hop chain verified end to end.
2. Verified no Ingress Controller existed (`kubectl get pods,svc -n kube-system` → only CoreDNS + local-path-provisioner; OrbStack's k3s ships with Traefik disabled).
3. Installed ingress-nginx v1.11.3 (baremetal manifest) — 19 objects.
4. Read the controller's view via `kubectl describe ingress` — the Endpoint-resolution reveal.
5. Wrote and applied `0004-ingress.yaml` (path routing `/api` → api, `/` → web); both curls green through the new door.
6. Cleanup: deleted `web-svc` (already gone), `cm-dome` pod. Final state: 2 pods / 3 services / 1 ingress.
7. Phase 0 CLOSED; roadmap ticked.

## The acceptance chain (multi-service unit)

```
Mac curl → 127.0.0.1:30081 → service/web (NodePort) → web pod (nginx; default.conf from ConfigMap)
         → proxy_pass http://api → cluster DNS → service/api (ClusterIP) → api pod → "hello from api v1"
```

Six stations, every one hand-built. Multi-service unit closed.

## Ingress lesson

**The problem Ingress solves**: NodePort eats one port per service and only routes on L4 (port → service). No host/path routing, no TLS termination at a shared door.

**The four-step ladder of exposure** (know where you are):
```
ClusterIP   in-cluster only (service/api lives here)
NodePort    one port per service on every node (service/web :30081)
Ingress     ONE door, L7 routing by host/path to many Services
(LoadBalancer = cloud LB on top; not applicable locally)
```

**Resource vs Controller — the #1 concept**:
- Ingress resource = a routing TABLE (a YAML sheet)
- Ingress Controller = the POD that reads all tables and executes routing (the switchboard operator)
- Without a controller, an Ingress is a sheet nobody reads.

**Installed components, in 5 groups**:
| Group | Objects | Role |
|---|---|---|
| The switchboard itself | Deployment `ingress-nginx-controller` | watches all Ingress resources + Services/Endpoints, generates nginx.conf, hot-reloads |
| Its badge | ServiceAccount + Role/RoleBinding + **ClusterRole/ClusterRoleBinding** | must see ALL namespaces (routing is cluster-wide) |
| Its number | Service `ingress-nginx-controller` (NodePort **32600**/31654) | the single outside door |
| The bouncer | ValidatingWebhook + 2 Jobs (cert generation) | bad Ingress YAML rejected at admission, not after |
| The roster | IngressClass `nginx` | says "Ingress objects with ingressClassName=nginx belong to me" |

## `describe` — the reveal that matters

```
Rules:
  /api   api:80 (192.168.194.21:5678)
  /      web:80 (192.168.194.22:80)
```

The parenthesized values are **resolved endpoints**: the controller bypasses the ClusterIP and routes straight to Pod IP + container port. Note `5678` — the http-echo container's real listening port, i.e. the Service's `targetPort` made visible. **A Service is a label contract; the real body is always Pod IP.** Events showed `Sync` — routing table read, nginx hot-reloaded, no pod restart.

`kubectl describe` = full HR file of an object: Spec + Status + recent Events. `get` = roll-call table. First command of any troubleshooting session after `get` shows something wrong.

## Ingress YAML (4 layers)

```yaml
apiVersion: networking.k8s.io/v1        # identity layer
kind: Ingress
metadata: {name: main-ingress}
spec:
  ingressClassName: nginx               # which switchboard
  rules:                                # the table
    - http:                             # no host = match any host
        paths:                          # a LIST of paths
          - path: /api
            pathType: Prefix            # prefix match
            backend: {service: {name: api, port: {number: 80}}}
          - path: /
            pathType: Prefix
            backend: {service: {name: web, port: {number: 80}}}
```

YAML law check: `- path:` elements belong to `paths` (first shallower key above), `path/pathType/backend` are aligned siblings.

## Gotcha of the day: `web-svc` NotFound ×2

`kubectl delete service web-svc` → `NotFound` twice. Not an error: the Service had already been deleted earlier in the session (output unseen). **NotFound on delete = desired state already achieved**; delete is safe to re-run (declarative tooling). Lesson: trust the final state query (`kubectl get`), not the command's success message.

## Other gotchas
1. k3s **often** bundles Traefik — OrbStack's does not. Verify (`-n kube-system`) before designing around it.
2. ingress-nginx v1.11.3 baremetal leaves NodePorts **auto-assigned** (ours: 32600/31654); older versions hardcode 30080/30443 and WILL collide with existing services.
3. `admission-patch` job restarting once is normal (waits for the cert Job to finish first).
4. Curiosity note: two doors to api coexisted — old (30081 → web nginx → proxy_pass api) and new (32600 → Ingress → api). Old door kept as a live NodePort-vs-Ingress contrast exhibit.

## Cleanup executed
- `service/web-svc` (already gone), pod `cm-dome` deleted.
- Kept: `service/web` NodePort 30081 (contrast evidence), all YAML sources, Docker lab (compose 18095 / l2-web 18080 / l2-data) — decision deferred.
- Final cluster state: pods api + web (web RESTARTS 8 = old nginx-semicolon scar, healed 41h+), services api/web/kubernetes, ingress main-ingress.

## Phase 0 CLOSED (ops track)
Cluster start → Pod lifecycle → Deployment/Service → rolling update/rollback → Docker L1/L2 → ConfigMap (hot/cold) → YAML structure → multi-service (api+web+DNS) → Ingress. Roadmap Phase 0 ticked 2026-11-12. Both tracks' Phase 0 now done; ops checkpoint was 2027-01-31 → **~11 weeks early**.

## Weak-answer log (opening quiz, 2026-11-12)
- Q1 ConfigMap hot/cold: **forgot** (re-taught: env baked at exec → cold; volume via kubelet `..data` symlink swap → hot ≤1min)
- Q2 zombie-pod hijack: **forgot** (re-taught: selector matches labels only, never ownership)
- Q3 YAML laws: half (got sibling alignment, missed parent = first shallower key above)
→ Re-quiz next session; also add: Ingress resource vs controller, endpoint resolution (Service port ≠ targetPort).

## Next step
- Phase 0 done → decide Phase 1 start (Linux primitives + networking, CKA-oriented) — ops is secondary, agent track stays primary until its Phase 1 pattern tour completes.
- Re-quiz seeds: ConfigMap hot/cold, label hijack, YAML parent law, Ingress paper-vs-controller, describe anatomy, Service port vs targetPort.
- Open: Docker lab cleanup decision; relay key rotation (agent-track security item, still pending).
