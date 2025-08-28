import asyncio
import os
import sys
import time

from services.printers import CustomLogger
from services.startup_validator import env_verify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from services.commands import Commands


async def main():
    start_time = time.time()
    # Load environment variables from .env file
    load_dotenv()

    # Necessary environmental variables
    env_variables = {
        'VERSION': os.getenv('VERSION'),
        'TRAEFIK_VERSION': os.getenv('TRAEFIK_VERSION'),
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
        'SCRIPT_OUTPUT': os.getenv('SCRIPT_OUTPUT'),
        'UPDATE_MODULE_LIST': os.getenv('UPDATE_MODULE_LIST'),
        'FORCE_UPDATE': os.getenv('FORCE_UPDATE'),
        'FORCE_REBUILD': os.getenv('FORCE_REBUILD'),
    }

    # Create logger
    logger = CustomLogger("odoo_deploy", env_variables['SCRIPT_OUTPUT'])

    # Verify environment variables
    env_verify(env_variables=env_variables, logger=logger)

    # Create a command class
    commands = Commands(logger=logger, environment=env_variables)

    # Start the containers
    await commands.start_containers()
    end_time = time.time() - start_time
    logger.print_success(f"Total time:{end_time}")

if __name__ == "__main__":
    asyncio.run(main())