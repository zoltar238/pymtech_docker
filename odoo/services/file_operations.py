import hashlib
import json
import os
import shutil
from typing import List, Tuple, Dict


from .printers import CustomLogger

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


def list_updated_addons(addons_folder: str, addons_cache_file: str, logger: CustomLogger) -> Tuple[List[str], Dict[str, Dict[str, str]]]:
    """
    Lists updated addons in the provided addons folder. The function checks if
    the given folder exists and scans for directories representing addons.
    It checks the content hash of each addon folder to detect changes.

    :param addons_folder: The path to the folder containing addon directories.
    :type addons_folder: str
    :param addons_cache_file: The path to the file where addon metadata is cached.
    :type addons_cache_file: str
    :param logger: Logger instance for printing messages.
    :type logger: CustomLogger
    :return: A tuple containing a list of updated addon names and the updated cache dictionary.
    :rtype: Tuple[List[str], Dict[str, Dict[str, str]]]
    :raises Exception: If the provided addons folder does not exist.
    """

    # Read the addons' cache file, if any error occurs, return an empty dict
    cached_addons = {}
    try:
        with open(addons_cache_file, "r") as f:
            cached_addons = json.load(f)
    except Exception as e:
        logger.print_warning(f"Error reading addons cache file: {e}. New cache file will be created.")

    def calculate_addon_hash(addon_path: str) -> str:
        """
        Calculate MD5 hash for all files within an addon directory.

        :param addon_path: Path to the addon directory
        :return: Combined MD5 hash of all files in the addon
        """
        file_hashes = {}

        # Walk through all files in the addon directory
        for root, dirs, files in os.walk(addon_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, addon_path)

                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        file_hashes[relative_path] = file_hash
                except Exception as e:
                    logger.print_warning(f"Error reading file {file_path}: {e}")
                    continue

        # Create combined hash from all file hashes
        if file_hashes:
            combined = ''.join(sorted(file_hashes.values()))
            return hashlib.md5(combined.encode()).hexdigest()
        else:
            # Return empty hash if no files found
            return hashlib.md5(b'').hexdigest()

    to_update_list = []

    # Get list of addon directories
    addon_list = [item for item in os.listdir(addons_folder) if os.path.isdir(os.path.join(addons_folder, item))]

    for addon in addon_list:
        addon_path = os.path.join(addons_folder, addon)
        current_hash = calculate_addon_hash(addon_path)

        # Check if addon exists in cache and compare hashes
        if addon in cached_addons:
            cached_hash = cached_addons[addon].get('content_hash', '')

            if cached_hash != current_hash:
                # Hash changed, addon needs update
                cached_addons[addon]['content_hash'] = current_hash
                to_update_list.append(addon)
                logger.print_status(f"Addon '{addon}' content changed, marked for update.")
        else:
            # New addon, add to cache and update list
            cached_addons[addon] = {
                'content_hash': current_hash
            }
            to_update_list.append(addon)
            logger.print_status(f"New addon '{addon}' detected, marked for update.")

    # Check for removed addons (exist in cache but not in folder)
    cached_addon_names = list(cached_addons.keys())
    for cached_addon in cached_addon_names:
        if cached_addon not in addon_list:
            del cached_addons[cached_addon]
            logger.print_status(f"Addon '{cached_addon}' no longer exists, removed from cache.")

    return to_update_list, cached_addons


def update_addons_cache(addons_json, addons_cache_file):
    json.dump(addons_json, open(addons_cache_file, "w"))


def list_updated_addons_2(addons_folder: str) -> List[str]:
    """
    Lists updated addons in the provided addons folder. The function checks if
    the given folder exists and scans for directories representing addons.
    It can also check the modified times of addon folders.

    :param addons_folder: The path to the folder containing addon directories.
    :type addons_folder: str
    :return: A list of updated addon names.
    :rtype: List[str]
    :raises Exception: If the provided addons folder does not exist.
    """

    # Return the names of all the addons
    return [item for item in os.listdir(addons_folder) if os.path.isdir(os.path.join(addons_folder, item))]