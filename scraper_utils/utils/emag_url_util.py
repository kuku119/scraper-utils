"""
Emag URL 相关工具
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote_plus as _quote_plus


if TYPE_CHECKING:
    from typing import Generator

__all__ = [
    'BASE_URL',
    'build_search_url',
    'build_search_urls',
]

BASE_URL = 'https://www.emag.ro'


def build_search_url(keyword: str, page: int = 1) -> str:
    """构造搜索页 url"""
    if page < 1:
        raise ValueError(f'page 必须大于 0，page={page}')

    keyword = _quote_plus(keyword)
    if page == 1:
        return f'{BASE_URL}/search/{keyword}'
    else:
        raise RuntimeError('# TODO')


def build_search_urls(keyword: str, max_page: int = 1) -> Generator[str, None, None]:
    """构造多页的搜索页 url"""
    return (build_search_url(keyword=keyword, page=i) for i in range(1, max_page + 1))
