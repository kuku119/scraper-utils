"""
亚马逊 URL 相关工具
"""

from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as _quote_plus

from ..enums.amazon_enum import AmazonSite
from .text_util import is_number as _is_number

if TYPE_CHECKING:
    from typing import Generator, Optional


__all__ = [
    'AmazonSite',
    'validate_asin',
    'build_search_url',
    'build_search_urls',
    'build_detail_url',
    'build_bsr_url',
    'clean_product_image_url',
]


def build_search_url(site: str, keyword: str, page: int = 1, language: Optional[str] = None) -> str:
    """根据站点、关键词、页码构造关键词搜索页 url"""
    if page < 1:
        raise ValueError(f'page 必须大于 0，page={page}')
    if len(keyword) == 0:
        raise ValueError(f'keyword 不能为空')

    keyword = _quote_plus(keyword)
    result = (
        f'{AmazonSite.get_url(site=site)}/s?k={keyword}'
        if page == 1
        else f'{AmazonSite.get_url(site=site)}/s?k={keyword}&page={page}'
    )
    return result if language is None else result + f'&language={language}'


def build_search_urls(site: str, keyword: str, max_page: int = 1) -> Generator[str, None, None]:
    """根据站点、关键词、最大页码构造多个关键词搜索页 url"""
    return (build_search_url(site=site, keyword=keyword, page=i) for i in range(1, max_page + 1))


__asin_pattern = _re.compile(r'^[A-Z0-9]{10}$')


def validate_asin(asin: str) -> bool:
    """判断是否符合 ASIN 格式"""
    if len(asin) != 10:
        return False
    return __asin_pattern.match(asin) is not None


def build_detail_url(site: str, asin: str, language: Optional[str] = None) -> str:
    """根据站点、ASIN 构造产品详情页 url"""
    if validate_asin(asin):
        if language is None:
            return f'{AmazonSite.get_url(site=site)}/dp/{asin}'
        return f'{AmazonSite.get_url(site=site)}/-/{language}/dp/{asin}'
    raise ValueError(f'"{asin}" 不符合 ASIN 规范')


def build_bsr_url(site: str, node: str, language: Optional[str] = None) -> str:
    """根据站点、BSR 节点构造 BSR url"""
    if _is_number(s=node):
        # TODO 到底要怎么拼接 bsr 链接？
        # return f'{AmazonSite.get_url(site=site)}/-/zgbs/-/{node}'
        # return f'{AmazonSite.get_url(site=site)}/-/en/gp/bestsellers/-/{node}'
        if language is None:
            return f'{AmazonSite.get_url(site=site)}/bestsellers/-/{node}'
        else:
            return f'{AmazonSite.get_url(site=site)}/-/{language}/bestsellers/-/{node}'
    raise ValueError(f'"{node}" 不符合节点规范')


def clean_product_image_url(url: str) -> str:
    """清理产品图 url，提取产品图的原图 url"""
    return _re.sub(r'\._.*?_\.', '.', url)
