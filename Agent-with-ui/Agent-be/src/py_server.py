import sys
import gc
import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from py_types import *
import json


# Try importing torch for VRAM clearing, handle if not installed
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from llama_cpp import Llama, GGML_TYPE_Q8_0

# --- CONFIGURATION ---
MODEL_PATH = "/home/harsh/RAG/Agent-with-ui/models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
N_CTX = 100000
HOST = "0.0.0.0"
PORT = 5000

# Global variable to hold the model
llm = None

# --- MEMORY CLEANUP FUNCTION ---
def clean_memory():
    """Forcefully frees VRAM for other models (embeddings)."""
    global llm
    if llm:
        print("🔻 Closing LlamaCPP model...")
        llm.close()
        del llm
        llm = None
    
    # Python Garbage Collection
    gc.collect()
    
    # PyTorch CUDA Cache (Critical for embedding models)
    if HAS_TORCH and torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    print("✨ [SYSTEM] Memory/VRAM Forcefully Cleared.")

# --- LIFECYCLE MANAGEMENT ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model automatically
    load_model()
    yield
    # Shutdown: Clean up
    clean_memory()

app = FastAPI(lifespan=lifespan)

# --- HELPER: LOAD MODEL ---
def load_model():
    global llm
    if llm is not None:
        print("⚠️ Model is already loaded.")
        return

    print(f"🚀 Loading model into VRAM: {MODEL_PATH}")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_gpu_layers=-1,
        flash_attn=True,
        # Using Q4_0 as discussed for stability with high context
        type_k=GGML_TYPE_Q8_0, 
        type_v=GGML_TYPE_Q8_0,
        n_batch=512,
        verbose=False
    )
    print("✅ Model loaded and ready!")

# --- EXISTING HELPERS ---
def convert_history_to_prompt(history: List[Message]) -> str:
    prompt = ""
    for msg in history:
        if msg.role == "system":
            prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
        elif msg.role == "user":
            prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        elif msg.role == "assistant" or msg.role == "model":
            # Prefer 'after_think' if it exists (the actual answer), otherwise content
            content = msg.after_think if msg.after_think else msg.content
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt

def parse_deepseek_response(raw_text: str):
    if "</think>" in raw_text:
        parts = raw_text.split("</think>")
        thought_process = parts[0].replace("<think>", "").strip()
        final_answer = parts[1].strip()
    else:
        thought_process = ""
        final_answer = raw_text.strip()
    return thought_process, final_answer

# --- NEW ROUTES ---

@app.post("/close-model")
async def close_model_route():
    """Free up VRAM so you can load your embedding model."""
    clean_memory()
    return {"status": "success", "message": "Model closed. VRAM cleared."}

@app.post("/open-model")
async def open_model_route():
    """Reload the LLM when you are done with embeddings."""
    load_model()
    return {"status": "success", "message": "Model reloaded."}

# --- GENERATE ROUTE (Updated with Safety Check) ---
@app.post("/generate-model")
async def generate_text(request:GenerateRequest):
    global llm
    
    # 🛑 Safety Check
    if llm is None:
        return{
            "valid":False
        }
    state=request.working_memory
    json_state=json.dumps(state)
    prompt = convert_history_to_prompt(request)
    
    print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

    # Stream to stdout for debugging
    stream = llm(
        prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stop=["<|im_end|>"],
        stream=True
    )

    full_text = ""
    for output in stream:
        token = output['choices'][0]['text']
        sys.stdout.write(token)
        sys.stdout.flush()
        full_text += token

    print("\n------------------------------------------------\n")
    
    thought, answer = parse_deepseek_response(full_text)
    
    return {
        "valid":True,
        "full_response": full_text,
        "before_think": thought,
        "after_think": answer
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)