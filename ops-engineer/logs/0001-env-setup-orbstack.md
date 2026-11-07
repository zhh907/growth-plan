# 0001 · Environment setup (K8s on macOS via OrbStack)

**Date: 2026-11-07**

## What I did
Audited local env — found OrbStack 2.2.5 + kubectl already installed, context `orbstack` set, but cluster not started (API server 127.0.0.1:26443 refused).

## Key insight
On Mac you don't build a cluster from scratch — you use a local provider (OrbStack / minikube / kind). OrbStack = lightest for Apple Silicon. `orbctl start k8s` boots a single-node cluster (control-plane + worker in one VM); kubeconfig lands at `~/.orbstack/k8s/config.yml`.

## Gotchas
None at this point — `orbctl start k8s` not yet executed.

## Next step
`orbctl start k8s` → `kubectl get nodes` → first Pod.
