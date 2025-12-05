import sys
import os
import re
import gc
import json
import subprocess
import pickle
import torch
import numpy as np
import faiss
from llama_cpp import Llama

# ==============================
# CONFIGURATION
# ==============================
CONTEXT_DIR = "context"
STORAGE_DIR = "rag_storage"

# --- MODELS ---
# Ensure these paths are correct for your system
QUERY_MODEL_PATH = "../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
GENERATION_MODEL_PATH="../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"
EMBED_MODEL_PATH = "../models/gte-Qwen2-1.5B-instruct-f16.gguf"

# --- TUNING ---
# Unified Context Size for DeepSeek (Used for both Query Gen and RAG)
# Lower this to 4096 if you still get crashes. Raise to 24576 if you have 24GB+ VRAM.
GEN_MODEL_CTX = 8192*3

# RAG specific settings
CHUNK_SIZE = 512
OVERLAP = 50
TOP_K_RETRIEVAL = 5

os.makedirs(CONTEXT_DIR, exist_ok=True)
os.makedirs(STORAGE_DIR, exist_ok=True)

class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'

# ==============================
# HELPER: MEMORY CLEANER
# ==============================
def clean_memory(model_obj=None):
    """Aggressively clears VRAM to prevent crashes between steps."""
    if model_obj:
        del model_obj
    gc.collect()
    torch.cuda.empty_cache()

# ==============================
# PART 1: QUERY GENERATION
# ==============================
def generate_search_queries(user_input):
    print(f"{Colors.SYSTEM}--- Generating Search Queries (DeepSeek) ---{Colors.RESET}")
    
    # We use a smaller context for this step if possible to save time, 
    # but using the unified global setting is safer for code simplicity.
    try:
        llm = Llama(
            model_path=QUERY_MODEL_PATH,
            n_gpu_layers=-1,      # -1 = Use all GPU layers
            n_ctx=GEN_MODEL_CTX,  # Unified context size
            verbose=False,
            chat_format="chatml"
        )
    except Exception as e:
        print(f"{Colors.SYSTEM}[Error] Could not load model: {e}{Colors.RESET}")
        return [user_input]

    # Preserve original prompt structure
    history = []

    prompt_for_queries ="""You are an intelligent AI agent that cannot use your own internal knowledge.
You may ONLY answer based on SEARCH_RESULTS.

Your goal is to generate Google-style keyword search queries.
You must assume you know NOTHING about the people, brands, or events mentioned.

You MUST obey the "Search Architecture" below to ensure complete context:

------------------------------------------------------------
SEARCH ARCHITECTURE (The 3-Step Process)
------------------------------------------------------------

For any USER_QUERY, you must generate queries covering these three layers:

LAYER 1: Entity Definition (MANDATORY)
Identify EVERY proper noun (Person, Brand, Channel, Event, Meme, Place).
For EACH entity, generate a broad background query.
- Format: "who is [Entity Name]", "[Entity Name] wiki", or "[Entity Name] profile"
- Example: "who is Harkirat Singh", "Samay Raina biography"

LAYER 2: Entity Correlation (Intersection)
Generate queries that combine the entities to find their relationship.
- Format: "[Entity A] [Entity B] relation", "[Entity A] [Entity B] collab", "[Entity A] [Entity B] controversy"
- Example: "Harkirat Singh Samay Raina stream", "Harkirat Singh Samay Raina podcast"

------------------------------------------------------------
RULE 1 — KEYWORDS ONLY (Strict Syntax)
------------------------------------------------------------
Your queries must look like something a user types into a search bar.

STRICT NEGATIVE CONSTRAINTS:
- DO NOT use full sentences.
- DO NOT use question marks.

BAD: "Did Harkirat and Samay meet on stream?"
GOOD: "Harkirat Singh Samay Raina stream recording"

BAD: "Who is the creator Coffeezilla?"
GOOD: "Coffeezilla youtuber wiki"

------------------------------------------------------------
RULE 2 — NO REDUNDANCY
------------------------------------------------------------
Do not generate two queries that search for the exact same thing.
However, defining an entity ("who is X") and finding the event ("X Y event") are NOT redundant. They are distinct needs.

------------------------------------------------------------
QUESTIONING MODE OUTPUT FORMAT (STRICT)
------------------------------------------------------------

You MUST output ONLY the following JSON:

{
  "questions": [
    "string_query_1",
    "string_query_2",
    "string_query_3"
  ]
}

NO explanations.
NO reasoning.
NO commentary.

============================================================
CURRENT USER QUERY
============================================================
USER_QUERY:"
"""
    prompt_for_queries+=user_input

    history.append({"role": "user", "content": prompt_for_queries})

    print(f"{Colors.SYSTEM}[Debug] Processing request...{Colors.RESET}")
    
    queries = [user_input] # Default fallback
    try:
        response = llm.create_chat_completion(
            messages=history,
            temperature=0.6,
            stream=False 
        )
        
        content = response['choices'][0]['message']['content']
        
        # Remove <think> tags
        clean_content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        # Extract JSON
        match = re.search(r'\[.*\]', clean_content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list) and len(parsed) > 0:
                queries = parsed
            
    except Exception as e:
        print(f"[Warn] JSON parsing failed, using raw query. Error: {e}")

    print(f"{Colors.SYSTEM}Generated Queries: {queries}{Colors.RESET}")

    # CRITICAL: Free memory before the next step loads the embedding model
    clean_memory(llm)
    
    return queries

