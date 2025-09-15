import asyncio
import os
import time

import typer
from services.config_manager import set_config
from services.constants import Constants
from services.containers import stop_running_containers, build_docker_images, launch_database_only, \
    get_database_names, launch_containers
from services.custom_logger import CustomLogger
from services.database_creator import create_database, check_service_health
from services.env_validator import env_verify
from services.file_operations import copy_requirements, list_updated_addons, update_addons_cache
from services.module_manager import list_to_install_addons, list_addons_in_folder
from services.traefik import configure_traefik

app = typer.Typer(add_completion=False,
                  help="Odoo Deploy command line tool, run without arguments nor commands to start the deployment process")
base_dir = os.getcwd()

async def async_main():
    start_time = time.time()

    # Load configuration
    constants = Constants.from_env(base_dir)

    # Verify environment variables
    env_verify(constants)

    # Copy the requirements file to the addons folder
    copy_requirements(
        base_dir=constants.BASE_DIR,
        requirements_file=os.path.join(constants.ODOO_ADDONS, 'requirements.txt'),
        logger=constants.logger
    )

    # Stop running containers
    stop_running_containers(constants)

    # Configure traefik
    configure_traefik(constants)

    # Build images if necessary
    build_docker_images(constants)

    if constants.AUTO_INSTALL_MODULES == 'true' or constants.AUTO_UPDATE_MODULES == 'true':
        constants.logger.print_header("UPDATING DATABASES AND INSTALLING MODULES")
        launch_database_only(constants)

        # Get all database names
        database_list = get_database_names(constants)
        # If no databases were found, and the deployment target is development, create a new database
        if not database_list:
            # Launch containers without updating nor installing modules
            launch_containers(constants)
            # After launching containers, create a new database if necessary
            if constants.DEPLOYMENT_TARGET == 'dev' and constants.AUTO_CREATE_DATABASE == 'true':
                # Wait for the database to be ready
                await check_service_health(constants)
                # Create the new database
                await create_database(constants.ODOO_EXPOSED_PORT, constants.logger)

                # Gather the new database name and the list of addons inside the addons folder
                database_list = get_database_names(constants)
                addons_list = list_addons_in_folder(constants.ADDONS_FOLDER, constants.logger)

                for index, db in enumerate(database_list):
                    install_addons_string = list_to_install_addons(constants, addons_list, db)
                    if install_addons_string:
                        constants.logger.print_status(f"Installing modules on database {db}")
                    cmd = f"odoo -d {db} -i {install_addons_string} --stop-after-init"
                    launch_containers(constants, cmd)
                    constants.logger.print_success(f"Installing modules on database {db} completed")

                # Launch containers again with the updated addons list
                constants.logger.print_header("DEPLOYING ENVIRONMENT")
                launch_containers(constants)
        else:
            # Get the list of addons that need to be updated
            addons_list = list_addons_in_folder(constants.ADDONS_FOLDER, constants.logger)

            update_addons_list = []
            update_addons_json = {}
            if constants.UPDATE_MODULE_LIST:
                update_addons_string = constants.UPDATE_MODULE_LIST
            else:
                # Get the list of addons that need to be updated
                update_addons_list, update_addons_json = list_updated_addons(constants.ADDONS_FOLDER,
                                                                             os.path.join(constants.CACHE_ADDONS_FILE),
                                                                             constants.logger)
                # Transform the addon list to string
                update_addons_string = ','.join(update_addons_list)

            # Force update option
            force_update = '--dev=all' if constants.FORCE_UPDATE == 'true' else ''

            # Update and install modules
            for index, db in enumerate(database_list):
                # Install modules if the option is enabled, and the list of addons to be installed is not empty
                install_addons_string = list_to_install_addons(constants, addons_list, db)
                if constants.AUTO_INSTALL_MODULES == "true" and install_addons_string:
                    constants.logger.print_status(f"Installing modules on database {db}")
                    cmd = f"odoo -d {db} -i {install_addons_string} --stop-after-init"
                    launch_containers(constants, cmd)
                    constants.logger.print_success(f"Installing modules on database {db} completed")
                # Update modules
                if constants.AUTO_UPDATE_MODULES == "true" and update_addons_list:
                    constants.logger.print_status(f"Updating modules on database {db}")
                    cmd = f"odoo -d {db} -u {update_addons_string} {force_update} --stop-after-init"
                    launch_containers(constants, cmd)
                    constants.logger.print_success(f"Updating modules on database {db} completed")

            # Launch containers again with the updated addons list
            constants.logger.print_header("DEPLOYING ENVIRONMENT")
            launch_containers(constants)

            # Update addons_cache.json
            update_addons_cache(update_addons_json, constants.CACHE_ADDONS_FILE)
    else:
        # Fully launch containers
        constants.logger.print_header("DEPLOYING ENVIRONMENT")
        launch_containers(constants)

        # Create a new database if necessary
        if constants.DEPLOYMENT_TARGET == 'dev' and constants.AUTO_CREATE_DATABASE == 'true':
            # Get all database names
            database_list = get_database_names(constants)
            if not database_list:
                await create_database(constants.ODOO_EXPOSED_PORT, constants.logger)

    # Check odoo state after launching containers
    constants.logger.print_header("Verifying Odoo state")
    if constants.DEPLOYMENT_TARGET == 'prod':
        await asyncio.gather(
            check_service_health(constants),
            check_service_health(constants, constants.DOMAIN)
        )
    else:
        await asyncio.gather(
            check_service_health(constants),
        )

    end_time = time.time() - start_time
    constants.logger.print_success(f"Total time: {end_time:.2f} seconds") \

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """ Launch and configure Odoo and PostgresSQL containers """
    if not ctx.invoked_subcommand:
        asyncio.run(async_main())


@app.command()
def auto_config():
    """ Autoconfigure Odoo and PostgresSQL config files based on server capacity"""
    logger = CustomLogger("configurator")
    set_config(
        base_dir=base_dir,
        logger=logger
    )


def deploy():
    app()


# Entry point
if __name__ == "__main__":
    deploy()
