# 0006 · Docker L2: container networking + volumes + Compose (Docker unit complete)

**Date: 2026-11-09 · Session 6**

## What I did
1. Opening quiz on session 5 (image layers, PID 1, filebeat anti-pattern, errors-as-data): scored **1.5/4** (trend now 1.5/4 → 0.5/3 → 2.5/4 → 1.5/4). All four corrected on the spot; all four logged for re-quiz.
2. Docker L2 hands-on, three parts, all on the local OrbStack Docker:
   - Networking: bridge subnet discovery, `-p` listener hunt, Mac→container-IP reachability test, routing-table autopsy.
   - Volumes: three demos (writable layer dies / named volume survives / bind mount alias).
   - Compose: two-service yaml (web + probe), auto network + DNS, three real errors fixed by reading messages.

## Key insights

**1. Opening quiz corrections (review list):**
- Cache invalidation is PREFIX-based: from the FIRST changed layer onward everything re-runs. requirements.txt before code = the 254MB layer eats cache.
- PID namespace gives each container its own PID table; main process = 1. PID 1 has no default signal handlers (SIGTERM must be handled or docker stop degrades to SIGKILL) and must reap orphans.
- filebeat baked into a business image = coupling (one upgrade → rebuild every image) + wrong process model. k8s cure: sidecar container (same Pod, shared netns/volume, independent lifecycle).
- Errors-as-data: a tool returning an error dict lets the MODEL read and self-correct next round; an exception kills the whole agent program. "Exceptions kill programs; error data educates models."

**2. Bridge = virtual switch, veth = cable.**
Every container gets a veth pair into the docker bridge; same-bridge containers reach each other by IP directly, no `-p` needed. Local subnet measured: 192.168.215.0/24, gateway .1 (OrbStack's own allocation, NOT the textbook 172.17).

**3. Who holds `-p` ports: the OrbStack main process.**
`lsof -nP -iTCP:18080 -sTCP:LISTEN` → OrbStack PID 52836 owns IPv4+IPv6 listeners. One process multiplexes ALL forwarded ports (my pstub prediction was wrong — data beat expectation; pstub serves other purposes). Full path: Mac curl → OrbStack process → VM → bridge → veth → container eth0 → nginx. Same gatekeeper pattern as k8s NodePort.

**4. Case closed: container IP instant 200, Pod IP timeout — the routing table explains both.**
`netstat -rn -f inet | grep 192.168`:
- 192.168.215 → bridge102 direct route, with the container's MAC registered → Mac and containers are L2 NEIGHBORS.
- No route for 192.168.194 (Pod subnet) → those packets fall into the broad `192.168.0/16 → utun4` route (VPN tunnel) → black hole → 75s timeout.
- Two ways to time out: no route (dropped) vs a route into a black hole. The routing table is the first crime scene.
- Bonus rows: bridge100 (192.168.128) = OrbStack VM network; bridge101 (192.168.147) = some work compose network.

**5. inspect schema change.**
`.NetworkSettings.IPAddress` → `map has no entry` on new Docker. IP is now per-connection: `.NetworkSettings.Networks.bridge.IPAddress`. Reason: a container can join multiple networks; IP is a property of the connection, not the container.

**6. Volume trilogy (three demos, one control group):**
- Demo 1: file in writable layer → `rm -f` → recreate → gone. Clay layer is cremated with the container.
- Demo 2: `docker volume create l2-data` → mount at docroot → `rm -f` + recreate → curl still 200. Volume lives at /var/lib/docker/volumes/ inside the VM. First mount over a non-empty dir COPIES image content into the volume (default page survived).
- Demo 3: bind mount `~/.../site:/usr/share/nginx/html:ro` → default page GONE (bind mount covers, never copies); edit file on Mac → curl sees it instantly (an alias to ONE file, not a sync). `:ro` = read-only inside, protects source.

**7. Compose = declarative + free DNS.**
One yaml (services: web + probe) → `up -d` builds containers AND a network (`docker-l2_default`) I never created. probe (bare alpine) fetched `wget -qO- http://web` BY NAME — service-name DNS, same bloodline as k8s Service DNS. `depends_on` = start ORDER, not READINESS (probe needed `sleep 2`; k8s cures this with readinessProbe).

**8. Three real errors, all self-fixed by reading the message:**
- `services.web additional properties 'probe' not allowed` → probe indented 4 spaces too deep, landed inside web's dict. YAML structure error, error names the trespasser.
- `Bind for 0.0.0.0:18090 failed: port is already allocated` → squatter = smartpeak-apollo-adminservice (work service). Don't touch others' services — changed MY port to 18095.
- `.Name` → `.Names`: docker ps format fields are plural.

**9. Misc finds:**
- `$(date)` = command substitution; `${data}` = variable expansion (empty when undefined) — bit me on the first index.html write.
- apollo-adminservice went from `Restarting (1)` (morning) to `Up` (later): its dependency recovered; docker restart policy = docker-grade self-heal, previews k8s CrashLoopBackOff.
- nginx logs show `1#1` (PID 1, thread 1) and workers starting at PID 29 — PID numbering is namespace-local and contiguous.

## Gotchas
1. OrbStack ≠ textbook: bridge subnet is 192.168.215.x, not 172.17.x; `-p` listeners live in the OrbStack main process, not per-port proxies.
2. A VPN's broad route (192.168.0/16 via utun4) silently swallows packets to unrouted private subnets → mysterious timeouts. Check `netstat -rn` before blaming the network.
3. Named volume vs bind mount on FIRST mount over a non-empty dir: volume copies image content in; bind mount covers with nothing. Opposite behaviors, easy to confuse.
4. `depends_on` does not wait for readiness — sleep is duct tape, readinessProbe is the cure.

## Artifacts
- `projects/docker-l2/docker-compose.yaml` — web + probe compose stack (port 18095 after conflict fix)
- `projects/docker-l2/site/index.html` — bind-mount source dir
- Live leftovers (kept, not cleaned): compose stack up on 18095, l2-web container on 18080, l2-data volume
- `reports/0006-report-2026-11-09.html` — daily report

## Next step
- Re-quiz the 4 misses; ops Phase 0 closes with ConfigMap/Ingress + multi-service app.
- Lab still running (compose stack + l2-web + l2-data) — decide cleanup next session.
