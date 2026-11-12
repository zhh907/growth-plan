"""
  0007 Parallel auditors : fan-out / fan-in (L2)

  orchestrator (deterministic Python)
    1. recon file , split into N segments
    2. fan-out: N segment auditors run CONCURRENTLY (threads),each gets its segment's text in the FIRST message - no tools needed
    3. fan-in : results collected BY SEGMENT INDEX (submission order),never by arrival order
  REUSE run_agent from 0006 (one nit fixed: first_message used verbatim )
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"],auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

# ----- recon tools : used by the ORCHESTRATOR itself (plain Python, no LLM) ----

def resolve_path(path:str) -> str:
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR,path)
    return path

def get_file_info(path:str) -> dict:
    try:
        with open(resolve_path(path),"rb") as f:
            data = f.read()
    except OSError as e:
        return {"error":f"cannot read file {path}: {e}"}
    return {"path":path,"bytes":len(data),"lines":data.decode(errors="replace").count("\n") + 1}



def read_file_chunk(path:str,start_line:int,end_line:int) -> dict:
    if start_line < 1:
        return {"error":"start_line must be >=1"}
    if end_line < start_line:
        return {"error":f"end_line ({end_line}) must be >= start_line ({start_line})"}

    try:
        with open(resolve_path(path),"r",encoding="utf-8",errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        return {"error":f"cannot read file {path}: {e}"}

    total = len(lines)
    if start_line > total:
        return {"error":f"start_line ({start_line}) beyond end of file (total {total} lines)"}

    end_line = min(end_line,total) # clamp:reading past EOF is benign,not an error
    chunk = [f"[{i}] {lines[i-1].rstrip()}" for i in range(start_line,end_line+1)]
    return {
        "path":path,
        "total_lines":total,
        "start":start_line,
        "end":end_line,
        "content":"\n".join(chunk),
    }

# ---- the ONE role : segment auditor (not tools - content arrives in message 1) ----

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

# ------- the agent loop: UNCHANGED from 0006 except frist_message is now verbatim ------

def run_agent(system_prompt: str , first_message : str ,max_rounds:int) -> tuple[str | None , int , int]:
    messages=[{
        "role":"user",
        "content":first_message,
    }]
    total_in = total_out = 0

    for round_n in range(1,max_rounds+1):
        resp = client.messages.create(
            model="glm-5.3",
            system=system_prompt,
            max_tokens=20000,
            messages=messages,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens
        tool_calls = [b for b in resp.content if b.type=="tool_use"]
        print(f"-----round {round_n} : stop={resp.stop_reason}, tools={[t.name for t in tool_calls]}-----")

        if not tool_calls:
            if resp.stop_reason == "max_tokens":
                print("ERROR: output bugget_exhausted (stop = max_tokens) ", file=sys.stderr)
                return None,total_in,total_out
            text = next((b.text for b in resp.content if b.type=="text"),"")
            return text,total_in,total_out

        messages.append({"role":"assistant","content": resp.content})
        results = []
        for tc in tool_calls:
            results.append({
                "type":"tool_result",
                "tool_use_id": tc.id,
                "content":"no tools in this role",
            })
        messages.append({"role":"user","content": results})
    return None,total_in,total_out

# -----orchestrator helpers ----
def split_segments(total_lines: int ,n: int) -> list[tuple [int,int]]:
    size = total_lines //n
    segments = []
    start = 1
    for i in range(n):
     end = total_lines if i == n-1 else start + size - 1
     segments.append((start,end))
     start = end + 1
    return segments

def audit_segment(index: int ,path: str,start: int,end:int ,max_rounds: int):
    chunk = read_file_chunk(path,start,end)
    first = (f"You are auditing line {start}-{end} of an MQL4 file."
          f"Global line numbers are prefixed [n]. \n\n {chunk['content']}")
    report,tin,tout = run_agent(SEGMENT_AUDITOR_PROMPT,first,max_rounds)
    return {"index":index,"start":start , "end":end , "report":report, "in":tin, "out":tout }

# ------ main = the orchestrator (deterministic Python) ------

def main():
    parser = argparse.ArgumentParser(description="Parallel segment auditors: fan-out  / fan-in")
    parser.add_argument("mql4file",help="Path to the.mq4 file to review ")
    parser.add_argument("--segments",type=int,default=3,help="number of parallel auditors")
    parser.add_argument("--max-rounds",type=int,default=3,help="pre-agent loop hard cap")
    args = parser.parse_args()

    info = get_file_info(args.mql4file)
    if "error" in info:
        print(info["error"],file=sys.stderr)
        sys.exit(2)

    segments= split_segments(info["lines"],args.segments)
    print(f"file:{info['lines']} lines -> {args.segments} segments:{segments}")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.max_rounds) as pool:
        futures = [pool.submit(audit_segment,i,args.mql4file,s,e,args.max_rounds)
                   for i,(s,e) in enumerate(segments)]
        results = [f.result() for f in futures]   # submission order ,NOT arrival order
    elapsed = time.time() - t0

    print(f"\fan-in:{len(results)} segment reports in {elapsed: 1f}s wall-clock")
    any_bugs = False
    total_in = total_out = 0
    for r in sorted(results ,key=lambda x: x["index"]):
        total_in +=  r["in"]
        total_out += r["out"]
        print(f"\n ===== SEGMENT {r['index']+1} (lines {r['start']}-{r['end']}) in={r['in']} out={r['out']} =====")
        print(r["report"] if r["report"] else "ERROR: segment agent failed to finish")
        if r["report"] and "NO BUGS FOUND" not in r["report"]:
            any_bugs = True
    print(f"\n total usage: in={total_in} out={total_out} wall-clock={elapsed:.1f}s =====")
    sys.exit(1 if any_bugs else 0)

if __name__ == "__main__":
    main()