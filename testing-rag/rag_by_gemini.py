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
STORAGE_DIR = "advanced_rag_storage"

# Models
EMBED_MODEL_PATH = "../models/gte-Qwen2-1.5B-instruct-f16.gguf"
GEN_MODEL_PATH = "../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"

# Advanced Settings
CHUNK_SIZE_SMALL = 256  # Small chunks for precise searching
CHUNK_SIZE_LARGE = 512 # Parent chunks for context reading
OVERLAP = 50
TOP_K_RETRIEVAL = 9    # Fetch more initially
TOP_K_RERANK = 3       # Rerank down to top 5

os.makedirs(STORAGE_DIR, exist_ok=True)

# ==========================================
# SYSTEM: MEMORY MANAGEMENT
# ==========================================
def clean_memory(model_obj=None):
    if model_obj:
        del model_obj
    gc.collect()
    torch.cuda.empty_cache()

# ==========================================
# COMPONENT 1: GGUF WRAPPERS
# ==========================================
class LocalLLM:
    """Handles Generation and Reranking/Translation tasks"""
    def __init__(self, model_path, context_size=8192):
        print(f"    [LOAD] Loading LLM: {model_path}...")
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,
            n_ctx=context_size,
            verbose=False
        )

    def generate(self, prompt, stop_tokens=["<|im_end|>"]):
        output = self.llm(prompt, max_tokens=None, stop=stop_tokens, temperature=0.6)
        return output['choices'][0]['text'].strip()

    def stream_generate(self, prompt, stop_tokens=["<|im_end|>"]):
        return self.llm(prompt, max_tokens=None, stop=stop_tokens, stream=True, temperature=0.6)

class LocalEmbedder:
    def __init__(self, model_path):
        print(f"    [LOAD] Loading Embedder: {model_path}...")
        self.llm = Llama(
            model_path=model_path, 
            embedding=True, 
            n_gpu_layers=-1, 
            verbose=False
        )

    def encode(self, texts):
        embeddings = []
        expected_dim = None # Store the dimension of the first successful chunk

        for i, text in enumerate(texts):
            try:
                resp = self.llm.create_embedding(text)
                
                # 1. Normalize Response Format (Dict vs List)
                if isinstance(resp, dict):
                    vec = resp["data"][0]["embedding"]
                else:
                    vec = resp
                
                # 2. Fix List-of-Lists (Common in some llama-cpp versions)
                # If we get [[0.1, 0.2...]], flatten it to [0.1, 0.2...]
                if isinstance(vec, list) and len(vec) > 0 and isinstance(vec[0], list):
                    vec = vec[0]

                # 3. Dynamic Dimension Detection
                if expected_dim is None:
                    expected_dim = len(vec)
                    print(f"    [SYSTEM] Auto-detected Embedding Dimension: {expected_dim}")

                embeddings.append(vec)

            except Exception as e:
                # 4. Safe Fallback using detected dimension
                current_dim = expected_dim if expected_dim else 1536 # Default only if very first fails
                # print(f"[WARN] Chunk {i} failed. Appending zero vector of size {current_dim}.")
                embeddings.append([0.0] * current_dim)

        return np.array(embeddings, dtype="float32")

# ==========================================
# COMPONENT 2: HIERARCHICAL INGESTION
# ==========================================
def ingest_hierarchical():
    """
    Implements Parent Document Retrieval logic.
    We split text into LARGE chunks (Parents) to store the content,
    and SMALL chunks (Children) to generate embeddings for search.
    """
    if os.path.exists(os.path.join(STORAGE_DIR, "index.faiss")):
        print("Index found. Skipping ingestion.")
        return

    print("--- 1. STARTING HIERARCHICAL INGESTION ---")
    
    # 1. Read Raw Text
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        full_text = f.read()

    # 2. Create Parent Chunks (Large context windows)
    words = full_text.split()
    parent_chunks = []
    child_chunks = [] # These will be embedded
    
    p_id = 0
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE_LARGE
        parent_text = " ".join(words[start:end])
        parent_chunks.append({
            "id": p_id,
            "text": parent_text,
            "source": "Main Doc"
        })
        
        # 3. Create Child Chunks (derived from this specific parent)
        # We index the child, but the metadata points to the Parent ID
        c_start = 0
        p_words = parent_text.split()
        while c_start < len(p_words):
            c_end = c_start + CHUNK_SIZE_SMALL
            child_text = " ".join(p_words[c_start:c_end])
            child_chunks.append({
                "text": child_text,
                "parent_id": p_id # LINK TO PARENT
            })
            c_start += (CHUNK_SIZE_SMALL - OVERLAP)
            
        start += (CHUNK_SIZE_LARGE - OVERLAP)
        p_id += 1

    print(f"    Generated {len(parent_chunks)} Parents and {len(child_chunks)} Children.")

    # 4. Embed ONLY Children
    embedder = LocalEmbedder(EMBED_MODEL_PATH)
    texts_to_embed = [c['text'] for c in child_chunks]
    embeddings = embedder.encode(texts_to_embed)
    
    clean_memory(embedder.llm)

    # 5. Save
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    faiss.write_index(index, os.path.join(STORAGE_DIR, "index.faiss"))
    
    # Save Metadata: We need both Child mappings and Parent data
    with open(os.path.join(STORAGE_DIR, "metadata.pkl"), "wb") as f:
        pickle.dump({"parents": parent_chunks, "children": child_chunks}, f)
    
    print("--- INGESTION COMPLETE ---")