# ==============================
# PART 2: SCRAPER
# ==============================
def get_next_context_filename():
    base_name = "context"
    ext = ".txt"
    file_path = os.path.join(CONTEXT_DIR, f"{base_name}{ext}")
    if not os.path.exists(file_path):
        return file_path
        
    counter = 2
    while True:
        file_path = os.path.join(CONTEXT_DIR, f"{base_name}{counter}{ext}")
        if not os.path.exists(file_path):
            return file_path
        counter += 1

def run_scraper(filename, queries):
    print(f"{Colors.SYSTEM}--- Running Web Scraper ---{Colors.RESET}")
    # Calls the updated scrap_playwrith1.js
    cmd = ["node", "scrap_playwrith1.js", filename] + queries
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"{Colors.SYSTEM}[Error] Scraper execution failed: {e}{Colors.RESET}")

# ==============================
# PART 3: RAG INGESTION
# ==============================
class GGUFEmbedder:
    def __init__(self, model_path):
        # Embedder usually needs less context, 8192 is standard for GTE-Qwen
        self.llm = Llama(
            model_path=model_path,
            embedding=True,
            n_gpu_layers=-1,
            n_ctx=8192*3, 
            verbose=False
        )

    def encode(self, texts):
        embeddings = []
        for text in texts:
            try:
                response = self.llm.create_embedding(text)
                if isinstance(response, dict) and "data" in response:
                    vector = response["data"][0]["embedding"]
                else:
                    vector = response
                # Handle list-of-lists edge case
                if isinstance(vector[0], list):  
                    vector = np.mean(vector, axis=0).tolist()
                embeddings.append(vector)
            except:
                embeddings.append([0.0] * 1536) # Zero vector fallback
        return np.array(embeddings, dtype="float32")

def ingest_data(input_file):
    print("--- 1. STARTING INGESTION ---")
    
    if not os.path.exists(input_file):
        return False
        
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
        
    # Parse "--- SOURCE: url ---" format
    pattern = r"--- SOURCE:\s+(.*?)\s+---\n"
    parts = re.split(pattern, raw_text, flags=re.DOTALL)
    
    documents = []
    start_idx = 1 if len(parts) > 1 else 0
    for i in range(start_idx, len(parts), 2):
        if i + 1 < len(parts):
            documents.append({"source": parts[i].strip(), "content": parts[i+1].strip()})

    if not documents:
        print("[Warn] No documents found in file.")
        return False

    # Chunking
    all_chunks = []
    for doc in documents:
        words = doc['content'].split()
        start = 0
        while start < len(words):
            end = start + CHUNK_SIZE
            chunk_text = " ".join(words[start:end])
            all_chunks.append({"text": chunk_text, "source": doc['source']})
            start += (CHUNK_SIZE - OVERLAP)
    
    texts = [c['text'] for c in all_chunks]
    
    # Load Embedder
    embedder = GGUFEmbedder(EMBED_MODEL_PATH)
    embeddings = embedder.encode(texts)
    
    # Clean Embedder
    clean_memory(embedder.llm)
    del embedder

    # Save Index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    faiss.write_index(index, os.path.join(STORAGE_DIR, "index.faiss"))
    with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "wb") as f:
        pickle.dump(all_chunks, f)
        
    return True

