import os
import shutil

def synchronize_folders(source_folder, destination_folder):
    """
    Synchronizes files from the source folder to the destination folder.
    The modification check is based exclusively on file size.
    Files and folders existing in the destination but not in the source will be deleted.
    """
    # Initialize operation counters
    operations = {
        "folders_created": 0,
        "files_copied": 0,
        "files_updated": 0,
        "files_deleted": 0,
        "folders_deleted": 0,
        "copy_errors": 0,
        "delete_file_errors": 0,
        "delete_folder_errors": 0
    }
    
    # Check if the source folder exists
    if not os.path.exists(source_folder):
        print(f"Error: The source folder '{source_folder}' was not found.")
        return operations

    # Ensure the base destination folder exists
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f"📁 Destination folder created: {destination_folder}")
        operations["folders_created"] += 1

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
            operations["folders_created"] += 1

        # 2. Check the files inside the current folder
        for file in files:
            source_file_path = os.path.join(root, file)
            destination_file_path = os.path.join(current_destination_path, file)

            needs_copying = False
            is_update = False

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
                    is_update = True

            # Perform the copy if the flag was activated
            if needs_copying:
                try:
                    # copy2 attempts to preserve original file metadata (like creation date)
                    shutil.copy2(source_file_path, destination_file_path)
                    if is_update:
                        operations["files_updated"] += 1
                    else:
                        operations["files_copied"] += 1
                except Exception as e:
                    print(f"❌ Error copying file '{file}': {e}")
                    operations["copy_errors"] += 1

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
                    operations["files_deleted"] += 1
                except Exception as e:
                    print(f"❌ Error deleting file '{file}': {e}")
                    operations["delete_file_errors"] += 1
                    
        # Check and delete orphaned directories
        if relative_path != ".":
            if not os.path.exists(current_source_path):
                try:
                    os.rmdir(root)
                    print(f"🗑️ Deleted subfolder not in source: {relative_path}")
                    operations["folders_deleted"] += 1
                except Exception as e:
                    print(f"❌ Error deleting subfolder '{relative_path}': {e}")
                    operations["delete_folder_errors"] += 1

    print("\n✅ Synchronization complete!")
    return operations

# ==========================================
# Usage example:
# ==========================================
if __name__ == "__main__":
    # Define the paths to your folders here (you can use absolute or relative paths)
    source = os.environ.get("MIRROR_FOLDERS_SOURCE", "./my_source_folder")
    destination = os.environ.get("MIRROR_FOLDERS_DESTINATION", "./my_destination_folder")
    
    operations = synchronize_folders(source, destination)
    
    # Print summary of operations
    print("\n" + "="*50)
    print("📊 OPERATION SUMMARY")
    print("="*50)
    print(f"📁 Folders created:        {operations['folders_created']}")
    print(f"📄 Files copied:           {operations['files_copied']}")
    print(f"🔄 Files updated:          {operations['files_updated']}")
    print(f"🗑️  Files deleted:          {operations['files_deleted']}")
    print(f"🗑️  Folders deleted:        {operations['folders_deleted']}")
    print(f"❌ Copy errors:            {operations['copy_errors']}")
    print(f"❌ File delete errors:     {operations['delete_file_errors']}")
    print(f"❌ Folder delete errors:   {operations['delete_folder_errors']}")
    print("="*50)
    
    # Wait for user input before exit
    input("\nPress Enter to exit...")