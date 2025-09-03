import os
import psutil


def modify_config():
    workers = os.cpu_count() * 2 + 1
    system_ram = psutil.virtual_memory().total
    # Total ram available for Odoo
    odoo_ram = system_ram * 0.5
    postgres_ram = system_ram * 0.2
    redish_ram = system_ram * 0.2
    limit_memory_soft = round((system_ram * 0.8) / 1e9, 2)
    limit_memory_hard = round((system_ram * 0.9) / 1e9, 2)

    print(f"cpu_count: {workers}")
    print(f"limit_memory_soft: {limit_memory_soft} GB")
    print(f"limit_memory_hard: {limit_memory_hard} GB")
