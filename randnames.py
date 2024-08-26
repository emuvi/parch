import os
import random
import string

def get_random_name(length=12):
    """Generate a random string of numbers of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def rename_files_in_directory():
    current_dir = os.getcwd()
    script_name = os.path.basename(__file__)

    for filename in os.listdir(current_dir):
        if filename == script_name:
            # Skip renaming the script itself
            continue

        file_path = os.path.join(current_dir, filename)

        if os.path.isfile(file_path):
            file_extension = os.path.splitext(filename)[1]  # Get the file extension
            new_name = get_random_name() + file_extension
            new_file_path = os.path.join(current_dir, new_name)
            
            os.rename(file_path, new_file_path)
            print(f'Renamed: {filename} -> {new_name}')

def main():
    proceed = input("Do you want to proceed with renaming files in the current directory? (yes/no): ").strip().lower()
    if proceed == 'yes':
        rename_files_in_directory()
        print("Renaming completed.")
    else:
        print("Operation canceled.")

if __name__ == "__main__":
    main()