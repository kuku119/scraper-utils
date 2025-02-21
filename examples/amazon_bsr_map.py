"""
亚马逊各站点之间的 BSR 链接映射
"""

import asyncio
from pathlib import Path
import random
import re
import sys
import time
from typing import Generator, Iterable, Optional

from loguru import logger
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from playwright.async_api import Page

from scraper_utils.constants.time_constant import MS1000
from scraper_utils.enums.browser_enum import ResourceType
from scraper_utils.exceptions.browser_exception import PlaywrightError
from scraper_utils.utils.amazon_url_util import (
    build_bsr_url,
    build_detail_url,
    build_new_releases_url,
    build_search_url,
    validate_asin,
)
from scraper_utils.utils.browser_util import (
    launch_persistent_browser,
    create_new_page,
    close_browser,
)
from scraper_utils.utils.other_util import any_none
from scraper_utils.utils.workbook_util import (
    read_workbook_sync,
    write_workbook_sync,
)


logger.remove()
logger.add(
    sys.stderr,
    format=(
        '[<green>{time:HH:mm:ss}</green>] [<level>{level:.3}</level>] '
        '[<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>] >>> '
        '<level>{message}</level>'
    ),
)

cur_work_dir = Path.cwd()

# 从 BSR 链接中提取 BSR 品类节点的正则表达式
bsr_url_node_pattern = re.compile(r'/(\d+)($|/|/ref)')


def load_bsr_url(workbook_path: Path, target_rows: Iterable[int]) -> Generator[str]:
    """读取表格，生成需要爬取的 bsr 链接"""
    logger.info(f'读取表格 "{workbook_path}"')

    workbook = read_workbook_sync(file=workbook_path, read_only=True)
    sheet: Worksheet = workbook.active
    for row in target_rows:
        de_bsr_url: Optional[str] = sheet[f'C{row}'].value

        if de_bsr_url is None:  # 如果为空就跳过该行
            continue

        yield de_bsr_url


async def start_scrape(cwd: Path):
    """"""
    target_rows = range(2, 10)  # 目标行

    # 存储结果用的工作簿
    result_workbook = Workbook()
    result_sheet: Worksheet = result_workbook.active

    # 创建标题行
    result_sheet['A1'] = '德国品类名'
    result_sheet['B1'] = '德国 BSR 链接'
    result_sheet['C1'] = '德国新品链接'
    result_sheet['D1'] = '美国品类名'
    result_sheet['E1'] = '美国 BSR 链接'
    result_sheet['F1'] = '美国新品链接'

    try:
        for row, origin_bsr_url in enumerate(
            load_bsr_url(cwd.joinpath('temp/类目对应bsr.xlsx'), target_rows), start=2
        ):
            logger.debug(f'正在处理第 {row} 行')
            try:

                # 解析 bsr 页
                bsr_page = await create_new_page()
                await bsr_page.goto(origin_bsr_url, timeout=60 * MS1000)
                origin_category = await parse_bsr_page(bsr_page)
                await bsr_page.close()

                await asyncio.sleep(10 + random.uniform(0, 10))  # 随机等待 10-20 秒

                # 如果解析到的 BSR 类目为空，就跳过
                if origin_category is None:
                    logger.warning(f'解析到的 BSR 品类为空')
                    continue

                # 解析搜索页
                category_search_url = build_search_url(
                    site='us', keyword=origin_category, language='en'
                )
                search_page = await create_new_page()
                await search_page.goto(category_search_url, timeout=60 * MS1000)
                first_search_asin = await parse_search_page(search_page)
                await search_page.close()

                await asyncio.sleep(10 + random.uniform(0, 10))  # 随机等待 10-20 秒

                # 如果解析到的 ASIN 为空，就跳过
                if first_search_asin is None:
                    logger.warning('解析到的 ASIN 为空')
                    continue

                # 解析详情页
                detail_url = build_detail_url(site='us', asin=first_search_asin, language='en')
                detail_page = await create_new_page()
                await detail_page.goto(detail_url, timeout=60 * MS1000)
                target_category, target_node = await parse_detail_page(detail_page)
                await detail_page.close()

                await asyncio.sleep(10 + random.uniform(0, 10))  # 随机等待 10-20 秒

            except PlaywrightError as pe:
                logger.error(pe)

            else:

                # 如果解析到的 BSR 品类节点为空就跳过
                if target_node is None:
                    logger.warning('解析到的 BSR 品类节点为空')
                    continue

                target_bsr_url = build_bsr_url(site='us', node=target_node, language='en')
                logger.success(f'找到 BSR 品类链接 "{target_bsr_url}"')

                origin_category
                origin_bsr_url
                origin_new_url = None
                origin_bsr_node_match = bsr_url_node_pattern.search(origin_bsr_url)
                if origin_bsr_node_match is not None:
                    origin_new_url = build_new_releases_url(
                        site='de', node=origin_bsr_node_match.group(1), language='en'
                    )

                target_category
                target_bsr_url
                target_new_url = build_new_releases_url(site='us', node=target_node, language='en')

                result_sheet[f'A{row}'] = origin_category
                result_sheet[f'B{row}'] = origin_bsr_url
                result_sheet[f'C{row}'] = origin_new_url
                result_sheet[f'D{row}'] = target_category
                result_sheet[f'E{row}'] = target_bsr_url
                result_sheet[f'F{row}'] = target_new_url

            finally:
                await asyncio.sleep(10 + random.uniform(0, 10))  # 随机等待 10-20 秒

    finally:
        result_path = write_workbook_sync(
            file=cwd.joinpath('temp/类目对应bsr_结果.xlsx'), workbook=result_workbook
        )
        logger.success(f'爬取结果已保存至 "{result_path}"')


