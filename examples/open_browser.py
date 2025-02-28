"""启动浏览器的示例"""

import asyncio
from pathlib import Path

from scraper_utils.utils.browser_util import (
    BrowserManager,
    PersistentContextManager,
    ResourceType,
    MS1000,
    stealth,
)

CWD = Path.cwd()

ANTI_BOT_URL = 'https://bot.sannysoft.com/'

EXECUTABLE_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


wait = lambda: input('Enter...')


async def browser_manager_test():
    """启动非持久化浏览器"""
    async with BrowserManager(
        executable_path=EXECUTABLE_PATH,
        channel='chrome',
        headless=False,
    ) as bm:
        context_1 = await bm.new_context(need_stealth=True)
        page_1 = await context_1.new_page()
        await page_1.goto(ANTI_BOT_URL)

        page_2 = await bm.new_page(need_stealth=True)
        await page_2.goto(ANTI_BOT_URL)

        wait()

        await page_1.close()
        await context_1.close()
        await page_2.close()


async def persistent_context_test():
    """启动持久化上下文"""
    async with PersistentContextManager(
        executable_path=EXECUTABLE_PATH,
        user_data_dir=CWD.joinpath('temp/chrome_data'),
        channel='chrome',
        headless=False,
    ) as pcm:
        page_1 = await pcm.new_page(need_stealth=True)
        await page_1.goto(ANTI_BOT_URL)

        wait()

        await page_1.close()


if __name__ == '__main__':

    async def main():
        """"""
        await browser_manager_test()
        await persistent_context_test()

    asyncio.run(main())
