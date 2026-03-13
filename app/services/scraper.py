from playwright.async_api import async_playwright
import logging
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class ScraperService:
    @staticmethod
    async def fetch_html(url: str) -> str:
        """
        Fetches the HTML content of a given URL using Playwright for JS rendering.
        Runs in a thread with an explicit ProactorEventLoop on Windows to avoid
        SelectorEventLoop's lack of subprocess support.
        """
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, ScraperService._fetch_html_in_thread, url)

    @staticmethod
    def _fetch_html_in_thread(url: str) -> str:
        if sys.platform == 'win32':
            new_loop = asyncio.ProactorEventLoop()
        else:
            new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(ScraperService._fetch_html_impl(url))
        finally:
            new_loop.close()

    @staticmethod
    async def _fetch_html_impl(url: str) -> str:
        try:
            async with async_playwright() as p:
                logger.info(f"Launching browser for {url}...")
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                logger.info(f"Navigating to {url}...")
                await page.goto(url, wait_until="load", timeout=45000)

                await asyncio.sleep(2)

                html_content = await page.content()
                await browser.close()
                return html_content
        except Exception as e:
            logger.error(f"Playwright error details: {type(e).__name__}: {str(e)}")
            raise Exception(f"Playwright failed: {type(e).__name__} - {str(e)}")
