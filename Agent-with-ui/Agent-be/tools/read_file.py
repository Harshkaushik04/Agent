import os

def read_file(file_path: str) -> str:
    """
    Reads the content of a file and returns it as a string.
    Returns an error message if the file does not exist.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content

    except Exception as e:
        print(f"Error reading file {file_path}: {e}")