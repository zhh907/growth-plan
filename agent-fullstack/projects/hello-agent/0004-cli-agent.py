import json
import argparse
import sys
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"], auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

TOOLS = [{
    "name": "get_file_info",
    "description": "Get line count and byte size of a file on disk.Use for any question about file size or length.",
    "input_schema": {
        "type": "object",
        "properties":{
            "path": {"type": "string","description":"Relative or absolute path to a file path"}
        },
        "required": ["path"]
    }
}]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_info(path: str) -> dict:
    """The REAL execution - this is your code,not the model's"""
    if not os.path.isabs(path):
        path = os.path.join(SCRIPT_DIR, path)
    with open(path,"rb") as f:
        data = f.read()
    return {"path":path,"bytes":len(data),"lines":data.decode().count("\n")+1}

def run_agent(question:str,max_rounds: int) -> tuple[str|None,int,int]:
    """Agent loop core.Returns (final_answer,input_tokens,output_tokens)."""
    messages = [{"role":"user","content":question}]
    total_in = total_out = 0
    for round_no in range(1,max_rounds+1):
        resp = client.messages.create(
            model="glm-5.3",
            max_tokens=1000,
            tools=TOOLS,
            messages=messages
        )
        total_in += resp.usage.input_tokens
        total_out += resp.usage.output_tokens

        tool_calls = [b for b in resp.content if b.type == "tool_use"]
        print(f"---- round{round_no}: stop reason={resp.stop_reason},tool_calls={[t.name for t in tool_calls]}")

        if not tool_calls:
            text = next((b.text for b in resp.content if b.type == "text"),"")
            return text,total_in,total_out
        # append assistant turn,execute tools ,append tool result
        messages.append({"role":"assistant","content": resp.content})

        results = []
        for tc in tool_calls:
            print("RAW tool_use block:",tc.model_dump())
            try:
                output = get_file_info(**tc.input)
            except Exception as e:
                output = {"error":str(e)}
            print(f" tool {tc.name} ({tc.input})->{output}")
            results.append({
                "type":"tool_result",
                "tool_use_id":tc.id,
                "content":json.dumps(output),
            })
        messages.append({"role":"user","content":results})
    return None,total_in,total_out
def main():
    parser = argparse.ArgumentParser(description="File QA agent with tool use")
    parser.add_argument("question",nargs="+",help="The question to ask(words are joined)")
    parser.add_argument("--max-rounds",type=int,default=5,help="agent loop hard cap")
    args = parser.parse_args()

    question = "".join(args.question)

    answer,total_in,total_out = run_agent(question,args.max_rounds)

    if answer is None:
        print("ERROR:hit round cap without a final answer",file=sys.stderr)
        sys.exit(1)

    print(f"\n FINAL ANSWER:\n {answer}")
    print(f"usage:in={total_in} out={total_out}")


if __name__ == "__main__":
    main()