# 0007 · ConfigMap + multi-service app + cluster DNS — and a YAML/k8s debugging masterclass

**Date: 2026-11-10 · Session 7**

## What I did
1. Opening quiz: 6 questions (2 full / 2 half / 2 blank). Q1 (routing-table story) and Q2 (volume vs bind first-mount) blank — re-quiz next session.
2. **YAML structure lesson (user-requested pause)**: stopped copy-transcribing and learned the format properly.
3. ConfigMap: both injection paths (env + volume), observed the symlink machinery, proved hot-update vs frozen-env with a live experiment.
4. Multi-service app: api (http-echo) + web (nginx reverse proxy), config for BOTH delivered via ConfigMap, service-to-service call via cluster DNS.
5. Debugged 6+ failures across THREE layers (yaml layer / nginx-conf layer / cluster-state layer).

## Key insights

**1. YAML = JSON without braces (the structural lesson)**
- Only 3 building blocks: mapping (`key: value`), list (`- item`), scalar. A yaml file is ONE nested dict.
- Indent +2 spaces = enter a new `{`; dedent = close `}`. Every "wrong level" bug = "key placed in the wrong `{}`".
- **Law 1 (find the parent):** a line's parent = the first key ABOVE it with SHALLOWER indentation.
- **Law 2 (siblings align):** same column = same parent. Not aligned = not siblings = error or misadoption. No third outcome.
- `- name: api` = "new array element, which is a dict, first pair is name: api". All `-` of one array must align.
- Proof artifact: `kubectl.kubernetes.io/last-applied-configuration` annotation stores the JSON form — the cluster itself shows yaml≡json.
- Error-path syntax (`spec.containers[0].volumes`) and jsonpath are the SAME language.

**2. ConfigMap — three questions answered**
- What: etcd key-value store for config. Why: one image, many environments (12-factor; config drift seen live in session 5 rollback).
- Injection paths: env (baked into process memory at exec — CANNOT hot-update) vs volume (projected as files — syncs in ≤1min).
- **The symlink machinery (seen live in `/etc/app/`):**
  ```
  ..2026_11_10_03_24_12.2834397692   ← real data dir (timestamped)
  ..data -> <timestamped dir>        ← stable entry, atomically re-pointed
  ENV -> ..data/ENV                  ← stable paths for the app
  ```
  Update = write NEW dir + swap `..data` symlink atomically. Never in-place. Same idea as git refs / DB WAL: **don't modify, swap the pointer. No torn reads.**
- **Hot/cold proof (live):** patch MAX_CONN 100→200 → file showed 200 without restart; patch ENV→production → file updated, but `env | grep APP_ENV` stayed `staging` forever. Rule: hot-update needs volume path; env path accepts restart.
- ConfigMap volume mounts are READ-ONLY (nginx entrypoint log: "read-only file system?") — feature: source of truth is etcd.

**3. Multi-service + DNS**
- Architecture: `web (nginx, /api → proxy_pass http://api)` → `api (http-echo:1.0, text from ConfigMap)`.
- Service = stable ClusterIP + name; CoreDNS resolves `api` → `api.default.svc.cluster.local`. Pod IPs are temporary (saw .15→.16 churn in session 4); never hardcode.
- Label triangle: Deployment `matchLabels` (self-healing ownership) + Service `selector` (forwarding roster) both claim pods via the same `app: api` label.
- Deployment `template:` sits at spec level (2 spaces) — NOT inside selector. Fell into this hole TWICE.

**4. The debug saga (layer by layer)**

| # | Symptom | Layer | Root cause | Lesson |
|---|---|---|---|---|
| 1 | `did not find expected '-' indicator` line 17 | yaml | `volumes:` block on a different ladder than `containers:` | parser at dash-column expected a new list item, got `volumes:` |
| 2 | `unknown field spec.containers[0].volumes` | k8s schema | volumes indented INTO the container | error path names array index + field — precise localization; move 2 spaces left |
| 3 | `apiVersion not set` (line 1 WAS apiVersion: v1) | yaml | value dropped: `apiVersion:` with nothing after colon | first suspicion: invisible chars — `cat -A` forensics (BOM `M-oM-;M-?`, tab `^I`, CR `^M`) — all innocent here, culprit was plain transcription loss |
| 4 | `unknown field spec.selector.template` | k8s schema | `template:` inside `selector:` (AGAIN) | selector only accepts matchLabels; template is spec's child |
| 5 | CrashLoopBackOff on web pod | nginx-conf (inside ConfigMap value!) | `proxy_pass http://api` missing `;` | nginx [emerg] `unexpected "}"` at line 8 = **crime scene, not culprit** — culprit is the line above (parser waited for `;`, got `}`). Bug stack is 3 layers: yaml nesting / ConfigMap transport / nginx syntax — debug with the syntax of the layer that errored |
| 6 | curl `/` returned default nginx welcome page; `/api` 404 | cluster state | **zombie pods**: 2-day-old `web-deploy` pods carried the same `app: web` label → Service roster filled with them, new pod was crashlooping | **labels are cluster-wide matchmaking — no blood relation checked.** Old resources with matching labels hijack traffic. Classic prod incident |
| 7 | After ConfigMap fix, restart 7 still crashed | timing | kubelet symlink swap takes up to ~1min; container started on old config | hot-update has propagation delay; impatient? delete the pod |
| 8 | restart gaps: 84s → 5m15s | k8s | CrashLoopBackOff exponential backoff | crash → longer waits (30s→1m→2m→4m...) to protect the node; CKA material |

Also: paste through terminal strips indentation (transfer yaml as files); kubectl has no `-y`/`-p`; `l` vs `1` in pod suffixes (`hh7l4`); kubectl suggests near-miss commands.

## Gotchas
1. Multi-doc yaml (`---`) applies each object independently — partial success is normal; re-apply shows `unchanged` for the done ones.
2. `metadata.name` typo = the resource IS that name forever (pod `cm-dome`); kubectl doesn't validate intent.
3. Read the error's PATH first — k8s names container index and field.
4. Don't wait for crash backoff — `kubectl delete pod` forces immediate rebuild.
5. Cleanup check BEFORE deploying a same-named-label service: `kubectl get deploy` first.

## Artifacts
- `projects/k8s-configmap/0001-cm-pod.yaml` — cm-demo pod (typo'd `cm-dome`), env + volume dual injection
- `projects/k8s-configmap/0002-api.yaml` — ConfigMap + Deployment + Service (http-echo, $(MESSAGE) expansion)
- `projects/k8s-configmap/0003-web.yaml` — nginx + ConfigMap-injected reverse proxy + NodePort 30081

## Status at session end
- web pod restart 8 = Running; zombie web-deploy deleted.
- **PENDING: final acceptance curl** — `curl localhost:30081/` expect `web frontend OK`; `curl localhost:30081/api` expect `hello from api v1`. Run FIRST next session.
- Ingress (stage 3) NOT started.

## Next step
- Open next session: run the final acceptance curls; then quiz seeds: ① ConfigMap hot/cold paths (volume symlink swap vs env frozen in process memory) ② Law 1/Law 2 yaml reading ③ label triangle (matchLabels/selector/labels) ④ why zombie pods hijacked the Service ⑤ CrashLoopBackOff backoff behavior ⑥ Q1/Q2 blanks from today re-quiz.
- Then: Ingress (stage 3) to close Phase 0.
