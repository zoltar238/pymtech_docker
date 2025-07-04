#!/usr/bin/env python3
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from dotenv import load_dotenv

from commands import env_verify, start_containers, auto_update_modules
from printers import print_status, print_success, print_header


async def main():
    # Load environment variables from .env file
    load_dotenv()

    # Necessary environmental variables
    env_variables = {
        'COMPOSE_PROJECT_NAME': os.getenv('COMPOSE_PROJECT_NAME'),
        'DEPLOYMENT_TARGET': os.getenv('DEPLOYMENT_TARGET'),
        'ODOO_VERSION': os.getenv('ODOO_VERSION'),
        'POSTGRES_VERSION': os.getenv('POSTGRES_VERSION'),
        'ODOO_EXPOSED_PORT': os.getenv('ODOO_EXPOSED_PORT'),
        'ODOO_INTERNAL_PORT': os.getenv('ODOO_INTERNAL_PORT'),
        'ODOO_LOG': os.getenv('ODOO_LOG'),
        'ODOO_CONFIG': os.getenv('ODOO_CONFIG'),
        'ODOO_ADDONS': os.getenv('ODOO_ADDONS'),
        'ODOO_REQUIREMENTS': os.getenv('ODOO_REQUIREMENTS'),
        'DOMAIN': os.getenv('DOMAIN'),
        'OPTIONAL_WHISPER': os.getenv('OPTIONAL_WHISPER'),
        'AUTO_INSTALL_MODULES': os.getenv('AUTO_INSTALL_MODULES'),
        'AUTO_UPDATE_MODULES': os.getenv('AUTO_UPDATE_MODULES'),
    }

    auto_update_modules(env_variables)

    # Determine environment mode
    mode = "Producción" if env_variables['DEPLOYMENT_TARGET'] == "prod" else "Desarrollo"

    # Verify environment variables
    print_header("VERIFICANDO VARIABLES DE ENTORNO")
    env_verify(env_variables)
    print_success("Las variables de entorno son válidas")

    # Star containers
    print_header("CONFIGURACION DEL ENTORNO")

    print_status(f"Nombre del proyecto: {env_variables['COMPOSE_PROJECT_NAME']}")
    print_status(f"Version de Odoo: {env_variables['ODOO_VERSION']}")
    print_status(f"Version de Postgres: {env_variables['POSTGRES_VERSION']}")
    print_status(f"Lanzando en modo:{mode}")
    print_status(f"Dominio: {env_variables['DOMAIN']}")
    print_status("Paquetes opcionales:")
    print_status(f"Instalar whisper para el reconocimiento de voz: {env_variables['OPTIONAL_WHISPER']}")

    # Start containers
    print_header("ARRANCANDO CONTENEDORES")
    await start_containers(env_variables)


if __name__ == "__main__":
    asyncio.run(main())