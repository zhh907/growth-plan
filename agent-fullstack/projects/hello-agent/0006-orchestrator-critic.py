"""
    0006  Orchestrator Critic:two agents in series, Python as the orchestrator

    stage 1 auditor : 0005's reviewer unchanged（checklist patrol,findings w/ line cites）
    stage 2 critic : NEW role - re-reads the cited lines and verifies each finding
    main() = the orchestrator (deterministic Python, NOT an LLM)
            short-circuit: auditor sqys NO BUGS FOUND -> critic never runs
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"],auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

TOOLS = [
    {
        "name": "get_file_info",
        "description":"Get line count and byte size of a file on disk."
                        "Use this FIRST to learn a file's total lines before reading chunks",
        "input_schema":{
            "type":"object",
            "properties":{
                "path":{"type":"string","description":"Relative or absolute path to a file"},
            },
            "required":["path"]
        }
    },
    {
        "name": "read_file_chunk",
        "description":"Read a range of lines (inclusive,1-based)from a file"
                        "Each returned line is prefixed with its global line number like[42]"
                        "Call get_file_info first to learn total_lines,then patrol the file in chunks",
        "input_schema":{
            "type":"object",
            "properties":{
                "path":{"type":"string","description":"Relative or absolute path to file"},
                "start_line":{"type":"integer","description":"First line to read, >=1"},
                "end_line":{"type":"integer","description":"Last line to read, inclusive"},
            },
            "required":["path","start_line","end_line"]
        }
    }
]

def resolve_path(path:str) -> str:
    """Anchor relative paths to the script's own directory (CWD-proof)"""
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR,path)
    return path

def get_file_info(path:str) -> dict:
    """Recon:total lines + bytes. Model uses this to plan its chunk reads"""
    try:
        with open(resolve_path(path),"rb") as f:
            data = f.read()
    except OSError as e:
        return {"error":f"cannot read file {path}: {e}"}
    return {"path":path,"bytes":len(data),"lines":data.decode(errors="replace").count("\n") + 1}



def read_file_chunk(path:str,start_line:int,end_line:int) -> dict:
    """Patrol:read lines [start_line,end_line] inclusive, each prefixed with its global number.

        Boundary policy:clamp end_line to total lines,but REJECT structurally wrong ranges.
        Errors are returned as data (the model can read them and self-correct),never raised.
    """
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

def execute_tool(name:str,tool_input:dict) -> dict:
    """Dispatch a model tool call to its implementation.Error as data,never raised"""
    if name == "get_file_info":
        return get_file_info(**tool_input)
    elif name == "read_file_chunk":
        return read_file_chunk(**tool_input)
    return {"error":f"unknown tool : {name}"}

# --------------- prompts : two roles , two clean contexts ---------

AUDITOR_PROMPT = """You are s senior MQL4 (MetaTrader 4 Expert Advisor) code reviewer.

workflow 
1.Call get_file_info FIRST to learn the file's total lines.
2.Read the WHOLE file with read_file_chuck in ordered chunks (e.g. 1-120 ,121-240, ...).Never skip lines.
3.Only then report findings.

Bug checklist (the exam syllabus):
1.LOT SIZE CONTROL - lot not normalized to MODE_LOTSTEP, or outside MINLOT ..MAXLOT. Fatal:broker rejects the order, or position size mismatches risk.
2.SAME-BAR REPEATED ENTRIES - no new-bar guard AND no check for already-open orders,so an entry signal fires on every tick of the same bar. Fatal: one signal becomes N stacked positions.
3.MISSING STOP LOSS - OrderSend without SL, and no OrderModify adding one later.Fatal:one bad trade can wipe the account.

Report rules:
- Cite the exact line number(s) for every finding.
- If a checklist item does not apply to this file, say so explicitly.
- Do NOT invent bugs beyond the checklist .

Output format:
VERDICT:BUGS FOUND <n> | NO BUGS FOUND
Then per finding:
[SERVERITY HIGH/MED/LOW] checklist item | lines:<n>
    code: <quoted line(s)>
    why fatal: <one sentence>
    fix :<one sentence>
"""

