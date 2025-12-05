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
GEN_MODEL_PATH = "../models/Llama-3-8B-Instruct-GGUF-Q4_K_M.gguf"

# Settings
MAX_CONTEXT = 14000 # Qwen models handle large context well
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

        print(f"    [EMBEDDER] Loading Local Embedding Model: {model_path}...")
        
        self.llm = Llama(
            model_path=model_path,
            embedding=True,
            n_gpu_layers=-1,
            n_ctx=8192, 
            verbose=False
        )
        print("    [EMBEDDER] Model loaded.\n")

    def encode(self, texts, show_progress_bar=False):
        embeddings = []
        total = len(texts)
        print(f"    [EMBEDDER] Encoding {total} text chunks...")

        for i, text in enumerate(texts):
            if show_progress_bar and i % 5 == 0:
                print(f"    Embedding {i}/{total}...", end='\r')

            # debug: show input snippet
            print(f"\n    [EMBEDDER] --- CHUNK {i} INPUT (first 200 chars) ---")
            print("    " + text.replace("\n", " ") + ("..." if len(text) > 200 else ""))
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

                print(f"    [EMBEDDER] Output vector length: {len(vector)}")
                embeddings.append(vector)
            except Exception as e:
                print(f"\n[WARN] Failed to embed chunk {i}: {e}")
                # Append zero vector to maintain shape consistency
                embeddings.append([0.0] * 1536) # Assuming 1536 dim, adjust if needed

        if show_progress_bar:
            print(f"    Embedding {total}/{total} Done.")

        emb_array = np.array(embeddings, dtype="float32")
        print(f"\n    [EMBEDDER] Final embeddings shape: {emb_array.shape}\n")
        return emb_array


# ==========================================
# PART 1: INGESTION
# ==========================================
def parse_documents(file_path):
    print(f"[INGEST] Parsing documents from: {file_path}")
    if not os.path.exists(file_path):
        print(f"[ERROR] Input file not found: {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # debug raw length
    print(f"[INGEST] Raw text length: {len(raw_text)} chars")

    pattern = r"--- SOURCE:\s+(.*?)\s+---\n"
    parts = re.split(pattern, raw_text, flags=re.DOTALL)
    documents = []
    start_idx = 1 if len(parts) > 1 else 0
    for i in range(start_idx, len(parts), 2):
        if i + 1 < len(parts):
            source = parts[i].strip()
            content = parts[i+1].strip()
            print(f"\n[INGEST] Found document from SOURCE: {source}")
            print("[INGEST] Content preview (first 300 chars):")
            print(content.replace("\n", " ") + ("..." if len(content) > 300 else ""))
            documents.append({"source": source, "content": content})
    print(f"\n[INGEST] Total documents parsed: {len(documents)}\n")
    return documents

def chunk_document(doc):
    print(f"[CHUNK] Chunking document from source: {doc['source']}")
    words = doc['content'].split()
    chunks = []
    start = 0
    idx = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_text = " ".join(words[start:end])
        print(f"    [CHUNK] Chunk {idx}: words {start}–{end}, length {len(chunk_text)} chars")
        chunks.append({"text": chunk_text, "source": doc['source']})
        start += (CHUNK_SIZE - OVERLAP)
        idx += 1
    print(f"[CHUNK] Total chunks from this document: {len(chunks)}\n")
    return chunks

def ingest_data():
    if os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("[INGEST] Index found. Skipping ingestion.\n")
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
    print(f"[INGEST] Total chunks across all docs: {len(texts)}")

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
        print(f"[INGEST] Embedding dimension: {dimension}")
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        faiss.write_index(index, os.path.join(STORAGE_DIR, "index.faiss"))
        with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "wb") as f:
            pickle.dump(all_chunks, f)
        print("[INGEST] Saved FAISS index and metadata.\n")
        print("--- INGESTION COMPLETE ---\n")
    else:
        print("[ERROR] No valid embeddings generated.")

