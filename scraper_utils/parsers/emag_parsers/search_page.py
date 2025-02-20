"""
Emag 的搜索页面的解析器
"""

from __future__ import annotations

import random
import re
import time
from typing import TYPE_CHECKING

from ...constants.time_constant import MS1000
from ...utils.emag_url_util import (
    validate_pnk,
    build_product_url,
    clean_product_image_url,
)

if TYPE_CHECKING:
    from typing import Optional

    from playwright.async_api import Page

    from ...models.emag_models.search_page import KeywordResults, CardItem

__all__ = [
    'data_url_pnk_pattern',
    'parse_search',
]


# 解析 data-url 中的 pnk
data_url_pnk_pattern = re.compile(r'/pd/([0-9A-Z]{9})(/|$)')


async def parse_search(page: Page):
    """
    解析 Emag 的搜索页
    """

    # TODO

    # 模拟鼠标滚轮向下滚动网页，直至 item_card_tag 数量达标或者时间超时
    timeout_time = 10  # 超时为 10 秒
    expect_item_card_tag_count = 72  # 目标数量 72
    wheel_start_time = time.perf_counter()
    while True:
        item_card_tags = page.locator(
            '//div[(@class="card-item card-fashion js-product-data js-card-clickable" '
            'or @class="card-item card-standard js-product-data js-card-clickable ") '
            'and @data-url!=""]'
        )
        if await item_card_tags.count() >= expect_item_card_tag_count:
            break

        await page.mouse.wheel(delta_y=random.randint(500, 1000), delta_x=0)
        await page.wait_for_timeout(random.uniform(0, 0.5) * MS1000)

        if time.perf_counter() - wheel_start_time >= timeout_time:
            break

    for item_card_tag in await item_card_tags.all():

        data_url: str = await item_card_tag.get_attribute('data-url', timeout=MS1000)
        pnk_match = data_url_pnk_pattern.search(data_url)
        # 只有能解析到合法的 pnk 时才会继续解析这个 item-card 的余下内容
        if pnk_match is not None:
            pnk: str = pnk_match.group(1)
            if not validate_pnk(pnk=pnk):
                # 解析不到合法的 pnk 就跳过
                continue

            # 产品名
            product_title: Optional[str] = None
            product_title_tag = item_card_tag.locator(
                '//h2[@class="card-v2-title card-v2-fashion-title card-v2-title-wrapper"]' '/span'
            )
            if product_title_tag.count() == 0:
                continue
            product_title = await product_title_tag.inner_text(timeout=MS1000)

            # 存放单个 item-card 解析到的产品数据
            card_item = CardItem(
                pnk=pnk,
                title=product_title,
            )

            # 产品详情页 url
            product_url = build_product_url(pnk=pnk)
            if len(product_url) == 0:
                # 解析不到合法的产品 url 就跳过
                continue

            # 产品图
            product_image_url: Optional[str] = None
            product_image_tag = item_card_tag.locator(
                '//div[@class="img-component position-relative card-v2-thumb-inner"]'
                '/img[@src!=""]'
            )
            if await product_image_tag.count() > 0:
                product_image_url = await product_image_tag.get_attribute('src', timeout=MS1000)
            if product_image_url is not None:
                product_image_url = clean_product_image_url(url=product_image_url)
            card_item.image_url = product_image_url

            # Top Favorite 标志

            # 评论数

            # 价格
