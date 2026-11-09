"""
    0005 · MQL4 code analyzer - step A : chunked reading tool + smoke test

    Two tools: get_file_info(recon) + read_file_chunk(patrol).
    The agent wiring(Step B) comes later-this file only proves the tool layer

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

SYSTEM_PROMPT = """You are s senior MQL4 (MetaTrader 4 Expert Advisor) code reviewer.

workflow 
1.Call get_file_info FIRST to learn the file's total lines.
2.Read the WHOLE file with read_file_chuck in ordered chunks (e.g. 1-120 ,121-240, ...).Never skip lines.
3.Only then report findings.

Bug checklist (the exam syllabus):
1.LOT SIZE CONTROL - lot not normalized to MODE_LOTSTEP, or outside MINLOT ..MAXLOT,or hardcoded fixed lots with no risk-based sizing. Fatal:broker rejects the order, or position size mismatches risk.
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
def execute_tool(name:str,tool_input:dict) -> dict:
    """Dispatch a model tool call to its implementation.Error as data,never raised"""
    if name == "get_file_info":
        return get_file_info(**tool_input)
    elif name == "read_file_chunk":
        return read_file_chunk(**tool_input)
    return {"error":f"unknown tool : {name}"}

def run_agent(file_path:str ,max_rounds:int) -> tuple[str | None , int , int]:
    """Agent loop:reviewer reads the file in chunks ,then reports bugs."""
    messages=[{
        "role":"user",
        "content":f"Analyze this MQL4 file for bugs:{file_path}",
    }]
    total_in = total_out = 0

    for round_on in range(1,max_rounds+1):
        resp = client.messages.create(
            model="glm-5.3",
            system=SYSTEM_PROMPT,
            max_tokens=20000,
            tools=TOOLS,
            messages=messages,
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens

        print("RAW content:",[b.model_dump() for b in resp.content])
        print("block types:",[b.type for b in resp.content])

        tool_calls = [b for b in resp.content if b.type=="tool_use"]
        print(f"-----round {round_on} : stop={resp.stop_reason}, tools={[t.name for t in tool_calls]}-----")

        if not tool_calls:
            text = next((b.text for b in resp.content if b.type=="text"),"")
            return text,total_in,total_out

        messages.append({"role":"assistant","content": resp.content})

        results = []
        for tc in tool_calls:
            try:
                output = execute_tool(tc.name, tc.input)
            except Exception as e:
                output = {"error" : f"{type(e).__name__}:{e}"}
            print(f"tool {tc.name} ({tc.input}) --> lines {output.get('start','?')}..{output.get('end','?')} ")
            results.append({
                "type":"tool_result",
                "tool_use_id": tc.id,
                "content":json.dumps(output),
            })

        messages.append({"role":"user","content": results})
    return None,total_in,total_out

def main():
    parser = argparse.ArgumentParser(description="MQL4 bug analyzer agent")
    parser.add_argument("mql4file",help="Path to the.mq4 file to review ")
    parser.add_argument("--max-rounds",type=int,default=15,help="agent loop hard cap")
    args = parser.parse_args()

    answer, total_in,total_out = run_agent(args.mql4file,args.max_rounds)

    if answer is None:
        print("ERROR: hit rount cap without a final answer", file=sys.stderr)
        sys.exit(1)

    print(f"\n FINAL REPORT:\n {answer}")
    print(f"usage: in={total_in} out={total_out}")

if __name__ == "__main__":
    main()