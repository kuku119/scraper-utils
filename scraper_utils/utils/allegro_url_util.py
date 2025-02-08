"""
Allegro URL 相关工具
"""

from __future__ import annotations

import re as __re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as __quote_plus

if TYPE_CHECKING:
    from typing import Generator, Optional


BASE_URL = 'https://allegro.pl'
__clean_product_id_pattern = __re.compile(r'oferta/[a-zA-Z0-9-]*?(\d{11})')


def build_search_url(keyword: str, page: int = 1) -> str:
    """根据关键词和页码构造搜索页 URL"""
    keyword = __quote_plus(keyword)
    if page == 1:
        return f'{BASE_URL}/listing?string={keyword}'
    else:
        return f'{BASE_URL}/listing?string={keyword}&p={page}'


def build_search_urls(
    keyword: str,
    max_page: int = 1,
) -> Generator[str, None, None]:
    """根据关键词和页码构造搜索页 URL"""
    return (build_search_url(keyword=keyword, page=i) for i in range(1, max_page + 1))


def build_shop_url(shop_name: str) -> str:
    """根据店铺名构造店铺 URL"""
    return f'{BASE_URL}/uzytkownik/{shop_name}/sklep'


def build_product_url(product_id: str) -> str:
    """根据产品编号构造产品详情页 URL"""
    return f'{BASE_URL}/oferta/{product_id}'


def clean_product_id(url: str) -> Optional[str]:
    """清理产品详情页 URL，从中提取产品编号"""
    result = __clean_product_id_pattern.search(url)
    if result is not None:
        return result.group(1)
    return None
