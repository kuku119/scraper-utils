"""Scrapy 中间件的基类"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Iterable, Optional, Self

    from scrapy.crawler import Crawler
    from scrapy.http.request import Request
    from scrapy.http.response import Response
    from scrapy.item import Item
    from scrapy.spiders import Spider


__all__ = [
    'DownloadMiddlewareABC',
    'SpiderMiddlewareABC',
]


class DownloadMiddlewareABC(ABC):
    """下载中间件的抽象基类"""

    @classmethod
    @abstractmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        """返回中间件实例"""

    @abstractmethod
    def process_request(
        self,
        request: Request,
        spider: Spider,
    ) -> Optional[Request | Response]:
        """在下载前处理请求"""

    @abstractmethod
    def process_response(
        self,
        request: Request,
        response: Response,
        spider: Spider,
    ) -> Request | Response:
        """在下载后处理响应"""

    @abstractmethod
    def process_exception(
        self,
        request: Request,
        exception: Exception,
        spider: Spider,
    ) -> Optional[Request | Response]:
        """处理异常"""


class SpiderMiddlewareABC(ABC):
    """爬虫中间件的抽象基类"""

    @classmethod
    @abstractmethod
    def from_crawler(cls, crawler: Crawler) -> Self:
        """返回中间件实例"""

    @abstractmethod
    def process_spider_input(
        self,
        response: Response,
        spider: Spider,
    ) -> None:
        """在输入到 `spider` 前处理响应"""

    @abstractmethod
    def process_spider_output(
        self,
        response: Response,
        result: Iterable[Item | Request],
        spider: Spider,
    ) -> Iterable[Item | Request]:
        """处理从 `spider` 输出的结果或请求"""

    @abstractmethod
    def process_spider_exception(
        self,
        response: Response,
        exception: Exception,
        spider: Spider,
    ) -> Optional[Iterable[Item | Request]]:
        """处理异常"""
