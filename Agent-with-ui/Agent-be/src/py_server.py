import sys
import gc
import re
from contextlib import asynccontextmanager,redirect_stdout, redirect_stderr
from fastapi import FastAPI, HTTPException,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from py_types import *
import json
import signal
import threading
import time
import io
from tools.search_query_generation import i_search_query_generation
from tools.file_checker import file_checker
from tools.generation_from_context import i_generation_from_context
from tools.html_cleaner import i_html_cleaner
from tools.make_rag_database import i_make_rag_database
from tools.merged_files import merge_files
from tools.model import i_run_model,load_model,clean_memory
from tools.question_answer import i_question_answer
from tools.read_file import read_file
from tools.write_file import write_file
from tools.retrieval_from_database import i_retrieval_from_database
from tools.search_engine_1 import i_search_engine_1
from tools.search_engine_2 import i_search_engine_2
from tools.summarise import i_summarise

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv("../../.env")

llm_lock = threading.Lock()
shutting_down = False
current_generation = False

def handle_shutdown(sig, frame):
    global shutting_down

    if shutting_down:
        return

    print(f"\n[SYSTEM] Received signal {sig}, shutting down safely...")
    shutting_down = True

    # Wait for generation to finish (max 10s)
    start = time.time()
    while current_generation and time.time() - start < 10:
        print("[SYSTEM] Waiting for generation to finish...")
        time.sleep(0.5)

    try:
        clean_memory()
    finally:
        print("[SYSTEM] Exit.")
        sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)  # kill PID
signal.signal(signal.SIGINT, handle_shutdown)   # Ctrl+C
signal.signal(signal.SIGHUP, handle_shutdown)   # terminal close / SSH drop

import torch

from llama_cpp import Llama, GGML_TYPE_Q8_0

# --- CONFIGURATION ---
MODEL_PATH = "/home/harsh/RAG/models/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf"
N_CTX = 80000
MAX_TOKENS=4196
TEMPERATURE=0.6
HOST = "0.0.0.0"
PORT = 5000

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Global variable to hold the model
llm = None

# --- MEMORY CLEANUP FUNCTION ---
def clean_memory():
    """Forcefully frees VRAM for other models (embeddings)."""
    global llm
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

