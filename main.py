import os
import eel
import itertools
from enum import Enum
import subprocess
import send2trash
import json


# Enum for path-related operations
class PathStatus(Enum):
    SUCCESSFUL = 1
    DEST_NOT_CLEAR = 2
    DEST_NOT_EXIST = 3
    FILE_ALREADY_EXISTS = 4
    ERROR = 5
    DEST_CLEAR = 6


# Global variables
inventory_directory = ""
root_path = ""
tags = []
PATHS_FILE = "paths.json"


# ------------------------
# Path Management Functions
# ------------------------

def load_paths_from_file():
    """
    Load inventory and root paths from the paths file if it exists.
    """
    global inventory_directory, root_path

    if os.path.exists(PATHS_FILE):
        print("Loading paths from file...")
        try:
            with open(PATHS_FILE, "r") as file:
                paths = json.load(file)
                inventory_directory = paths.get("inventory_path", "")
                root_path = paths.get("root_path", "")
                print(f"Loaded paths: Inventory -> {inventory_directory}, Root -> {root_path}")
        except Exception as e:
            print(f"Error reading paths file: {e}")

def save_paths_to_file(inventory_path, root_path):
    """
    Save inventory and root paths to the paths file.

    Args:
        inventory_path (str): Path to the inventory directory.
        root_path (str): Path to the root directory.
    """
    paths = {
        "inventory_path": inventory_path,
        "root_path": root_path
    }
    try:
        with open(PATHS_FILE, "w") as file:
            json.dump(paths, file)
    except Exception as e:
        print(f"Error writing to paths file: {e}")


def set_inventory_path(path):
    """
    Set the inventory directory path if it exists.

    Args:
        path (str): Path to set as the inventory directory.

    Returns:
        dict: Dictionary with the inventory path set.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified inventory path does not exist: {path}")

    global inventory_directory
    inventory_directory = path
    return {"inventory_path": inventory_directory}


def set_root_path(path):
    """
    Set the root directory path if it exists and update tags.

    Args:
        path (str): Path to set as the root directory.

    Returns:
        dict: Dictionary with the root path set.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"The specified root path does not exist: {path}")

    global root_path, tags
    root_path = path
    tags = collect_all_tags()
    return {"root_path": root_path}


# ------------------------
# Eel Exposed Functions
# ------------------------

@eel.expose
def go_one_dir_back(current_dir):
    """
    Move one directory back, ensuring it doesn't go beyond the inventory directory.

    Args:
        current_dir (str): Current directory path.

    Returns:
        str: Parent directory path or inventory directory.
    """
    if os.path.commonpath([current_dir, inventory_directory]) != inventory_directory:
        return inventory_directory

    parent_dir = os.path.dirname(current_dir)

    if os.path.commonpath([parent_dir, inventory_directory]) != inventory_directory:
        return inventory_directory

    return parent_dir


@eel.expose
def set_paths_with_feedback(inventory_path, root_path):
    """
    Set both inventory and root paths with feedback and error handling.

    Args:
        inventory_path (str): Path to set as inventory directory.
        root_path (str): Path to set as root directory.

    Returns:
        dict: Dictionary with success status and messages for each path.
    """
    response = {"success": True, "messages": []}

    try:
        inventory_result = set_inventory_path(inventory_path)
        response["messages"].append(f"Inventory path set successfully: {inventory_result['inventory_path']}")
    except FileNotFoundError as e:
        response["success"] = False
        response["messages"].append(str(e))
    except Exception as e:
        response["success"] = False
        response["messages"].append(f"Unexpected error with inventory path: {str(e)}")

    try:
        root_result = set_root_path(root_path)
        response["messages"].append(f"Root path set successfully: {root_result['root_path']}")
    except FileNotFoundError as e:
        response["success"] = False
        response["messages"].append(str(e))
    except Exception as e:
        response["success"] = False
        response["messages"].append(f"Unexpected error with root path: {str(e)}")

    if response["success"]:
        save_paths_to_file(inventory_directory, root_path)

    return response


