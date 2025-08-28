import os
import subprocess

from .printers import CustomLogger


def env_verify(logger: CustomLogger, env_variables: dict) -> None:
    """
    Method that verifies that the set environment variables are correct.
    :param env_variables:
    :param logger:
   :return: None
    """

    # Determine environment mode
    mode = "Production" if env_variables['DEPLOYMENT_TARGET'] == "prod" else "Development"
    logger.print_header("VERIFYING ENVIRONMENT VARIABLES")
    logger.print_status("--- Core Configuration ---")
    logger.print_status(f"Project name: {env_variables['COMPOSE_PROJECT_NAME']}")
    logger.print_status(f"Deployment target:{mode}")
    logger.print_status(f"Script output: {env_variables['SCRIPT_OUTPUT']}")
    logger.print_status("--- Container Versions ---")
    logger.print_status(f"Odoo version: {env_variables['ODOO_VERSION']}")
    logger.print_status(f"Postgres version: {env_variables['POSTGRES_VERSION']}")
    logger.print_status("--- Network & Connectivity ")
    logger.print_status(f"Odoo exposed port: {env_variables['ODOO_EXPOSED_PORT']}")
    logger.print_status(f"Odoo internal port: {env_variables['ODOO_INTERNAL_PORT']}")
    logger.print_status(f"Domain: {env_variables['DOMAIN']}")
    logger.print_status("--- Files & Paths ---")
    logger.print_status(f"Odoo log path: {env_variables['ODOO_LOG']}")
    logger.print_status(f"Odoo config path: {env_variables['ODOO_CONFIG']}")
    logger.print_status(f"Odoo addons path: {env_variables['ODOO_ADDONS']}")
    logger.print_status("--- Module Management ---")
    logger.print_status(f"Auto install modules: {env_variables['AUTO_INSTALL_MODULES']}")
    logger.print_status(f"Auto update modules: {env_variables['AUTO_UPDATE_MODULES']}")
    logger.print_status(f"Force update modules: {env_variables['FORCE_UPDATE']}")
    logger.print_status(f"Update module list: {env_variables['UPDATE_MODULE_LIST']}")
    logger.print_status("--- Build & Development ---")
    logger.print_status(f"Rebuild images: {env_variables['FORCE_REBUILD']}")
    logger.print_status("--- Optional Features ---")
    logger.print_status(f"Install wisper for voice recognition: {env_variables['OPTIONAL_WHISPER']}")

    # Variables can't be null
    for variable, value in env_variables.items():
        if (variable != 'DOMAIN' and variable != 'UPDATE_MODULE_LIST') and (value is None or value == ''):
            logger.print_error(f"Variable {variable} can't be null")
            exit(1)

    try:
        # Odoo version must be correct
        if env_variables['ODOO_VERSION'] not in ['16', '17', '18']:
            logger.print_error(
                f"La versión de Odoo: {env_variables['ODOO_VERSION']} no es válida. Debe ser 16, 17 o 18")
            exit(1)
        # Deployment target must be correct
        if env_variables['DEPLOYMENT_TARGET'] not in ['dev', 'prod']:
            logger.print_error(f"Target inválido. Debe ser 'dev' o 'prod'")
            exit(1)
        # Check it the addons path exists
        if not os.path.exists(env_variables['ODOO_ADDONS']):
            logger.print_error(f"The addons path: {env_variables['ODOO_ADDONS']} does not exist")
            exit(1)

        # Verify port
        port = int(env_variables['ODOO_EXPOSED_PORT'])
        containers = get_containers_using_port(logger, port)

        if containers:
            # Verificar si el contenedor que usa el puerto es parte del proyecto actual
            current_project = env_variables['COMPOSE_PROJECT_NAME']
            for container in containers:
                if not container['name'].startswith(current_project):
                    logger.print_error(
                        f"The port: {port} is occupied by other container: {container['name']}")
                    exit(1)

        logger.print_success("Environment variables verified successfully")

    except ValueError:
        logger.print_error(f"Port {env_variables['ODOO_EXPOSED_PORT']} must be a number")


def get_containers_using_port(logger: CustomLogger, port):
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
        logger.print_error(f"Error al verificar los puertos: {e}")
        if e.stderr:
            logger.print_error(f"Detalles del error: {e.stderr}")
        exit(1)
    except Exception as e:
        logger.print_error(f"Error al verificar los puertos: {e}")
        exit(1)