def load_file(filepath):
    """Helper to read file content safely"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return "file is currently not made"
def to_str(obj):
    if obj is None:
        return "none"
    elif isinstance(obj,(dict,list)):
        return json.dumps(obj,indent=2,ensure_ascii=False)
    return str(obj)

async def extract_output(func:str,inputs:dict[str,str]):
    if(func=="search_query_generation" or func=="generation_from_context" or func=="question_answer" 
       or func=="summarise"):
        inputs["llm"]=llm
    if(func=="retrieval_from_database"):
        inputs["gen_llm"]=llm
    capture = io.StringIO()
    with redirect_stdout(capture), redirect_stderr(capture):
        match func:
            case "search_query_generation":
                output=i_search_query_generation(**inputs)
            case "search_engine_1":
                output=await i_search_engine_1(**inputs)
            case "search_engine_2":
                output=await i_search_engine_2(**inputs)
            case "html_cleaner":
                output=i_html_cleaner(**inputs)
            case "write_file":
                output=write_file(**inputs)
            case "read_file":
                output=read_file(**inputs)
            case "merge_files":
                output=merge_files(**inputs)
            case "make_rag_database":
                output=i_make_rag_database(**inputs)
            case "retrieval_from_database":
                output=i_retrieval_from_database(**inputs)
            case "generation_from_context":
                output=i_generation_from_context(**inputs)
            case "file_checker":
                output=file_checker(**inputs)
            case "question_answer":
                output=i_question_answer(**inputs)
            case "summarise":
                output=i_summarise(**inputs)
            case _:
                output="function not implemented right now"
    print_output = capture.getvalue()
    print_output=to_str(print_output)
    output=to_str(output)
    return output,print_output

# --- LIFECYCLE MANAGEMENT ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model automatically
    load_model()
    yield
    # Shutdown: Clean up
    clean_memory()

app = FastAPI(lifespan=lifespan)

# --- HELPER: LOAD MODEL ---
def load_model():
    global llm
    if llm is not None:
        print(" Model is already loaded.")
        return

    print(f" Loading model into VRAM: {MODEL_PATH}")
    llm = Llama(
        model_path=MODEL_PATH,
        n_ctx=N_CTX,
        n_gpu_layers=-1,
        flash_attn=True,
        # Using Q4_0 as discussed for stability with high context
        type_k=GGML_TYPE_Q8_0, 
        type_v=GGML_TYPE_Q8_0,
        n_batch=512,
        verbose=False
    )
    print("Model loaded and ready!")

def make_generate_working_memory_prompt(state_json,feedback):
    prompt_template=load_file("../prompts/generate_working_memory.txt")
    tools=load_file("../prompts/essentials/tools.txt")
    example_generate_working_memory=load_file("../prompts/essentials/example_generate_working_memory.txt")
    prompt_template=prompt_template.replace("{{TOOLS}}",tools)
    prompt_template=prompt_template.replace("{{EXAMPLE}}",example_generate_working_memory)
    prompt_template=prompt_template.replace("{{STATE}}",state_json)
    prompt_template=prompt_template.replace("{{FEEDBACK}}",feedback)
    return prompt_template

def fake_make_generate_working_memory_prompt(state_json,feedback):
    prompt=load_file("../prompts/extras/fake_test_gwm_2.txt")
    return prompt

def fake_make_reasoning_prompt(state_json,feedback):
    prompt=load_file("../prompts/extras/fake_test_reasoning.txt")
    return prompt

def make_reasoning_prompt(state_json,feedback):
    prompt_template=load_file("../prompts/reasoning.txt")
    tools=load_file("../prompts/essentials/tools.txt")
    example_reasoning=load_file("../prompts/essentials/example_reasoning.txt")
    prompt_template=prompt_template.replace("{{TOOLS}}",tools)
    prompt_template=prompt_template.replace("{{EXAMPLE}}",example_reasoning)
    prompt_template=prompt_template.replace("{{STATE}}",state_json)
    prompt_template=prompt_template.replace("{{FEEDBACK}}",feedback)
    return prompt_template

def make_execute_prompt(state_json,function_output,function_stdout_stderr_output,feedback):
    prompt_template=load_file("../prompts/execute.txt")
    tools=load_file("../prompts/essentials/tools.txt")
    example_execute=load_file("../prompts/essentials/example_execute.txt")
    prompt_template=prompt_template.replace("{{TOOLS}}",to_str(tools))
    prompt_template=prompt_template.replace("{{EXAMPLE}}",to_str(example_execute))
    prompt_template=prompt_template.replace("{{STATE}}",to_str(state_json))
    prompt_template=prompt_template.replace("{{FUNCTION_OUTPUT}}",to_str(function_output))
    prompt_template=prompt_template.replace("{{FUNCTION_STDOUT_STDERR_OUTPUT}}",to_str(function_stdout_stderr_output))
    prompt_template=prompt_template.replace("{{FEEDBACK}}",to_str(feedback))
    return prompt_template

def make_log_prompt():
    return ""

def make_update_working_memory_prompt():
    return ""

# --- EXISTING HELPERS ---
def convert_history_to_prompt(history: List[Message]) -> str:
    prompt = ""
    for msg in history:
        if msg.role == "system":
            prompt += f"<|im_start|>system\n{msg.content}<|im_end|>\n"
        elif msg.role == "user":
            prompt += f"<|im_start|>user\n{msg.content}<|im_end|>\n"
        elif msg.role == "assistant" or msg.role == "model":
            # Prefer 'after_think' if it exists (the actual answer), otherwise content
            content = msg.after_think if msg.after_think else msg.content
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    return prompt

def parse_deepseek_response(raw_text: str):
    if "</think>" in raw_text:
        parts = raw_text.split("</think>")
        thought_process = parts[0].replace("<think>", "").strip()
        final_answer = parts[1].strip()
    else:
        thought_process = ""
        final_answer = raw_text.strip()
    return thought_process, final_answer

import re
import json
#solves problem for ```json ```
def extract_json_from_markdown(text: str) -> str:
    """
    Extracts the JSON content from a string that might be wrapped in Markdown code blocks.
    Example input: "Here is the JSON:\n```json\n{'a': 1}\n```"
    Example output: "{'a': 1}"
    """
    # Pattern explanation:
    # ```       -> Matches opening backticks
    # (?:json)? -> Optionally matches the language identifier "json" (non-capturing)
    # \s* -> Matches optional whitespace/newlines after the tag
    # (.*?)     -> Captures the actual JSON content (non-greedy)
    # \s* -> Matches optional whitespace/newlines before the closing tag
    # ```       -> Matches closing backticks
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)  # Return the content inside the backticks
    
    # Fallback: If no code blocks are found, return the original text
    # (The LLM might have sent raw JSON without markdown)
    return text.strip()

# --- NEW ROUTES ---

# --- ADD THIS HANDLER ---
@app.exception_handler(RequestValidationError)
async def debug_validation_exception_handler(request: Request, exc: RequestValidationError):
    # 1. Get the raw body bytes
    body = await request.body()
    
    # 2. Decode it to string (so you can read it)
    body_str = body.decode("utf-8")
    
    # 3. Print it to your server console
    print(f"\n--- 422 VALIDATION ERROR ---")
    print(f"URL: {request.url}")
    print(f"RAW BODY RECEIVED:\n{body_str}")
    print(f"PYDANTIC ERRORS:\n{exc.errors()}")
    print(f"----------------------------\n")

    # 4. Return the standard 422 response so the frontend still knows it failed
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body_received": body_str},
    )
# ------------------------

@app.post("/close-model")
async def close_model_route():
    """Free up VRAM so you can load your embedding model."""
    clean_memory()
    return {"status": "success", "message": "Model closed. VRAM cleared."}

@app.post("/open-model")
async def open_model_route():
    """Reload the LLM when you are done with embeddings."""
    load_model()
    return {"status": "success", "message": "Model reloaded."}

# --- GENERATE ROUTE (Updated with Safety Check) ---
@app.post("/generate-working-memory")
async def generate_working_memory(request:GenerateWorkingMemoryRequest):
    # print(f"[entered-generate_working_memory]")
    global llm,current_generation,shutting_down
    if shutting_down:
        raise HTTPException(status_code=503,detail="py server shut down")
    
    # Safety Check
    if llm is None:
        return{
            "valid":False
        }
    with llm_lock:
        current_generation=True
        try:
            state=request.state
            feedback=request.feedback
            json_state=state.model_dump_json()
            prompt = fake_make_generate_working_memory_prompt(json_state,feedback)
            print("prompt:",prompt)
            # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

            # Stream to stdout for debugging
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
                    print("[SYSTEM] Generation interrupted")
                    break
                token = output['choices'][0]['text']
                sys.stdout.write(token)
                sys.stdout.flush()
                full_text += token

            print("\n------------------------------------------------\n")
        finally:
            current_generation=False
    
    thought, answer = parse_deepseek_response(full_text)
    output_updation_state=[]
    try:
        output_updation_state=extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [generate_working_memory]:\n {e}")
    return {
        "stateUpdationObject":output_updation_state,
        "valid":True
    }
@app.post("/openrouter-generate-working-memory")
async def openrouter_generate_working_memory(request: GenerateWorkingMemoryRequest):
    global current_generation, shutting_down
    
    if shutting_down:
        raise HTTPException(status_code=503, detail="py server shut down")
    
    current_generation = True
    print("\n[System] Sending request (Non-Streaming)... Waiting for DeepSeek to think...")
    
    try:
        state = request.state
        feedback = request.feedback
        json_state = state.model_dump_json()
        
        prompt_content = make_generate_working_memory_prompt(json_state, feedback)
        print("prompt:", prompt_content)

        # FIX: Use Non-Streaming to prevent "Network Lost" on silence
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Agent Server",
            },
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            stream=False,      # <--- DISABLED STREAMING FOR STABILITY
            timeout=600.0      # <--- 10 Minute Timeout
        )

        print("[System] Response received!")

        # 1. Extract The Message
        message = response.choices[0].message
        
        # 2. Get Answer (Content)
        final_content_text = message.content or ""

        # 3. Get Thoughts (Reasoning)
        # (Safely check for 'reasoning_content' as it may not exist in all responses)
        reasoning_text = getattr(message, 'reasoning_content', "") or ""
        
        # If empty, sometimes it's hidden in 'model_extra' depending on SDK version
        if not reasoning_text and hasattr(message, 'model_extra'):
            reasoning_text = (message.model_extra or {}).get('reasoning_content', "")

        # Debug Prints
        if reasoning_text:
            print(f"\n<think>\n{reasoning_text}\n</think>")
        print(final_content_text)
        print("\n------------------------------------------------\n")

        # 4. Reconstruct for your Parser
        if reasoning_text:
            full_text = f"<think>{reasoning_text}</think>\n{final_content_text}"
        else:
            full_text = final_content_text

    except Exception as e:
        print(f"API Error: {e}")
        return {"valid": False, "error": str(e)}
        
    finally:
        current_generation = False
    
    # 5. Standard Parsing
    thought, answer = parse_deepseek_response(full_text)
    print("answer:",answer)
    output_updation_state = []
    try:
        output_updation_state = extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [generate_working_memory]:\n {e}")
        print(f"Failed Answer String: {answer}")
        
    return {
        "stateUpdationObject": output_updation_state,
        "valid": True
    }
@app.post("/reasoning")
async def reasoning(request:ReasoningRequest):
    global llm
    
    # Safety Check
    if llm is None:
        return{
            "valid":False
        }
    state=request.state
    feedback=request.feedback
    json_state=state.model_dump_json()
    prompt = make_reasoning_prompt(json_state,feedback)
    print("prompt:",prompt)
    # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

    # Stream to stdout for debugging
    stream = llm(
        prompt,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        stop=["<|im_end|>"],
        stream=True
    )

    full_text = ""
    for output in stream:
        token = output['choices'][0]['text']
        sys.stdout.write(token)
        sys.stdout.flush()
        full_text += token

    print("\n------------------------------------------------\n")
    
    thought, answer = parse_deepseek_response(full_text)
    try:
        output_state_updation_object=extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [reasoning]:\n {e}")
    return {
        "stateUpdationObject":output_state_updation_object,
        "valid":True
    }


@app.post("/execute")
async def execute(request:ExecuteRequest):
    #change this function to run tools instead of llm call and also only return log, instead of stateUpdationObject too
    global llm
    
    # Safety Check
    if llm is None:
        return{
            "valid":False
        }
    state=request.state
    feedback=request.feedback
    json_state=state.model_dump_json()
    current_function=state.current_function_to_execute.function_name
    inputs=state.current_function_to_execute.inputs
    func_output,func_print_output=await extract_output(current_function,inputs)
    prompt=make_execute_prompt(json_state,func_output,func_print_output,feedback)
    print("prompt:",prompt)
    # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

    # Stream to stdout for debugging
    stream = llm(
        prompt,
        max_tokens=N_CTX,
        temperature=TEMPERATURE,
        stop=["<|im_end|>"],
        stream=True
    )

    full_text = ""
    for output in stream:
        token = output['choices'][0]['text']
        sys.stdout.write(token)
        sys.stdout.flush()
        full_text += token

    print("\n------------------------------------------------\n")
    
    thought, answer = parse_deepseek_response(full_text)
    output_state_updation_object=[]
    try:
        output_state_updation_object=extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [execute]:\n {e}")
    return {
        "stateUpdationObject":output_state_updation_object,
        "valid":True,
        "log":"" #do something here
    }

@app.post("/openrouter-reasoning")
async def openrouter_reasoning(request: ReasoningRequest):
    global current_generation, shutting_down
    
    if shutting_down:
        raise HTTPException(status_code=503, detail="py server shut down")
    
    current_generation = True
    full_text = ""
    
    try:
        state = request.state
        # FIX: Added feedback extraction (was missing in your local version)
        feedback = request.feedback 
        json_state = state.model_dump_json()
        
        prompt_content = make_reasoning_prompt(json_state, feedback)
        print("prompt:", prompt_content)

        # 1. Call OpenRouter
        stream = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Agent Server",
            },
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            stream=True
        )

        # 2. Iterate and Stream to Console
        for chunk in stream:
            if shutting_down:
                print("[SYSTEM] Generation interrupted")
                break
            
            delta = chunk.choices[0].delta
            
            # Print thoughts (DeepSeek R1 specific)
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                sys.stdout.write(delta.reasoning_content)
                sys.stdout.flush()

            # Print answer
            if delta.content:
                sys.stdout.write(delta.content)
                sys.stdout.flush()
                full_text += delta.content

        print("\n------------------------------------------------\n")
        
    except Exception as e:
        print(f"API Error in [reasoning]: {e}")
        return {"valid": False, "error": str(e)}
        
    finally:
        current_generation = False
    
    # 3. Parse and Return
    thought, answer = parse_deepseek_response(full_text)
    
    output_state_updation_object = []
    try:
        output_state_updation_object = extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [reasoning]:\n {e}")
        
    return {
        "stateUpdationObject": output_state_updation_object,
        "valid": True
    }


@app.post("/openrouter-execute")
async def openrouter_execute(request: ExecuteRequest):
    global current_generation, shutting_down
    
    if shutting_down:
        raise HTTPException(status_code=503, detail="py server shut down")
        
    current_generation = True
    full_text = ""
    
    try:
        state = request.state
        # FIX: Added feedback extraction
        feedback = request.feedback
        
        # 1. Execute the Tool (Local Python Function)
        current_function = state.current_function_to_execute.function_name
        inputs = state.current_function_to_execute.inputs
        
        # NOTE: This runs locally on your server before calling the LLM
        func_output, func_print_output = await extract_output(current_function, inputs)
        
        # 2. Prepare Prompt with Tool Outputs
        json_state = state.model_dump_json()
        prompt_content = make_execute_prompt(json_state, func_output, func_print_output, feedback)
        # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

        # 3. Call OpenRouter to Interpret Results
        stream = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Agent Server",
            },
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "user", "content": prompt_content}
            ],
            stream=True
        )

        for chunk in stream:
            if shutting_down:
                print("[SYSTEM] Generation interrupted")
                break

            delta = chunk.choices[0].delta
            
            # Print thoughts
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                sys.stdout.write(delta.reasoning_content)
                sys.stdout.flush()

            # Print answer
            if delta.content:
                sys.stdout.write(delta.content)
                sys.stdout.flush()
                full_text += delta.content

        print("\n------------------------------------------------\n")

    except Exception as e:
        print(f"API Error in [execute]: {e}")
        return {"valid": False, "error": str(e)}

    finally:
        current_generation = False
    
    # 4. Parse and Return
    thought, answer = parse_deepseek_response(full_text)
    
    output_state_updation_object = []
    try:
        output_state_updation_object = extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [execute]:\n {e}")
        
    return {
        "stateUpdationObject": output_state_updation_object,
        "valid": True,
        "log": "" # You can populate this if needed
    }

@app.post("/interpret-output")
async def interpret_output(request:MakeLogRequest):
    global llm
    
    # Safety Check
    if llm is None:
        return{
            "valid":False
        }
    state=request.state
    json_state=state.model_dump_json()
    prompt = make_log_prompt()
    
    # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

    # Stream to stdout for debugging
    stream = llm(
        prompt,
        max_tokens=N_CTX,
        temperature=TEMPERATURE,
        stop=["<|im_end|>"],
        stream=True
    )

    full_text = ""
    for output in stream:
        token = output['choices'][0]['text']
        sys.stdout.write(token)
        sys.stdout.flush()
        full_text += token

    print("\n------------------------------------------------\n")
    
    thought, answer = parse_deepseek_response(full_text)
    output_state_updation_object=[]
    try:
        output_state_updation_object=extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [interpret_output]:\n {e}")
    return {
        "stateUpdationObject":output_state_updation_object,
        "valid":True
    }

@app.post("/update-working-memory")
async def update_working_memory(request:UpdateWorkingMemoryRequest): #keeps size of working memory in check
    global llm
    
    # Safety Check
    if llm is None:
        return{
            "valid":False
        }
    state=request.state
    json_state=state.model_dump_json()
    prompt = make_update_working_memory_prompt()
    
    # print(f"\n--- NEW REQUEST [Chat Length: {len(request.history)}] ---")

    # Stream to stdout for debugging
    stream = llm(
        prompt,
        max_tokens=N_CTX,
        temperature=TEMPERATURE,
        stop=["<|im_end|>"],
        stream=True
    )

    full_text = ""
    for output in stream:
        token = output['choices'][0]['text']
        sys.stdout.write(token)
        sys.stdout.flush()
        full_text += token

    print("\n------------------------------------------------\n")
    
    thought, answer = parse_deepseek_response(full_text)
    output_state_updation_object=[]
    try:
        output_state_updation_object=extract_json_from_markdown(answer)
    except json.JSONDecodeError as e:
        print(f"json parsing error in [update_working_memory]:\n {e}")
    return {
        "stateUpdationObject":output_state_updation_object,
        "valid":True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)