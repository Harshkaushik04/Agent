import os
import uuid

def file_checker(file_path: str) -> str:
    """
    Checks if a file path exists. 
    If it exists, appends a random unique suffix to create a new path 
    instantly, avoiding slow sequential loops.
    """
    # 1. If the file doesn't exist, return the original path immediately
    if not os.path.exists(file_path):
        return file_path

    # 2. Split the path components
    directory, filename = os.path.split(file_path)
    name, extension = os.path.splitext(filename)

    # 3. Generate a random unique path
    while True:
        # Generate a short 8-char random string (e.g., "a1b2c3d4")
        random_suffix = uuid.uuid4().hex[:8]
        
        new_filename = f"{name}_{random_suffix}{extension}"
        new_file_path = os.path.join(directory, new_filename)
        
        # This will almost always be False on the first try
        if not os.path.exists(new_file_path):
            return new_file_path