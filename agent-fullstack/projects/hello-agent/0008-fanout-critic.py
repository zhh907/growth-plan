"""
    0008 fanout + whole -file critic : mapreduce shape (fixes l2 boundary blindness)

    stage 1(MAP) : 0007 unchanged - parallel segment auditors, cheap,honest,boundary-blind
    short-circuit: all segments clean -> critic never runs,exit 0
    stage 2 (REDUCE) : ONE critic gets the WHOLE file + all segment reports in its first message (tooless).Whole-file view= the cure for slice-blindness.
    Exit code:      string-matched from "SURVIVED" : n of N" - the KNOWN hazard,Killed by structured output in the next lesson.
"""

import argparse
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"], auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


# ----- recon tools : used by the ORCHESTRATOR itself (plain Python, no LLM) ----

def resolve_path(path: str) -> str:
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    return path


def get_file_info(path: str) -> dict:
    try:
        with open(resolve_path(path), "rb") as f:
            data = f.read()
    except OSError as e:
        return {"error": f"cannot read file {path}: {e}"}
    return {"path": path, "bytes": len(data), "lines": data.decode(errors="replace").count("\n") + 1}


def read_file_chunk(path: str, start_line: int, end_line: int) -> dict:
    if start_line < 1:
        return {"error": "start_line must be >=1"}
    if end_line < start_line:
        return {"error": f"end_line ({end_line}) must be >= start_line ({start_line})"}

    try:
        with open(resolve_path(path), "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        return {"error": f"cannot read file {path}: {e}"}

    total = len(lines)
    if start_line > total:
        return {"error": f"start_line ({start_line}) beyond end of file (total {total} lines)"}

    end_line = min(end_line, total)  # clamp:reading past EOF is benign,not an error
    chunk = [f"[{i}] {lines[i - 1].rstrip()}" for i in range(start_line, end_line + 1)]
    return {
        "path": path,
        "total_lines": total,
        "start": start_line,
        "end": end_line,
        "content": "\n".join(chunk),
    }


# ---- role prompts ----

SEGMENT_AUDITOR_PROMPT = """
    You are a junior MQL4 code reviewer auditing ONE SEGMENT of a larger file.You will receive the segment's code in the first message,with global line numbers prefixed like [42]

    Bug checklist:
    1. LOT SIZE CONTROL - lot not normalized to MODE_LOTSTEP,or outside MINLOT .. MAXLOT.
    2. SAME-BAR REPEATED ENTRIES - no new-bar guard AND no same-type entry refusal: the bug exists if an entry signal can fire again  while a same-type position is already open.A MaxTrades/order-count cap > 1 does NOT count as refusal (it only limits how many time you get burned).
    3. MISSING STOP LOSS - OrderSend without SL (and a slice may simply not contain the OrderSend call - then say so).

    Rules:
    - Report ONLY bugs whose cited lines are INSIDE your segment. Never speculate about code you cannot see.
    - If a checklist item cannot be judged from your segment , say "NOT JUDGEABLE FROM SEGMENT" for it.
    - If no bugs: reply with exactly NO BUGS FOUND.

    Output format:
    VERDICT: BUGS FOUND <n> | NO BUGS FOUND
    Then per finding:
    [SEVERITY HIGH/MED/LOW] checklist item | lines:<n>
        code: <quoted line(s)>
        why fatal: <one sentence> 
"""

CRITIC_PROMPT = """
    You are a senior MQL4 code reviewer adjudicating findings from junior auditors.
    You will receive the COMPLETE file plus all segment reports in the first message.
    
    for EACH finding reported by the auditors:
    1. Check the cited lines against the actual code.
    2.If the finding claims protective logic is MISSING,search the WHOLE FILE ;first - the guard may exist in lines the auditor's segment never contained.
    3.Verdict: VERIFIED (real bug) or REFUTED (cite the exact lines that refute it).
    
    Output format:
    CRITIC SUMMARY: SURVIVED:<n> or <N>
    Then per finding:
    FINDING <i> : [VERIFIED |  REFUTED] <checklist item> | lines : <n>
        evidence: <one sentence citing exact line numbers> 
"""

# ------- the agent loop (unchanged from 0007)------

def run_agent(system_prompt: str, first_message: str, max_rounds: int) -> tuple[str | None, int, int]:
    messages = [{
        "role": "user",
        "content": first_message,
    }]
    total_in = total_out = 0

    for round_n in range(1, max_rounds + 1):
        resp = client.messages.create(
            model="deepseek-chat",
            system=system_prompt,
            max_tokens=20000,
            messages=messages,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        tool_calls = [b for b in resp.content if b.type == "tool_use"]
        print(f"-----round {round_n} : stop={resp.stop_reason}, tools={[t.name for t in tool_calls]}-----")

        if not tool_calls:
            if resp.stop_reason == "max_tokens":
                print("ERROR: output bugget_exhausted (stop = max_tokens) ", file=sys.stderr)
                return None, total_in, total_out
            text = next((b.text for b in resp.content if b.type == "text"), "")
            return text, total_in, total_out

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for tc in tool_calls:
            results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": "no tools in this role",
            })
        messages.append({"role": "user", "content": results})
    return None, total_in, total_out


