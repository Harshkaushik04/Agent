from llama_cpp import Llama,GGML_TYPE_Q8_0
import gc 
import torch

def load_model(model_path,n_ctx):
    llm = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_gpu_layers=-1,
        flash_attn=True,
        # Using Q4_0 as discussed for stability with high context
        type_k=GGML_TYPE_Q8_0, 
        type_v=GGML_TYPE_Q8_0,
        n_batch=512,
        verbose=False
    )
    print("Model loaded and ready!")
    return llm

def convert_history_to_prompt(history):
    prompt = ""
    for msg in history:
        role = msg["role"]
        content = msg["content"] 

        if role == "system":
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        elif role == "user":
            prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
        elif role == "model":
            prompt += f"<|im_start|>assistant\n{msg["after_think"]}<|im_end|>\n"

    # Prepare the model to speak
    prompt += "<|im_start|>assistant\n"
    return prompt

def i_run_model(model_path,prompt,n_gpu_layers,n_ctx,max_tokens,n_batch,temperature):
    model=Llama(
        model_path=model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        n_batch=n_batch,
        verbose=False,
        type_k=GGML_TYPE_Q8_0, # Your Quantized Cache fix
        type_v=GGML_TYPE_Q8_0,
        flash_attn=True,
        chat_format="chatml"
    )
    history=[]
    history.append({"role":"system","content":"start thinking with <think> tag and stop thinking with </think> tag ,after that give the actual answer"})
    history.append({"role":"user","content":prompt})
    raw_prompt=convert_history_to_prompt(history)
    stream=model.create_completion(
        prompt=raw_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
        stop=["<|im_end|>"]
    )
    full_response = ""
    
    for chunk in stream:
        content = chunk["choices"][0]["text"]
        print(content, end="", flush=True)
        full_response += content

    before_think = ""
    after_think = ""
    
    closing_tag = "</think>"
    
    if closing_tag in full_response:
        parts = full_response.split(closing_tag, 1)
        before_think = parts[0].replace("<think>", "").strip() 
        after_think = parts[1].strip()
    else:
        before_think = ""
        after_think = full_response
        
    clean_memory(model)
    return full_response, before_think, after_think

def run_model(model_path,prompt):
    return i_run_model(model_path=model_path,
                       prompt=prompt,
                       n_gpu_layers=-1,
                       n_ctx=100000,
                       max_tokens=8192,
                       n_batch=512,
                       temperature=0.6)

def clean_memory(llm):
    """Forcefully frees VRAM for other models (embeddings)."""
    if llm:
        print(" Closing LlamaCPP model...")
        llm.close()
        del llm
        llm = None
    
    # Python Garbage Collection
    gc.collect()
    
    # PyTorch CUDA Cache (Critical for embedding models)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        
    print("✨ [SYSTEM] Memory/VRAM Forcefully Cleared.")