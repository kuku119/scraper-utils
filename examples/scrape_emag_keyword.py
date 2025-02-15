"""
根据关键词爬取 emag 搜索页的产品 url
"""

import asyncio
from pathlib import Path

from playwright.async_api import Page


async def start_request():
    """打开浏览器，初始化页面，读取关键词，根据关键词生成搜索页，生成加载完的页面"""
    # TODO


async def parse_search_page(page: Page) -> list[str]:
    """解析页面，返回产品 url 列表"""
    # TODO


if __name__ == '__main__':
    cwd = Path().cwd()

    async def main():
        pass

    asyncio.run(main())
