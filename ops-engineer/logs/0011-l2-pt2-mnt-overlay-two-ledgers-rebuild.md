# 0011 — L2 namespaces pt2: mnt + overlayfs decode + two-ledgers re-derivation

Date: 2026-11-13 (afternoon session 3, same day as 0009/0010). Lab: same `docker run --rm -it --privileged ubuntu:24.04 bash` container.

## 1. Experiment E — mnt room + tmpfs (verified)

```
unshare --mount bash
mount -t tmpfs tmpfs /mnt      # attach a RAM disk at /mnt, recorded on the PRIVATE copy
touch /mnt/secret.txt
ls /mnt                        # secret.txt (inside)
exit
ls /mnt                        # empty (outside)
```

Two distinct effects, learner initially only saw the second:
1. **Visibility isolation from the moment of recording**: `unshare --mount` copies the mount TABLE (the ledger); the `mount` entry lands only on the copy. Outside processes read the original table → no entry → /mnt is an empty hole. Isolation holds even while the room lives.
2. **Destruction**: tmpfs is RAM-backed and its lifecycle is tied to the room+mount; room teardown evaporates the disk AND its contents (secret.txt unrecoverable — "断电即焚" literally).

Analogy mapping (the load-bearing one): mount table = the LEDGER. Same two-ledger model as pid//proc in 0010.

## 2. Experiment F — real container mount table (verified)

`cat /proc/mounts | grep '/'` (greedy match, caught everything) → the overlay line decoded:

- `lowerdir=A:B` — read-only image layers (colon-separated), SHARED by all containers of the same image (cache economics)
- `upperdir=.../diff` — per-container writable layer; every byte written in the container lands here
- `workdir=...` — overlay's scratch space for copy-up mechanics

Log 0005's "layer cake + clay" model now has its bookkeeping voucher: the merged view is one mount entry in the container's private mount table, attached at `/`.

Bonus finds (bind mounts from /dev/vdb1, subvol=/docker): **/etc/hostname, /etc/hosts, /etc/resolv.conf** are individually bind-mounted INTO the container by docker — image stays generic, per-container identity injected via three file mounts. Closes the uts-lesson loose end (hostname comes from a file docker injects, plus the uts room). Also spotted: `cgroup2 ... nsdelegate` mount = L3 preview.

## 3. user / cgroup rooms — verbal sweep only

- user room not swapped in default containers (inode 4026531837 = host-initial) → in-container root IS host root; CKS topic.
- cgroup room = prettified cgroup path view; details in L3.

## 4. nsenter/lsns — NOT RUN (deferred)

Batch was handed out (unshare --net sleep 600 & → /proc/$PID/net/dev peek vs nsenter -t $PID -n enter) but learner reported "感觉怎么看不懂了" before executing. Deferred to next session. Word-by-word dissection already in this session's chat, redo it when re-offered.

## 5. Comprehension incident + re-derivation (mentor log)

Learner flagged fog ("怎么看不懂了"); located via options → fog started at the two-ledgers section (mid-0010 material), meaning everything after (mnt/overlay/nsenter) was built on sand. Response: full stop, zero new commands, re-derived the two-ledger model from scratch in 4 plain sentences:

1. ps = a roster-reader; /proc = the archive room, folder name = PID
2. same person, two numbering scopes (楼内门牌 101 vs 全市户籍第 34 户)
3. `$$`=1 asked the NEW ledger; `readlink /proc/self`=34 asked the OLD one — both true, different worlds
4. ps crash = carrying ledger A into archive B to find itself; `--mount-proc` = give the room its own archive

Mantra: **`--pid` 管"编号哪来的",`/proc` 管"档案放哪的",必须配套。**

Verification (paper question, map private mount table to the ledger analogy): learner answered "销毁了/为空了" — outcome correct (destruction), mapping missing (visibility isolates at RECORDING time, not destruction). Counted 0.5/1; mentor completed the mapping. Model is now built but "not yet dry" — no new material this session.

Rule reinforced (memory #10): command stacking hides understanding loss; mid-stack plain-language re-derivation + prediction checkpoints are mandatory. Second incident same day → for future sessions: one load-bearing model per session max, verify it with a paper question BEFORE stacking the next batch.

## 6. Acceptance status

L2: pid ✅ uts ✅ net ✅ mnt ✅ overlay-decode ✅ two-ledgers (rebuilt, needs re-verification) ⚠️ nsenter/lsns ⏳. Next session: ① re-quiz two-ledger model FIRST (paper), ② run the deferred nsenter batch, ③ close L2 → L3 cgroups.

Re-quiz seeds: mount table = ledger mapping; lowerdir/upperdir meaning; /etc/hostname bind-mount injection; $$ vs /proc/self; why --fork mandatory; lookup-self crash.
