import hashlib
import json
import os
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


def check_config_changes(env_file: str, dockerfile_file: str, config_cache_file: str, logger: CustomLogger) -> Tuple[
    bool, Dict[str, str]]:

    # Get modification dates
    env_file_modified_time = os.path.getmtime(env_file)
    dockerfile_file_modified_time = os.path.getmtime(dockerfile_file)

    # Read the addons' cache file, if any error occurs, return an empty dict
    cached_config_json = {}
    try:
        with open(config_cache_file, "r") as f:
            cached_config_json = json.load(f)
    except Exception as e:
        logger.print_warning(f"Error reading config cache file: {e}. New cache file will be created.")
        # Assign the new values to the json config
        cached_config_json['env_file_modified_time'] = env_file_modified_time
        cached_config_json['dockerfile_file_modified_time'] = dockerfile_file_modified_time
        return True, cached_config_json

    # Verify if the values match
    if cached_config_json.get('env_file_modified_time', '') != env_file_modified_time or cached_config_json.get(
            'dockerfile_file_modified_time', '') != dockerfile_file_modified_time:

        # Assign new values to the json cache
        cached_config_json['env_file_modified_time'] = env_file_modified_time
        cached_config_json['dockerfile_file_modified_time'] = dockerfile_file_modified_time
        return True, cached_config_json
    else:
        return False, cached_config_json


def replace_cache_file(cached_config_json: Dict[str, str], base_cache_dir:str, config_cache_file: str) -> None:
    """
    Replace the cache file with the new data.
    :param cached_config_json: json containing the new data.
    :param config_cache_file: path to the cache file.
    :param base_cache_dir: path to the base cache directory, needed to create the cache directory if it doesn't exist.
    :return:
    """

    # Create the cache directory if it doesn't exist
    if not os.path.exists(base_cache_dir):
        os.makedirs(base_cache_dir)

    # Write the json data to the document
    json.dump(cached_config_json, open(config_cache_file, "w"))


def list_updated_addons(addons_folder: str, addons_cache_file: str, logger: CustomLogger) -> Tuple[
    List[str], Dict[str, Dict[str, str]]]:
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

    logger.print_status("Fetching list of addons to update")
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

        # Check if addon exists in the cache and compare hashes
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

    if not to_update_list:
        logger.print_success(f"No addons found to be updated")

    return to_update_list, cached_addons


def update_addons_cache(addons_json, addons_cache_file):
    json.dump(addons_json, open(addons_cache_file, "w"))