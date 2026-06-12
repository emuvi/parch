import re
from pathlib import Path

def format_filename(filename: str) -> str:
    """
    Formats a filename according to the specified rules:
    1. Inserts a hyphen between a lowercase letter and an uppercase letter.
    2. Removes all spaces.
    3. Converts the name (excluding extension) to uppercase.
    """
    path = Path(filename)
    name = path.stem    # The file name without the extension
    ext = path.suffix   # The file extension 

    # Step 1: Insert '-' between a lowercase letter and an uppercase letter
    name = re.sub(r'([a-z])([A-Z])', r'\1-\2', name)

    # Step 2: Remove all empty spaces
    name = name.replace(" ", "")

    # Step 3: Convert all letters to uppercase
    name = name.upper()

    # Return the newly assembled name
    return f"{name}{ext}"

def rename_files_in_directory(directory: str = '.'):
    """
    Iterates through all files in the target directory and renames them.
    Includes a temporary rename step to bypass OS case-insensitivity bugs.
    """
    target_dir = Path(directory)
    current_script = Path(__file__).name

    print(f"Scanning directory: {target_dir.absolute()}\n")

    for file_path in target_dir.iterdir():
        # Only process files, skip directories and this script
        if file_path.is_file() and file_path.name != current_script:
            
            new_name = format_filename(file_path.name)
            new_file_path = file_path.with_name(new_name)

            # Check if the name actually needs to change
            if file_path.name != new_name:
                
                # OS Case-Insensitivity Fix: 
                # If the only difference is uppercase/lowercase, use a temp file
                if file_path.name.lower() == new_name.lower():
                    temp_path = file_path.with_name(file_path.name + ".tmp")
                    file_path.rename(temp_path)       # Rename to temp
                    temp_path.rename(new_file_path)   # Rename to final uppercase
                else:
                    # If it's a completely different name, rename normally
                    file_path.rename(new_file_path)

                print(f"Renamed: '{file_path.name}' -> '{new_name}'")

if __name__ == "__main__":
    rename_files_in_directory()
    print("\nRenaming process complete.")