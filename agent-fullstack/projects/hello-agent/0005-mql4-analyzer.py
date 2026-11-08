"""
    0005 · MQL4 code analyzer - step A : chunked reading tool + smoke test

    Two tools: get_file_info(recon) + read_file_chunk(patrol).
    The agent wiring(Step B) comes later-this file only proves the tool layer

"""
import argparse
import json
import os

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
            "type":"onject",
            "properties":{
                "path":{"type":"string","description":"Relative or obsolute path to a file"},
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
            "type":"onject",
            "properties":{
                "path":{"type":"string","description":"Relative or obsolute path to file"},
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


if __name__ == "__main__":
    # Smoke test - ZERO API calls, deterministic layer only.
    target = "0004-cli-agent.py"

    print("=== 1.get_file_info ===")
    print(get_file_info(target))

    print("=== 2.normal chunk (lines 30-38) ===")
    r = read_file_chunk(target,start_line=30,end_line=38)
    print(f"meta:start{r['start']}end{r['end']} total={r['total_lines']}")
    print(r["content"])

    print("=== 3.clamp: end_line=9999 beyond EOF ===")
    r = read_file_chunk(target,1,9999)
    print(f"clamped end={r['end']} (total={r['total_lines']})")

    print("=== 4.rejections ===")
    print("start=0:",read_file_chunk(target,0,0))
    print("end<start:",read_file_chunk(target,10,3))
    print("start>EOF:",read_file_chunk(target,100000,499999))
    print("no file",read_file_chunk("no-such-file.mq4",20,100))