# -----orchestrator helpers ----
def split_segments(total_lines: int, n: int) -> list[tuple[int, int]]:
    size = total_lines // n
    segments = []
    start = 1
    for i in range(n):
        end = total_lines if i == n - 1 else start + size - 1
        segments.append((start, end))
        start = end + 1
    return segments


def audit_segment(index: int, path: str, start: int, end: int, max_rounds: int):
    chunk = read_file_chunk(path, start, end)
    first = (f"You are auditing line {start}-{end} of an MQL4 file."
             f"Global line numbers are prefixed [n]. \n\n {chunk['content']}")
    report, tin, tout = run_agent(SEGMENT_AUDITOR_PROMPT, first, max_rounds)
    return {"index": index, "start": start, "end": end, "report": report, "in": tin, "out": tout}

def parse_survived(text: str | None) -> tuple[int | None, int | None]:
    m = re.search(r"SURVIED : \s*(\d+)\s*of\s*(\d+)",text or "")
    return (int(m.group(1)), int(m.group(2))) if m else (None,None)

# ------ main = the orchestrator (deterministic Python) ------

def main():
    parser = argparse.ArgumentParser(description="Fan-out auditors + whole-file critic (MapReduce)")
    parser.add_argument("mql4file", help="Path to the.mq4 file to review ")
    parser.add_argument("--segments", type=int, default=3, help="number of parallel auditors")
    parser.add_argument("--max-rounds", type=int, default=3, help="pre-agent loop hard cap")
    args = parser.parse_args()

    info = get_file_info(args.mql4file)
    if "error" in info:
        print(info["error"], file=sys.stderr)
        sys.exit(2)

    # ----- Stage 1 : MAP (identical to 0007) ----
    segments = split_segments(info["lines"], args.segments)
    print(f"file:{info['lines']} lines -> {args.segments} segments:{segments}")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_rounds) as pool:
        futures = [pool.submit(audit_segment, i, args.mql4file, s, e, args.max_rounds)
                   for i, (s, e) in enumerate(segments)]
        results = [f.result() for f in futures]  # submission order ,NOT arrival order
    map_elapsed = time.time() - t0
    total_in = sum(r["in"] for r in results)
    total_out = sum(r["out"] for r in results)

    # ----- Short-circuit : no findings -> no court -----
    clean = [r for r in results if r["report"] and "NO BUGS FOUND" in r["report"]]
    if len(clean) == len(results):
        print(f"\nall {len(results)} segments clean -> critic skippped (short-circuit)")
        print(f"total usage: in={total_in} out={total_out} map={map_elapsed: 1f}s critic=0s")
        sys.exit(0)

    # ----- Stage 2:REDUCE (whole-file critic,toolless)----
    print(f"\n{len(results)-len(clean)} segment(s) reported findings -> convening critic")
    for r in sorted (results, key=lambda x: x["index"]):
        print(f"\n====== SEGMENT {r['index']+1} (lines {r['start']}-{r['end']}) in ={r['in']} out={r['out']} =====")
        print(r["report"] if r["report"] else "ERROR: segment agent failed to finish")

    whole = read_file_chunk(args.mql4file, 1, info["lines"])
    reports_block = "\n\n".join(
        f"--- SEGMENT {r['index']+1} (lines {r['start']}-{r['end']}) report ---\n{r['report']}"
        for r in sorted(results, key=lambda x: x["index"]))
    critic_first = (f"Adjudicate the auditor reports below against the COMPLETE file.\n\n"
                    f"=== COMPLETE FILE ({info['lines']} lines) ===\n{whole['content']}\n\n"
                    f"=== AUDITOR REPORTS ===\n{reports_block}")

    t1 = time.time()
    verdict, cin, cout = run_agent(CRITIC_PROMPT, critic_first, args.max_rounds)
    critic_elapsed = time.time() - t1
    total_in += cin
    total_out += cout

    print(f"\n===== CRITIC VERDICT in={cin} out={cout} ({critic_elapsed:.1f}s) =====")
    print(verdict if verdict else "ERROR: critic failed to finish")
    print(f"\ntotal usage: in={total_in} out={total_out} "
          f"map={map_elapsed:.1f}s critic={critic_elapsed:.1f}s")

    survived, filed = parse_survived(verdict)
    if survived is None:
        print("WARNING: SURVIVED line not found in critic output (the known string-match hazard)",
              file=sys.stderr)
        sys.exit(2)
    sys.exit(1 if survived > 0 else 0)

if __name__ == "__main__":
    main()