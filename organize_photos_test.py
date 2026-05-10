import os
import shutil
import re

def parse_date(filename):
    """
    Parse the date from the filename using various patterns.
    Returns (year, month) as integers, or (None, None) if not found.
    """
    # Pattern 1: YYYYMMDD (e.g., IMG-20250317-WA0003.jpg, IMG_20250317_150019976.jpg)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if match:
        y, m, d = match.groups()
        year, month = int(y), int(m)
        # Basic validation: year between 2000 and 2030, month 1-12
        if 2000 <= year <= 2030 and 1 <= month <= 12:
            return year, month
    
    # Pattern 2: YYYY-MM-DD (e.g., WhatsApp Image 2026-03-25 at 15.06.20.jpeg)
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', filename)
    if match:
        y, m, d = match.groups()
        year, month = int(y), int(m)
        if 2000 <= year <= 2030 and 1 <= month <= 12:
            return year, month
    
    # If no pattern matches, return None
    return None, None

def organize_files(root_folder, dry_run=True):
    """
    Organize photos and videos in the root folder into subfolders by year and month.
    If dry_run is True, only print what would be done without moving files.
    """
    # Supported extensions for photos and videos
    extensions = ['.jpg', '.jpeg', '.png', '.mp4', '.avi', '.mov', '.webp', '.gif', '.bmp']
    
    for filename in os.listdir(root_folder):
        filepath = os.path.join(root_folder, filename)
        
        # Skip if not a file or not a supported extension
        if not os.path.isfile(filepath):
            continue
        if not any(filename.lower().endswith(ext) for ext in extensions):
            continue
        
        # Parse date
        year, month = parse_date(filename)
        if year is None or month is None:
            print(f"Skipping {filename}: no valid date found")
            continue
        
        # Create destination directory
        dest_dir = os.path.join(root_folder, str(year), f"{month:02d}")
        if not dry_run:
            os.makedirs(dest_dir, exist_ok=True)
        
        # Move the file
        dest_path = os.path.join(dest_dir, filename)
        if os.path.exists(dest_path):
            # If file already exists, append a number to avoid overwrite
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(dest_dir, f"{base}_{counter}{ext}")):
                counter += 1
            dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
        
        if dry_run:
            print(f"Would move {filename} to {dest_path}")
        else:
            shutil.move(filepath, dest_path)
            print(f"Moved {filename} to {dest_path}")

if __name__ == "__main__":
    # Root folder path
    root_folder = r"."
    
    # Run in dry-run mode first
    print("Running in dry-run mode...")
    organize_files(root_folder, dry_run=True)
    print("Dry-run complete.")