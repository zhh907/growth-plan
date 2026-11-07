import os
from dotenv import load_dotenv
# from openai import OpenAI
from anthropic import Anthropic


load_dotenv()
# client = OpenAI(base_url=os.environ["OPENAI_BASE_URL"],api_key=os.environ["OPENAI_API_KEY"])
client = Anthropic(base_url=os.environ["ANTHROPIC_BASE_URL"],auth_token=os.environ["ANTHROPIC_AUTH_TOKEN"])


CANDIDATES=[
    "glm-5.3",
    "deepseek-chat"
]

for model in CANDIDATES:
    try:
        # response = client.chat.completions.create(
        #     model=model,
        #     messages=[{"role":"user","content":"hi"}],
        #     max_tokens=5,
        # )
        response = client.messages.create(
            model=model,
            messages=[{"role":"user","content":"hi"}],
            max_tokens=1000,
        )
        text=next((b.text for b in response.content if b.type == "text"),"no text block")
        print(f"ok {model}:{text!r}")

        print(f"{response.content}")
    except Exception as e:
        msg=str(e)[:80]
        print(f"FAIL {model}:{msg}")