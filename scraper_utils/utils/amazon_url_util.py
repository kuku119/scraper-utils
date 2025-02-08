"""
亚马逊 URL 相关工具
"""

from __future__ import annotations

import re as __re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as __quote_plus

from ..enums.amazon_site_enum import AmazonSite as __AmazonSite

if TYPE_CHECKING:
    from typing import Generator, Optional


def is_asin(asin: Optional[str]) -> bool:
    """判断是否符合 ASIN 格式"""
    if asin is None or len(asin) != 10:
        return False
    return all(('0' <= c <= '9') or ('A' <= c <= 'Z') for c in asin)


def build_search_url(site: str, keyword: str, page: int = 1) -> str:
    """根据站点、关键词、页码构造关键词搜索页 url"""
    if page < 1:
        raise ValueError(f'Page must be greater than 0, page={page}')

    if page == 1:
        return __AmazonSite.get_url(site=site) + '/s?k=' + __quote_plus(keyword)
    else:
        return __AmazonSite.get_url(site=site) + '/s?k=' + __quote_plus(keyword) + '&page=' + str(page)


def build_search_urls(site: str, keyword: str, max_page: int = 1) -> Generator[str, None, None]:
    """根据站点、关键词、最大页码构造多个关键词搜索页 url"""
    for page in range(1, max_page + 1):
        yield build_search_url(site=site, keyword=keyword, page=page)


def build_detail_url(site: str, asin: str) -> str:
    """根据站点、ASIN 构造产品详情页 url"""
    if is_asin(asin):
        return __AmazonSite.get_url(site=site) + '/dp/' + asin
    raise ValueError(f'ASIN {asin} is not valid')


def clean_product_image_url(url: str) -> str:
    """清理产品图 url，提取产品图的原图 url"""
    return __re.sub(r'\._.*?_\.', '.', url)
