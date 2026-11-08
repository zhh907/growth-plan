import json
import os

from anthropic.resources.messages import messages
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

def get_file_info(path: str) -> dict:
    """The REAL execution - this is your code,not the model's"""
    with open(path,"rb") as f:
        data = f.read()
    return {"path":path,"bytes":len(data),"lines":data.decode().count("\n")+1}

messages = [{
    "role":"user",
    "content":"which script is longer,0000-probe.py or 0002-structured-output.py? Answer with both line counts and the verdict."
}]

total_in = total_out = 0
for round_no in range(1,5):
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
        print(f"\n FINAL ANSWER:\n{text}")
        break
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
print(f"\n usage total_in={total_in} total_out={total_out}")