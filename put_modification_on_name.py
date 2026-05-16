import os
import datetime

def main():
    current_dir = os.getcwd()
    # Get the name of this script so we don't rename it
    script_name = os.path.basename(__file__)
    
    # Iterate over all items in the current directory
    for filename in os.listdir(current_dir):
        # Skip directories and the script itself
        if not os.path.isfile(filename) or filename == script_name:
            continue
            
        # Get the modification time of the file
        mtime = os.path.getmtime(filename)
        
        # Format the modification time to yyyy-mm-dd
        date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
        prefix = f"{date_str} - "
        
        # Check if the filename already starts with the prefix
        if not filename.startswith(prefix):
            new_filename = prefix + filename
            
            # Rename the file
            try:
                os.rename(filename, new_filename)
                print(f'Renamed: "{filename}" -> "{new_filename}"')
            except Exception as e:
                print(f'Error renaming "{filename}": {e}')

if __name__ == "__main__":
    main()