# ==========================================
# COMPONENT 3: PIPELINE STAGES (Decoupled)
# ==========================================

def stage_1_hyde(query, model_path):
    print("\n--- STAGE 1: HyDE TRANSLATION ---")
    clean_memory() # Ensure clean slate
    
    # 1. Load LLM
    llm = LocalLLM(model_path)
    
    # 2. Run HyDE
    print(f"    [HyDE] Generating hypothetical answer...")
    prompt = f"""<|im_start|>system
You are a helpful assistant. Write a short, hypothetical paragraph that answers the user's question. 
Do not include true facts, just write what a relevant document might look like.
<|im_end|>
<|im_start|>user
{query}
<|im_end|>
<|im_start|>assistant
"""
    hypothetical_doc = llm.generate(prompt)
    print(f"    [HyDE] Generated: {hypothetical_doc[:100]}...")
    
    # 3. Unload LLM
    print("    [SYSTEM] Unloading LLM to free VRAM...")
    del llm
    clean_memory()
    
    return hypothetical_doc

def stage_2_retrieval(query, hyde_doc, model_path, storage_dir):
    print("\n--- STAGE 2: VECTOR RETRIEVAL ---")
    clean_memory()
    
    # 1. Load Embedder
    embedder = LocalEmbedder(model_path)
    
    # 2. Load Index
    index = faiss.read_index(os.path.join(storage_dir, "index.faiss"))
    with open(os.path.join(storage_dir, "metadata.pkl"), "rb") as f:
        metadata = pickle.load(f)
    
    # 3. Search
    search_query = f"{query} {hyde_doc}"
    query_vec = embedder.encode([search_query])
    distances, indices = index.search(query_vec, k=TOP_K_RETRIEVAL)
    
    # 4. Map Children -> Parents
    parent_ids = set()
    retrieved_parents = []
    
    for idx in indices[0]:
        if idx < len(metadata['children']):
            p_id = metadata['children'][idx]['parent_id']
            if p_id not in parent_ids:
                # Find parent by ID
                parent = next((p for p in metadata['parents'] if p['id'] == p_id), None)
                if parent:
                    retrieved_parents.append(parent)
                    parent_ids.add(p_id)
    
    print(f"    [RETRIEVAL] Found {len(retrieved_parents)} unique parent docs.")
    
    # 5. Unload Embedder
    print("    [SYSTEM] Unloading Embedder to free VRAM...")
    del embedder
    clean_memory()
    
    return retrieved_parents

def stage_3_rerank_and_gen(query, retrieved_docs, model_path):
    print("\n--- STAGE 3: RERANKING & GENERATION ---")
    clean_memory()
    
    # 1. Load LLM (Again)
    llm = LocalLLM(model_path)
    
    # --- RERANKING ---
    print(f"    [RERANK] Scoring {len(retrieved_docs)} documents...")
    scored_docs = []
    for doc in retrieved_docs:
        prompt = f"""<|im_start|>system
Rate the relevance of the text to the query on a scale of 0 to 10. Output ONLY the number.
<|im_end|>
<|im_start|>user
Query: {query}
Text: {doc['text'][:500]}...
<|im_end|>
<|im_start|>assistant
"""
        try:
            score_text = llm.generate(prompt)
            # Extract number
            match = re.search(r"\d+", score_text)
            score = float(match.group()) if match else 0
        except:
            score = 0
        scored_docs.append((score, doc))

    # Sort and slice
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    top_docs = [doc for score, doc in scored_docs[:TOP_K_RERANK]]
    
    # --- GENERATION ---
    print("\n--- FINAL GENERATION ---")
    context_str = "\n\n".join([f"[Doc ID: {d['id']}]\n{d['text']}" for d in top_docs])
    
    prompt = f"""<|im_start|>system
You are DeepSeek-R1. Use the Context below to answer the user.
<|im_end|>
<|im_start|>user
Context:
{context_str}

Question: {query}
<|im_end|>
<|im_start|>assistant
"""
    stream = llm.stream_generate(prompt)
    for output in stream:
        print(output['choices'][0]['text'], end='', flush=True)
    print("\n")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # 1. Ingestion (Only runs if index is missing)
    ingest_hierarchical()
    
    user_query = "What is the best language for game dev?"
    
    # 2. Run Pipeline Stages strictly sequentially
    
    # Step A: HyDE (Uses LLM)
    hyde_result = stage_1_hyde(user_query, GEN_MODEL_PATH)
    
    # Step B: Retrieve (Uses Embedder)
    raw_docs = stage_2_retrieval(user_query, hyde_result, EMBED_MODEL_PATH, STORAGE_DIR)
    
    # Step C: Rerank & Gen (Uses LLM)
    if raw_docs:
        stage_3_rerank_and_gen(user_query, raw_docs, GEN_MODEL_PATH)
    else:
        print("[ERROR] No documents retrieved.")
    
    print("--- DONE ---")