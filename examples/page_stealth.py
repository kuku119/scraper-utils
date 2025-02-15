"""
检测 page stealth 是否正常生效
"""

# TODO 如何让新打开的页面能支持 stealth ?

import asyncio
from pathlib import Path

from scraper_utils.enums.browser_enum import ResourceType as RT
from scraper_utils.utils.browser_util import (
    launch_persistent_browser,
    create_new_page,
    close_browser,
    stealth_page,
)


if __name__ == '__main__':
    CWD = Path.cwd()

    abort_resources = (
        RT.MEDIA,
        RT.IMAGE,
    )  # 屏蔽图片、音视频资源

    async def main_1():
        browser = await launch_persistent_browser(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            user_data_dir=CWD.joinpath('temp/chrome_data'),
            channel='chrome',
            headless=False,
            slow_mo=1_000,
            stealth_browser=True,
            abort_resources=abort_resources,
        )
        page = await create_new_page()

        await page.goto('https://www.baidu.com')  # 打开百度首页

        kw_input_locator = page.locator(r'//input[@id="kw" and @name="wd"]')  # 搜索输入框
        await kw_input_locator.focus()  # 聚焦搜索输入框
        await kw_input_locator.fill('bot.sannysoft.com')  # 聚焦搜索输入框
        async with page.expect_navigation():  # 点击搜索按钮然后等待导航
            await page.click(r'//input[@id="su" and @type="submit"]')
        await page.screenshot(path=CWD.joinpath('temp/page_stealth/百度搜索截图_1.png'))  # 截图搜索结果页

        async with browser.expect_page() as new_page_event:  # 点击搜索结果然后等待新页面加载
            await page.click(r'//div[@mu="https://bot.sannysoft.com/"]//a[text()="Antibot"]')

        new_page = await new_page_event.value  # 拿到打开的新页面

        await new_page.screenshot(path=CWD.joinpath('temp/page_stealth/AntiBot_1.png'))  # 截图 AntiBot

        input('Enter...')

        await close_browser()

    async def main_2():
        browser = await launch_persistent_browser(
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            user_data_dir=CWD.joinpath('temp/chrome_data'),
            channel='chrome',
            headless=False,
            slow_mo=1_000,
            abort_resources=abort_resources,
        )
        page = await create_new_page()
        await stealth_page(page=page)

        await page.goto('https://www.baidu.com')  # 打开百度首页
        kw_input_locator = page.locator(r'//input[@id="kw" and @name="wd"]')  # 搜索输入框
        await kw_input_locator.focus()  # 聚焦搜索输入框
        await kw_input_locator.fill('bot.sannysoft.com')  # 聚焦搜索输入框
        async with page.expect_navigation():  # 点击搜索按钮然后等待导航
            await page.click(r'//input[@id="su" and @type="submit"]')
        await page.screenshot(path=CWD.joinpath('temp/page_stealth/百度搜索截图_2.png'))  # 截图搜索结果页

        async with browser.expect_page() as new_page_event:  # 点击搜索结果然后等待新页面加载
            await page.click(r'//div[@mu="https://bot.sannysoft.com/"]//a[text()="Antibot"]')

        new_page = await new_page_event.value  # 拿到打开的新页面

        await new_page.screenshot(path=CWD.joinpath('temp/page_stealth/AntiBot_2.png'))  # 截图 AntiBot

        await stealth_page(page=new_page)
        await new_page.reload()  # 刷新过后 stealth 是有效的
        await new_page.screenshot(path=CWD.joinpath('temp/page_stealth/AntiBot_2_刷新.png'))  # 再次截图 AntiBot

        input('Enter...')

        await close_browser()

    # asyncio.run(main_1())
    # asyncio.run(main_2())
