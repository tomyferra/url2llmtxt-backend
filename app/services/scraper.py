from playwright.async_api import async_playwright
import logging
import asyncio

logger = logging.getLogger(__name__)

class ScraperService:
    @staticmethod
    async def fetch_html(url: str) -> str:
        """
        Fetches the HTML content of a given URL using Playwright for JS rendering.
        """
        try:
            async with async_playwright() as p:
                logger.info(f"Launching browser for {url}...")
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                
                logger.info(f"Navigating to {url}...")
                # Use 'load' instead of 'networkidle' as some sites have persistent connections
                await page.goto(url, wait_until="load", timeout=45000)
                
                # Wait a bit for JS to settle if needed
                await asyncio.sleep(2)
                
                html_content = await page.content()
                await browser.close()
                return html_content
        except Exception as e:
            logger.error(f"Playwright error details: {type(e).__name__}: {str(e)}")
            raise Exception(f"Playwright failed: {type(e).__name__} - {str(e)}")
