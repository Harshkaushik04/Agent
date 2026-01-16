from dotenv import load_dotenv
import os
from llama_cpp import Llama
import re
import json
import torch
import gc
load_dotenv("../../.env")
class Colors:
    USER = '\033[92m'      # Green
    AI = '\033[96m'        # Cyan
    SYSTEM = '\033[93m'    # Yellow
    RESET = '\033[0m'
    BOLD = '\033[1m'
GEN_MODEL_CTX = 8192*3

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

def modified_search_query_generation(llm,input_query,prompt_path,before_formated_words,after_formated_words):
    print(f"{Colors.SYSTEM}--- Generating Search Queries (DeepSeek) ---{Colors.RESET}")
    # Preserve original prompt structure
    history = []
    with open(prompt_path,"r") as f:
        prompt_for_queries=f.read()
    len1=len(before_formated_words)
    len2=len(after_formated_words)
    if len1!=len2:
        raise ValueError("[Error] length of before formatted words array not equal to after formatted words array")
    for i in range(len1):
        prompt_for_queries = prompt_for_queries.replace(f"{{{before_formated_words[i]}}}", after_formated_words[i])
    print("prompt:",prompt_for_queries)
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
    return final_queries

def i_search_query_generation(llm,sentences):
    prompt_path="/home/harsh/RAG/Agent-with-ui/Agent-be/prompts/tools/search_query_generation.txt"
    search_queries=[]
    for sentence in sentences:
        search_query_list=modified_search_query_generation(
                                     llm=llm,
                                     input_query=sentence,
                                     prompt_path=prompt_path,
                                     before_formated_words=["user_query"],
                                     after_formated_words=[sentence])
        search_queries.append({
            "sentence":sentence,
            "search_queries":search_query_list
        })
    return search_queries
# inp=input("enter search query:")
# search_query_generation(inp,"../prompts/search_query_generation.txt")