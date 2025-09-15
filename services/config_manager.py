import configparser
import os

import psutil

from .custom_logger import CustomLogger


def set_config(base_dir: str, logger: CustomLogger) -> None:
    logger.print_header("Setting up Odoo configuration")

    cpu_count = os.cpu_count()
    system_ram = psutil.virtual_memory().total

    # Total ram available for Odoo
    odoo_ram = system_ram * 0.65
    # Total ram available for Postgres
    postgres_ram = system_ram * 0.2

    # Odoo config parameters
    workers = cpu_count * 2
    max_cron_threads = 1
    limit_memory_soft = int(odoo_ram / (cpu_count + max_cron_threads))
    limit_memory_hard = int(limit_memory_soft * 1.40)
    db_maxconn = 32

    # Postgres config parameters
    shared_buffers = f"{int(postgres_ram * 0.4 / 1e6)}MB"
    effective_cache_size = f"{int(system_ram * 0.5 / 1e6)}MB"
    max_connections = int((workers + max_cron_threads) * db_maxconn * 1.1)
    work_mem = f"{int((system_ram * 0.25) / max_connections / 1e6)}MB"
    maintenance_work_mem = f"{int((system_ram * 0.05) / 1e6)}MB"

    # Create a configuration dictionary with the calculated values
    config = {
        'odoo': {
            'workers': workers,
            'max_cron_threads': max_cron_threads,
            'limit_memory_soft': limit_memory_soft,
            'limit_memory_hard': limit_memory_hard,
            'db_maxconn': db_maxconn
        },
        'postgres': {
            'listen_addresses': '*',
            'shared_buffers': shared_buffers,
            'effective_cache_size': effective_cache_size,
            'max_connections': max_connections,
            'work_mem': work_mem,
            'maintenance_work_mem': maintenance_work_mem
        }
    }

    logger.print_status("--- Calculated values for Odoo ---")
    logger.print_status(f"workers: {config['odoo']['workers']}")
    logger.print_status(f"max_cron_threads: {config['odoo']['max_cron_threads']}")
    logger.print_status(f"limit_memory_soft: {config['odoo']['limit_memory_soft']}")
    logger.print_status(f"limit_memory_hard: {config['odoo']['limit_memory_hard']}")
    logger.print_status(f"db_maxconn: {config['odoo']['db_maxconn']}")

    logger.print_status("--- Calculated values for Postgres ---")
    logger.print_status(f"shared_buffers: {config['postgres']['shared_buffers']}")
    logger.print_status(f"effective_cache_size: {config['postgres']['effective_cache_size']}")
    logger.print_status(f"max_connections: {config['postgres']['max_connections']}")
    logger.print_status(f"work_mem: {config['postgres']['work_mem']}")
    logger.print_status(f"maintenance_work_mem: {config['postgres']['maintenance_work_mem']}")

    odoo_config_file = os.path.join(base_dir, 'config', 'odoo.conf')
    postgres_config_file = os.path.join(base_dir, 'config', 'postgresql.conf')
    update_config_files(
        postgres_config_file=postgres_config_file,
        odoo_config_file=odoo_config_file,
        config_dict=config,
        logger=logger
    )


def update_config_files(postgres_config_file: str, odoo_config_file: str, config_dict, logger: CustomLogger) -> None:
    try:
        logger.print_status("Writing new configuration files")

        # Verify if the file exists
        if not os.path.exists(odoo_config_file):
            raise FileNotFoundError(f"Config file not found: {odoo_config_file}")

        if not os.path.exists(postgres_config_file):
            raise FileNotFoundError(f"Postgres config file not found: {postgres_config_file}")

        # Read the existing configuration file, starting with the odoo config file
        config_override = configparser.ConfigParser()
        config_override.read(odoo_config_file)

        # Ensure the 'options' section exists
        if 'options' not in config_override:
            config_override.add_section('options')

        config_override.set('options', 'workers', str(config_dict['odoo']['workers']))
        config_override.set('options', 'max_cron_threads', str(config_dict['odoo']['max_cron_threads']))
        config_override.set('options', 'limit_memory_soft', str(config_dict['odoo']['limit_memory_soft']))
        config_override.set('options', 'limit_memory_hard', str(config_dict['odoo']['limit_memory_hard']))
        config_override.set('options', 'db_maxconn', str(config_dict['odoo']['db_maxconn']))

        # Write back to the file
        with open(odoo_config_file, 'w') as configfile:
            config_override.write(configfile)

        postgres_config_lines = [
            f"listen_addresses = '{config_dict['postgres']['listen_addresses']}'",
            f"shared_buffers = {config_dict['postgres']['shared_buffers']}",
            f"effective_cache_size = {config_dict['postgres']['effective_cache_size']}",
            f"max_connections = {config_dict['postgres']['max_connections']}",
            f"work_mem = {config_dict['postgres']['work_mem']}",
            f"maintenance_work_mem = {config_dict['postgres']['maintenance_work_mem']}"
        ]

        with open(postgres_config_file, 'w') as configfile:
            configfile.write("\n".join(postgres_config_lines))

        logger.print_success("Odoo and Postgres config files have been successfully written")
    except Exception as e:
        logger.print_error(f"Failed to update configuration files: {e}")
