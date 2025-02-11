"""
爬取 Emag 搜索页的 listing
"""

import asyncio
from random import randint, uniform
from pathlib import Path
from time import perf_counter
from zipfile import ZipFile

from loguru import logger
from openpyxl.workbook import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from playwright.async_api import Page

from scraper_utils.constants.time_constant import MS1000
from scraper_utils.enums.browser_enum import ResourceType as RT
from scraper_utils.utils.browser_util import launch_persistent_browser, create_new_page, close_browser
from scraper_utils.utils.emag_url_util import build_search_url
from scraper_utils.utils.json_util import write_json_async, read_json_async
from scraper_utils.utils.time_util import now_str
from scraper_utils.utils.workbook_util import read_workbook_async, write_workbook_async


async def parse_search(page: Page) -> list[str]:
    """解析搜索页"""
    logger.debug(f'解析：{page.url}')

    result: list[str] = list()

    wheel_start_time = perf_counter()
    while True:  # 模拟鼠标滚轮向下滚动网页，直至 item_card_tag 数量达标或者时间超时
        item_card_tags_1 = page.locator(r'//div[@class="card-item card-standard js-product-data js-card-clickable "]')
        item_card_tags_2 = page.locator(r'//div[@class="card-item card-fashion js-product-data js-card-clickable"]')

        item_card_tag_count = await item_card_tags_1.count() + await item_card_tags_2.count()
        if item_card_tag_count >= 64:
            break

        await page.mouse.wheel(delta_y=randint(50, 150), delta_x=0)
        await page.wait_for_timeout(uniform(0, 0.5) * MS1000)
        if perf_counter() - wheel_start_time >= 30:  # 30 秒后数量还不够，就有多少爬多少（有些关键词的搜索结果就那么多）
            break

    logger.debug(f'定位到 {item_card_tag_count} 个 item_card_tag')
    for item_card_tag in await item_card_tags_1.all() + await item_card_tags_2.all():
        top_favourite_tag = item_card_tag.locator(r'//span[text()="Top Favorite"]')
        if await top_favourite_tag.count() > 0:
            item_title_tag = item_card_tag.locator(r'//a[@data-zone="title"]')
            if await item_title_tag.count() > 0:
                item_title = await item_title_tag.inner_text(timeout=MS1000)
                result.append(item_title)

    logger.debug(f'找到 {len(result)} 个符合条件的 listing')
    return result


async def scrape_search(CWD: Path, json_save_dir: Path, target_rows: list):
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
    worksheet = workbook.active

    for row in target_rows:
        keyword = str(worksheet.cell(row, 4).value)
        search_url = build_search_url(keyword=keyword, page=1)
        logger.info(f'爬取关键词：[row] {keyword}')

        page = await create_new_page(stealth=True, abort_resources=abort_resources)
        await page.goto(search_url, timeout=60 * MS1000)

        listings = await parse_search(page=page)
        await write_json_async(
            file=json_save_dir.joinpath(f'{row}.json'),
            data={
                'keyword': keyword,
                'listings': listings,
            },
            indent=4,
        )

        await asyncio.sleep(randint(20, 40))  # 随机延时
        await page.close()

    await close_browser()


async def concat_search(CWD: Path, json_save_dir: Path):
    """合并爬取结果"""
    red_bold_font = Font(color='FF0000', bold=True, size=14)  # 红字、加粗、14 号字
    yellow_bg = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')  # 黄底
    align = Alignment(wrap_text=True, horizontal='center', vertical='center')  # 居中、自动换行

    workbook = Workbook()
    sheet = workbook.active

    # 写入数据
    files = sorted(list(json_save_dir.glob('*.json')), key=lambda p: int(p.stem))
    for i, f in enumerate(files):
        data: dict[str, str | list[str]] = await read_json_async(file=f)
        keyword: str = data['keyword']
        listings: list[str] = data['listings']

        sheet.cell(row=1, column=i + 1, value=keyword)
        sheet.cell(row=1, column=i + 1).font = red_bold_font
        sheet.cell(row=1, column=i + 1).fill = yellow_bg

        for row, listing in enumerate(listings, start=2):
            sheet.cell(row=row, column=i + 1, value=listing)

    # 设置各列宽度为 50
    for col in sheet.columns:
        col_letter = col[0].column_letter
        sheet.column_dimensions[col_letter].width = 30

    # 设置各单元格居中
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = align

    result_path = await write_workbook_async(file=CWD.joinpath('temp/emag_listings.xlsx'), workbook=workbook)
    logger.success(f'程序结束，结果保存至：{result_path}')


def backup_file(CWD: Path, json_save_dir: Path):
    """把上一次爬取的 json 保存成 zip 文件"""
    backup_json_files = list(_ for _ in json_save_dir.glob('*.json'))
    if len(backup_json_files) > 0:
        with ZipFile(CWD.joinpath(f'temp/emag_jsons/backup.{now_str('%Y%m%d_%H%M%S')}.zip'), 'w') as zfp:
            for file in json_save_dir.glob('*.json'):
                zfp.write(file, arcname=file.name)
                file.unlink(missing_ok=True)


if __name__ == '__main__':
    CWD = Path.cwd()
    json_save_dir = CWD.joinpath('temp/emag_jsons')

    async def main():
        backup_file(CWD, json_save_dir=json_save_dir)
        try:
            await scrape_search(CWD, json_save_dir=json_save_dir, target_rows=list(range(4, 62)))
        except:
            pass
        await concat_search(CWD, json_save_dir=json_save_dir)

    asyncio.run(main())