# ==============================
# PART 4: RAG GENERATION
# ==============================
def retrieve_and_generate(query):
    print("--- 2. RETRIEVAL PHASE ---")
    
    if not os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("[Error] No index found.")
        return

    # Load Embedder (Briefly)
    embedder = GGUFEmbedder(EMBED_MODEL_PATH)
    task_instruction = f"Query: {query}"
    query_vec = embedder.encode([task_instruction])
    
    clean_memory(embedder.llm)
    del embedder

    # Search Index
    index = faiss.read_index(os.path.join(STORAGE_DIR, "index.faiss"))
    with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "rb") as f:
        meta = pickle.load(f)
        
    distances, indices = index.search(query_vec, k=TOP_K_RETRIEVAL)
    context_chunks = [meta[i] for i in indices[0] if i < len(meta)]

    print("--- 3. GENERATION PHASE ---")
    
    context_str = ""
    for item in context_chunks:
        context_str += f"[Source: {item['source']}]\n{item['text']}\n\n"

    print(f"    [LOAD] Loading Generation Model ({GEN_MODEL_CTX} ctx)...")
    
    try:
        llm = Llama(
            model_path=GENERATION_MODEL_PATH,
            n_gpu_layers=-1,
            n_ctx=14000, # Unified Context
            n_batch=512,
            verbose=False
        )
    except Exception as e:
        print(f"[Critical Error] Failed to load Model: {e}")
        return

    # Original Prompt
    prompt = f"""<|start_header_id|>system<|end_header_id|>

You are a strictly grounded assistant.

RULES:
1. You MUST answer using ONLY the provided Context.
2. If the answer is NOT in the Context, you must output EXACTLY this phrase and nothing else:
   "I don’t have enough information in the context to answer this question."
3. DO NOT add apologies, explanations, or "useful info" from your own knowledge. 
4. DO NOT say "However..." or "But...".
5. If the context is empty or irrelevant, just say the refusal phrase and STOP.

--- CONTEXT START ---
{context_str}
--- CONTEXT END ---
<|eot_id|><|start_header_id|>user<|end_header_id|>

{query}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
"""
    print(f"prompt:{prompt}")
    print("======================================================")

    print(f"\n{Colors.AI}{Colors.BOLD}Llama:{Colors.RESET}")
    
    stream = llm(
        prompt, 
        max_tokens=None, 
        stop=["<|im_end|>"], 
        stream=True, 
        temperature=0.6
    )
    
    for output in stream:
        token = output['choices'][0]['text']
        print(token, end='', flush=True)
    print("\n")

    clean_memory(llm)

# ==============================
# MAIN
# ==============================
def main():
    print(f"{Colors.USER}{Colors.BOLD}Enter your research query: {Colors.RESET}", end="")
    user_query = input().strip()
    if not user_query: return

    # 1. Generate Queries
    search_queries = generate_search_queries(user_query)
    
    # 2. Scrape
    context_file = get_next_context_filename()
    print(f"{Colors.SYSTEM}Writing context to: {context_file}{Colors.RESET}")
    run_scraper(context_file, search_queries)

    # 3. RAG Pipeline
    if os.path.exists(context_file):
        # We check if file has size > 0
        if os.path.getsize(context_file) > 0:
            if ingest_data(context_file):
                retrieve_and_generate(user_query)
            else:
                print("Ingestion failed.")
        else:
            print("[Error] Scraper file is empty. Check internet or selectors.")
    else:
        print("[Error] Context file was not created.")

if __name__ == "__main__":
    clean_memory()
    main()