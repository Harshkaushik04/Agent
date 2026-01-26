from llama_cpp import Llama, GGML_TYPE_Q8_0
import threading
import signal
import time
import sys
from tools.model import clean_memory

# --- GLOBAL STATE ---
llm_lock = threading.Lock()
shutting_down = False
current_generation = False
active_llm_ref = None  # Needed so handle_shutdown knows which model to clean

class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'

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

MAX_TOKENS = 8192
TEMPERATURE = 0.6

def parse_deepseek_response(raw_text: str):
    if "</think>" in raw_text:
        parts = raw_text.split("</think>")
        thought_process = parts[0].replace("<think>", "").strip()
        final_answer = parts[1].strip()
    else:
        thought_process = ""
        final_answer = raw_text.strip()
    return thought_process, final_answer

def i_question_answer(llm, query):
    global current_generation, shutting_down, active_llm_ref
    
    # 1. Update global ref for safety
    active_llm_ref = llm
    
    # 2. Apply Chat Template (CRITICAL for correct answers)
    # Without this, the model behaves like a text completion engine, not a chatbot.
    formatted_prompt = f"""<|im_start|>system
You are a helpful assistant. Answer the user's question clearly and concisely.
<|im_end|>
<|im_start|>user
{query}
<|im_end|>
<|im_start|>assistant
"""
    
    with llm_lock:
        current_generation = True
        try:
            print(f"{Colors.SYSTEM}--- Generating Answer ---{Colors.RESET}")
            stream = llm(
                formatted_prompt,
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
            return f"Error during generation: {str(e)}"
        finally:
            current_generation = False
    
    # 3. Parse and Return
    thought, answer = parse_deepseek_response(full_text)
    return answer