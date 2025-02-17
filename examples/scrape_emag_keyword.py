"""
根据关键词爬取 emag 搜索页的产品 url
"""

import asyncio
import re
from asyncio.exceptions import CancelledError
from dataclasses import dataclass, field
from pathlib import Path
from random import randint, uniform
from re import Pattern
from time import perf_counter
from typing import Optional, Self, Sequence

from aiohttp import ClientResponseError, ClientSession
from fake_http_header import FakeHttpHeader
from loguru import logger
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.fills import PatternFill
from openpyxl.styles.fonts import Font
from openpyxl.workbook import Workbook
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.worksheet.worksheet import Worksheet
from playwright.async_api import Page

from scraper_utils.constants.time_constant import MS1000
from scraper_utils.enums.browser_enum import ResourceType
from scraper_utils.exceptions.browser_exception import PlaywrightError
from scraper_utils.utils.browser_util import launch_persistent_browser, close_browser, create_new_page
from scraper_utils.utils.emag_url_util import build_search_urls, build_product_url, clean_product_image_url
from scraper_utils.utils.file_util import write_bytes_async
from scraper_utils.utils.workbook_util import (
    read_workbook_sync,
    write_workbook_sync,
    string_column_to_integer_column as s2i,
)


@dataclass
class ItemCardParseResult:
    pnk: str
    top_favorite: bool = False  # 是否带有 top 标志
    image_url: Optional[str] = None  # 产品图 url
    review_count: Optional[int] = None  # 评论数
    price: Optional[float] = None  # 价格

    def __hash__(self):
        return hash(self.pnk)

    def __eq__(self, other: Self):
        return self.pnk == other.pnk

    @property
    def url(self) -> str:
        """产品详情页 url"""
        return build_product_url(pnk=self.pnk)

    @property
    def origin_image_url(self) -> Optional[str]:
        """产品图原图 url"""
        if self.image_url is not None:
            return clean_product_image_url(url=self.image_url)
        return None


@dataclass
class KeywordSearchResults:
    keyword: str
    products: list[ItemCardParseResult] = field(default_factory=list)

    def __add__(self, other: Self):
        """合并两个结果，并去除其中的重复产品"""
        if self.keyword != other.keyword:
            raise ValueError('两者的关键词不同，无法合并')
        return KeywordSearchResults(
            keyword=self.keyword,
            products=list(dict.fromkeys(self.products + other.products)),
        )


