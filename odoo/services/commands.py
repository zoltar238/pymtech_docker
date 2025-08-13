import asyncio
import os
import subprocess
import time
from os.path import dirname
from typing import Any

import requests

from .file_operations import compare_files, replace_cache_file, list_updated_addons_2, list_updated_addons, \
    update_addons_cache
from .printers import CustomLogger


class Commands:
    def __init__(self, logger: CustomLogger, environment: dict):
        # logger
        self.logger = logger
        # Environmental variables
        self.environment = environment
        # Get the parent directory of this file
        self.parent_dir = dirname(dirname(os.path.abspath(__file__)))

    async def start_containers(self, environment):
        # Stop running containers
        self.stop_running_containers()

        # Rebuild images if necessary
        self.build_docker_images()

        # Launch containers
        if self.environment['AUTO_INSTALL_MODULES'] == 'true' or self.environment['AUTO_UPDATE_MODULES'] == 'true':
            # Launch only the database to get all database names
            self.logger.print_header("UPDATING DATABASES AND INSTALLING MODULES")
            self.launch_database_only()

            # Get all database names
            databases = self.get_database_names()

            # Get the list of addons that need to be updated
            install_addons_list = []
            update_addons_list = []
            update_addons_json = {}
            install_addons_string = ''
            update_addons_string = ''
            if self.environment['UPDATE_MODULE_LIST']:
                update_addons_string = self.environment['UPDATE_MODULE_LIST']
            else:
                # Get the list of addons that need to be updated
                install_addons_list = list_updated_addons_2(environment['ODOO_ADDONS'])
                update_addons_list, update_addons_json = list_updated_addons(environment['ODOO_ADDONS'],
                                                                             './cache/addons_cache.json', self.logger)
                # Transform addons list to string
                install_addons_string = ','.join(install_addons_list)
                update_addons_string = ','.join(update_addons_list)

            # Force update option
            force_update = '--dev=all' if self.environment['FORCE_UPDATE'] == 'true' else ''

            # Update and install modules
            if len(databases) > 0:
                for index, db in enumerate(databases):
                    # Install modules
                    if len(install_addons_list) > 0:
                        if self.environment['AUTO_INSTALL_MODULES'] == "true":
                            self.logger.print_status(f"Installing modules on database {db}")
                            cmd = f"odoo -d {db} -i {install_addons_string} --stop-after-init"
                            self.launch_containers(cmd)
                            self.logger.print_success(f"Installing modules on database {db} completed")
                    # Update modules
                    if len(update_addons_list) > 0:
                        if self.environment['AUTO_UPDATE_MODULES'] == "true":
                            self.logger.print_status(f"Updating modules on database {db}")
                            cmd = f"odoo -d {db} -u {update_addons_string} {force_update} --stop-after-init"
                            self.launch_containers(cmd)
                            self.logger.print_success(f"Updating modules on database {db} completed")
                    else:
                        self.logger.print_success(f"No modules to update or install on database {db}")
            self.launch_containers()

            # Update addons_cache.json
            update_addons_cache(update_addons_json, './cache/addons_cache.json')

        else:
            # Fully launch containers
            self.logger.print_header("DEPLOYING ENVIRONMENT")
            self.launch_containers()

        # Check odoo state
        self.logger.print_header("Verifying Odoo state")
        if environment['DEPLOYMENT_TARGET'] == 'prod':
            await asyncio.gather(
                self.check_service_health(port=environment['ODOO_EXPOSED_PORT']),
                self.check_service_health(domain=environment['DOMAIN'])
            )
        else:
            await asyncio.gather(
                self.check_service_health(port=environment['ODOO_EXPOSED_PORT']),
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
            env_file = f"{self.parent_dir}/.env"
            cached_env_file = f"{self.parent_dir}/cache/cached.env"
            label_file = f"labels/labels-{self.environment['DEPLOYMENT_TARGET']}.yml"

            # Build images only if environment variables have been modified
            if not compare_files(env_file, cached_env_file) or self.environment['FORCE_REBUILD'] == "true":
                self.logger.print_status("Detected changes in environment variables, building images")
                subprocess.run(
                    f"docker compose -f docker-compose.yml -f {label_file} build",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir
                )

                # Copy .env file to cache
                replace_cache_file(env_file, cached_env_file)
                self.logger.print_success("Container images were successfully built")
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error building docker images: {str(e)} \n {e.stderr} \n {e.stdout}")
            exit(1)

    def launch_database_only(self) -> None:
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
                # Verify that the container is running properly before attemting to get the database names
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
            with open(odoo_logs_path, "r") as f:
                lines = f.readlines()[-50:]
                self.logger.print_warning("".join(lines))
        else:
            self.logger.print_warning(f"Odoo log file not found at path: {odoo_logs_path}")
