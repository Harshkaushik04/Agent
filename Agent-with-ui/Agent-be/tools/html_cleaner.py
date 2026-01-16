import os
import uuid
from bs4 import BeautifulSoup

# Ensure directory for cleaned files exists
CLEANED_DIR = "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/cleaned_text"
if not os.path.exists(CLEANED_DIR):
    os.makedirs(CLEANED_DIR)

def parse_and_clean_html(html_content, url):
    """
    Core logic to strip HTML tags and extract meaningful text.
    """
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. Remove noise/boilerplate tags
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'link', 'svg', 'footer', 'nav', 'header', 'aside', 'form', 'button', 'meta']):
        tag.decompose()

    text_content = []
    
    # 2. Extract text from likely content tags
    targets = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'article', 'div', 'span'])
    
    for el in targets:
        # Get text, strip whitespace
        text = el.get_text(separator=' ', strip=True)
        # Filter out very short snippets (nav items, menu labels)
        if len(text) > 40:
            text_content.append(text)

    # 3. Remove duplicates while preserving order
    seen = set()
    unique_content = [x for x in text_content if not (x in seen or seen.add(x))]
    
    # Add a header so the AI knows where this text came from
    return f"--- SOURCE: {url} ---\n" + "\n".join(unique_content)

def i_html_cleaner(list_url_file_path_json):
    """
    Input: List of { "url": str, "file_store_path": str }
    Output: List of { "url": str, "file_store_path": str } (pointing to CLEANED text files)
    """
    cleaned_results = []

    for item in list_url_file_path_json:
        url = item["url"]
        raw_path = item["file_store_path"]
        
        try:
            # 1. Read the Raw HTML file
            if not os.path.exists(raw_path):
                print(f"⚠️ File not found: {raw_path}")
                continue
                
            with open(raw_path, "r", encoding="utf-8") as f:
                raw_html = f.read()

            # 2. Clean it
            cleaned_text = parse_and_clean_html(raw_html, url)
            
            # 3. Save to a new 'cleaned' file
            # Generate a unique name or reuse the original filename with a prefix
            original_filename = os.path.basename(raw_path)
            clean_filename = f"clean_{original_filename}.txt" # e.g. clean_raw_a1b2.html.txt
            clean_path = os.path.join(CLEANED_DIR, clean_filename)
            
            with open(clean_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
            
            # 4. Add to results
            cleaned_results.append({
                "url": url,
                "file_store_path": clean_path
            })
            
            print(f"✅ Cleaned: {clean_path}")

        except Exception as e:
            print(f"❌ Error cleaning {url}: {e}")
            # Optionally append the original path or skipped logic here
    
    return cleaned_results