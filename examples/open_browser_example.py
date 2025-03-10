import asyncio
from pathlib import Path

from scraper_utils.utils.browser_util import BrowserManager, PersistentContextManager, ResourceType


CWD = Path.cwd()

ANTI_BOT_URL = 'https://bot.sannysoft.com/'

EXECUTABLE_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
USER_DATA_DIR = CWD.joinpath('temp/chrome_data')


async def open_browser():
    """打开非持久化浏览器"""
    async with BrowserManager(
        executable_path=EXECUTABLE_PATH,
        channel='chrome',
        headless=False,
        args=['--window-size=1000,750'],
    ) as bm:
        context1 = await bm.new_context(abort_res_types=(ResourceType.MEDIA, ResourceType.IMAGE))
        page11 = await context1.new_page()
        page12 = await context1.new_page()
        # pass

        context2 = await bm.new_context()
        page21 = await context2.new_page()
        # pass

        page3 = await bm.new_page()
        # pass

        input('Continue...')


async def open_persistent_context():
    """打开持久化上下文"""
    async with PersistentContextManager(
        executable_path=EXECUTABLE_PATH,
        user_data_dir=USER_DATA_DIR,
        channel='chrome',
        headless=False,
    ) as pcm:
        page1 = await pcm.new_page()
        page2 = await pcm.new_page()
        # pass

        input('Continue...')


async def main():
    await open_browser()

    await open_persistent_context()


if __name__ == '__main__':
    asyncio.run(main())
