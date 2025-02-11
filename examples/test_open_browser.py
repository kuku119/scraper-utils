"""测试访问 emag"""

if __name__ == '__main__':
    import asyncio
    from pathlib import Path

    from scraper_utils.utils.browser_util import (
        launch_browser,
        launch_persistent_browser,
        close_browser,
        create_new_page,
    )
    from scraper_utils.enums.browser_enum import ResourceType

    async def main():
        await launch_persistent_browser(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            user_data_dir=Path.cwd().joinpath('temp/chrome_data'),
            headless=False,
            channel='chrome',
        )
        page = await create_new_page(
            stealth=True,
            # abort_resources=['image', 'media'],
            abort_resources=[ResourceType.IMAGE, ResourceType.MEDIA],
        )
        await page.goto('https://www.emag.ro/')
        # await page.goto('https://www.amazon.com/')

        input('Enter...')

        await close_browser()

    asyncio.run(main())
