import os

MAX_LENGTH = 150


def truncate_filename(filename, max_length=MAX_LENGTH):
    if len(filename) <= max_length:
        return filename
    
    # Find the last space before max_length
    truncated = filename[:max_length]
    last_space = truncated.rfind(' ')
    
    if last_space == -1:
        # No space found, do not truncate to avoid cutting words
        return filename
    
    return filename[:last_space]

def rename_long_files(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if len(filename) > MAX_LENGTH:
                new_filename = truncate_filename(filename)
                old_path = os.path.join(dirpath, filename)
                new_path = os.path.join(dirpath, new_filename)
                
                # Avoid renaming if new name is the same or empty or if file already exists
                if new_filename and new_filename != filename and not os.path.exists(new_path):
                    try:
                        os.rename(old_path, new_path)
                        print(f"Renamed: {old_path} -> {new_path}")
                    except Exception as e:
                        print(f"Error renaming {old_path}: {e}")
                else:
                    print(f"Skipped renaming {old_path}: new name already exists or unchanged")

if __name__ == "__main__":
    root_directory = r"c:\Users\MTPA\OneDrive\Documentos\Educação\POSGR\ESPEC\TIN - Tecnologia da Informação"
    rename_long_files(root_directory)