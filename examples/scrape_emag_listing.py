"""
爬取 Emag 的 listing
"""

import asyncio
from pathlib import Path

from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from playwright.async_api import Page

from scraper_utils.enums.browser_enum import ResourceType as RT
from scraper_utils.utils.browser_util import launch_persistent_browser, create_new_page, close_browser
from scraper_utils.utils.emag_url_util import build_search_url
from scraper_utils.utils.json_util import write_json_async, read_json_async
from scraper_utils.utils.workbook_util import read_workbook_async, write_workbook_async


async def parse_search(page: Page) -> list[str]:
    """解析搜索页"""
    result: list[str] = list()
    item_cards = page.locator(r'//div[@class="card-item card-standard js-product-data js-card-clickable "]')
    for item_card in await item_cards.all():
        top_favourite = item_card.locator(r'//div[@class="card-v2-badge-cmp badge commercial-badge"]')
        if await top_favourite.count() > 0:
            pass
        # TODO


async def scrape_search(CWD: Path):
    """爬取并单独保存成 json 文件"""
    await launch_persistent_browser(
        executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        user_data_dir=Path.cwd().joinpath('temp/chrome_data'),
        channel='chrome',
        headless=False,
    )
    abort_resources = (RT.MEDIA, RT.IMAGE)

    workbook = await read_workbook_async(CWD.joinpath('temp/emag_keyword.xlsx'), read_only=True)
    worksheet = workbook['Wg wartości sprzedaży']

    for index in range(4, 62):
        keyword = str(worksheet.cell(index, 4).value)
        search_url = build_search_url(keyword=keyword, page=1)

        page = await create_new_page(stealth=True, abort_resources=abort_resources)
        await page.goto(search_url)

        listings = await parse_search(page=page)
        await write_json_async(
            file=CWD.joinpath(f'temp/emag_listings/{index}.json'),
            data={
                'keyword': keyword,
                'listings': listings,
            },
        )

        await asyncio.sleep(30)

    await close_browser()


async def concat_search(CWD: Path):
    """合并爬取结果"""
    workbook = Workbook()
    for json_file in CWD.joinpath('temp/emag_listings/').glob('*.json'):
        data: dict[str, str | list[str]] = await read_json_async(file=json_file)
        sheet: Worksheet = workbook.create_sheet(title=data['keyword'])
        for index, product in enumerate(data['listings'], start=1):
            sheet.cell(row=index, column=1, value=product)

    await write_workbook_async(file=CWD.joinpath('temp/emag_listings.xlsx'), workbook=workbook)


if __name__ == '__main__':
    CWD = Path.cwd()

    async def main():
        await scrape_search(CWD)
        await concat_search(CWD)

    asyncio.run(main())
