import hashlib
import json
import os
import shutil
from typing import List, Tuple, Dict

from .constants import Constants
from .custom_logger import CustomLogger


def copy_requirements(base_dir: str, requirements_file: str, logger: CustomLogger) -> None:
    # Destination path for the requirements file inside the docker addons folder
    destination = os.path.join(base_dir, 'addons', 'requirements.txt')

    # Create an empty requirements file if it doesn't exist in the provided addons folder
    if requirements_file != './addons/requirements.txt' and not os.path.exists(requirements_file):
        logger.print_warning(f"Requirements file not found at {requirements_file}, creating an empty file")
        with open(requirements_file, 'w') as f:
            f.write("")
        logger.print_success(f"Successfully created empty requirements file at {requirements_file}")

    # Copy the requirements file from the provided addons folder to the docker addons folder
    if requirements_file != './addons/requirements.txt':
        shutil.copyfile(requirements_file, destination)

    # Create an empty requirements file if it doesn't exist in the docker addons folder
    if not os.path.exists(destination):
        logger.print_warning(f"Requirements file not found, creating an empty file")
        with open(destination, 'w') as f:
            f.write("")
        logger.print_success(f"Successfully created empty requirements file")

def check_config_changes(constants: Constants) -> Tuple[
    bool, Dict[str, str]]:
    # Get modification dates
    env_file_modified_time = os.path.getmtime(constants.ENV_FILE)
    dockerfile_file_modified_time = os.path.getmtime(constants.DOCKERFILE_FILE)

    # Read the addons' cache file, if any error occurs, return an empty dict
    cached_config_json = {}
    try:
        with open(constants.CACHE_CONFIG_FILE, "r") as f:
            cached_config_json = json.load(f)
    except Exception as e:
        constants.logger.print_warning(f"Error reading config cache file: {e}. New cache file will be created.")
        # Assign the new values to the JSON config
        cached_config_json['env_file_modified_time'] = env_file_modified_time
        cached_config_json['dockerfile_file_modified_time'] = dockerfile_file_modified_time
        return True, cached_config_json

    # Verify if the values match
    if cached_config_json.get('env_file_modified_time', '') != env_file_modified_time or cached_config_json.get(
            'dockerfile_file_modified_time', '') != dockerfile_file_modified_time:

        # Assign new values to the JSON cache
        cached_config_json['env_file_modified_time'] = env_file_modified_time
        cached_config_json['dockerfile_file_modified_time'] = dockerfile_file_modified_time
        return True, cached_config_json
    else:
        return False, cached_config_json


def replace_cache_file(cached_config_json: Dict[str, str], base_cache_dir: str, config_cache_file: str) -> None:
    """
    Replace the cache file with the new data.
    :param cached_config_json: JSON containing the new data.
    :param config_cache_file: path to the cache file.
    :param base_cache_dir: path to the base cache directory, needed to create the cache directory if it doesn't exist.
    :return:
    """

    # Create the cache directory if it doesn't exist
    if not os.path.exists(base_cache_dir):
        os.makedirs(base_cache_dir)

    # Write the JSON data to the document
    json.dump(cached_config_json, open(config_cache_file, "w"))


def calculate_addon_hash(addon_path: str, logger: CustomLogger) -> str:
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



    to_update_list = []

    # Get the list of addon directories
    addon_list = [item for item in os.listdir(addons_folder) if os.path.isdir(os.path.join(addons_folder, item))]

    for addon in addon_list:
        addon_path = os.path.join(addons_folder, addon)
        current_hash = calculate_addon_hash(addon_path, logger)

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