async def start_scrape(cwd: Path, target_rows: Sequence[int]):
    """打开浏览器，初始化页面，读取关键词，根据关键词生成搜索页，生成加载完的页面"""
    # 读取工作簿
    input_workbook_path = cwd.joinpath('temp/scrape_emag_keyword_示例关键词.xlsx')
    logger.info(f'读取表格 "{input_workbook_path}"')
    input_workbook = read_workbook_sync(
        file=input_workbook_path,
        read_only=True,
    )
    keyword_sheet: Worksheet = input_workbook.active

    ##########

    # 特定单元格的样式
    red_bold_font = Font(color='FF0000', bold=True)  # 红字、加粗，标题栏用
    yellow_fill_color = PatternFill(fill_type='solid', fgColor='FFFF00')  # 黄色前景色，标题栏用
    hyperlink_font = Font(color='0000FF', underline='single')  # 超链接字体，蓝色下划线，超链接单元格用
    align = Alignment(wrap_text=True, horizontal='center', vertical='center')  # 居中、自动换行

    # 准备用于存储结果的工作簿
    result_workbook = Workbook()
    result_workbook.remove(result_workbook.active)  # 移除第一个工作表

    ##########

    # 遍历关键词用于爬取
    pnk_pattern = re.compile(r'/pd/([0-9A-Z]{9})(/|$)')
    review_count_pattern = re.compile(r'\((\d+)\)')
    price_pattern = re.compile(r'[^\d,]')

    total_result: list[KeywordSearchResults] = list()  # 整个关键词表格的搜索结果

    # 下载产品图用
    client_session = ClientSession()
    fake_header = FakeHttpHeader()

    try:
        for row in target_rows:
            keyword = keyword_sheet.cell(row=row, column=s2i('A')).value
            if keyword is None:  # 跳过空行
                continue
            keyword = str(keyword)
            one_keyword_result = KeywordSearchResults(keyword=keyword, products=list())  # 单个关键词的爬取结果
            logger.info(f'开始爬取关键词 "{keyword}"')
            # 爬取关键词搜索结果
            for url in build_search_urls(keyword=keyword, max_page=1):
                page = await create_new_page()
                try:
                    await page.goto(url, timeout=60 * MS1000)
                except PlaywrightError as pe:
                    logger.error(pe)
                else:
                    one_page_result = KeywordSearchResults(
                        keyword=keyword,
                        products=await parse_search_page(
                            page=page,
                            pnk_pattern=pnk_pattern,
                            review_count_pattern=review_count_pattern,
                            price_pattern=price_pattern,
                        ),
                    )  # 单个页面的爬取结果
                    one_keyword_result = one_keyword_result + one_page_result
                finally:
                    await asyncio.sleep(30 + randint(0, 30))  # 每爬完一个 url 就随机等待 30-60 秒
                    await page.close()
            total_result.append(one_keyword_result)
            logger.success(f'关键词 "{keyword}" 爬取结束')

            ##########

            # 每爬完一个关键词就写入一个工作表
            one_keyword_result_sheet: Worksheet = result_workbook.create_sheet(
                title=keyword if len(keyword) < 28 else keyword[:28] + '...',
            )  # sheet_name 有长度上限，超出部分就用省略号代替

            # 创建标题行
            one_keyword_result_sheet['A1'] = '产品链接'
            one_keyword_result_sheet['B1'] = '产品图'
            one_keyword_result_sheet['C1'] = '是否有 Top Favorite'
            one_keyword_result_sheet['D1'] = '评论数'
            one_keyword_result_sheet['E1'] = '价格'

            for col in range(1, 6):  # 设置标题行的样式
                one_keyword_result_sheet.cell(1, col).alignment = align
                one_keyword_result_sheet.cell(1, col).font = red_bold_font
                one_keyword_result_sheet.cell(1, col).fill = yellow_fill_color

            # 设置图片列的宽度
            one_keyword_result_sheet.column_dimensions['B'].width = 40

            # 遍历爬取结果，插入到工作表中
            for result_row, product_result in enumerate(one_keyword_result.products, start=2):
                # 设置该行的高度
                one_keyword_result_sheet.row_dimensions[result_row].height = 40

                # 产品详情页 url
                one_keyword_result_sheet.cell(row=result_row, column=1, value=product_result.url)
                one_keyword_result_sheet.cell(row=result_row, column=1).alignment = align

                # 产品图
                if product_result.image_url is not None:
                    # TODO 插入图片
                    one_keyword_result_sheet.cell(row=result_row, column=2, value=product_result.origin_image_url)
                    one_keyword_result_sheet.cell(row=result_row, column=2).alignment = align
                    one_keyword_result_sheet.cell(row=result_row, column=2).hyperlink = Hyperlink(
                        ref=product_result.origin_image_url,
                        target=product_result.origin_image_url,
                    )
                    one_keyword_result_sheet.cell(row=result_row, column=2).font = hyperlink_font
                    one_keyword_result_sheet.cell(row=result_row, column=2)

                # Top Favorite
                one_keyword_result_sheet.cell(row=result_row, column=3, value=str(product_result.top_favorite))
                one_keyword_result_sheet.cell(row=result_row, column=3).alignment = align

                # 评论数
                if product_result.review_count is not None:
                    one_keyword_result_sheet.cell(row=result_row, column=4, value=product_result.review_count)
                    one_keyword_result_sheet.cell(row=result_row, column=4).alignment = align

                # 价格
                if product_result.price is not None:
                    one_keyword_result_sheet.cell(row=result_row, column=5, value=product_result.price)
                    one_keyword_result_sheet.cell(row=result_row, column=5).alignment = align

    # Ctrl + C 不会退出程序，而是停止爬取并运行下面的结果保存
    except CancelledError:
        logger.warning('CancelledError: 爬取任务被中断')
    except KeyboardInterrupt:
        logger.warning('KeyboardInterrupt: 爬取任务被中断')
    finally:
        await client_session.close()
        result_path = write_workbook_sync(
            file=cwd.joinpath(f'temp/scrape_emag_keyword_结果_{min(target_rows)}-{max(target_rows)}.xlsx'),
            workbook=result_workbook,
        )
        logger.success(f'结果已保存至 "{result_path}"')


