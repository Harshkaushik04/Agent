import os
import re
import gc
import pickle
import torch
import numpy as np
import faiss
from llama_cpp import Llama

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "context/context8.txt"
STORAGE_DIR = "rag_storage"

# --- 1. EMBEDDING MODEL (LOCAL) ---
EMBED_MODEL_PATH = "../models/gte-Qwen2-1.5B-instruct-f16.gguf"

# --- 2. GENERATION MODEL (LOCAL DEEPSEEK) ---
# Ensure this file exists inside your 'models/' folder
GEN_MODEL_PATH = "../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

# Settings
MAX_CONTEXT = 8192*3  # Qwen models handle large context well
CHUNK_SIZE = 512    # Increased slightly for better context retention
OVERLAP = 50

os.makedirs(STORAGE_DIR, exist_ok=True)

# ==========================================
# HELPER: MEMORY CLEANER
# ==========================================
def clean_memory(model_obj=None):
    if model_obj:
        del model_obj
    gc.collect()
    torch.cuda.empty_cache()
    if torch.cuda.is_available():
        free = torch.cuda.mem_get_info()[0] / 1024**3
        print(f"    [SYSTEM] VRAM Free: {free:.2f} GB")

# ==========================================
# HELPER: GGUF EMBEDDER
# ==========================================
class GGUFEmbedder:
    def __init__(self, model_path):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"CRITICAL: Embedding model not found at '{model_path}'.")

        print(f"    [LOAD] Using Local Embedding Model: {model_path}...")
        
        self.llm = Llama(
            model_path=model_path,
            embedding=True,
            n_gpu_layers=-1,
            n_ctx=8192, 
            verbose=False
        )

    def encode(self, texts, show_progress_bar=False):
        embeddings = []
        total = len(texts)

        for i, text in enumerate(texts):
            if show_progress_bar and i % 5 == 0:
                print(f"    Embedding {i}/{total}...", end='\r')

            try:
                response = self.llm.create_embedding(text)
                
                # Handle varying response formats from llama-cpp-python versions
                if isinstance(response, dict) and "data" in response:
                    vector = response["data"][0]["embedding"]
                else:
                    vector = response

                # Fix: If vector is list-of-lists (rare edge case), flatten it
                if isinstance(vector[0], list):  
                    vector = np.mean(vector, axis=0).tolist()

                embeddings.append(vector)
            except Exception as e:
                print(f"\n[WARN] Failed to embed chunk {i}: {e}")
                # Append zero vector to maintain shape consistency
                embeddings.append([0.0] * 1536) # Assuming 1536 dim, adjust if needed

        if show_progress_bar:
            print(f"    Embedding {total}/{total} Done.")

        return np.array(embeddings, dtype="float32")


# ==========================================
# PART 1: INGESTION
# ==========================================
def parse_documents(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] Input file not found: {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    pattern = r"--- SOURCE:\s+(.*?)\s+---\n"
    parts = re.split(pattern, raw_text, flags=re.DOTALL)
    documents = []
    start_idx = 1 if len(parts) > 1 else 0
    for i in range(start_idx, len(parts), 2):
        if i + 1 < len(parts):
            documents.append({"source": parts[i].strip(), "content": parts[i+1].strip()})
    return documents

def chunk_document(doc):
    words = doc['content'].split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_text = " ".join(words[start:end])
        chunks.append({"text": chunk_text, "source": doc['source']})
        start += (CHUNK_SIZE - OVERLAP)
    return chunks

def ingest_data():
    if os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("Index found. Skipping ingestion.")
        return

    print("--- 1. STARTING INGESTION ---")
    docs = parse_documents(INPUT_FILE)
    if not docs:
        print("[ERROR] No documents found to ingest.")
        return

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    
    texts = [c['text'] for c in all_chunks]
    print(f"    Processed {len(texts)} chunks.")

    # LOAD EMBEDDER
    embedder = GGUFEmbedder(EMBED_MODEL_PATH)
    
    # Run
    embeddings = embedder.encode(texts, show_progress_bar=True)
    
    # UNLOAD
    print("    [OFFLOAD] Cleaning Embedder...")
    clean_memory(embedder.llm)
    del embedder

    # Save
    if embeddings.size > 0:
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        faiss.write_index(index, os.path.join(STORAGE_DIR, "index.faiss"))
        with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "wb") as f:
            pickle.dump(all_chunks, f)
        print("--- INGESTION COMPLETE ---\n")
    else:
        print("[ERROR] No valid embeddings generated.")

