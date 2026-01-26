import os
import uuid
import datetime

# Ensure directory for merged files exists
MERGED_DIR = "/home/harsh/RAG/Agent-with-ui/Agent-be/downloads/merged_files"
if not os.path.exists(MERGED_DIR):
    os.makedirs(MERGED_DIR)

def merge_files(file_paths: list[str]) -> str:
    """
    Reads multiple files and merges their content into a single new file.
    Returns the path of the newly created merged file.
    """
    try:
        # Generate a unique filename for the merged result
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:6]
        merged_filename = f"merged_{timestamp}_{unique_id}.txt"
        merged_file_path = os.path.join(MERGED_DIR, merged_filename)

        with open(merged_file_path, 'w', encoding='utf-8') as outfile:
            for path in file_paths:
                # Skip if file doesn't exist
                if not os.path.exists(path):
                    print(f"Warning: Skipping missing file: {path}")
                    outfile.write(f"\n\n--- [MISSING FILE: {path}] ---\n\n")
                    continue
                
                try:
                    with open(path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        # Add a clear separator so the AI knows where one doc ends and another starts
                        outfile.write(f"\n\n{'='*20}\n")
                        outfile.write(f"--- START OF FILE: {os.path.basename(path)} ---\n")
                        outfile.write(f"{'='*20}\n\n")
                        outfile.write(content)
                        outfile.write(f"\n\n--- END OF FILE: {os.path.basename(path)} ---\n")
                except Exception as read_err:
                    print(f"Error reading {path}: {read_err}")
                    outfile.write(f"\n\n--- [ERROR READING FILE: {path}] ---\n\n")

        print(f"✅ Merged {len(file_paths)} files into: {merged_file_path}")
        return merged_file_path

    except Exception as e:
        print(f"Critical error merging files: {e}")
        return ""