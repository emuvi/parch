import os

def rename_all_files(folder, starts_with, rename_for):
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        return

    print(f"Starting file rename operation in: '{os.path.abspath(folder)}'")
    
    renamed_count = 0
    errors = []
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.startswith(starts_with):
                new_filename = rename_for + filename[len(starts_with):]
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: '{old_path}' -> '{new_path}'")
                    renamed_count += 1
                except Exception as e:
                    errors.append(f"P: {old_path}\nE: {e}")
        
    print("-" * 50)
    print(f"File renaming complete. Renamed {renamed_count} file(s).")
    if (len(errors) > 0):
        print("-" * 50)
        print("Erros:")
        for error in errors:
            print(error)
    
    

if __name__ == "__main__":
    rename_all_files(".", "Stk ", "+ ")
    input()
