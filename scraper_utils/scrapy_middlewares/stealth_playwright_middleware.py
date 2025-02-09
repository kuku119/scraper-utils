"""
Stealth Playwright 中间件
"""

# TODO: 这东西写对了吗？

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright_stealth import stealth_async

if TYPE_CHECKING:
    from typing import Self, Optional

    from playwright.async_api import Page
    from scrapy.crawler import Crawler
    from scrapy.http.request import Request
    from scrapy.spiders import Spider
    from scrapy import signals


class StealthPlaywrightMiddleware:
    """
    往 Playwright 的 Page 注入 stealth 防爬虫检测的脚本

    ---

    设置 request.meta['stealth_page'] = True 来启用

    （还需设置 request.meta['playwright_include_page'] 确认要传递 Playwright 的 Page）
    """

    def __init__(self):
        pass

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        middleware = cls()
        return crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)

    def spider_opened(self, spider: Spider) -> None:
        pass

    async def process_request(self, request: Request, spider: Spider):
        playwright_page_flag: Optional[bool] = request.meta.get('playwright_include_page', None)
        stealth_page_flag: Optional[bool] = request.meta.get('stealth_page', None)
        if stealth_page_flag is True and playwright_page_flag is True:
            page: Optional[Page] = request.meta.get('playwright_page', None)
            if page is None:
                raise RuntimeError('playwright_page is None')
            else:
                await stealth_async(page)