# ==========================================
# PART 2: RETRIEVAL
# ==========================================
def retrieve(query, top_k=5):
    print("--- 2. RETRIEVAL PHASE ---")
    print(f"[RETRIEVE] User query: {query}")
    
    if not os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("[ERROR] No index found. Run ingestion first.")
        return []

    embedder = GGUFEmbedder(EMBED_MODEL_PATH)
    
    # Task instruction helps optimization for some embedding models
    task_instruction = f"Query: {query}" 
    print(f"[RETRIEVE] Embedding query as: {task_instruction}")
    query_vec = embedder.encode([task_instruction])
    print(f"[RETRIEVE] Query embedding shape: {query_vec.shape}")
    
    print("    [OFFLOAD] Cleaning Embedder after query encoding...")
    clean_memory(embedder.llm)
    del embedder

    index = faiss.read_index(os.path.join(STORAGE_DIR, "index.faiss"))
    with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "rb") as f:
        meta = pickle.load(f)
        
    distances, indices = index.search(query_vec, k=top_k)
    print(f"[RETRIEVE] FAISS distances: {distances}")
    print(f"[RETRIEVE] FAISS indices: {indices}")

    results = []
    for rank, i in enumerate(indices[0]):
        if i < len(meta):
            item = meta[i]
            print(f"\n[RETRIEVE] Result #{rank+1} (index {i}) from source: {item['source']}")
            print("           Text preview (first 300 chars):")
            print("           " + item['text'].replace("\n", " ") + ("..." if len(item['text']) > 300 else ""))
            results.append(item)
        else:
            print(f"[WARN] Retrieved index {i} is out of metadata range {len(meta)}")
    print("")
    return results

# ==========================================
# PART 3: GENERATION (LOCAL DEEPSEEK)
# ==========================================
def generate(query, context_chunks):
    print("--- 3. GENERATION PHASE (DeepSeek R1 Local) ---")
    
    if not os.path.exists(GEN_MODEL_PATH):
        print(f"[ERROR] DeepSeek model not found at: {GEN_MODEL_PATH}")
        return

    print(f"[GENERATE] Number of retrieved context chunks: {len(context_chunks)}")
    context_str = ""
    for idx, item in enumerate(context_chunks):
        context_str += f"[Source: {item['source']}]\n{item['text']}\n\n"
        print(f"\n[GENERATE] Context chunk {idx} from source: {item['source']}")
        print("           Text preview (first 300 chars):")
        print("           " + item['text'].replace("\n", " ") + ("..." if len(item['text']) > 300 else ""))

    print("\n[GENERATE] Final concatenated context length:", len(context_str), "chars")

    print(f"    [LOAD] Loading {GEN_MODEL_PATH}...")
    
    llm = Llama(
        model_path=GEN_MODEL_PATH,
        n_gpu_layers=-1,
        n_ctx=MAX_CONTEXT,
        n_batch=512,
        verbose=False
    )

    # REMOVED <|begin_of_text|> from the start
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

    print("\n[GENERATE] Final prompt sent to LLM (first 1000 chars):")
    print(prompt + ("..." if len(prompt) > 1000 else ""))

    print(f"\nUser: {query}")
    print("\n--- AGENT THINKING / RAW STREAM ---\n")
    
    # Qwen/DeepSeek uses <|im_end|> to stop, not <|eot_id|>
    stream = llm(
        prompt, 
        max_tokens=None, 
        stop=["<|im_end|>"], 
        stream=True, 
        temperature=0.6
    )
    
    buffer = ""
    for output in stream:
        token = output['choices'][0]['text']
        print(token, end='', flush=True)
        buffer += token

    print("\n\n[GENERATE] Full raw model output captured.\n")

    print("    [OFFLOAD] Cleaning LLM...")
    clean_memory(llm)

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    clean_memory()
    ingest_data()
    
    user_query = "which planet is inhabitable from solar system"
    print(f"[MAIN] User query: {user_query}\n")
    retrieved_data = retrieve(user_query, top_k=5)
    
    if retrieved_data:
        generate(user_query, retrieved_data)
    else:
        print("[ERROR] No context retrieved. Skipping generation.")
    
    print("--- DONE ---")
