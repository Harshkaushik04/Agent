import os

def write_file(file_path: str, content: str, whether_addition: bool):
    """
    Writes content to a file.
    - If whether_addition is True: Appends content to the existing file.
    - If whether_addition is False: Overwrites the file with new content.
    """
    try:
        # Determine the mode: 'a' for append, 'w' for overwrite
        mode = 'a' if whether_addition else 'w'
        
        # Ensure the directory exists before trying to open the file
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, mode, encoding='utf-8') as f:
            f.write(content)
            
        print(f"Successfully wrote to {file_path}")

    except Exception as e:
        print(f"Error writing to file {file_path}: {e}")