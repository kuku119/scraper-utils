"""用于 Scrapy-Playwright 隐藏的中间件"""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from ..meta_keys.scrapy_playwright_key import (
    PLAYWRIGHT_ENABLED,
    GET_PLAYWRIGHT_PAGE,
)
from ..utils.browser_util import stealth
from .base import ASyncDownloadMiddlewareABC

if TYPE_CHECKING:
    from typing import Self, Optional

    from scrapy.crawler import Crawler
    from scrapy.http.request import Request
    from scrapy.http.response import Response
    from scrapy.settings import Settings
    from scrapy.spiders import Spider
    from playwright.async_api import Page

META_KEY_NEED_STEALTH_PLAYWRIGHT_PAGE = 'stealth_playwright_page'


class PlaywrightPageStealthMiddleware(ASyncDownloadMiddlewareABC):
    """隐藏 `Page` 的爬虫特征"""

    # TODO: 未完成

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @override
    @classmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        """从 `crawler` 获取配置信息"""
        return cls(crawler.settings)

    @override
    async def process_request(self, request: Request, spider: Spider):
        """隐藏浏览器页面"""
        enable_playwright: bool = request.meta.get(PLAYWRIGHT_ENABLED, False)
        need_stealth: bool = request.meta.get(META_KEY_NEED_STEALTH_PLAYWRIGHT_PAGE, False)
        page: Optional[Page] = request.meta.get(GET_PLAYWRIGHT_PAGE, None)

        if enable_playwright and need_stealth and page is not None:
            await stealth(context_page=page)
