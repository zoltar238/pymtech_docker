import asyncio
import json
import os
import subprocess
import time
from os.path import dirname
from typing import Any

import requests

from .file_operations import compare_files, replace_cache_file, list_updated_addons
from .printers import CustomLogger


class Commands:
    def __init__(self, name: str, level: str, environment: dict):
        # Create logger
        self.name = name
        self.level = level
        self.logger = CustomLogger(name, level)

        # Environmental variables
        self.environment = environment

        # Get the parent directory of this file
        self.parent_dir = dirname(dirname(os.path.abspath(__file__)))

    def env_verify(self, env_variables) -> None:
        """
        Method that verifies that the set environment variables are correct.
        :param env_variables:
        :return: None
        """

        # Determine environment mode
        mode = "Producción" if env_variables['DEPLOYMENT_TARGET'] == "prod" else "Desarrollo"

        self.logger.print_header("VERIFYING ENVIRONMENT VARIABLES")
        self.logger.print_status(f"Nombre del proyecto: {env_variables['COMPOSE_PROJECT_NAME']}")
        self.logger.print_status(f"Version de Odoo: {env_variables['ODOO_VERSION']}")
        self.logger.print_status(f"Version de Postgres: {env_variables['POSTGRES_VERSION']}")
        self.logger.print_status(f"Lanzando en modo:{mode}")
        self.logger.print_status(f"Dominio: {env_variables['DOMAIN']}")
        self.logger.print_status("Paquetes opcionales:")
        self.logger.print_status(f"Instalar whisper para el reconocimiento de voz: {env_variables['OPTIONAL_WHISPER']}")

        # Variables cant be null
        for variable, value in env_variables.items():
            if variable != 'DOMAIN' and value is None:
                self.logger.print_error(f"La variable {variable} no puede ser nula")
                exit(1)

        try:
            # Odoo version must be correct
            if env_variables['ODOO_VERSION'] not in ['16', '17', '18']:
                self.logger.print_error(
                    f"La versión de Odoo: {env_variables['ODOO_VERSION']} no es válida. Debe ser 16, 17 o 18")
                exit(1)
            # Deployment target must be correct
            if env_variables['DEPLOYMENT_TARGET'] not in ['dev', 'prod']:
                self.logger.print_error(f"Target inválido. Debe ser 'dev' o 'prod'")
                exit(1)

            # Verify port
            port = int(env_variables['ODOO_EXPOSED_PORT'])
            containers = self.get_containers_using_port(port)

            if containers:
                # Verificar si el contenedor que usa el puerto es parte del proyecto actual
                current_project = env_variables['COMPOSE_PROJECT_NAME']
                for container in containers:
                    if not container['name'].startswith(current_project):
                        self.logger.print_error(
                            f"El puerto {port} está siendo usado por el servicio: {container['name']}")
                        exit(1)

            self.logger.print_success("Environment variables verified successfully")

        except ValueError:
            self.logger.print_error(f"Port {env_variables['ODOO_EXPOSED_PORT']} must be a number")

    def get_containers_using_port(self, port):
        """
        Method that returns all containers that use a specific port.
        :param port:
        :return:
        """
        try:
            # List every container running
            result = subprocess.run([
                'docker', 'ps', '--format', '{{.Names}}\t{{.Ports}}'
            ], capture_output=True, text=True, check=True)

            using_port = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    name, ports = line.split('\t')
                    if f":{port}->" in ports or f"0.0.0.0:{port}" in ports:
                        using_port.append({
                            'name': name,
                            'ports': ports
                        })

            return using_port

        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error al verificar los puertos: {e}")
            if e.stderr:
                self.logger.print_error(f"Detalles del error: {e.stderr}")
            exit(1)
        except Exception as e:
            self.logger.print_error(f"Error al verificar los puertos: {e}")
            exit(1)

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
            addons_cache_file = f"{self.parent_dir}/cache/addons_cache.json"

            addons_list, addons_cache = list_updated_addons(environment['ODOO_ADDONS'], addons_cache_file)
            addons_string = ','.join(addons_list)

            # Update and install modules
            if len(addons_list) > 0 and len(databases) > 0:
                for index, db in enumerate(databases):
                    # Run update on each database
                    if self.environment['AUTO_INSTALL_MODULES'] == "true":
                        self.logger.print_status(f"Installing modules on database {db}")
                        cmd = f"odoo -d {db} -i {addons_string} --stop-after-init"
                        self.launch_containers(cmd)
                        self.logger.print_success(f"Installing modules on database {db} completed")
                    if self.environment['AUTO_UPDATE_MODULES'] == "true":
                        self.logger.print_status(f"Updating modules on database {db}")
                        cmd = f"odoo -d {db} -u {addons_string} --stop-after-init"
                        self.launch_containers(cmd)
                        self.logger.print_success(f"Updating modules on database {db} completed")
                with open(addons_cache_file, "w") as f:
                    json.dump(addons_cache, f)
            self.launch_containers()
        else:
            # Fully launch containers
            self.logger.print_header("DEPLOYING ENVIRONMENT")
            self.launch_containers()


        # Check odoo state
        self.logger.print_header("Verifying Odoo state")
        await asyncio.gather(
            self.check_service_health(port=environment['ODOO_EXPOSED_PORT']),
            self.check_service_health(domain=environment['DOMAIN'],
                                      deployment_target=environment['DEPLOYMENT_TARGET'])
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
            if not compare_files(env_file, cached_env_file):
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
            # Spin up containers
            self.logger.print_status("Spinning up containers")

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
                self.logger.print_success("Containers were successfully started")
            else :
                subprocess.run(
                    f"{base_cmd} up -d",
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=self.parent_dir
                )
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error launching containers: {str(e)}")
            self.logger.print_critical(f"Aborting deployment: {e.stderr}")
            exit(1)

    def get_database_names(self) -> list[Any] | None:
        for i in range(10):
            try:
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
                self.logger.print_warning(f"Failed getting databases names on try {i+1}: \n{str(e)} \n{e.stderr} \n{e.stdout}")
                pass
        return None

    async def check_service_health(self, port=None, domain=None, deployment_target="dev"):
        max_attempts = 10
        attempt = 1
        wait_time = 0.5
        url = ""

        if domain is not None and deployment_target == "prod":
            url = f"https://{domain}"
        elif domain is not None and deployment_target == "dev":
            url = f"http://test.{domain}"
        elif port is not None and domain is None:
            url = f"http://localhost:{port}"

        self.logger.print_status(f"Checking odoo state on: {url}")

        while attempt <= max_attempts:
            try:
                response = requests.head(url, allow_redirects=False)
                status = response.status_code

                if status == 303:
                    self.logger.print_success(
                        f"Odoo is working properly on: {url} (HTTP {status})")
                    return True
            except requests.RequestException:
                pass

            time.sleep(wait_time)
            attempt += 1

        if url.startswith("http://test"):
            self.logger.print_error("You can add local this local domain by modifying: /etc/hosts")
        else:
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
            print(output)
        except subprocess.CalledProcessError as e:
            self.logger.print_error(f"Error getting Docker logs: {str(e)}")

        print()

        # Odoo logs
        odoo_logs_path = f"{self.parent_dir}/log/odoo-server.log"
        if os.path.exists(odoo_logs_path):
            self.logger.print_status("Displaying Odoo server logs:")
            with open(odoo_logs_path, "r") as f:
                lines = f.readlines()[-30:]
                print("".join(lines))
        else:
            self.logger.print_warning(f"Odoo log file not found at path: {odoo_logs_path}")
