# 0005 · Docker L1: image layers + container=process (step 6 started)

**Date: 2026-11-09 (session ran late 11-08) · Session 5**

## What I did
1. First session under the NEW opening-recap rule: 4-question quiz on rolling update & rollback — scored 2.5/4 (improving trend: 1.5/4 → 0.5/3 → 2.5/4).
2. Docker lesson 1 concepts: image = layered read-only stack; container = process + writable top layer.
3. Hands-on: dissected the WORK project image `smartpeak-agent:local` (581MB) via `docker history`; contrasted with `alpine` (2 layers, 8.66MB); exec'd into the old Tomcat container (`ps aux` + `top` inside); caught k8s pods appearing in `docker ps`.

## Key insights

**1. Quiz corrections (review list):**
- Rolling update ORDER is the point: new pod must be Ready BEFORE old pod dies → failed rollout = zero old pods sacrificed.
- undo reverts the CLUSTER only; the yaml file stays wrong → next apply re-detonates. Fix the file.
- pause holds the network NAMESPACE (IP + stack + localhost); sibling containers JOIN it — that's why pod-mates share 127.0.0.1.
- 5 hops: Mac → OrbStack port map → nodePort (iptables match) → DNAT to PodIP → cni0 into netns → nginx.

**2. Image = read-only layer cake, container = cake + writable clay.**
Every Dockerfile instruction = one layer; layers are shared on disk (why pulls print "already exists") and cache-hit on rebuild. Container writes go to a copy-on-write top layer; container deletion discards it, image untouched. Same image → N isolated instances.

**3. Layer-cake archaeology on smartpeak-agent:local (581MB):**
- 72% of the image = two fat layers: pip install 254MB + filebeat binary COPY 164MB.
- GOOD practice already present: `COPY requirements.txt` (older timestamp) separate from `COPY backend/` (newer) — rebuilds after code changes only redo the 15.8MB code layer; the 254MB deps layer eats cache. The timestamps prove it.
- `RUN sed -i '1s/^\xef\xbb\xbf//' requirements.txt` — a BOM scar: someone edited requirements on Windows, pip choked on Linux, patch instruction left in the image. `docker history` = the project's medical record.
- Optimization ledger (for the multi-stage lesson): --no-cache-dir / prune unused heavy deps; filebeat baked into the business image is an anti-pattern → k8s sidecar container is the cure.
- ENTRYPOINT (forced entry, project's entrypoint.sh) vs CMD (default, base's python3) both visible in one history.

**4. Same process, two world views (PID namespace):**
Node view: java at PID 381 among hundreds. In-container view: java at **PID 1**, 3 processes total. Same process, different tables. `top` inside showed 10 CPUs — a trimmed "whole machine" view. A container is not a VM, but every namespace builds it a parallel worldview.

**5. Grand unification frame: k8s pods seen in `docker ps`.**
`k8s_nginx_web-deploy-..._default_<uid>_0` and `rancher/mirrored-pause /pause` — the pod from today's k8s lessons IS two ordinary docker containers. Naming: k8s_<ctr>_<pod>_<ns>_<uid>_<restart-count>. Three days of layers (k8s orchestration → docker → namespaces) in one screenshot.

**6. Misc finds:**
- Tomcat base = Alpine 3.9.4 (2019) + Java 8 — 7-year-old base, security debt; "runs" ≠ "should stay".
- Image inventory: 3 CAT variants (~2.2GB) + two MySQL 8.x (~1.4GB) idle — cleanup candidate, recorded NOT executed (destructive op discipline).
- alpine: 2 layers / 8.66MB vs smartpeak: 21 layers / 581MB — image shape is designed, not innate.

## Gotchas
1. `docker history` reads BOTTOM-UP (base at the bottom); `<missing>` layer IDs are normal (content-addressed storage).
2. 0B layers still count as layers (ENV/EXPOSE/CMD only touch metadata).
3. BOM on requirements breaks pip on Linux — keep requirements out of Windows editors (or keep the sed).

## Artifacts
- No new file; existing work image smartpeak-agent:local used as the specimen.

## Next step
- Docker L2: container networking (what `-p` really does — pstub already seen) + volumes (data that survives container death) + Compose.
- Opening quiz seeds: rebuild-from-which-layer (answered), PID 1 inside a container means what, why filebeat-in-image is an anti-pattern.
