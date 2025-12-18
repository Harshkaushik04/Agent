from llama_cpp import Llama
import json,argparse
from dotenv import load_dotenv
import os

load_dotenv()  # looks for .env in current directory
# ==============================
# CONFIGURATION
# ==============================
MODEL_PATH = os.getenv("DEEPSEEK_REASONING_MODEL_PATH")
CONTEXT_SIZE = 8192*3 
GPU_LAYERS = -1   # Set to -1 for GPU, 0 for CPU
BATCH_SIZE = 1024 
parser = argparse.ArgumentParser()
parser.add_argument("--user_prompt")
args = parser.parse_args()
try:
    user_prompt=json.loads(args.user_prompt)
except Exception as e:
    pass


def main():
    print("[make_plan.py] serving the request")
    llm = Llama(
        model_path=MODEL_PATH,
        n_gpu_layers=GPU_LAYERS,
        n_ctx=CONTEXT_SIZE,
        n_batch=BATCH_SIZE,
        verbose=False,
        chat_format="chatml"
    )
    with open("prompts/make_plan.txt","r",encoding="utf-8") as f:
        prompt=f.read()
    prompt=prompt.replace("{user_query}",user_prompt)
    history = []
    history.append({"role": "user", "content": prompt})
    
    stream = llm.create_chat_completion(
        messages=history,
        temperature=0.6,
        max_tokens=None, 
        stream=True
    )

    full_response = ""
    after_think = ""
    after_think_mode = False

    for chunk in stream:
        delta = chunk['choices'][0]['delta']
        if 'content' not in delta:
            continue

        content = delta['content']
        full_response += content

        # 1. PRINT NATURALLY (like before)
        print(content, end="", flush=True)

        # 2. Extract after </think>
        if after_think_mode:
            after_think += content

        if "</think>" in content:
            # Enable capture starting AFTER the tag, not including chunk
            after_think_mode = True
    return full_response,after_think

full_response,after_think=main()
# with open("com/make_plan.txt","w") as f:
#     f.write(after_think)