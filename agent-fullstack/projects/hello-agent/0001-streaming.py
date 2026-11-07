import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"],auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])

# 1）stream instead of create()：events flow to us as they are generated
print("=== streaming from glm-5.3 === \n")

with client.messages.stream(
    model="glm-5.3",
    max_tokens=10000,
    messages=[{
        "role":"user",
        "content":"In one sentence: why do ops engineers need to understand Linux internals?"
    }],
) as stream:
    for event in stream:
        # 2) one stream, mixed block types:distinguish thinking vs text
        if event.type == "content_block_delta" and hasattr(event.delta,"text"):
            print(event.delta.text,end="",flush=True)


# 3) after the stream ends,get the assembled message - usage = the bill
final = stream.get_final_message()
print("\n\n === usage (the bill) ===")
print(f"input tokens:{final.usage.input_tokens}")
print(f"ouput tokens:{final.usage.output_tokens}")