async def parse_bsr_page(page: Page) -> Optional[str]:
    """解析 bsr 页，拿到 bsr 标签"""
    logger.debug(f'解析 BSR 页 "{page.url}"')

    card_title_tag = page.locator('//div[@class="_cDEzb_card-title_2sYgw"]/h1')
    if await card_title_tag.count() > 0:
        card_title_text = await card_title_tag.inner_text(timeout=MS1000)
        bsr_category_match = re.search(r'Best Sellers in (.*)', card_title_text)

        if bsr_category_match is None:
            logger.warning(f'正则表达式匹配不到 BSR 品类 "{card_title_text}"')

        bsr_category: str = bsr_category_match.group(1)
        logger.debug(f'解析到 BSR 品类 "{bsr_category}"')
        return bsr_category

    logger.warning('定位不到 BSR 品类标签 "//div[@class="_cDEzb_card-title_2sYgw"]/h1"')
    return None


async def parse_search_page(page: Page) -> Optional[str]:
    """解析搜索页，拿到第一个搜索结果的产品 asin"""
    logger.debug(f'解析搜索页 "{page.url}"')

    listitem_tag = page.locator('//div[@role="listitem" and @data-asin!=""]')
    if await listitem_tag.count() > 0:
        asin = await listitem_tag.first.get_attribute('data-asin')

        if asin is None:  # 理论上不需要判断为空
            logger.warning('解析到的 ASIN 为空')
            return None

        if not validate_asin(asin=asin):
            logger.warning(f'解析到的 "{asin}" 不符合 ASIN 规范')

        return asin

    logger.warning('定位不到产品标签 "//div[@role="listitem" and @data-asin!=""]"')
    return None