@eel.expose
def get_inventory_path():
    """
    Get the inventory directory path.

    Returns:
        str: Inventory directory path.
    """
    return inventory_directory


@eel.expose
def get_root_path():
    """
    Get the root directory path.

    Returns:
        str: Root directory path.
    """
    return root_path

@eel.expose
def get_path_status_message(status_name):
    """
    Returns a custom message for a given PathStatus name.

    Args:
        status_name (str): The name of the PathStatus (e.g., 'SUCCESSFUL', 'DEST_NOT_EXIST').

    Returns:
        str: A custom message corresponding to the PathStatus name.
    """
    messages = {
        "SUCCESSFUL": "Successfully moved to: ",
        "DEST_NOT_CLEAR": "The destination is ambiguous or not clearly defined. Please refine your tag selection or selected 'new'.",
        "DEST_NOT_EXIST": "The specified destination does not exist. Would you like to create it? Select 'new'",
        "FILE_ALREADY_EXISTS": "A file with the same name already exists at the destination. Change the name to proceed!",
        "ERROR": "An unexpected error occurred.",
        "DEST_CLEAR": "The destination is clear and ready for the operation.",
    }

    return messages.get(status_name, "Unknown status. Please check the input.")

# ------------------------
# Tag Management Functions
# ------------------------

@eel.expose
def collect_all_tags():
    """
    Collect all tags (directory names) in the root directory.

    Returns:
        list: List of all collected tags.
    """
    global tags
    tags = {os.path.basename(dirpath) for dirpath, _, _ in os.walk(root_path)}
    return list(tags)


@eel.expose
def recommend_tags(input_string):
    """
    Recommend tags based on input string.

    Args:
        input_string (str): Input string to match tags.

    Returns:
        list: List of matching tags.
    """
    return [tag for tag in tags if input_string.lower() in tag.lower()]


@eel.expose
def get_files(directory=None):
    """
    Retrieve a list of files and directories in the specified directory.

    Args:
        directory (str, optional): Directory to list files from. Defaults to the inventory directory.

    Returns:
        list: List of dictionaries containing file or directory details.
    """
    try:
        target_directory = directory if directory else inventory_directory
        if not os.path.exists(target_directory):
            raise FileNotFoundError(f"Directory not found: {target_directory}")
        
        # Filter visible (non-hidden) files and directories
        visible_files = [
            filename for filename in os.listdir(target_directory)
            if not filename.startswith(".")  # Exclude hidden files
        ]

        return [
            {
                "name": filename,
                "type": "file" if os.path.isfile(os.path.join(target_directory, filename)) else "directory",
                "path": os.path.join(target_directory, filename)
            }
            for filename in visible_files
        ]
    except Exception as e:
        print(f"Error: {e}")
        return []


@eel.expose
def open_file(filename):
    """
    Open a file in the default system application.

    Args:
        filename (str): Name of the file to open.

    Returns:
        str: Status message indicating success or failure.
    """
    file_path = os.path.join(inventory_directory, filename)
    if not os.path.isfile(file_path):
        return f"File does not exist: {filename}"

    try:
        if os.name == 'posix':
            subprocess.call(('open', file_path))
        elif os.name == 'nt':
            os.startfile(file_path)
        return f"Opened file: {filename}"
    except Exception as e:
        return f"Error opening file: {e}"

@eel.expose
def find_possible_paths(tag_list):
    """
    Find all directory paths matching the provided list of tags.

    Args:
        tag_list (list): List of tags to search for.

    Returns:
        list: List of matching directory paths.
    """
    matching_paths = []
    for dirpath, _, _ in os.walk(root_path):
        if all(tag in dirpath for tag in tag_list) and os.path.basename(dirpath) in tag_list:
            matching_paths.append(dirpath)
    return matching_paths


