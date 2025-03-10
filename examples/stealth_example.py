import asyncio
from pathlib import Path

from scraper_utils.utils.browser_util import BrowserManager, MS1000


CWD = Path.cwd()

ANTI_BOT_URL = 'https://bot.sannysoft.com/'

EXECUTABLE_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


async def main():
    async with BrowserManager(
        executable_path=EXECUTABLE_PATH,
        channel='chrome',
        headless=False,
    ) as bm:
        page_stealthed = await bm.new_page(need_stealth=True, default_navigation_timeout=60 * MS1000)
        page_no_stealthed = await bm.new_page(need_stealth=False, default_navigation_timeout=60 * MS1000)

        await page_stealthed.goto(ANTI_BOT_URL, wait_until='networkidle')
        await page_no_stealthed.goto(ANTI_BOT_URL, wait_until='networkidle')

        await page_stealthed.screenshot(path=CWD.joinpath('temp/page_stealthed.png'))
        await page_no_stealthed.screenshot(path=CWD.joinpath('temp/page_no_stealthed.png'))


if __name__ == '__main__':
    asyncio.run(main())
