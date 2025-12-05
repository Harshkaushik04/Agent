import sys
import signal
import os
from llama_cpp import Llama

# ==============================
# CONFIGURATION
# ==============================
MODEL_PATH = "../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
CONTEXT_SIZE = 8192*3 
GPU_LAYERS = -1   # Set to -1 for GPU, 0 for CPU
BATCH_SIZE = 1024 

class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    THOUGHT = '\033[90m'   # Dark Gray
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'

def signal_handler(sig, frame):
    print(f"\n\n{Colors.SYSTEM}--- Chat Session Ended ---{Colors.RESET}")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    print(f"{Colors.SYSTEM}--- Loading DeepSeek R1... ---{Colors.RESET}")
    
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=GPU_LAYERS,
            n_ctx=CONTEXT_SIZE,
            n_batch=BATCH_SIZE,
            verbose=False,
            chat_format="chatml"
        )
    except Exception as e:
        print(f"{Colors.SYSTEM}Error: {e}{Colors.RESET}")
        return

    # Basic system prompt (The heavy lifting happens in your loaded file)
    history = [
        {
            "role": "system", 
            "content": "You are DeepSeek-R1. You are an advanced autonomous agent. Think step-by-step."
        }
    ]

    print(f"{Colors.SYSTEM}--- Chat Started ---{Colors.RESET}")
    print(f"{Colors.SYSTEM}Commands:{Colors.RESET}")
    print(f"  {Colors.BOLD}LOAD filename.txt{Colors.RESET} -> Load a long prompt from a file")
    print(f"  {Colors.BOLD}CLEAR{Colors.RESET}             -> Clear memory")
    print(f"  {Colors.BOLD}Ctrl+C{Colors.RESET}            -> Quit\n")

    while True:
        try:
            print(f"{Colors.USER}{Colors.BOLD}You: {Colors.RESET}", end="")
            user_input = input().strip()
            
            if not user_input:
                continue

            # --- COMMAND: LOAD FILE ---
            if user_input.upper().startswith("LOAD "):
                filename = user_input[5:].strip()
                if os.path.exists(filename):
                    try:
                        with open(filename, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        user_input = file_content
                        print(f"{Colors.SYSTEM}[System] Loaded '{filename}' successfully.{Colors.RESET}")
                    except Exception as e:
                        print(f"{Colors.SYSTEM}[Error] Could not read file: {e}{Colors.RESET}")
                        continue
                else:
                    print(f"{Colors.SYSTEM}[Error] File '{filename}' not found.{Colors.RESET}")
                    continue

            # --- COMMAND: CLEAR ---
            elif user_input.upper() == "CLEAR":
                history = [history[0]] # Keep system prompt
                print(f"{Colors.SYSTEM}[System] Context cleared.{Colors.RESET}")
                continue

            # DEBUG: Token Count
            tokens = llm.tokenize(user_input.encode('utf-8'))
            print(f"{Colors.SYSTEM}[Debug] Sending {len(tokens)} tokens to model...{Colors.RESET}")

            history.append({"role": "user", "content": user_input})

            # Generate
            print(f"{Colors.AI}{Colors.BOLD}DeepSeek: {Colors.RESET}", end="", flush=True)
            
            stream = llm.create_chat_completion(
                messages=history,
                temperature=0.6,
                max_tokens=None, 
                stream=True
            )

            full_response = ""
            after_think=""
            after_think_mode=False
            # thinking_mode = False

            for chunk in stream:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    content = delta['content']
                    
                    if "<think>" in content:
                        print(Colors.THOUGHT, end="")
                        thinking_mode = True
                    
                    print(content, end="", flush=True)
                    full_response += content
                    if(after_think_mode):
                        after_think+=content
                    if "</think>" in content:
                        print(Colors.RESET, end="")
                        thinking_mode = False
                        after_think_mode=True

            print("\n")
            history.append({"role": "assistant", "content": full_response})
            print("============================")
            print(after_think)

            # Memory management
            if len(history) > 10:
                history = [history[0]] + history[-9:]

        except KeyboardInterrupt:
            print(f"\n\n{Colors.SYSTEM}--- Chat Session Ended ---{Colors.RESET}")
            break
        except Exception as e:
            print(f"\n{Colors.SYSTEM}Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()