@eel.expose
def check_path(tag_list):
    """
    Check the status of a path based on provided tags.

    Args:
        tag_list (list): List of tags to check for a valid path.

    Returns:
        tuple: Path status (str) and associated path (if any).
    """
    if not tag_list:
        return PathStatus.DEST_NOT_CLEAR.name, ""

    possible_paths = find_possible_paths(tag_list)
    if not possible_paths:
        return PathStatus.DEST_NOT_EXIST.name, ""
    if len(possible_paths) > 1:
        return PathStatus.DEST_NOT_CLEAR.name, ""
    return PathStatus.DEST_CLEAR.name, possible_paths[0]


@eel.expose
def move_file(new_name, file_name, tags, create_new=False, intelligent=False):
    """
    Move a file to a destination directory based on tags.

    Args:
        new_name (str): New name for the file.
        file_name (str): Current file name.
        tags (list): Tags to determine the destination directory.
        create_new (bool): Whether to create a new path if none exists.
        intelligent (bool): Enable intelligent path creation.

    Returns:
        tuple: Path status and destination directory path.
    """
    if not tags:
        return PathStatus.DEST_NOT_CLEAR.name, ""

    if not create_new:
        status, destination_directory = check_path(tags)
        if status != PathStatus.DEST_CLEAR.name:
            return status, ""
    else:
        destination_directory = create_new_path(tags, intelligent)

    return _move_file_to_destination(new_name, file_name, destination_directory), destination_directory

@eel.expose
def move_to_trash(file_path):
    """
    Move a file to the trash.

    Args:
        file_path (str): Path to the file to move to trash.

    Returns:
        tuple: Path status and status message.
    """
    if not os.path.exists(file_path):
        return PathStatus.ERROR.name, f"File not found: {file_path}"

    try:
        send2trash.send2trash(file_path)
        return PathStatus.SUCCESSFUL.name, f"File successfully moved to trash: {file_path}"
    except Exception as e:
        return PathStatus.ERROR.name, f"An error occurred: {e}"


@eel.expose
def create_new_path(tag_list, intelligent=False):
    """
    Create a new path based on tags, optionally using intelligent path creation.

    Args:
        tag_list (list): List of tags for the new path.
        intelligent (bool): Whether to use intelligent path creation.

    Returns:
        str: The newly created directory path.
    """
    if intelligent and check_path(tag_list)[0] != PathStatus.DEST_CLEAR.name:
        subsets = _create_all_subsets(tag_list)
        for subset in subsets:
            possible_paths = find_possible_paths(list(subset))
            if possible_paths:
                base_path = min(possible_paths, key=len)
                return _create_new_directory(base_path, [tag for tag in tag_list if tag not in subset])
    return _create_new_directory(root_path, tag_list)


def _move_file_to_destination(new_name, file_path, destination_directory):
    """
    Internal function to move a file to a destination directory.

    Args:
        new_name (str): New name for the file.
        file_path (str): Current file path.
        destination_directory (str): Destination directory path.

    Returns:
        str: Path status indicating success or failure.
    """
    source_file = file_path
    destination_file = os.path.join(destination_directory, new_name)
    if os.path.exists(destination_file):
        return PathStatus.FILE_ALREADY_EXISTS.name

    try:
        os.rename(source_file, destination_file)
        return PathStatus.SUCCESSFUL.name
    except Exception as e:
        print(f"Error moving file: {e}")
        return PathStatus.ERROR.name


def _create_new_directory(base_directory, tag_list):
    """
    Internal function to create a new directory based on tags.

    Args:
        base_directory (str): Base directory path.
        tag_list (list): List of tags for the new directory.

    Returns:
        str: The path of the newly created directory.
    """
    new_path = os.path.join(base_directory, *tag_list)
    os.makedirs(new_path, exist_ok=True)
    return new_path


def _create_all_subsets(tag_list):
    """
    Create all subsets of a given tag list.

    Args:
        tag_list (list): List of tags.

    Returns:
        list: List of subsets sorted by length in descending order.
    """
    subsets = [set(combo) for i in range(len(tag_list) + 1) for combo in itertools.combinations(tag_list, i)]
    return sorted(subsets, key=len, reverse=True)


# ------------------------
# Initialization
# ------------------------

load_paths_from_file()
tags = collect_all_tags()
eel.init('web')
eel.start("index.html", size=(1000, 750), mode="default")
