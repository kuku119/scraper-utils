"""
爬取 Emag 搜索页的 listing
"""

import asyncio
from random import randint, uniform
from pathlib import Path
from time import perf_counter

from loguru import logger
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from playwright.async_api import Page

from scraper_utils.constants.time_constant import MS1000
from scraper_utils.enums.browser_enum import ResourceType as RT
from scraper_utils.utils.browser_util import launch_persistent_browser, create_new_page, close_browser
from scraper_utils.utils.emag_url_util import build_search_url
from scraper_utils.utils.json_util import write_json_async, read_json_async
from scraper_utils.utils.workbook_util import read_workbook_async, write_workbook_async


async def parse_search(page: Page) -> list[str]:
    """解析搜索页"""
    result: list[str] = list()

    wheel_start_time = perf_counter()
    while True:  # 模拟鼠标滚轮向下滚动网页
        item_card_tags = page.locator(r'//div[@class="card-item card-standard js-product-data js-card-clickable "]')
        if await item_card_tags.count() >= 67:
            break
        await page.mouse.wheel(delta_y=randint(50, 150), delta_x=0)
        await page.wait_for_timeout(uniform(0, 0.5) * MS1000)
        if perf_counter() - wheel_start_time >= 10:  # 10 秒后数量还不够，就有多少爬多少
            break

    logger.debug('定位到 ' + str(await item_card_tags.count()) + ' 个 item_card_tags')
    for item_card_tag in await item_card_tags.all():
        top_favourite_tag = item_card_tag.locator(r'//span[text()="Top Favorite"]')
        if await top_favourite_tag.count() > 0:
            logger.debug('定位到 1 个 top_favourite_tag')
            item_title_tag = item_card_tag.locator(r'//a[@data-zone="title"]')
            if await item_title_tag.count() > 0:
                logger.debug('定位到 1 个 item_title_tag')
                item_title = await item_title_tag.inner_text(timeout=MS1000)
                logger.debug(f'找到 1 个 listing: {item_title}')
                result.append(item_title)

    logger.debug(f'总计找到 {len(result)} 个 listing')
    return result


async def scrape_search(CWD: Path):
    """爬取并单独保存成 json 文件"""
    await launch_persistent_browser(
        executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        user_data_dir=Path.cwd().joinpath('temp/chrome_data'),
        channel='chrome',
        headless=False,
        timeout=60 * MS1000,
    )
    abort_resources = (RT.MEDIA, RT.IMAGE)  # 屏蔽图片、音视频资源

    workbook = await read_workbook_async(CWD.joinpath('temp/emag_keyword.xlsx'), read_only=True)
    worksheet = workbook['Sheet1']

    for index in range(4, 62):
        keyword = str(worksheet.cell(index, 4).value)
        search_url = build_search_url(keyword=keyword, page=1)

        page = await create_new_page(stealth=True, abort_resources=abort_resources)
        await page.goto(search_url)

        logger.info(f'正在爬取：{keyword}')
        listings = await parse_search(page=page)
        await page.close()
        await write_json_async(
            file=CWD.joinpath(f'temp/emag_listings/{index}.json'),
            data={
                'keyword': keyword,
                'listings': listings,
            },
        )

        await asyncio.sleep(30)  # 60 秒的延时

    await close_browser()


async def concat_search(CWD: Path):
    """合并爬取结果"""
    workbook = Workbook()
    for json_file in CWD.joinpath('temp/emag_listings/').glob('*.json'):
        data: dict[str, str | list[str]] = await read_json_async(file=json_file)
        sheet: Worksheet = workbook.create_sheet(title=data['keyword'])
        for index, product in enumerate(data['listings'], start=1):
            sheet.cell(row=index, column=1, value=product)

    result_path = await write_workbook_async(file=CWD.joinpath('temp/emag_listings.xlsx'), workbook=workbook)
    logger.success(f'程序结束，结果保存至：{result_path}')


if __name__ == '__main__':
    CWD = Path.cwd()

    async def main():
        await scrape_search(CWD)
        await concat_search(CWD)

    asyncio.run(main())
