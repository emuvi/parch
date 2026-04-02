"""
Random File Opener

This script selects and opens a random file from the current directory and all its
subdirectories using the system's default application. It excludes the script file
itself from selection.

Note: This script is designed for Windows systems, as it uses os.startfile().
"""

import os
import random

def open_random_file():
    """
    Opens a random file from the script's directory and its subdirectories.

    The function walks through the directory tree starting from the script's location,
    collects all files (excluding the script itself), and randomly selects one to open
    with the default system application.

    If no files are found, it prints a message and returns without action.
    """
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
