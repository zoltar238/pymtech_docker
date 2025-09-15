import time

import requests
from playwright.async_api import async_playwright

from .constants import Constants
from .custom_logger import CustomLogger


async def check_service_health(constants: Constants, url: str = None) -> None:
    max_attempts = 20
    attempt = 1
    wait_time = 0.5

    if constants.DOMAIN is not None and not url is None:
        url = f"https://{constants.DOMAIN}"
    else:
        url = f"http://localhost:{constants.ODOO_EXPOSED_PORT}"

    constants.logger.print_status(f"Checking odoo state on: {url}")

    while attempt <= max_attempts:
        try:
            response = requests.head(url, allow_redirects=False)
            status = response.status_code

            if status == 303:
                constants.logger.print_success(f"Odoo is working properly on: {url} (HTTP {status})")
                return
        except requests.RequestException:
            pass

        time.sleep(wait_time)
        attempt += 1

    constants.logger.print_error("Check service logs")
    constants.logger.print_error(f"Service not available on {url} after {max_attempts * wait_time} seconds")


async def create_database(port: str, logger: CustomLogger) -> None:
    logger.print_status("Creating database")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(f"http://localhost:{port}")
            await page.fill("input[name=\"master_pwd\"]", "master")
            await page.fill("input[name=\"name\"]", "master")
            await page.fill("input[name=\"login\"]", "master")
            await page.fill("input[name=\"password\"]", "master")
            await page.select_option('#lang', 'es_ES')
            await page.select_option('#country', 'es')
            await page.click("text=Create database")

        logger.print_success("Database created successfully")
    except Exception as e:
        logger.print_error(f"Failed to create database: {e}")
