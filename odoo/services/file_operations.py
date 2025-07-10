import json
import os
import shutil
from typing import List, Tuple, Dict


def compare_files(file1: str, file2: str) -> bool:
    """
    Compare two files and return True if they are the same, False otherwise.
    :param file1: The first file to compare
    :param file2: The second file to compare
    :return: bool: True if the files are the same, False otherwise
    """

    # Compare byte size first
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    # If the byte size is the same, compare content
    else:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            while True:
                data1 = f1.read(1024)
                data2 = f2.read(1024)
                if not data1 or not data2:
                    break
                if data1 != data2:
                    return False

    return True


def replace_cache_file(env_file: str, cache_env_file: str) -> None:
    """
    Replace the cache file with the current environment file.
    :param env_file: Original .env file
    :param cache_env_file: Copied file for chache
    :return: None
    """
    # Remove original cache file
    os.remove(cache_env_file)
    # Create new cache file
    shutil.copyfile(env_file, cache_env_file)


def list_updated_addons(addons_folder: str, addons_cache_file: str) -> Tuple[List[str], Dict[str, Dict[str, float]]]:
    """
    Lists updated addons in the provided addons folder. The function checks if
    the given folder exists and scans for directories representing addons.
    It can also check the modified times of addon folders.

    :param addons_folder: The path to the folder containing addon directories.
    :type addons_folder: str
    :param addons_cache_file: The path to the file where addon metadata is cached.
    :type addons_cache_file: str
    :return: A list of updated addon names.
    :rtype: List[str]
    :raises Exception: If the provided addons folder does not exist.
    """

    # Read the addons cache file
    with open(addons_cache_file, "r") as f:
        cached_addons = json.load(f)

    to_update_list = []

    addon_list = [item for item in os.listdir(addons_folder) if os.path.isdir(os.path.join(addons_folder, item))]
    for addon in addon_list:
        os.path.getmtime(f"{addons_folder}/{addon}")
        if addon in cached_addons:
            if cached_addons[addon]['modified_time'] != os.path.getmtime(f"{addons_folder}/{addon}"):
                cached_addons[addon]['modified_time'] = os.path.getmtime(f"{addons_folder}/{addon}")
                to_update_list.append(addon)
        else:
            cached_addons.update(
                {
                    f"{addon}": {
                        'modified_time': os.path.getmtime(f"{addons_folder}/{addon}")
                    }
                }
            )
            to_update_list.append(addon)

    return to_update_list, cached_addons
