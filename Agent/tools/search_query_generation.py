from dotenv import load_dotenv
import os
from llama_cpp import Llama
import re
import json
import torch
import gc
load_dotenv("../.env")
class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'
def clean_memory(model_obj=None):
    """Aggressively clears VRAM to prevent crashes between steps."""
    if model_obj:
        del model_obj
    gc.collect()
    torch.cuda.empty_cache()
# ==============================
# CONFIGURATION
# ==============================
# --- MODELS ---
# Ensure these paths are correct for your system

QUERY_MODEL_PATH = os.getenv("DEEPSEEK_REASONING_MODEL_PATH")
# print(QUERY_MODEL_PATH,f"hi {type(QUERY_MODEL_PATH)}")
GENERATION_MODEL_PATH=os.getenv("LLAMA_INSTRUCT_MODEL_PATH")
EMBED_MODEL_PATH = os.getenv("QWEN_EMBEDDING_MODEL_PATH")

# --- TUNING ---
# Unified Context Size for DeepSeek (Used for both Query Gen and RAG)
# Lower this to 4096 if you still get crashes. Raise to 24576 if you have 24GB+ VRAM.
GEN_MODEL_CTX = 8192*3

# RAG specific settings
CHUNK_SIZE = 512
OVERLAP = 50
TOP_K_RETRIEVAL = 5


load_dotenv("../.env")

def extract_json_from_response(content):
    """
    Robustly extracts JSON from LLM output, handling:
    1. Markdown code blocks (```json ... ```)
    2. Plain JSON text
    3. The specific {"questions": [...]} format
    """
    try:
        # 1. Remove <think> tags if present
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

        # 2. Try to find JSON inside Markdown code blocks first
        code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
        match = re.search(code_block_pattern, content, re.DOTALL)
        
        json_str = ""
        if match:
            json_str = match.group(1)
        else:
            # 3. Fallback: Find the first '{' and last '}'
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                json_str = content[start:end+1]
            else:
                # 4. Emergency Fallback: Look for just the list '[' ... ']'
                start_list = content.find('[')
                end_list = content.rfind(']')
                if start_list != -1 and end_list != -1:
                    json_str = content[start_list:end_list+1]

        # 5. Parse
        if not json_str:
            raise ValueError("No JSON-like syntax found")
            
        parsed = json.loads(json_str)

        # 6. Normalize output (Handle both Dict and List formats)
        if isinstance(parsed, dict) and "questions" in parsed:
            return parsed["questions"]
        elif isinstance(parsed, list):
            return parsed
        else:
            print(f"[Warn] JSON found but unexpected structure: {type(parsed)}")
            return []

    except json.JSONDecodeError:
        print(f"[Warn] JSON decoding failed. Content was: {content[:50]}...")
        return []
    except Exception as e:
        print(f"[Warn] Parsing error: {e}")
        return []

def search_query_generation(input_query,prompt_path):
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
        return [input_query]

    # Preserve original prompt structure
    history = []

    with open(prompt_path,"r") as f:
        prompt_for_queries=f.read()
    prompt_for_queries = prompt_for_queries.replace("{user_query}", input_query)

    history.append({"role": "user", "content": prompt_for_queries})

    print(f"{Colors.SYSTEM}[Debug] Processing request...{Colors.RESET}")
    
    queries = [input_query] # Default fallback
    final_queries={}
    try:
        response = llm.create_chat_completion(
            messages=history,
            temperature=0.6,
            stream=False 
        )
        
        content = response['choices'][0]['message']['content']
        print(f"[Debug] Raw LLM Output: {content}") # Uncomment for debugging

        # Use the robust extractor
        extracted = extract_json_from_response(content)
        
        if extracted:
            final_queries = extracted
            
    except Exception as e:
        print(f"{Colors.SYSTEM}[Error] Model execution failed: {e}{Colors.RESET}")

    print(f"{Colors.SYSTEM}Generated Queries: {final_queries}{Colors.RESET}")

    # Memory Cleanup
    clean_memory(llm)
    
    return final_queries
# inp=input("enter search query:")
# search_query_generation(inp,"../prompts/search_query_generation.txt")