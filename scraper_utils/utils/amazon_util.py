"""
亚马逊相关工具
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
    """根据站点、关键词、页码构造关键词搜索页链接"""
    if page < 1:
        raise ValueError(f'page 必须大于 0，page={page}')
    if len(keyword) == 0:
        raise ValueError(f'keyword 不能为空')

    keyword = _quote_plus(keyword)

    if page == 1:
        result = f'{AmazonSite.get_url(site=site)}/s?k={keyword}'
    else:
        result = f'{AmazonSite.get_url(site=site)}/s?k={keyword}&page={page}'

    if language is not None:
        result += f'&language={language}'

    return result


def build_search_urls(site: str, keyword: str, max_page: int = 1) -> Generator[str]:
    """根据站点、关键词、最大页码构造多页关键词搜索页链接"""
    return (build_search_url(site=site, keyword=keyword, page=i) for i in range(1, max_page + 1))


def validate_asin(asin: str) -> bool:
    """验证是否符合 ASIN 格式"""
    if len(asin) != 10:
        return False
    # return _asin_pattern.match(asin) is not None
    return _re.match(r'^[A-Z0-9]{10}$', asin) is not None


def build_detail_url(site: str, asin: str, language: Optional[str] = None) -> str:
    """根据站点、ASIN 构造产品详情页链接"""
    if validate_asin(asin):
        if language is None:
            result = f'{AmazonSite.get_url(site=site)}/dp/{asin}'
        else:
            result = f'{AmazonSite.get_url(site=site)}/-/{language}/dp/{asin}'

        return result

    raise ValueError(f'"{asin}" 不符合 ASIN 规范')


def build_bsr_url(site: str, node: str, language: Optional[str] = None) -> str:
    """根据站点、BSR 节点构造 BSR 链接"""
    if _is_number(s=node):
        if language is None:
            result = f'{AmazonSite.get_url(site=site)}/bestsellers/-/{node}'
        else:
            result = f'{AmazonSite.get_url(site=site)}/-/{language}/bestsellers/-/{node}'

        return result

    raise ValueError(f'"{node}" 不符合节点规范')


def build_new_releases_url(site: str, node: str, language: Optional[str] = None) -> str:
    """根据站点、节点构造新品链接"""
    if _is_number(s=node):
        if language is None:
            result = f'{AmazonSite.get_url(site=site)}/new-releases/-/{node}'
        else:
            result = f'{AmazonSite.get_url(site=site)}/-/{language}/new-releases/-/{node}'

        return result

    raise ValueError(f'"{node}" 不符合节点规范')


def clean_product_image_url(url: str) -> str:
    """清理产品图 url，提取产品图的原图链接"""
    return _re.sub(r'\._.*?_\.', '.', url)
