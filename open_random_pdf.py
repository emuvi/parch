"""
Random PDF Opener

This script selects and opens a random PDF file from the current directory and all its
subdirectories using the system's default application.

Note: This script is designed for Windows systems, as it uses os.startfile().
"""

import os
import random

def open_random_pdf():
    """
    Opens a random PDF file from the script's directory and its subdirectories.

    The function walks through the directory tree starting from the script's location,
    collects all PDF files (excluding the script itself if it's a PDF), and randomly
    selects one to open with the default system application.

    If no PDF files are found, it prints a message and returns without action.
    """
    script_path = os.path.abspath(__file__)
    directory = os.path.dirname(script_path)

    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdf_files.append(full_path)

    # Exclude the script itself if it's a PDF (unlikely, but safe)
    if script_path in pdf_files:
        pdf_files.remove(script_path)

    if not pdf_files:
        print("No PDF files found in this directory or its subdirectories.")
        return

    random_pdf_path = random.choice(pdf_files)

    print(f"Opening: {random_pdf_path}")
    os.startfile(random_pdf_path)

if __name__ == "__main__":
    open_random_pdf()