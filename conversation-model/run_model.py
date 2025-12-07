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
MODEL_PATH = os.path.join(script_dir, f"../models/{model}.gguf")

CONTEXT_SIZE = 4096
if model == "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M":
    CONTEXT_SIZE = 8192 * 2 
GPU_LAYERS = 0 
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

    history = []
    if old_history and "messages" in old_history:
        for msg in old_history["messages"]:
            content = msg.get("content", "")
            
            # If main text is empty, try to combine parts
            if not content:
                part1 = msg.get("before_think", "")
                part2 = msg.get("after_think", "")
                content = f"{part1}\n{part2}".strip()

            history.append({
                "role": msg.get("role", "user"),
                "content": content
            })

    history.append({"role": "user", "content": user_message})
    raw_prompt=convert_history_to_prompt(history)
    print("prompt:",raw_prompt)
    # Stream Generation
    stream = llm.create_completion(
        prompt=raw_prompt,
        temperature=0.6,
        max_tokens=None,
        stream=True,
        stop=["User:"]
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
    "content": full_response,       
    "before_think": before_think,
    "after_think": after_think
}

HistoryModel.update_one({
    "username":username,
    "model":model,
    "title":f"title{chat_number}"},
    {"$push":{"messages":user_message}}
)
HistoryModel.update_one(
    {"username":username,
     "model":model,
     "title":f"title{chat_number}"},
     {"$push":{"messages":new_message}}
)
