# 0002 · Lesson 1: First Pod — full lifecycle (create → run → self-verify → destroy)

**Date: 2026-11-08**

## What I did
Resumed cluster (`orbctl start k8s`, silent success = Unix culture), verified node Ready (v1.36.5). Created `first-pod` (nginx) via `kubectl run`, watched status go `ContainerCreating` → `Running`, got Pod IP `192.168.194.10`. Executed a real HTTP request INSIDE the container (`kubectl exec -it first-pod -- wget -qO- http://localhost`) — got full nginx welcome HTML. Deleted the pod.

## Key insight
A Pod is the smallest deployable unit: one or more containers sharing network/storage. Status is a state machine (`ContainerCreating` → `Running`; failure states: `ImagePullBackOff`, `CrashLoopBackOff`). "Running" is just kubelet's claim — deep health check means sending a REAL request (`wget` from inside, `kubectl exec`) to prove the process actually serves.

## Gotchas
1. `kubectl exec -it pod --wget ...` → `error: unknown flag: --wget`. Root cause: missing space in `--` separator — kubectl parsed `--wget` as ITS OWN flag. `--` means "everything after this is the command to run in the container, not kubectl args". Same convention as `git log -- --x`, `npm run -- --watch`.
2. `-q0-` vs `-qO-`: the letter is capital **O** (Output to stdout), not digit zero. Two typos that "look identical to the eye but differ in bytes" — when you see `unknown flag` / `invalid option`, diff the command character by character.
3. `orbctl start k8s` prints nothing on success — silent success is normal Unix behavior, absence of error IS the success signal.

## Pending (next session opener)
Answer the 3 recap questions: where does the container actually run / what does describe's Events section resemble / relationship between Pod IP and host Mac IP.

## Next step
Lesson 2: Deployment + Service.
