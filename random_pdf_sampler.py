"""
Random PDF Sampler

This script randomly selects up to a specified number of PDF files from a source directory
('body' folder in the current working directory) and its subdirectories. It then copies
the selected files to the current directory, handling filename conflicts by appending
a counter. Optionally, it can delete the original files after copying.

Configuration:
- total_to_get: Maximum number of files to select (default: 30)
- file_extension: File extension to look for (default: ".pdf")
- source_dir: Directory to search for files (default: 'body' in current dir)
- destination_dir: Where to copy files (default: current directory)
"""

import os
import random
import shutil

# Script configuration
total_to_get = 30
file_extension = ".pdf"
root_dir = os.getcwd()
source_dir = os.path.join(root_dir, 'body')
destination_dir = root_dir

# Check if the source directory exists
if not os.path.isdir(source_dir):
    print(f"Error: The directory '{source_dir}' was not found.")
    exit()

print(f"Searching for '{file_extension}' files in '{source_dir}' and its subdirectories...")

# Collect all files with the specified extension from the source directory and subdirs
files_found = []
for dirpath, _, filenames in os.walk(source_dir):
    for filename in filenames:
        if filename.lower().endswith(file_extension):
            full_path = os.path.join(dirpath, filename)
            files_found.append(full_path)

print(f"Found {len(files_found)} files with extension '{file_extension}'.")

# Check the number of files and select them
if not files_found:
    print(f"No {file_extension} files found. The script will exit.")
    exit()

if len(files_found) < total_to_get:
    print(f"Warning: Fewer than {total_to_get} files found. Selecting all {len(files_found)} found files.")
    selected_files = files_found
else:
    print(f"Randomly selecting {total_to_get} {file_extension} files...")
    selected_files = random.sample(files_found, total_to_get)

# Copy the selected files to the destination directory
print(f"\nCopying {len(selected_files)} selected files to '{destination_dir}'...")
for file_path in selected_files:
    filename = os.path.basename(file_path)
    dest_path = os.path.join(destination_dir, filename)

    # If the file already exists, rename it by appending a counter
    if os.path.exists(dest_path):
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            new_filename = f"{base}_{counter}{ext}"
            dest_path = os.path.join(destination_dir, new_filename)
            counter += 1

    shutil.copy(file_path, dest_path)
    print(f"Copied: {file_path} -> {dest_path}")

print(f"\nCompleted! {len(selected_files)} files were copied successfully.")

# Ask if the user wants to delete the original files
delete_originals = input("\nDo you want to delete the original files that were copied? (y/n): ").strip().lower()
if delete_originals in ['y', 'yes']:
    print("Deleting original files...")
    for file_path in selected_files:
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except OSError as e:
            print(f"Error deleting '{file_path}': {e}")
    print("Original files deleted.")

print("Finished.")
input()