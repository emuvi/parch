#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to rename all files by prefixing them with numbers extracted from their parent folder names.

It recursively scans a specified root directory. For each file, it traverses its path
up to the root, looking for numbers enclosed in parentheses, e.g., "(01)", "(02)".
It extracts these numbers and prefixes the file's name with them, separated by underscores.

Example:
    Path: Root / (01) Module / (04) Topic / file.txt
    Resulting filename: 01_04_file.txt
"""

import os
import re
from pathlib import Path

def extract_numbers_from_path(file_path, root_path):
    """
    Extract numbers enclosed in parentheses from all folder names in the file's path.
    
    Traverses the directory hierarchy from the file's parent directory up to the 
    specified root path. It looks for patterns like '(XX)' in each directory name 
    and collects the extracted numbers in top-down order (root to leaf).
    
    Args:
        file_path (Path): The complete Path object of the target file.
        root_path (str or Path): The root directory where the traversal should stop.
        
    Returns:
        list of str: A list of extracted numbers as strings.
    """
    numbers = []
    
    # Get the full path and normalize it
    full_path = file_path.parent
    root = Path(root_path)
    
    # Build the complete path from root to the file's directory
    current = full_path
    path_parts = []
    
    # Traverse from file location up to root
    while current != current.parent:
        path_parts.insert(0, current.name)
        if current == root:
            break
        current = current.parent
    
    # Extract numbers from all folder names in order
    for part in path_parts:
        # Find all occurrences of (XX) pattern in each folder name
        matches = re.findall(r'\((\d+)\)', part)
        numbers.extend(matches)
    
    return numbers

def main():
    """
    Main execution function.
    
    Sets the target root directory, recursively finds all files within it, 
    and applies the renaming logic based on the extracted folder numbers.
    It checks if files are already prefixed to avoid duplicate prefixing,
    and prints a summary of the operations performed to the console.
    """
    root_path = os.path.dirname(os.path.abspath(__file__))
    
    # Get all files recursively
    files = list(Path(root_path).rglob('*'))
    files = [f for f in files if f.is_file()]
    
    total_files = len(files)
    renamed_count = 0
    
    print("Starting file rename operation...")
    print(f"Total files found: {total_files}")
    print()
    
    for file_path in files:
        # Get the relative path from root
        try:
            relative_path = file_path.relative_to(root_path).as_posix()
        except ValueError:
            continue
        
        # Extract all numbers from the complete path hierarchy
        numbers = extract_numbers_from_path(file_path, root_path)
        
        # Create prefix from extracted numbers
        prefix = "_".join(numbers) if numbers else ""
        
        # Get the current filename
        current_filename = file_path.name
        
        # Check if file already has the prefix (to avoid re-prefixing)
        if prefix and not current_filename.startswith(prefix + "_"):
            # Create new filename with prefix
            new_filename = f"{prefix}_{current_filename}"
            new_path = file_path.parent / new_filename
            
            # Rename the file
            try:
                file_path.rename(new_path)
                print(f"[✓] Renamed: {current_filename} -> {new_filename}")
                renamed_count += 1
            except Exception as e:
                print(f"[✗] Error renaming {current_filename}: {e}")
        elif not prefix:
            print(f"[⊘] No prefix found for: {current_filename}")
        else:
            print(f"[⊘] Already prefixed: {current_filename}")
    
    print()
    print("===================================")
    print("Operation completed!")
    print(f"Files renamed: {renamed_count} / {total_files}")
    print("===================================")

if __name__ == "__main__":
    main()