CRITIC_PROMPT = """You are a verification critic.Another reviewer agent has produced a bug report for an MQL4 file.
Your ONLY job is to fact-check each finding against the real file.

Workflow
1. For EVERY finding in the report ,read the cited line(s) (plus a few lines of context around them) with read_file_chunk.
2. Check: does the cited line exist,does the quoted code match, and does it actually support the claim?
3. You have NO opinion on code quality. You only compare claims against file content.

Verdict rules - mark each finding exactly one of:
- VERIFIED - the citation is real and supports the claim 
- REFUTED - the citation is wrong,the quote does not match ,or the code does not support the claim(e.g the protective logic EXISTS elsewhere in the file )

Output format:
FINDING 1 : VERIFIED | REFUTED - <one line of evidence>
FINDING 2: ...
SURVIVED: <n of n>
"""

# ------- the agent loop: generalized from 0005's run_agent ------

def run_agent(system_prompt: str , first_message : str ,max_rounds:int) -> tuple[str | None , int , int]:
    messages=[{
        "role":"user",
        "content":f"Analyze this MQL4 file for bugs:{first_message}",
    }]
    total_in = total_out = 0

    for round_on in range(1,max_rounds+1):
        resp = client.messages.create(
            model="glm-5.3",
            system=system_prompt,
            max_tokens=20000,
            tools=TOOLS,
            messages=messages,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens

        tool_calls = [b for b in resp.content if b.type=="tool_use"]
        print(f"-----round {round_on} : stop={resp.stop_reason}, tools={[t.name for t in tool_calls]}-----")

        if not tool_calls:
            if resp.stop_reason == "max_tokens":
                print("ERROR: output bugget_exhausted (stop = max_tokens) ", file=sys.stderr)
                return None,total_in,total_out
            text = next((b.text for b in resp.content if b.type=="text"),"")
            return text,total_in,total_out

        messages.append({"role":"assistant","content": resp.content})

        results = []
        for tc in tool_calls:
            try:
                output = execute_tool(tc.name, tc.input)
            except Exception as e:
                output = {"error" : f"{type(e).__name__}:{e}"}
            print(f"tool {tc.name} ({tc.input})")
            results.append({
                "type":"tool_result",
                "tool_use_id": tc.id,
                "content":json.dumps(output),
            })

        messages.append({"role":"user","content": results})
    return None,total_in,total_out

# ------ main = the orchestrator (deterministic Python) ------

def main():
    parser = argparse.ArgumentParser(description="MQL4 analyzer: auditor + critic in series")
    parser.add_argument("mql4file",help="Path to the.mq4 file to review ")
    parser.add_argument("--max-rounds",type=int,default=15,help="pre-agent loop hard cap")
    args = parser.parse_args()

    # Stage 1 : auditor
    print("==== STAGE 1 : AUDITOR ======")
    audit_report, a_in ,a_out = run_agent(
        AUDITOR_PROMPT, f"Analyze this MQL4 file for bugs:{args.mql4file}",args.max_rounds
    )
    if audit_report is None:
        print("ERROR: auditor failed to finish",file=sys.stderr)
        sys.exit(2)
    print(f"\n AUDITOR REPORT:\n {audit_report}")
    print(f"auditor usage: in = {a_in} out={a_out}")

    # Short-circuit : nothing to verify
    if "NO BUGS FOUND" in audit_report:
        print("\n No findings -> critic skipped (short-circuit). DONE.")
        print(f"total usage: in={a_in} out={a_out}")
        sys.exit(0)

    # Stage 2: critic
    print("\n ==== STAGE 2: CRITIC")
    critic_input = f"MQL4 file: {args.mql4file} \n\n Report to verify:\n {audit_report}"
    critic_report,c_in, c_out = run_agent(
        CRITIC_PROMPT,critic_input,args.max_rounds
    )
    if critic_report is None:
        print("ERROR: critic failed to finish" , file=sys.stderr)
        sys.exit(2)
    print(f"\n CRITIC: {critic_report}")
    print(f"critic usage: in={c_in} out={c_out}")
    print(f"total usage: in={a_in+c_in} out={a_out+c_out}")

   #Final verdict : findings that survived the critic
    if "SURVIVED: 0" in critic_report:
        sys.exit(0)

    sys.exit(1)

if __name__ == "__main__":
    main()