async def parse_detail_page(page: Page) -> tuple[str, str] | tuple[None, None]:
    """解析产品详情页，拿到该产品的 bsr 链接"""
    logger.debug(f'解析详情页 "{page.url}"')

    # 匹配 Best Sellers Rank 的表头的正则表达式
    bsr_table_head_pattern = re.compile(r'Best Sellers Rank')

    # Product information
    productDetails_th_tags = (
        await page.locator('//table[@id="productDetails_detailBullets_sections1"]//th').all()
        + await page.locator('//table[@id="productDetails_techSpec_section_1"]//th').all()
    )
    for productDetails_th_tag in productDetails_th_tags:
        th_text = await productDetails_th_tag.inner_text(timeout=MS1000)
        if bsr_table_head_pattern.search(th_text) is not None:
            bsr_url_a_tags = productDetails_th_tag.locator(
                'xpath=/following-sibling::td//a[@href!=""]'
            )
            if await bsr_url_a_tags.count() > 0:
                bsr_category = await bsr_url_a_tags.last.inner_text(timeout=MS1000)
                bsr_url = await bsr_url_a_tags.last.get_attribute('href', timeout=MS1000)

                if bsr_url is None:  # 理论上不需要判断为空
                    logger.warning(f'找到 BSR 品类 "{bsr_category}" 但 href 属性为空')
                    return None, None

                bsr_url_node_match = bsr_url_node_pattern.search(bsr_url)
                if bsr_url_node_match is None:
                    logger.debug(
                        f'找到 BSR 品类 "{bsr_category}" "{bsr_url}" 但正则表达式匹配不到品类节点'
                    )
                    return None, None

                bsr_url_node: str = bsr_url_node_match.group(1)
                logger.debug(f'找到 BSR 品类 "{bsr_category}" 的节点 "{bsr_url_node}"')
                return bsr_category, bsr_url_node

    # Product details
    detailBulletsWrapper_span_tags = (
        await page.locator(
            '#detailBulletsWrapper_feature_div>#detailBullets_feature_div>ul>li>span .a-text-bold'
        ).all()
        + await page.locator('#detailBulletsWrapper_feature_div>ul>li>span .a-text-bold').all()
    )
    for detailBulletsWrapper_span_tag in detailBulletsWrapper_span_tags:
        span_text = await detailBulletsWrapper_span_tag.inner_text(timeout=MS1000)
        if bsr_table_head_pattern.search(span_text) is not None:
            bsr_url_a_tags = detailBulletsWrapper_span_tag.locator('xpath=/parent::*//a[@href!=""]')
            if await bsr_url_a_tags.count() > 0:
                bsr_category = await bsr_url_a_tags.last.inner_text(timeout=MS1000)
                bsr_url = await bsr_url_a_tags.last.get_attribute('href', timeout=MS1000)

                if bsr_url is None:  # 理论上不需要判断为空
                    logger.warning(f'找到 BSR 品类 "{bsr_category}" 但 href 属性为空')
                    return None, None

                bsr_url_node_match = bsr_url_node_pattern.search(bsr_url)
                if bsr_url_node_match is None:
                    logger.debug(
                        f'找到 BSR 品类 "{bsr_category}" "{bsr_url}" 但正则表达式匹配不到品类节点'
                    )
                    return None, None

                bsr_url_node: str = bsr_url_node_match.group(1)
                logger.debug(f'找到 BSR 品类 "{bsr_category}" 的节点 "{bsr_url_node}"')
                return bsr_category, bsr_url_node

    logger.warning('找不到 BSR 品类')
    return None, None


if __name__ == '__main__':

    async def test():
        """测试"""
        page = await create_new_page()
        # await page.goto('https://www.amazon.com/-/en/dp/B0DQPX4CVX', timeout=0)
        await page.goto('https://www.amazon.de/-/en/dp/B09BVNG8GG', timeout=0)
        await parse_detail_page(page)

    async def main():
        logger.info('程序开始')
        start_time = time.perf_counter()

        abort_res = (
            ResourceType.MEDIA,
            ResourceType.IMAGE,
            ResourceType.STYLESHEET,
            ResourceType.FONT,
        )
        await launch_persistent_browser(
            user_data_dir=cur_work_dir.joinpath('temp/chrome_data'),
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            channel='chrome',
            headless=False,
            timeout=120 * MS1000,
            stealth=True,
            abort_resources=abort_res,
        )
        ##########

        await start_scrape(cwd=cur_work_dir)
        # await test()

        ##########
        await close_browser()
        logger.success(f'程序结束，总用时 {round(time.perf_counter()-start_time, 2)} 秒')

    asyncio.run(main())