async def parse_search_page(
    page: Page,
    pnk_pattern: Pattern[str],
    review_count_pattern: Pattern[str],
    price_pattern: Pattern[str],
) -> list[ItemCardParseResult]:
    """解析页面

    解析:
    1. 产品 pnk
    2. 是否有 Top Favorite 标志
    3. 产品图
    4. 评论数
    5. 价格
    """
    logger.debug(f'解析页面 "{page.url}"')

    # 模拟鼠标滚轮向下滚动网页，直至 item_card_tag 数量达标或者时间超时
    wheel_start_time = perf_counter()
    while True:
        item_card_tags_1 = page.locator(
            '//div[@class="card-item card-standard js-product-data js-card-clickable " and @data-url!=""]'
        )
        item_card_tags_2 = page.locator(
            '//div[@class="card-item card-fashion js-product-data js-card-clickable" and @data-url!=""]'
        )

        item_card_tag_count = await item_card_tags_1.count() + await item_card_tags_2.count()
        if item_card_tag_count >= 72:  # 目标数量 72
            break

        # 随机向下滚动
        await page.mouse.wheel(delta_y=randint(500, 1000), delta_x=0)
        await page.wait_for_timeout(uniform(0, 0.5) * MS1000)

        # 一定时间后后数量还不够，就有多少爬多少（有些关键词的搜索结果就那么多）
        if perf_counter() - wheel_start_time >= 10:  # 10 秒
            break
    logger.debug(f'定位到 {item_card_tag_count} 个 item_card_tag')

    ##########

    # 提取各个 item_card_tag 的产品 pnk 并判断其是否有 top 标
    result: list[ItemCardParseResult] = list()
    for item_card_tag in await item_card_tags_1.all() + await item_card_tags_2.all():
        # 查找 pnk
        data_url: str = await item_card_tag.get_attribute('data-url', timeout=MS1000)
        pnk_match = pnk_pattern.search(data_url)
        if pnk_match is not None:
            pnk = pnk_match.group(1)  # 1. 产品 pnk

            # 判断是否有 top 标
            top_favorite_tag = item_card_tag.locator('//span[text()="Top Favorite"]')
            top_favorite = await top_favorite_tag.count() > 0  # 2. 是否有 Top Favorite 标志

            one_item = ItemCardParseResult(pnk=pnk, top_favorite=top_favorite)

            # 获取产品图 url
            image_url: Optional[str] = None  # 3. 产品图 url
            image_tag = item_card_tag.locator(
                '//div[@class="img-component position-relative card-v2-thumb-inner"]/img[@src!=""]'
            )
            if await image_tag.count() > 0:
                image_url = await image_tag.first.get_attribute('src', timeout=MS1000)
            if image_url is not None:
                image_url = clean_product_image_url(url=image_url)
            one_item.image_url = image_url

            # 获取评论数
            review_count: Optional[int] = None  # 4. 评论数
            review_count_tag = item_card_tag.locator(
                '//div[@class="star-rating-text "]/span[@class="visible-xs-inline-block " and text()!=""]'
            )
            if await review_count_tag.count() > 0:
                review_count_text = await review_count_tag.first.inner_text(timeout=MS1000)
                review_count_match = review_count_pattern.search(review_count_text)
                if review_count_match is not None:
                    review_count = int(review_count_match.group(1))
            one_item.review_count = review_count

            # 获取价格
            price: Optional[float] = None  # 5. 价格
            price_tag = item_card_tag.locator('//p[@class="product-new-price"]')
            if await price_tag.count() > 0:
                price_text = await price_tag.first.inner_text(timeout=MS1000)
                if len(price_text) > 0:
                    price = float(price_pattern.sub('', price_text).replace(',', '.'))
            one_item.price = price

            result.append(one_item)

    logger.debug(f'爬取到 {len(result)} 个产品')

    return result


async def download_product_image(cwd: Path, url: str, pnk: str, client: ClientSession, fake_header: dict[str, str]):
    """下载产品图，用 pnk 做图片的文件名"""
    img_format = ''  # TODO 如何确定文件后缀名？
    async with client.get(
        url=url,
        headers=fake_header,
    ) as response:
        try:
            response.raise_for_status()
        except ClientResponseError as cre:
            logger.error(cre)
        else:
            content = await response.read()
            await write_bytes_async(file=cwd.joinpath(f'temp/emag_product_images/{pnk}.{img_format}'), data=content)  # TODO 这个 data 怎么传？


if __name__ == '__main__':
    cwd = Path().cwd()

    async def main():
        start_time = perf_counter()
        logger.info('程序启动')

        abort_res: tuple[ResourceType, ...] = (ResourceType.MEDIA, ResourceType.IMAGE, ResourceType.STYLESHEET, ResourceType.FONT)
        await launch_persistent_browser(
            user_data_dir=cwd.joinpath('temp/chrome_data'),
            executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            channel='chrome',
            headless=False,
            timeout=60 * MS1000,
            stealth=True,
            abort_resources=abort_res,
        )

        target_rows = list(_ for _ in range(3, 149 + 1))
        await start_scrape(cwd=cwd, target_rows=target_rows)

        await close_browser()

        end_time = perf_counter()
        logger.info(f'程序结束，用时 {round(end_time-start_time, 2)} 秒')

    asyncio.run(main())
