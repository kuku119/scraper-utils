"""
Emag URL 相关工具
"""

from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as _quote_plus


if TYPE_CHECKING:
    from typing import Generator

__all__ = [
    #
    'BASE_URL',
    #
    'build_search_url',
    'build_search_urls',
    #
    'build_product_url',
]

BASE_URL = 'https://www.emag.ro'


def build_search_url(
    keyword: str,
    page: int = 1,
) -> str:
    """构造搜索页 url"""
    if page < 1:
        raise ValueError(f'page 必须大于 0，page={page}')
    if keyword is None or len(keyword) == 0:
        raise ValueError(f'keyword 不能为空')

    keyword = _quote_plus(keyword)
    if page == 1:
        return f'{BASE_URL}/search/{keyword}'
    else:
        return f'{BASE_URL}/search/{keyword}/p{page}'


def build_search_urls(
    keyword: str,
    max_page: int = 1,
) -> Generator[str, None, None]:
    """构造多页的搜索页 url"""
    return (build_search_url(keyword=keyword, page=i) for i in range(1, max_page + 1))


def build_product_url(product_id: str):
    """构造产品页 url"""
    if product_id is None or len(product_id) == 0:
        raise ValueError('product_id 不能为空')
    return f'https://www.emag.ro/-/pd/{product_id}'


product_image_url_pattern = _re.compile(r'(.*?/images/res_[0-9a-zA-Z]+\.[a-zA-Z]{3})\??')


def clean_product_image_url(url: str):
    """清理产品图 url，返回原图 url"""
    return product_image_url_pattern.match(url).group(1)
