import os
import shutil

def synchronize_folders(source_folder, destination_folder):
    """
    Synchronizes files from the source folder to the destination folder.
    The modification check is based exclusively on file size.
    Files and folders existing in the destination but not in the source will be deleted.
    """
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        print(f"Error: The source folder '{source_folder}' was not found.")
        return

    # Ensure the base destination folder exists
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f"📁 Destination folder created: {destination_folder}")

    # Walk through the entire directory tree of the source folder
    for root, dirs, files in os.walk(source_folder):
        # Calculate the relative path of the current folder concerning the source folder
        relative_path = os.path.relpath(root, source_folder)
        
        # Determine the corresponding path in the destination
        current_destination_path = os.path.join(destination_folder, relative_path)

        # 1. Check and create non-existent subfolders
        if not os.path.exists(current_destination_path):
            os.makedirs(current_destination_path)
            print(f"📁 Subfolder created: {current_destination_path}")

        # 2. Check the files inside the current folder
        for file in files:
            source_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(current_destination_path, file)

            needs_copying = False

            # If the file does not exist in the destination
            if not os.path.exists(destination_file_path):
                print(f"📄 File does not exist in destination. Copying: {file}")
                needs_copying = True
            else:
                # If it exists, check for modification based on size
                source_size = os.path.getsize(source_file_path)
                destination_size = os.path.getsize(destination_file_path)

                if source_size != destination_size:
                    print(f"🔄 File modified (different size). Updating: {file}")
                    needs_copying = True

            # Perform the copy if the flag was activated
            if needs_copying:
                try:
                    # copy2 attempts to preserve original file metadata (like creation date)
                    shutil.copy2(source_file_path, destination_file_path)
                except Exception as e:
                    print(f"❌ Error copying file '{file}': {e}")

    # 3. Clean up destination (remove files and folders not in source)
    for root, dirs, files in os.walk(destination_folder, topdown=False):
        relative_path = os.path.relpath(root, destination_folder)
        current_source_path = os.path.join(source_folder, relative_path)

        # Check and delete orphaned files
        for file in files:
            destination_file_path = os.path.join(root, file)
            source_file_path = os.path.join(current_source_path, file)
            
            if not os.path.exists(source_file_path):
                try:
                    os.remove(destination_file_path)
                    print(f"🗑️ Deleted file not in source: {file}")
                except Exception as e:
                    print(f"❌ Error deleting file '{file}': {e}")
                    
        # Check and delete orphaned directories
        if relative_path != ".":
            if not os.path.exists(current_source_path):
                try:
                    os.rmdir(root)
                    print(f"🗑️ Deleted subfolder not in source: {relative_path}")
                except Exception as e:
                    print(f"❌ Error deleting subfolder '{relative_path}': {e}")

    print("\n✅ Synchronization complete!")

# ==========================================
# Usage example:
# ==========================================
if __name__ == "__main__":
    # Define the paths to your folders here (you can use absolute or relative paths)
    source = "./my_source_folder"
    destination = "./my_destination_folder"
    
    synchronize_folders(source, destination)