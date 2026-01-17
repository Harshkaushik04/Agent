from llama_cpp import Llama, GGML_TYPE_Q8_0
import threading
import signal
import time
import sys
import re
import json
import os
from tools.model import clean_memory
from dotenv import load_dotenv

# --- CONFIG ---
load_dotenv("/home/harsh/RAG/Agent-with-ui/.env")
PROMPT_PATH = "/home/harsh/RAG/Agent-with-ui/Agent-be/prompts/tools/search_query_generation.txt"
MAX_TOKENS = 8192
TEMPERATURE = 0.6

# --- GLOBAL STATE ---
llm_lock = threading.Lock()
shutting_down = False
current_generation = False
active_llm_ref = None  # Reference to the model for safe shutdown

class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'

# --- SIGNAL HANDLING ---
def handle_shutdown(sig, frame):
    global shutting_down, active_llm_ref

    if shutting_down:
        return

    print(f"\n{Colors.SYSTEM}[SYSTEM] Received signal {sig}, shutting down safely...{Colors.RESET}")
    shutting_down = True

    # Wait for generation to finish (max 10s)
    start = time.time()
    while current_generation and time.time() - start < 10:
        print(f"{Colors.SYSTEM}[SYSTEM] Waiting for generation to finish...{Colors.RESET}")
        time.sleep(0.5)

    try:
        if active_llm_ref:
            print(f"{Colors.SYSTEM}[SYSTEM] Cleaning memory...{Colors.RESET}")
            clean_memory(active_llm_ref)
    except Exception as e:
        print(f"[Error] Memory cleanup failed: {e}")
    finally:
        print(f"{Colors.SYSTEM}[SYSTEM] Exit.{Colors.RESET}")
        sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGHUP, handle_shutdown)


# --- PARSING HELPERS ---
def parse_deepseek_response(raw_text: str):
    """Separates <think> block from the actual answer."""
    if "</think>" in raw_text:
        parts = raw_text.split("</think>")
        thought_process = parts[0].replace("<think>", "").strip()
        final_answer = parts[1].strip()
    else:
        thought_process = ""
        final_answer = raw_text.strip()
    return thought_process, final_answer

def extract_json_from_response(content):
    """
    Robustly extracts JSON from LLM output.
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
            # If plain text (no JSON), wrap it in a list to prevent crash
            if len(content) < 200:
                return [content]
            raise ValueError("No JSON-like syntax found")
            
        parsed = json.loads(json_str)

        # 6. Normalize output
        if isinstance(parsed, dict) and "questions" in parsed:
            return parsed["questions"]
        elif isinstance(parsed, list):
            return parsed
        else:
            return []

    except Exception as e:
        print(f"[Warn] Parsing error: {e}")
        return []

def modified_search_query_generation(llm, prompt_template, before_formated_words, after_formated_words):
    global current_generation, shutting_down, active_llm_ref
    
    # Update global ref
    active_llm_ref = llm
    
    # 1. Format Prompt
    prompt_for_queries = prompt_template
    for i in range(len(before_formated_words)):
        prompt_for_queries = prompt_for_queries.replace(f"{{{before_formated_words[i]}}}", str(after_formated_words[i]))

    print(f"{Colors.SYSTEM}--- Generating Search Queries (DeepSeek) ---{Colors.RESET}")
    # print("DEBUG PROMPT:", prompt_for_queries[:100])

    with llm_lock:
        current_generation = True
        try:
            stream = llm(
                prompt_for_queries,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stop=["<|im_end|>"],
                stream=True
            )

            full_text = ""
            for output in stream:
                if shutting_down:
                    break
                token = output['choices'][0]['text']
                sys.stdout.write(Colors.AI + token + Colors.RESET)
                sys.stdout.flush()
                full_text += token

            print("\n------------------------------------------------\n")
        finally:
            current_generation = False
    
        # 2. Parse Output
        thought, answer = parse_deepseek_response(full_text)
        
        # 3. ✅ CRITICAL FIX: Extract JSON List
        final_list = extract_json_from_response(answer)
        return final_list

def i_search_query_generation(llm, sentences):
    """
    Main entry point. Returns a list of objects with generated queries.
    """
    # 1. Load Prompt ONCE
    if not os.path.exists(PROMPT_PATH):
        print(f"[Error] Prompt file not found: {PROMPT_PATH}")
        return []
        
    with open(PROMPT_PATH, "r") as f:
        prompt_template = f.read()

    search_queries = []
    
    for sentence in sentences:
        print(f"Processing Intent: {sentence}")
        
        # Call the generator
        query_list = modified_search_query_generation(
            llm=llm,
            prompt_template=prompt_template, # Pass the loaded string, not path
            before_formated_words=["user_query"],
            after_formated_words=[sentence]
        )
        
        search_queries.append({
            "sentence": sentence,
            "search_queries": query_list
        })
        
    return search_queries