# ==========================================
# PART 2: RETRIEVAL
# ==========================================
def retrieve(query, top_k=5):
    print("--- 2. RETRIEVAL PHASE ---")
    
    if not os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("[ERROR] No index found. Run ingestion first.")
        return []

    embedder = GGUFEmbedder(EMBED_MODEL_PATH)
    
    # Task instruction helps optimization for some embedding models
    task_instruction = f"Query: {query}" 
    query_vec = embedder.encode([task_instruction])
    
    print("    [OFFLOAD] Cleaning Embedder...")
    clean_memory(embedder.llm)
    del embedder

    index = faiss.read_index(os.path.join(STORAGE_DIR, "index.faiss"))
    with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "rb") as f:
        meta = pickle.load(f)
        
    distances, indices = index.search(query_vec, k=top_k)
    return [meta[i] for i in indices[0] if i < len(meta)]

# ==========================================
# PART 3: GENERATION (LOCAL DEEPSEEK)
# ==========================================
def generate(query, context_chunks):
    print("--- 3. GENERATION PHASE (DeepSeek R1 Local) ---")
    
    if not os.path.exists(GEN_MODEL_PATH):
        print(f"[ERROR] DeepSeek model not found at: {GEN_MODEL_PATH}")
        return

    context_str = ""
    for item in context_chunks:
        context_str += f"[Source: {item['source']}]\n{item['text']}\n\n"

    print(f"    [LOAD] Loading {GEN_MODEL_PATH}...")
    
    llm = Llama(
        model_path=GEN_MODEL_PATH,
        n_gpu_layers=-1,
        n_ctx=MAX_CONTEXT,
        n_batch=512,
        verbose=False
    )

    # UPDATED PROMPT: DeepSeek/Qwen uses ChatML format (<|im_start|>)
    # The previous Llama-3 format (<|start_header_id|>) will cause issues.
    prompt = f"""<|im_start|>system
You are DeepSeek-R1. Use the Context below to answer the user.
Only answer using the provided context. If the context does not contain enough information, say:
"I don’t have enough information in the context to answer this question.also cite the source of information(website name)(if given) you are citing in the end"

Context:
{context_str}<|im_end|>
<|im_start|>user
{query}<|im_end|>
<|im_start|>assistant
"""

    print(f"\nUser: {query}")
    print("\n--- AGENT THINKING ---")
    
    # Qwen/DeepSeek uses <|im_end|> to stop, not <|eot_id|>
    stream = llm(
        prompt, 
        max_tokens=None, 
        stop=["<|im_end|>"], 
        stream=True, 
        temperature=0.6
    )
    
    # Simple logic to separate thinking trace if present
    # (DeepSeek R1 outputs <think> content </think>)
    buffer = ""
    for output in stream:
        token = output['choices'][0]['text']
        print(token, end='', flush=True)

    print("\n")

    print("    [OFFLOAD] Cleaning LLM...")
    clean_memory(llm)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    clean_memory()
    ingest_data()
    
    user_query = "best language for beginner which wants to do gamedev later on"
    retrieved_data = retrieve(user_query, top_k=8)
    
    if retrieved_data:
        generate(user_query, retrieved_data)
    else:
        print("[ERROR] No context retrieved. Skipping generation.")
    
    print("--- DONE ---")