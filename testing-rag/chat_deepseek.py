import sys
import signal
from llama_cpp import Llama

# ==============================
# CONFIGURATION
# ==============================
MODEL_PATH = "../models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
CONTEXT_SIZE = 8192*3  
GPU_LAYERS = -1  # Set to -1 if you have a GPU, 0 for CPU
BATCH_SIZE = 1024 # Increased for faster processing of large prompts

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

def get_multiline_input():
    """Reads input until the user types 'END' on a new line."""
    print(f"{Colors.USER}{Colors.BOLD}You (Multi-line Mode - Type 'END' on a new line to submit):{Colors.RESET}")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

def main():
    signal.signal(signal.SIGINT, signal_handler)

    print(f"{Colors.SYSTEM}--- Loading DeepSeek R1... ---{Colors.RESET}")
    
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_gpu_layers=GPU_LAYERS,
            n_ctx=CONTEXT_SIZE,
            n_batch=BATCH_SIZE, # Helps ingest large pastes
            verbose=False,
            chat_format="chatml"
        )
    except Exception as e:
        print(f"{Colors.SYSTEM}Error: {e}{Colors.RESET}")
        return

    # We keep the system prompt simple so it doesn't conflict with your complex agent prompt
    history = [
        {
            "role": "system", 
            "content": "You are DeepSeek-R1. You are an advanced AI agent. Follow the user's instructions precisely. Think step-by-step."
        }
    ]

    print(f"{Colors.SYSTEM}--- Chat Started. Type 'PASTE' to enter multi-line mode. ---{Colors.RESET}\n")

    while True:
        try:
            # 1. Input Handling
            print(f"{Colors.USER}{Colors.BOLD}You: {Colors.RESET}", end="")
            first_line = input()
            
            user_input = ""
            
            # Detect Paste Mode
            if first_line.strip().upper() == "PASTE":
                user_input = get_multiline_input()
            else:
                user_input = first_line

            if not user_input.strip():
                continue

            # DEBUG: Check if the whole prompt was received
            tokens = llm.tokenize(user_input.encode('utf-8'))
            print(f"{Colors.SYSTEM}[Debug] Received {len(tokens)} tokens.{Colors.RESET}")

            history.append({"role": "user", "content": user_input})

            # 2. Generation
            print(f"{Colors.AI}{Colors.BOLD}DeepSeek: {Colors.RESET}", end="", flush=True)
            
            stream = llm.create_chat_completion(
                messages=history,
                temperature=0.6,
                max_tokens=None, 
                stream=True
            )

            full_response = ""
            thinking_mode = False

            for chunk in stream:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    content = delta['content']
                    
                    # Formatting <think> blocks
                    if "<think>" in content:
                        print(Colors.THOUGHT, end="")
                        thinking_mode = True
                    
                    print(content, end="", flush=True)
                    full_response += content

                    if "</think>" in content:
                        print(Colors.RESET, end="")
                        thinking_mode = False

            print("\n")
            history.append({"role": "assistant", "content": full_response})

            # Manage history size (Last 5 exchanges)
            if len(history) > 12:
                history = [history[0]] + history[-11:]

        except KeyboardInterrupt:
            print(f"\n\n{Colors.SYSTEM}--- Chat Session Ended ---{Colors.RESET}")
            break
        except Exception as e:
            print(f"\n{Colors.SYSTEM}Error: {e}{Colors.RESET}")

if __name__ == "__main__":
    main()