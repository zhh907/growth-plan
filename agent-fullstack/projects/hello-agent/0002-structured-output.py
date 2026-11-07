import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"],auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

SCHEMA_HINT = """Answer ONLY with a JSON object, no other text,no markdown fences.
Schema:
    {
        "risk_level":"low"|"medium"|"high",
        "reason":"<one short sentence>",
        "mitigation":"<one short sentence>"
    }
"""

question = "We deploy to production on Friday evening with no rollback plan."

resp = client.messages.create(
    model="glm-5.3",
    max_tokens=300,
    messages=[{
        "role":"user","content":f"{SCHEMA_HINT}\n\n Assess this {question}"
    }]
)
raw = next((b.text for b in resp.content if b.type == "text"),"")

# -- defense layer 2: robust extraction (strip fences / chatter) ----
start , end = raw.find("{"),raw.find("}")
parsed = None
if start != -1 and  end > start:
    try:
        parsed = json.loads(raw[start:end+1])
    except json.JSONDecodeError as e:
        print(f"PARSE FAIL:{e} \n raw was:{raw!r}")

# --- defense layer 3:validation after parsing ----
if parsed is not None:
    required = {"risk_level","reason","mitigation"}
    missing = required - parsed.keys()
    if missing:
        print(f"SCHEMA VIOLATION:missing {missing}")
    else:
        assert parsed["risk_level"] in {"low","medium","high"},f"bad enum:{parsed['risk_level']}"
        print(f"risk_level:{parsed['risk_level']}")
        print(f"reason:{parsed['reason']}")
        print(f"mitigation:{parsed['mitigation']}")

print(f"\n input tokens : {resp.usage.input_tokens}")
print(f"\n output tokens : {resp.usage.output_tokens}")