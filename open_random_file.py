import os
import random

def open_random_file():
    """Opens a random file from the script's directory or any of its subdirectories."""
    script_path = os.path.abspath(__file__)
    directory = os.path.dirname(script_path)
    
    all_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            all_files.append(full_path)
    
    # Exclude the script itself from the list of files
    if script_path in all_files:
        all_files.remove(script_path)
        
    if not all_files:
        print("No files to open in this directory or its subdirectories.")
        return
        
    random_file_path = random.choice(all_files)
    
    print(f"Opening: {random_file_path}")
    os.startfile(random_file_path)

if __name__ == "__main__":
    open_random_file()
