from playwright.async_api import async_playwright

from .printers import CustomLogger


# from playwright.sync_api import sync_playwright

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