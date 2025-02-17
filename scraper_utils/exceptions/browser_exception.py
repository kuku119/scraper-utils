"""
浏览器相关异常
"""

from playwright.async_api import Error as PlaywrightError

__all__ = [
    'PlaywrightError',
    'BaseBrowserError',
    'BrowserLaunchedError',
    'BrowserClosedError',
]


class BaseBrowserError(Exception):
    """浏览器相关异常的基类"""

    pass


class BrowserLaunchedError(BaseBrowserError):
    """浏览器已经启动时的异常"""

    pass


class BrowserClosedError(BaseBrowserError):
    """浏览器已经关闭或还未启动时的异常"""

    pass


class StealthError(BaseBrowserError):
    """尝试隐藏页面时的异常"""

    pass
