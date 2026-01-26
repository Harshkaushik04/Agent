from llama_cpp import Llama, GGML_TYPE_Q8_0
import threading
import signal
import time
import sys
import os
from tools.model import clean_memory

# --- CONFIG ---
MAX_TOKENS = 8192
TEMPERATURE = 0.6
PROMPT_PATH = "/home/harsh/RAG/Agent-with-ui/Agent-be/prompts/tools/generation_from_context.txt"

# --- GLOBAL STATE ---
llm_lock = threading.Lock()
shutting_down = False
current_generation = False
active_llm_ref = None  # Reference to the LLM for the signal handler

class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'

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
            print(f"{Colors.SYSTEM}[SYSTEM] Unloading model...{Colors.RESET}")
            clean_memory(active_llm_ref)
    except Exception as e:
        print(f"[Error] Memory cleanup failed: {e}")
    finally:
        print(f"{Colors.SYSTEM}[SYSTEM] Exit.{Colors.RESET}")
        sys.exit(0)

# Register Signals
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGHUP, handle_shutdown)

def parse_deepseek_response(raw_text: str):
    """Separates the <think> block from the final answer."""
    if "</think>" in raw_text:
        parts = raw_text.split("</think>")
        thought_process = parts[0].replace("<think>", "").strip()
        final_answer = parts[1].strip()
    else:
        thought_process = ""
        final_answer = raw_text.strip()
    return thought_process, final_answer

def modified_generation_from_context(llm, prompt, before_formated_words, after_formated_words):
    global current_generation, shutting_down, active_llm_ref
    
    # Update global ref for safety
    active_llm_ref = llm
    
    # Validate inputs
    if len(before_formated_words) != len(after_formated_words):
        raise ValueError("[Error] Mismatch in format arguments length.")

    # Format Prompt
    for i in range(len(before_formated_words)):
        # Use simple replace, but be careful if your prompt has other {} braces
        prompt = prompt.replace(f"{{{before_formated_words[i]}}}", str(after_formated_words[i]))

    # print(f"DEBUG PROMPT: {prompt[:100]}...") # Optional debug

    with llm_lock:
        current_generation = True
        try:
            stream = llm(
                prompt,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                stop=["<|im_end|>"],
                stream=True
            )

            full_text = ""
            for output in stream:
                if shutting_down:
                    print(f"\n{Colors.SYSTEM}[SYSTEM] Generation interrupted{Colors.RESET}")
                    break
                
                token = output['choices'][0]['text']
                sys.stdout.write(Colors.AI + token + Colors.RESET)
                sys.stdout.flush()
                full_text += token

            print("\n------------------------------------------------\n")
        except Exception as e:
            return f"Generation Error: {str(e)}"
        finally:
            current_generation = False
    
        _, answer = parse_deepseek_response(full_text)
        return answer

def i_generation_from_context(llm, whether_path_or_data, query, context):
    """
    Unified function to handle both raw string data and file paths.
    """
    # 1. Load Prompt Template (Fail fast if missing)
    if not os.path.exists(PROMPT_PATH):
        return f"[Error] Prompt file not found at: {PROMPT_PATH}"
    
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except Exception as e:
        return f"[Error] Failed to read prompt file: {e}"

    # 2. Resolve Context (Path vs Data)
    actual_context = ""
    
    if whether_path_or_data == "data":
        actual_context = context
    elif whether_path_or_data == "path":
        if not os.path.exists(context):
            return f"[Error] Context file not found at: {context}"
        try:
            with open(context, "r", encoding="utf-8") as f:
                actual_context = f.read()
        except Exception as e:
            return f"[Error] Failed to read context file: {e}"
    else:
        return f"[Error] Invalid mode '{whether_path_or_data}'. Use 'data' or 'path'."

    # 3. Generate
    return modified_generation_from_context(
        llm=llm,
        prompt=prompt_template,
        before_formated_words=["query", "context"],
        after_formated_words=[query, actual_context]
    )