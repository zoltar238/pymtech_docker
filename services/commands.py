import asyncio
import os
import subprocess
import time
from os.path import dirname
from typing import Any

import requests

from .database_creator import create_database
from .file_operations import replace_cache_file, list_updated_addons, \
    update_addons_cache, check_config_changes
from .module_manager import list_addons_in_folder, list_to_install_addons
from .printers import CustomLogger
from .traefik_configurator import configure_traefik
from .config_manager import modify_config


class Commands:
    def __init__(self, logger: CustomLogger, environment: dict):
        # logger
        self.database_list = None
        self.logger = logger
        # Environmental variables
        self.environment = environment
        # Get the parent directory of this file
        self.parent_dir = dirname(dirname(os.path.abspath(__file__)))

    async def start_containers(self):
        # Stop running containers
        self.logger.print_header("STOPPING RUNNING CONTAINERS")
        self.stop_running_containers()

        # Set values in the config file
        modify_config()

        # Configure traefik
        self.logger.print_header("CONFIGURING TRAEFIK")
        configure_traefik(target=self.environment['DEPLOYMENT_TARGET'], logger=self.logger, odoo_dir=self.parent_dir,
                          traefik_version=self.environment['TRAEFIK_VERSION'])

        # Rebuild images if necessary
        self.logger.print_header("APPLYING CONFIGURATION CHANGES")
        self.build_docker_images()

        # Launch containers
        if self.environment['AUTO_INSTALL_MODULES'] == 'true' or self.environment['AUTO_UPDATE_MODULES'] == 'true':
            self.logger.print_header("UPDATING DATABASES AND INSTALLING MODULES")
            # Launch database only
            self.launch_database_only()
            # Get all database names
            self.database_list = self.get_database_names()

            # If no databases were found, skip module installation and update
            if not self.database_list:
                self.logger.print_status("No databases found, skipping module installation and update")
                # Launch containers without updating nor installing modules
                self.logger.print_header("DEPLOYING ENVIRONMENT")
                self.launch_containers()
            else:
                # Get the list of addons that need to be updated
                addons_list = list_addons_in_folder(self.environment['ODOO_ADDONS'], self.logger)

                update_addons_list = []
                update_addons_json = {}
                update_addons_string = ''
                if self.environment['UPDATE_MODULE_LIST']:
                    update_addons_string = self.environment['UPDATE_MODULE_LIST']
                else:
                    # Get the list of addons that need to be updated
                    update_addons_list, update_addons_json = list_updated_addons(self.environment['ODOO_ADDONS'],
                                                                                 './cache/addons_cache.json',
                                                                                 self.logger)
                    # Transform the addon list to string
                    update_addons_string = ','.join(update_addons_list)

                # Force update option
                force_update = '--dev=all' if self.environment['FORCE_UPDATE'] == 'true' else ''

                # Update and install modules
                for index, db in enumerate(self.database_list):
                    # Install modules if the option is enabled, and the list of addons to be installed is not empty
                    install_addons_string = list_to_install_addons(self.environment['COMPOSE_PROJECT_NAME'], db,
                                                                   addons_list, self.logger)
                    if self.environment['AUTO_INSTALL_MODULES'] == "true" and (
                            install_addons_string and install_addons_string != ""):
                        self.logger.print_status(f"Installing modules on database {db}")
                        cmd = f"odoo -d {db} -i {install_addons_string} --stop-after-init"
                        self.launch_containers(cmd)
                        self.logger.print_success(f"Installing modules on database {db} completed")
                    # Update modules
                    if self.environment['AUTO_UPDATE_MODULES'] == "true" and len(update_addons_list) > 0:
                        self.logger.print_status(f"Updating modules on database {db}")
                        cmd = f"odoo -d {db} -u {update_addons_string} {force_update} --stop-after-init"
                        self.launch_containers(cmd)
                        self.logger.print_success(f"Updating modules on database {db} completed")

                # Launch containers again with the updated addons list
                self.logger.print_header("DEPLOYING ENVIRONMENT")
                self.launch_containers()

                # Update addons_cache.json
                update_addons_cache(update_addons_json, './cache/addons_cache.json')


        else:
            # Fully launch containers
            self.logger.print_header("DEPLOYING ENVIRONMENT")
            self.launch_containers()

        # Check odoo state
        self.logger.print_header("Verifying Odoo state")
        if self.environment['DEPLOYMENT_TARGET'] == 'prod':
            await asyncio.gather(
                self.check_service_health(port=self.environment['ODOO_EXPOSED_PORT']),
                self.check_service_health(domain=self.environment['DOMAIN'])
            )
        else:
            await asyncio.gather(
                self.check_service_health(port=self.environment['ODOO_EXPOSED_PORT']),
            )

    def stop_running_containers(self) -> None:
        """
        Stops all running containers of this deployment
        :return: None
        """
        try:
            # Shut down running containers
            self.logger.print_status("Stoping running containers")
            subprocess.run(
                "docker compose down",
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.parent_dir
            )

            self.logger.print_success("Running containers were successfully stopped")
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error stopping running containers: {str(e)}")
            self.logger.print_critical(f"Aborting deployment: {e.stderr}")
            exit(1)

    def build_docker_images(self) -> None:
        try:
            # Necessary files
            env_file = os.path.join(self.parent_dir, ".env")
            dockerfile_file = os.path.join(self.parent_dir, "odoo.Dockerfile")
            cache_file_dir = os.path.join(self.parent_dir, "cache")
            cached_config_file = os.path.join(self.parent_dir, "cache", "config_cache.json")
            label_file = f"labels/labels-{self.environment['DEPLOYMENT_TARGET']}.yml"

            changes_found, cached_config_json = check_config_changes(env_file, dockerfile_file, cached_config_file,
                                                                     self.logger)

            # Build images only if environment variables have been modified
            if changes_found or self.environment['FORCE_REBUILD'] == "true":
                self.logger.print_status("Detected changes in environment variables, building images")
                subprocess.run(
                    f"docker compose -f docker-compose.yml -f {label_file} build",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir
                )

                # Save the config data in the JSON after successfully building the images
                replace_cache_file(cached_config_json, cache_file_dir, cached_config_file)
                self.logger.print_success("Container images were successfully built")
            else:
                self.logger.print_success("No changes detected in environment variables, skipping image build")
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error building docker images: {str(e)} \n {e.stderr} \n {e.stdout}")
            exit(1)

    def launch_database_only(self) -> None:
        self.logger.print_status("Launching database")
        try:
            subprocess.run(
                f"docker compose up -d db",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=self.parent_dir
            )
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error starting up database: {str(e)} \n {e.stderr} \n {e.stdout}")
            exit(1)

    def launch_containers(self, command: str = None) -> None:
        """
        Deploys the docker containers
        :return: None
        """
        try:
            label_file = f"labels/labels-{self.environment['DEPLOYMENT_TARGET']}.yml"

            # Base command
            base_cmd = f"docker compose -f docker-compose.yml -f {label_file}"
            if command:
                subprocess.run(
                    f"{base_cmd} run --rm odoo {command}",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir
                )
            else:
                self.logger.print_status("Spinning up containers")
                subprocess.run(
                    f"{base_cmd} up -d",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir
                )
                self.logger.print_success("Containers were successfully started")

        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error launching containers: {str(e)}")
            self.logger.print_critical(f"Aborting deployment: {e.stderr}")
            self.show_logs_on_error()
            exit(1)

    def get_database_names(self) -> list[Any] | None:
        for i in range(10):
            try:
                # Verify that the container is running properly before attempting to get the database names
                while True:
                    cmd_check = f"docker exec {self.environment['COMPOSE_PROJECT_NAME']}_db pg_isready -U odoo"
                    result = subprocess.run(
                        cmd_check,
                        shell=True,
                        check=True,
                        capture_output=True,
                        text=True,
                        cwd=self.parent_dir,
                    )

                    if "accepting connections" in result.stdout:
                        self.logger.print_success("PostgreSQL is ready!")
                        break

                cmd_list_databases = f"docker exec {self.environment['COMPOSE_PROJECT_NAME']}_db psql -U odoo -l -A"
                result = subprocess.run(
                    cmd_list_databases,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir,
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
                    self.logger.print_warning(
                        f"Failed getting databases names on try {i + 1}: \n{str(e)} \n{e.stderr} \n{e.stdout}")
        return None

    async def check_service_health(self, port=None, domain=None):
        max_attempts = 10
        attempt = 1
        wait_time = 0.5
        url = ""

        if domain is not None:
            url = f"https://{domain}"
        elif port is not None and domain is None:
            url = f"http://localhost:{port}"

        self.logger.print_status(f"Checking odoo state on: {url}")

        while attempt <= max_attempts:
            try:
                response = requests.head(url, allow_redirects=False)
                status = response.status_code

                if status == 303:
                    self.logger.print_success(f"Odoo is working properly on: {url} (HTTP {status})")

                    # If the database list is empty, create a new database
                    if not self.database_list and self.environment[
                        'DEPLOYMENT_TARGET'] == 'dev':
                        await create_database(self.environment['ODOO_EXPOSED_PORT'], self.logger)
                    return True
            except requests.RequestException:
                pass

            time.sleep(wait_time)
            attempt += 1

        self.logger.print_error("Check service logs")
        self.logger.print_error(f"Service not available on {url} after {max_attempts * wait_time} seconds")
        return False

    def show_logs_on_error(self):
        self.logger.print_header("FAILURE LOGS")

        # Show docker logs
        self.logger.print_status("Displaying Docker container logs:")
        try:
            cmd = f"docker compose -f docker-compose.yml -f labels/labels-{self.environment['DEPLOYMENT_TARGET']}.yml logs --tail=30"
            output = subprocess.check_output(cmd, shell=True).decode()
            self.logger.print_warning(output)
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error getting Docker logs: {str(e)}")

        print()

        # Odoo logs
        odoo_logs_path = f"{self.parent_dir}/log/odoo-server.log"
        if os.path.exists(odoo_logs_path):
            self.logger.print_status("Displaying Odoo server logs:")
            with open(odoo_logs_path, "r", encoding="UTF-8") as f:
                lines = f.readlines()[-50:]
                self.logger.print_warning("".join(lines))
        else:
            self.logger.print_warning(f"Odoo log file not found at path: {odoo_logs_path}")
