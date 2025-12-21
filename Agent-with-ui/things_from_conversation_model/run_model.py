from llama_cpp import Llama
import json, argparse, sys
from pymongo import MongoClient
from dotenv import load_dotenv
from model import run_model
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
    # Fetch History
    old_history = HistoryModel.find_one({
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
    print(f"[run_model.py] Loading model {model}...")
    return run_model(MODEL_PATH,user_message)

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
