import os
import subprocess

from .constants import Constants
from .custom_logger import CustomLogger


def list_to_install_addons(constants: Constants, addon_list: list, db_name: str) -> str | None:
    constants.logger.print_status(f"Checking for addons to be installed on database {db_name}")
    try:
        cmd_list_databases = f"docker exec {constants.COMPOSE_PROJECT_NAME}_db psql -U odoo -d {db_name} -t -c \"SELECT name FROM ir_module_module WHERE state='installed';\""
        result = subprocess.run(
            cmd_list_databases,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )

        # Create a list of installed addons from the result, filter out empty spaces
        installed_addons = [
            addon.strip()
            for addon in result.stdout.strip().split('\n')
            # Remove empty lines
            if addon.strip()
        ]

        # Get the difference between the addon list and the installed addons
        non_installed_addons = list(set(addon_list) - set(installed_addons))

        # Let the user know which addons will be installed
        if not non_installed_addons:
            constants.logger.print_success(f"No addons to be installed found on database {db_name}")
            return None
        for addon in non_installed_addons:
            constants.logger.print_status(f"Uninstalled addon '{addon}' will be installed on database {db_name}")

        return ','.join(non_installed_addons)
    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error listing installed addons: {str(e)}")
        constants.logger.print_critical(f"Aborting deployment: {e.stderr}")
        exit(1)


def list_addons_in_folder(addons_folder: str, logger: CustomLogger) -> list[str]:
    """
    Fetches all addons in the provided addons folder. The function checks if
    the given folder exists and scans for directories representing addons.

    :param addons_folder: The path to the folder containing addon directories.
    :type addons_folder: str
    :param logger: The logger instance to use for logging.
    :type logger: CustomLogger
    :return: A list of addon names.
    :rtype: list[str]
    :raises Exception: If the provided addons folder does not exist or is not a directory.
    """

    logger.print_status(f"Fetching addons from: {addons_folder}")
    if not os.path.exists(addons_folder):
        logger.print_error(f"Addons folder does not exist: {addons_folder}")
        raise Exception(f"Addons folder does not exist: {addons_folder}")
    elif not os.path.isdir(addons_folder):
        logger.print_error(f"Addons folder is not a directory: {addons_folder}")
        raise Exception(f"Addons folder is not a directory: {addons_folder}")
    else:
        addons_list = [item for item in os.listdir(addons_folder) if os.path.isdir(os.path.join(addons_folder, item))]
        logger.print_success(f"Found {len(addons_list)} addons in folder: {addons_folder}")
        return addons_list
