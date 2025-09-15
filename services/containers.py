import os
import subprocess
from typing import Any

from services.constants import Constants
from services.file_operations import check_config_changes, replace_cache_file


def stop_running_containers(constants: Constants) -> None:
    """
    Stops all running containers of this deployment
    param config: contains all the relevant configurations and objects needed for deployment
    return: None
    """
    constants.logger.print_header("STOPPING RUNNING CONTAINERS")

    try:
        # Shut down running containers
        constants.logger.print_status("Stopping running containers")
        subprocess.run(
            "docker compose down",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            cwd=constants.BASE_DIR
        )

        constants.logger.print_success("Running containers were successfully stopped")
    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error stopping running containers: {str(e)}")
        constants.logger.print_critical(f"Aborting deployment: {e.stderr}")
        exit(1)


def build_docker_images(constants: Constants) -> None:
    constants.logger.print_header("APPLYING CONFIGURATION CHANGES")
    try:
        # Necessary files
        label_file = f"labels/labels-{constants.DEPLOYMENT_TARGET}.yml"

        changes_found, cached_config_json = check_config_changes(constants)

        # Build images only if environment variables have been modified
        if changes_found or constants.FORCE_REBUILD == "true":
            constants.logger.print_status("Detected changes in environment variables, building images")
            subprocess.run(
                f"docker compose -f docker-compose.yml -f {label_file} build",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR
            )

            # Save the config data in the JSON after successfully building the images
            replace_cache_file(cached_config_json, constants.CACHE_FOLDER, constants.CACHE_CONFIG_FILE)
            constants.logger.print_success("Container images were successfully built")
        else:
            constants.logger.print_success("No changes detected in environment variables, skipping image build")
    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error building docker images: {str(e)} \n {e.stderr} \n {e.stdout}")
        exit(1)


def launch_database_only(constants: Constants) -> None:
    constants.logger.print_status("Launching database")
    try:
        subprocess.run(
            f"docker compose up -d db",
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=constants.BASE_DIR
        )
    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error starting up database: {str(e)} \n {e.stderr} \n {e.stdout}")
        exit(1)


def get_database_names(constants: Constants) -> list[Any] | None:
    for i in range(10):
        try:
            # Verify that the container is running properly before attempting to get the database names
            while True:
                cmd_check = f"docker exec {constants.COMPOSE_PROJECT_NAME}_db pg_isready -U odoo"
                result = subprocess.run(
                    cmd_check,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=constants.BASE_DIR,
                )

                if "accepting connections" in result.stdout:
                    constants.logger.print_success("PostgreSQL is ready!")
                    break

            cmd_list_databases = f"docker exec {constants.COMPOSE_PROJECT_NAME}_db psql -U odoo -l -A"
            result = subprocess.run(
                cmd_list_databases,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR,
            )

            # Get all databases that aren't part of postgres
            lines = result.stdout.split('\n')
            databases = []

            for index, line in enumerate(lines):
                if '|' in line:
                    db_name = line.split('|')[0].strip()
                    if db_name not in ['postgres', 'template0', 'template1', 'Name'] and '=' not in db_name:
                        databases.append(db_name)

            return databases
        except subprocess.CalledProcessError as e:
            if i > 9:
                constants.logger.print_warning(
                    f"Failed getting databases names on try {i + 1}: \n{str(e)} \n{e.stderr} \n{e.stdout}")
    return None


def launch_containers(constants: Constants, command: str = None) -> None:
    """
    Deploys the docker containers
    :return: None
    """
    try:
        label_file = f"labels/labels-{constants.DEPLOYMENT_TARGET}.yml"

        # Base command
        base_cmd = f"docker compose -f docker-compose.yml -f {label_file}"
        if command:
            subprocess.run(
                f"{base_cmd} run --rm odoo {command}",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR
            )
        else:
            constants.logger.print_status("Spinning up containers")
            subprocess.run(
                f"{base_cmd} up -d",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=constants.BASE_DIR
            )
            constants.logger.print_success("Containers were successfully started")

    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error launching containers: {str(e)}")
        constants.logger.print_critical(f"Aborting deployment: {e.stderr}")
        show_logs_on_error(constants)
        exit(1)


def show_logs_on_error(constants: Constants) -> None:
    constants.logger.print_header("FAILURE LOGS")

    # Show docker logs
    constants.logger.print_status("Displaying Docker container logs:")
    try:
        cmd = f"docker compose -f docker-compose.yml -f labels/labels-{constants.DEPLOYMENT_TARGET}.yml logs --tail=30"
        output = subprocess.check_output(cmd, shell=True).decode()
        constants.logger.print_warning(output)
    except subprocess.CalledProcessError as e:
        constants.logger.print_error(f"Error getting Docker logs: {str(e)}")

    print()

    # Odoo logs
    odoo_logs_path = f"{constants.BASE_DIR}/log/odoo-server.log"
    if os.path.exists(odoo_logs_path):
        constants.logger.print_status("Displaying Odoo server logs:")
        with open(odoo_logs_path, "r", encoding="UTF-8") as f:
            lines = f.readlines()[-50:]
            constants.logger.print_warning("".join(lines))
    else:
        constants.logger.print_warning(f"Odoo log file not found at path: {odoo_logs_path}")
