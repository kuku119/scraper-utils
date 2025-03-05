"""
eMAG 相关相关工具
"""

from __future__ import annotations

import re as _re
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as _quote_plus


if TYPE_CHECKING:
    from typing import Generator, Optional

__all__ = [
    'BASE_URL',
    'build_search_url',
    'build_search_urls',
    'validate_pnk',
    'build_product_url',
    'parse_pnk',
    'clean_product_image_url',
]

BASE_URL = 'https://www.emag.ro'


def build_search_url(keyword: str, page: int = 1) -> str:
    """构造搜索页链接"""
    if page < 1:
        raise ValueError(f'page 必须大于 0，page={page}')
    if keyword is None or len(keyword) == 0:
        raise ValueError(f'keyword 不能为空')

    keyword = _quote_plus(keyword)
    if page == 1:
        result = f'{BASE_URL}/search/{keyword}'
    else:
        result = f'{BASE_URL}/search/{keyword}/p{page}'

    return result


def build_search_urls(keyword: str, max_page: int = 1) -> Generator[str]:
    """构造多页搜索页链接"""
    return (build_search_url(keyword=keyword, page=i) for i in range(1, max_page + 1))


def validate_pnk(pnk: str) -> bool:
    """验证是否符合 pnk 格式"""
    if len(pnk) != 9:
        return False
    return _re.match(r'^[0-9A-Z]{9}$', pnk) is not None


def build_product_url(pnk: str) -> str:
    """构造产品页链接"""
    if not validate_pnk(pnk=pnk):
        raise ValueError('pnk 不能为空')
    return f'{BASE_URL}/-/pd/{pnk}'


def parse_pnk(url: str) -> Optional[str]:
    """从链接中提取 pnk"""
    m = _re.search(r'/pd/([0-9A-Z]{9})($|/|\?)', url)
    if m is not None:
        return m.group(1)
    return None


def clean_product_image_url(url: str) -> str:
    """清理产品图 url，返回原图链接"""
    return _re.sub(r'\?width=\d+&height=\d+&hash=[0-9A-F]+', '', url)
