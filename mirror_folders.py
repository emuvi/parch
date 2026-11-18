import os
import shutil
import stat
import sys
import time


def _windows_long_path(path):
    path = os.path.abspath(path)
    if os.name != "nt" or path.startswith("\\\\?\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path[2:]
    return "\\\\?\\" + path


def _is_link_or_junction(path):
    return os.path.islink(path) or (
        hasattr(os.path, "isjunction") and os.path.isjunction(path)
    )


def _source_exists(path):
    try:
        os.lstat(path)
        return True
    except FileNotFoundError:
        return False


def _remove(path, directory=False, attempts=3):
    """Remove one file or empty directory, retrying transient access failures."""
    action = os.rmdir if directory else os.remove
    for attempt in range(attempts):
        try:
            action(path)
            return
        except PermissionError:
            if not directory and not _is_link_or_junction(path):
                mode = os.stat(path).st_mode
                if not mode & stat.S_IWRITE:
                    os.chmod(path, mode | stat.S_IWRITE)
            if attempt == attempts - 1:
                raise
            time.sleep(0.5)


def synchronize_folders(source_folder, destination_folder):
    """Mirror the source, comparing existing files by size before copying."""
    print("\n🔄 Starting synchronization")
    print(f"Source folder:      {source_folder}")
    print(f"Destination folder: {destination_folder}\n")

    operations = {
        "folders_created": 0,
        "files_copied": 0,
        "files_updated": 0,
        "files_deleted": 0,
        "folders_deleted": 0,
        "copy_errors": 0,
        "delete_file_errors": 0,
        "delete_folder_errors": 0,
        "scan_errors": 0,
    }

    source = _windows_long_path(source_folder)
    destination = _windows_long_path(destination_folder)
    source_real = os.path.normcase(os.path.realpath(source))
    destination_real = os.path.normcase(os.path.realpath(destination))
    try:
        common = os.path.commonpath((source_real, destination_real))
    except ValueError:
        common = None
    if common in (source_real, destination_real):
        raise ValueError("Source and destination must be separate, non-overlapping folders.")
    if not stat.S_ISDIR(os.stat(source).st_mode):
        raise NotADirectoryError(f"Source is not a directory: {source_folder}")

    if not os.path.exists(destination):
        os.makedirs(destination)
        print(f"📁 Destination folder created: {destination_folder}")
        operations["folders_created"] += 1

    def scan_error(error):
        print(f"❌ Error scanning folder: {error}")
        operations["scan_errors"] += 1

    for root, dirs, files in os.walk(source, onerror=scan_error):
        for name in dirs[:]:
            path = os.path.join(root, name)
            if _is_link_or_junction(path):
                dirs.remove(name)
                print(f"❌ Skipping source directory link or junction: {path}")
                operations["scan_errors"] += 1
        relative_path = os.path.relpath(root, source)
        target = destination if relative_path == "." else os.path.join(destination, relative_path)
        try:
            if _is_link_or_junction(target):
                raise OSError(f"Destination is a directory link or junction: {target}")
            if not os.path.exists(target):
                os.makedirs(target)
                print(f"📁 Subfolder created: {target}")
                operations["folders_created"] += 1
        except OSError as error:
            print(f"❌ Error creating folder '{target}': {error}")
            operations["copy_errors"] += 1
            dirs.clear()
            continue

        for name in files:
            source_file = os.path.join(root, name)
            target_file = os.path.join(target, name)
            try:
                if _is_link_or_junction(target_file):
                    raise OSError(f"Destination is a link: {target_file}")
                is_update = _source_exists(target_file)
                if is_update and not os.path.isfile(target_file):
                    raise OSError(f"Destination is not a regular file: {target_file}")
                if not is_update or os.path.getsize(source_file) != os.path.getsize(target_file):
                    shutil.copy2(source_file, target_file)
                    key = "files_updated" if is_update else "files_copied"
                    operations[key] += 1
                    print(f"📄 {'Updated' if is_update else 'Copied'} file: {target_file}")
            except OSError as error:
                print(f"❌ Error copying file '{source_file}' to '{target_file}': {error}")
                operations["copy_errors"] += 1

    if operations["scan_errors"] or operations["copy_errors"]:
        print("❌ Destination cleanup skipped because the source could not be fully synchronized.")
        return operations

    # Keep directory links out of the traversal; do not delete through junctions.
    visited = []
    for root, dirs, files in os.walk(destination, topdown=True, onerror=scan_error):
        for name in dirs[:]:
            path = os.path.join(root, name)
            if _is_link_or_junction(path):
                dirs.remove(name)
                print(f"❌ Skipping destination directory link or junction: {path}")
                operations["scan_errors"] += 1
        visited.append((root, files))

    if operations["scan_errors"]:
        print("❌ Destination cleanup skipped because the destination could not be fully scanned.")
        return operations

    for root, files in reversed(visited):
        relative_path = os.path.relpath(root, destination)
        source_root = source if relative_path == "." else os.path.join(source, relative_path)
        try:
            if not stat.S_ISDIR(os.stat(source).st_mode):
                raise NotADirectoryError(f"Source is no longer a directory: {source}")
            for name in files:
                source_file = os.path.join(source_root, name)
                target_file = os.path.join(root, name)
                try:
                    if not _source_exists(source_file):
                        _remove(target_file)
                        operations["files_deleted"] += 1
                        print(f"🗑️ Deleted file not in source: {target_file}")
                except OSError as error:
                    print(f"❌ Error checking or deleting file '{target_file}': {error}")
                    operations["delete_file_errors"] += 1

            if relative_path != "." and not _source_exists(source_root):
                try:
                    _remove(root, directory=True)
                    operations["folders_deleted"] += 1
                    print(f"🗑️ Deleted subfolder not in source: {relative_path}")
                except OSError as error:
                    print(f"❌ Error deleting subfolder '{root}': {error}")
                    operations["delete_folder_errors"] += 1
        except OSError as error:
            print(f"❌ Error checking source folder '{source_root}': {error}")
            operations["scan_errors"] += 1
            break

    if any(operations[key] for key in
           ("copy_errors", "delete_file_errors", "delete_folder_errors", "scan_errors")):
        print("\n❌ Synchronization finished with errors.")
    else:
        print("\n✅ Synchronization complete!")
    return operations


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    source = os.environ.get("MIRROR_FOLDERS_SOURCE", "./my_source_folder")
    destination = os.environ.get("MIRROR_FOLDERS_DESTINATION", "./my_destination_folder")
    try:
        operations = synchronize_folders(source, destination)
    except (OSError, ValueError) as error:
        print(f"❌ Synchronization failed: {error}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 50)
    print("📊 OPERATION SUMMARY")
    print("=" * 50)
    print(f"Source folder:      {source}")
    print(f"Destination folder: {destination}")
    print("=" * 50)
    for key, value in operations.items():
        print(f"{key.replace('_', ' ').capitalize():25} {value}")
    print("=" * 50)

    failed = any(operations[key] for key in
                 ("copy_errors", "delete_file_errors", "delete_folder_errors", "scan_errors"))
    if sys.stdin.isatty():
        input("\nPress Enter to exit...")
    sys.exit(1 if failed else 0)
