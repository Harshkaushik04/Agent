from bs4 import BeautifulSoup

def parse_and_clean_html(html, url):
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted tags
    for tag in soup(['script', 'style', 'noscript', 'iframe', 'link', 'svg', 'footer', 'nav', 'header', 'aside', 'form', 'button']):
        tag.decompose()

    text_content = []
    # Find relevant text elements
    targets = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'article'])
    
    for el in targets:
        text = el.get_text(separator=' ', strip=True)
        if len(text) > 40:
            text_content.append(text)

    # Remove duplicates while preserving order
    seen = set()
    unique_content = [x for x in text_content if not (x in seen or seen.add(x))]
    
    return f"\n--- SOURCE: {url} ---\n" + "\n".join(unique_content)

def html_cleaner(raw_html,url):
    return parse_and_clean_html(raw_html,url)