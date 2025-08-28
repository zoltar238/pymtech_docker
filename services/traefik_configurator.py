import os.path
import shutil
import subprocess
import configparser

from dotenv import load_dotenv
from .printers import CustomLogger


def configure_traefik(target: str, traefik_version: str, odoo_dir: str, logger: CustomLogger) -> None:
    """
    This method creates a traefik network if it doesn't exist.
    Traefik network is necessary for routing traffic to the containers.
    :return:
    """

    # The parent directory for traefik is the odoo parent directory
    parent_dir = os.path.dirname(odoo_dir)

    try:
        # Check if traefik network exists
        logger.print_status("Verifying traefik network")
        output = subprocess.check_output("docker network ls", shell=True).decode()

        # Create a traefik network if it doesn't exist
        if "traefik" in output:
            logger.print_success("Traefik network already exists")
        else:
            logger.print_status("Creating traefik network")
            subprocess.run(
                "docker network create traefik",
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                cwd=parent_dir
            )
            logger.print_success("Traefik network created successfully")

        # If the deployment target is production, verify traefik container
        if target == "prod":
            logger.print_status("Verifying traefik container")

            # Load traefik's dotenv file
            dotenv_path = os.path.join(parent_dir, "traefik", ".env")
            load_dotenv(dotenv_path, override=True)

            # If the traefik container doesn't exist or the traefik version is not up to date, update it
            if not os.path.exists(dotenv_path) or (
                    os.path.exists(dotenv_path) and os.getenv('VERSION') != traefik_version):
                logger.print_warning("Traefik version is not up to date, updating to the latest version")

                # Clean up previous traefik container
                _cleanup_previous_traefik(parent_dir, logger)

                # Clone the newest version of traefik
                logger.print_status("Updating traefik version")
                subprocess.run(
                    f"git clone --depth=1 https://github.com/zoltar238/pymtech_traefik.git traefik",
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=parent_dir
                )
                logger.print_success("Traefik container has been updated")
            else:
                logger.print_success("Traefik container is up to date")

            # Verify that the traefik container is running, launch it if it's not
            logger.print_status("Checking if traefik container is running")
            result = subprocess.run(
                "docker ps --filter name=traefik --format '{{.Names}}'",
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            if not result.stdout.strip():
                logger.print_status("Traefik container is not running, starting it")
                subprocess.run(
                    f"docker compose -p traefik up -d",
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.join(parent_dir, "traefik")
                )
                logger.print_success("Traefik container has been started")
            else:
                logger.print_success("Traefik container is running")

        # Update odoo config
        update_odoo_config(odoo_dir, logger, target)
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error verifying traefik network: {str(e)}")
        logger.print_critical(f"Aborting deployment: {e.stderr}")
        exit(1)


def _cleanup_previous_traefik(parent_dir: str, logger: CustomLogger) -> None:
    try:
        # Clean up previous traefik container
        logger.print_status("Removing traefik containers, volumes and images")

        # Clean up the rest of the previous traefik container
        delete_traefik_container(logger)

        # Delete previous traefik folder if it exists
        if os.path.exists(os.path.join(parent_dir, "traefik")):
            # Clean up previous traefik folder
            logger.print_status("Removing traefik folder")
            shutil.rmtree(os.path.join(parent_dir, "traefik"))
            logger.print_success("Previous traefik folder has been cleaned up")
    except subprocess.CalledProcessError as e:
        logger.print_error(f"Error cleaning up previous traefik container: {str(e)}")
        logger.print_critical(f"Aborting deployment: {e.stderr}")
        exit(1)


def delete_traefik_container(logger: CustomLogger) -> None:
    # Stop traefik container
    try:
        # Stop previous traefik container
        logger.print_status("Stopping previous traefik container")
        subprocess.run(
            "docker stop $(docker ps -f name=traefik -q)",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.print_success("Previous traefik container has been stopped")
    except subprocess.CalledProcessError:
        logger.print_warning(f"No previous traefik container was found running")

    # Remove container and volumes
    try:
        logger.print_status("Removing previous traefik container and volumes")
        subprocess.run(
            "docker rm -v $(docker ps -a -f name=traefik -q)",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.print_success("Previous traefik container and volumes have been removed")
    except subprocess.CalledProcessError:
        logger.print_warning(f"No previous traefik container found")

    # Remove traefik image
    try:
        logger.print_status("Removing traefik image")
        subprocess.run(
            "docker rmi $(docker images -f reference=traefik -q)",
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.print_success("Previous traefik image has been removed")
    except subprocess.CalledProcessError:
        logger.print_warning(f"No previous traefik image found")


def update_odoo_config(odoo_container_path: str, logger: CustomLogger, target: str) -> None:
    try:
        logger.print_status("Verifying odoo proxy config")

        config_file = os.path.join(odoo_container_path, "config", "odoo.conf")

        # Verify if the file exists
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")

        # Read the existing configuration file
        config_override = configparser.ConfigParser()
        config_override.read(config_file)

        # Ensure the 'options' section exists
        if 'options' not in config_override:
            config_override.add_section('options')

        # Update the proxy_mode option
        if target == "prod":
            config_override.set('options', 'proxy_mode', 'True')
        else:
            config_override.set('options', 'proxy_mode', 'False')

        # Write back to the file
        with open(config_file, 'w') as configfile:
            config_override.write(configfile)

        logger.print_success("Odoo proxy config has been updated")
    except Exception as e:
        logger.print_error(f"Failed to update odoo proxy config: {e}")
