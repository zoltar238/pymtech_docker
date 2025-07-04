import os
import subprocess
import time
import asyncio
import json
from pyexpat.errors import messages

import requests
from printers import print_status, print_success, print_error, print_warning, print_header


def env_verify(env_variables):
    # Variables cant be null
    for variable, value in env_variables.items():
        if variable != 'DOMAIN' and value is None:
            print_error(f"La variable {variable} no puede ser nula")
            exit(1)

    try:
        # Odoo version must be correct
        if env_variables['ODOO_VERSION'] not in ['16', '17', '18']:
            print_error(f"La versión de Odoo: {env_variables['ODOO_VERSION']} no es válida. Debe ser 16, 17 o 18")
            exit(1)
        # Deployment target must be correct
        if env_variables['DEPLOYMENT_TARGET'] not in ['dev', 'prod']:
            print_error(f"Target inválido. Debe ser 'dev' o 'prod'")
            exit(1)

        # Verificar puerto
        port = int(env_variables['ODOO_EXPOSED_PORT'])
        containers = get_containers_using_port(port)

        if containers:
            # Verificar si el contenedor que usa el puerto es parte del proyecto actual
            current_project = env_variables['COMPOSE_PROJECT_NAME']
            for container in containers:
                if not container['name'].startswith(current_project):
                    print_error(f"El puerto {port} está siendo usado por el servicio: {container['name']}")
                    exit(1)

    except ValueError as e:
        print_error(f"El puerto {env_variables['ODOO_EXPOSED_PORT']} debe ser un número")


def get_containers_using_port(port):
    """Obtiene todos los contenedores que usan un puerto específico"""
    try:
        # Listar todos los contenedores
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

    except Exception as e:
        print_error(f"Error al verificar los puertos: {e}")
        exit(1)


def _is_port_in_use(port) -> bool:
    """
    Verify if a port is in use
    :param port: The port to verify
    :return:
        bool: True if the port is in use, False otherwise
    """
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


async def start_containers(environment):
    try:
        # Shut down running containers
        print_status("Deteniendo contenedores corriendo")
        subprocess.run(
            "docker-compose down",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=None,
        )
        print_success("Los contenedores corriendo fueron detenidos correctamente")

        # Build images
        print_status("Construyendo imagenes")
        label_file = f"labels/labels-{environment['DEPLOYMENT_TARGET']}.yml"
        subprocess.run(
            f"docker-compose -f docker-compose.yml -f {label_file} build",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=None,
        )
        print_success("Las imagenes fueron construidas correctamente")

        # Spin up containers
        print_status("Iniciando contenedores")
        subprocess.run(
            f"docker-compose -f docker-compose.yml -f {label_file} up -d",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=None,
        )
        print_success("Los contenedores fueron iniciados correctamente")

        # Check container health
        if check_containers_health(environment['DEPLOYMENT_TARGET']):
            print_status("Verificando el estado de Odoo")
            await asyncio.gather(
                check_service_health(port=environment['ODOO_EXPOSED_PORT']),
                check_service_health(domain=environment['DOMAIN'], deployment_target=environment['DEPLOYMENT_TARGET'])
            )
        else:
            print_error("Los contenedores no han arrancado correctamente")
    except subprocess.CalledProcessError as e:
        print_error(f"Error iniciando los contenedores: {str(e)}")
        exit(1)


def auto_update_modules(env_variables):
    databases = "all"
    module_path = env_variables['ODOO_ADDONS']
    modules = os.listdir(module_path)
    modules.remove("requirements.txt")
    module_names = " ".join(modules)
    install_command = f"-i {module_names}"
    update_command = f"-u {module_names}"
    full_command = f"odoo {install_command} {update_command} -d {databases}"

    print(full_command)





def check_containers_health(environment):
    print_status("Verificando estado de los contenedores")

    try:
        cmd = f"docker-compose -f docker-compose.yml -f labels/labels-{environment}.yml ps -q"
        container_ids = subprocess.check_output(cmd, shell=True).decode().strip().split('\n')

        failed_containers = []
        for container_id in container_ids:
            if container_id:
                inspect_cmd = f"docker inspect --format='{{{{.Name}}}}: {{{{.State.Status}}}}' {container_id}"
                status = subprocess.check_output(inspect_cmd, shell=True).decode().strip()
                if 'running' not in status:
                    failed_containers.append(status)

        if failed_containers:
            print_error("Some containers are not running:")
            for container in failed_containers:
                print(container)
            return False

        print_success("Los contenedores han arrancado correctamente")

        # print("Comprobando modulos instalados")
        # command = f"docker exec {environment['COMPOSE_PROJECT_NAME']}_db psql -U odoo -d master -c \"SELECT name FROM ir_module_module WHERE state = 'installed' ORDER BY name;\""
        # modules = subprocess.check_output(command, shell=True).decode().strip().split('\n')
        # print(modules)
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Error checking containers: {str(e)}")
        return False


async def check_service_health(port=None, domain=None, deployment_target="dev"):
    max_attempts = 10
    attempt = 1
    wait_time = 1
    url = ""

    if domain is not None and deployment_target == "prod":
        url = f"https://{domain}"
    elif domain is not None and deployment_target == "dev":
        url = f"http://test.{domain}"
    elif port is not None and domain is None:
        url = f"http://localhost:{port}"

    print_status(f"Probando el estado del servicio en {url}")

    while attempt <= max_attempts:
        try:
            response = requests.head(url, allow_redirects=False)
            status = response.status_code

            if status == 303:
                print_success(f"El servicio de Odoo esta funcinando correctamente en {url}: (HTTP {status})")
                return True
        except requests.RequestException:
            if not url.startswith("http://test"):
                print_warning("Sin respuesta del servicio, reintentando")

        time.sleep(wait_time)
        attempt += 1

    if url.startswith("http://test"):
        print_error(f"Servicio no disponible en {url} despues de {max_attempts * wait_time} segundos")
        print_error("Puedes activar el dominio local modificando el archivo /etc/hosts")
    else:
        print_error(f"Servicio no disponible en {url} despues de {max_attempts * wait_time} segundos")
        print_error("Comprueba los logs del servicio")
    return False


def show_logs_on_error(environment):
    print_header("FAILURE LOGS")

    # Show docker logs
    print_status("Displaying Docker container logs:")
    try:
        cmd = f"docker-compose -f docker-compose.yml -f labels/labels-{environment}.yml logs --tail=30"
        output = subprocess.check_output(cmd, shell=True).decode()
        print(output)
    except subprocess.CalledProcessError as e:
        print_error(f"Error getting Docker logs: {str(e)}")

    print()

    # Odoo logs
    if os.path.exists("log/odoo-server.log"):
        print_status("Displaying Odoo server logs:")
        with open("log/odoo-server.log", "r") as f:
            lines = f.readlines()[-30:]
            print("".join(lines))
    else:
        print_warning("Odoo log file not found at path: log/odoo-server.log")
