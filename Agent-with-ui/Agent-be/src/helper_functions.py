import re
import json
from typing import List, Optional
from py_types import *

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

#solves problem for ```json ```
# def extract_json_from_markdown(text: str) -> str:
#     """
#     Extracts the JSON content from a string that might be wrapped in Markdown code blocks.
#     Example input: "Here is the JSON:\n```json\n{'a': 1}\n```"
#     Example output: "{'a': 1}"
#     """
#     # Pattern explanation:
#     # ```       -> Matches opening backticks
#     # (?:json)? -> Optionally matches the language identifier "json" (non-capturing)
#     # \s* -> Matches optional whitespace/newlines after the tag
#     # (.*?)     -> Captures the actual JSON content (non-greedy)
#     # \s* -> Matches optional whitespace/newlines before the closing tag
#     # ```       -> Matches closing backticks
#     pattern = r"```(?:json)?\s*(.*?)\s*```"
    
#     match = re.search(pattern, text, re.DOTALL)
#     if match:
#         return match.group(1)  # Return the content inside the backticks
    
#     # Fallback: If no code blocks are found, return the original text
#     # (The LLM might have sent raw JSON without markdown)
#     return text.strip()
import json

def extract_json_from_markdown(text: str):
    """
    Scans the text for ALL valid JSON lists and returns the LAST one found.
    This fixes issues where the model echoes the prompt (containing example JSON)
    before generating the real response.
    """
    decoder = json.JSONDecoder()
    valid_jsons = []
    
    # Clean known garbage headers to assist parsing
    text = text.replace("# OUTPUT", "").replace("# SOLUTION", "")
    
    pos = 0
    while pos < len(text):
        # 1. Find the next '['
        start_index = text.find('[', pos)
        if start_index == -1:
            break # No more lists found
        
        # 2. Try to decode a JSON object starting at this bracket
        try:
            # raw_decode returns tuple: (parsed_object, end_index_offset)
            # It stops exactly where the valid JSON ends, ignoring trailing garbage.
            obj, end_offset = decoder.raw_decode(text[start_index:])
            
            # We only care if it is a list (your schema is always a list of updates)
            if isinstance(obj, list):
                valid_jsons.append(obj)
            
            # Move position past this object to search for the next one
            pos = start_index + end_offset
            
        except json.JSONDecodeError:
            # If this '[' did not start a valid JSON, skip it and continue searching
            pos = start_index + 1
            
    if not valid_jsons:
        print(f"ERROR: No valid JSON lists found in output. Raw text snippet:\n{text}...")
        return []

    # 3. Return the LAST valid JSON list found (The Real Answer)
    print(f"SUCCESS: Found {len(valid_jsons)} JSON lists. Returning the last one.")
    return valid_jsons[-1]

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

__all__=[
    "make_generate_working_memory_prompt",
    "fake_make_generate_working_memory_prompt",
    "make_reasoning_prompt",
    "fake_make_reasoning_prompt",
    "make_execute_prompt",
    "make_log_prompt",
    "make_update_working_memory_prompt",
    "convert_history_to_prompt",
    "parse_deepseek_response",
    "extract_json_from_markdown",
    "load_file",
    "to_str"
]