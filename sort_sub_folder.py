import os
import random
import subprocess
import platform

def get_all_sub_folders(path):
    all_sub_folders = []
    for dirpath, dirnames, filenames in os.walk(path):
        for dirname in dirnames:
            all_sub_folders.append(os.path.join(dirpath, dirname))
    return all_sub_folders

def open_folder_in_explorer(folder_path):
    if platform.system() == "Windows":
        subprocess.run(["explorer", folder_path])
    elif platform.system() == "Darwin":  # macOS
        subprocess.run(["open", folder_path])
    else:
        subprocess.run(["xdg-open", folder_path])

def main():
    current_directory = os.getcwd()
    sub_folders = get_all_sub_folders(current_directory)

    if not sub_folders:
        print("No sub folders found in current directory.")
        return

    print(f"Sub folders found: ({len(sub_folders)}):")

    folders_to_choose_from = list(sub_folders)

    while True:
        if not folders_to_choose_from:
            print("All folders have already been suggested. Exiting the script.")
            break

        random_folder = random.choice(folders_to_choose_from)
        print("\n---")
        user_choice = input(f"Sub folder sorted: '{random_folder}'. Do you want to open it? (*/n):").lower()

        if user_choice != 'n':
            full_path = os.path.join(current_directory, random_folder)
            print(f"Opening the folder: {full_path}")
            open_folder_in_explorer(full_path)
            break
        else:
            print("Ok. Drawing another folder...")
            folders_to_choose_from.remove(random_folder)

if __name__ == "__main__":
    main()