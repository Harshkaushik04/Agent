from llama_cpp import Llama
import json, argparse, sys
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  
MONGO_URL = os.getenv("MONGO_URL")
client = MongoClient(MONGO_URL)
db = client["ConversationModel"] 
HistoryModel = db["histories"]

# ==============================
# CONFIGURATION
# ==============================
parser = argparse.ArgumentParser()
parser.add_argument("--model")
parser.add_argument("--chat_number")
parser.add_argument("--username")
parser.add_argument("--user_message")
args = parser.parse_args()

model = json.loads(args.model)
chat_number = json.loads(args.chat_number)
username = json.loads(args.username)
user_message = json.loads(args.user_message)

# Ensure path is correct relative to this script
script_dir = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(script_dir, f"../../models/{model}.gguf")

CONTEXT_SIZE =18000
if model == "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M":
    CONTEXT_SIZE = 18000
GPU_LAYERS =-1
BATCH_SIZE = 512

def convert_history_to_prompt(history):
    prompt = ""
    for msg in history:
        role = msg["role"]
        content = msg["content"] 

        if role == "system":
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == "user":
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "model":
            prompt += f"<|im_start|>assistant\n{msg["after_think"]}<|im_end|>\n"

    # Prepare the model to speak
    prompt += "<|im_start|>assistant\n"
    return prompt

def main():
    print(f"[run_model.py] Loading model {model}...")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=GPU_LAYERS,
            n_ctx=CONTEXT_SIZE,
            n_batch=BATCH_SIZE,
            verbose=False,
            chat_format="chatml"
        )
    except Exception as e:
        print(f"Error loading model: {e}")
        return "", "", ""

    # Fetch History
    old_history = HistoryModel.find_one({
        "username": username,
        "model": model,
        "title": f"title{chat_number}"
    })

    ld_history = HistoryModel.find_one({
        "username": username,
        "model": model,
        "title": f"title{chat_number}"
    })

    history = []
    if old_history and "messages" in old_history:
        for msg in old_history["messages"]:
            role = msg.get("role", "user")
            
            # You requested to assume content is always filled. 
            # We check "text" (DB schema) first, then fallback to "content" just in case.
            content = msg.get("text") or msg.get("content", "")

            if role == "model":
                # For the model, we include the extra thinking fields
                history.append({
                    "role": role,
                    "content": content,
                    "before_think": msg.get("before_think", ""),
                    "after_think": msg.get("after_think", "")
                })
            else:
                # For user or system, we strictly send only role and content
                history.append({
                    "role": role,
                    "content": content
                })

    # Append the current new message
    history.append({"role":"system","content":"start thinking with <think> tag and stop thinking with </think> tag ,after that give the actual answer"})
    history.append({"role": "user", "content": user_message})
    print(f"[run-model]history:{history}")
    raw_prompt=convert_history_to_prompt(history)

    # --- ADD THIS DEBUGGING BLOCK ---
    prompt_tokens = len(llm.tokenize(raw_prompt.encode('utf-8')))
    print(f"[DEBUG] Prompt Tokens: {prompt_tokens}")
    print(f"[DEBUG] Context Size (n_ctx): {llm.n_ctx()}")
    
    available_tokens = llm.n_ctx() - prompt_tokens
    print(f"[DEBUG] Available for generation: {available_tokens}")

    if available_tokens < 500:
        print("[WARNING] Your history is too long! The model has no space to think.")
    # --------------------------------

    print("prompt:",raw_prompt)
    # Stream Generation
    stream = llm.create_completion(
        prompt=raw_prompt,
        temperature=0.6,
        max_tokens=13000,
        stream=True,
        stop=["<|im_end|>"]
    )
    full_response = ""
    
    # 1. Stream the raw content to stdout
    # UPDATED: 'create_completion' uses chunk["choices"][0]["text"]
    for chunk in stream:
        content = chunk["choices"][0]["text"]
        print(content, end="", flush=True)
        full_response += content

    # 2. Post-Process Splitting (Logic remains the same)
    before_think = ""
    after_think = ""
    
    closing_tag = "</think>"
    
    if closing_tag in full_response:
        # If tag exists, split normally
        parts = full_response.split(closing_tag, 1)
        
        # Remove the opening <think> tag if it exists to keep DB clean
        before_think = parts[0].replace("<think>", "").strip() 
        after_think = parts[1].strip()
    else:
        # If no think tag, assume it's a standard answer
        before_think = ""
        after_think = full_response

    return full_response, before_think, after_think

full_response, before_think, after_think = main()

new_message = {
    "role":"model",
    "content": full_response,       
    "before_think": before_think,
    "after_think": after_think
}

HistoryModel.update_one({
    "username":username,
    "model":model,
    "title":f"title{chat_number}"},
    {"$push":{"messages":{"role":"user",
                          "content":user_message}}}
)
HistoryModel.update_one(
    {"username":username,
     "model":model,
     "title":f"title{chat_number}"},
     {"$push":{"messages":new_message}}
)
