# English Tech Vocabulary Accumulator

> Add entries as you meet them in real work. Format: term / how you met it / one-line meaning in your own words.
> Context economy: this file stays a SINGLE table (it is its own index). When it exceeds ~150 rows, archive rows older than 6 months into `vocab-archive/YYYY-MM.md` and note the archive here.

| Date | Term | Where I met it | My understanding (EN) |
|---|---|---|---|
| 2026-11-07 | control-plane | kubectl get nodes | the brain of a k8s cluster: API server, scheduler, controller manager |
| 2026-11-07 | kubeconfig | ~/.orbstack/k8s/config.yml | file telling kubectl which cluster to talk to and how to authenticate |
| 2026-11-07 | endpoint | API docs | a URL address where a service accepts requests |
| 2026-11-07 | probe | 0000-probe.py | a tiny test request that checks if something actually works |
| 2026-11-07 | relay / 中转 | api.new13.top | a proxy service that forwards API requests to many model providers |
| 2026-11-07 | config plane vs data plane | relay models list | what's configured vs what actually serves traffic |
| 2026-11-07 | deep health check | probe lesson | verifying a service by sending a REAL request, not just reading its status |
| 2026-11-07 | streaming | 0001 lesson | receiving output piece by piece as it is generated, not all at once |
| 2026-11-07 | SSE (Server-Sent Events) | streaming lesson | a web technology for a server to push events to a client continuously |
| 2026-11-07 | buffer / buffering | streaming diagnosis | holding data in a queue before passing it on (kills char-by-char streaming) |
| 2026-11-07 | bisection | debugging method | cutting the problem in half with each test to locate the failing layer |
| 2026-11-07 | allowlist vs denylist | parsing lesson | accept known-good (survives new types) vs block known-bad (breaks on new types) |
| 2026-11-07 | defensive parsing | content blocks | always expect malformed input; defaults + try/except instead of assuming |
| 2026-11-07 | chatter | JSON lesson | useless polite text the model adds before the actual answer |
| 2026-11-07 | markdown fence | JSON failure | the ``` ``` ``` wrapper around code blocks that breaks json.loads |
| 2026-11-07 | hallucination | JSON failure | model producing plausible-but-wrong output (e.g. invalid JSON) |
| 2026-11-07 | mitigation | 0002 schema | an action that reduces the severity of a risk |
| 2026-11-07 | rollback | 0002 prompt | reverting a deployment to the previous working version |
| 2026-11-07 | compromise (security) | key-leak lesson | a secret being exposed = treated as broken; rotate immediately |
| 2026-11-07 | rotation / rotate | key-leak lesson | replacing a leaked secret with a new one |
| 2026-11-07 | verification / signature | SignatureDelta | a cryptographic proof that content was not tampered with |
| 2026-11-08 | input_schema | 0003 tool definition | the contract key where a tool's parameter schema must live — typo = silent failure |
| 2026-11-08 | tool_use / tool_result | agent loop | block types: model requests a call / your code returns the outcome |
| 2026-11-08 | stop_reason / end_turn | agent loop | the control signal that says whether the model wants tools or is done |
| 2026-11-08 | parallel tool calls | 0003 round 1 | model issuing several tool calls in ONE round when the schema lets it |
| 2026-11-08 | observability | debugging doctrine | making internals visible (raw dumps, per-step logs) BEFORE theorizing |
| 2026-11-08 | smoke test | model selection | a minimal standard test run before committing to a dependency/model |
| 2026-11-08 | CWD (current working directory) | path bug | where relative paths resolve — the launch location, not the script location |
| 2026-11-08 | shadowing | import bug | an inner name hiding an outer one (junk import vs my messages list) |
| 2026-11-08 | silent failure | schema typo | wrong config key that doesn't error, just produces haunted behavior |
| 2026-11-08 | upstream_error | relay 400 | the relay reporting that the provider behind it rejected the request |
| 2026-11-08 | verdict | 0002 model output | the final judgment/decision in a structured answer |
| 2026-11-08 | hard cap | agent loop safety | max iterations to stop infinite loops from burning tokens |
| 2026-11-08 | separator (`--`) | kubectl exec lesson | marks "everything after this is the container's command, not kubectl's own flags" |
| 2026-11-08 | silent success | orbctl start k8s | Unix culture: no output + exit 0 means it worked |
| 2026-11-08 | state machine | pod status | a fixed set of states with defined transitions (ContainerCreating → Running) |
| 2026-11-08 | gracefully terminate | pod delete | SIGTERM first, wait for clean exit, then SIGKILL after timeout |
