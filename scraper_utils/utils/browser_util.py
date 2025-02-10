"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

import asyncio as _asyncio
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright as _async_playwright
from playwright_stealth import stealth_async as _stealth_async

from ..exceptions.browser_exception import (
    BrowserLaunchedError as _BrowserLaunchedError,
    BrowserClosedError as _BrowserClosedError,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import (
        Optional,
        Literal,
    )

    from playwright.async_api import (
        Page as PlaywrightPage,
        BrowserContext as PlaywrightBrowserContext,
        Browser as PlaywrightBrowser,
    )
    from playwright_stealth import StealthConfig

    StrOrPath = str | Path


__all__ = [
    #
    'stealth_page',
    #
    'launch_browser',
    'launch_persistent_browser',
    #
    'close_browser',
]

__lock = _asyncio.Lock()

__browser_launched = False

__browser: Optional[PlaywrightBrowser] = None
__persistent_browser: Optional[PlaywrightBrowserContext] = None


async def launch_browser(
    executable_path: StrOrPath,
    browser_type: Literal['chromium', 'firefox', 'webkit'] = 'chromium',
    show_browser: bool = False,
    **kwargs,
) -> PlaywrightBrowser:
    """启动非持久化浏览器"""
    global __browser
    global __browser_launched

    async with __lock:
        if __browser_launched is True and __browser is None:
            raise _BrowserLaunchedError('不要在已经启动了持久化浏览器的情况下启动非持久化浏览器')

        if __browser_launched is False:
            kwargs['headless'] = not show_browser
            async with _async_playwright() as pwr:
                match browser_type:
                    case 'chromium':
                        browser: PlaywrightBrowser = pwr.chromium.launch(
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case 'firefox':
                        browser: PlaywrightBrowser = pwr.firefox.launch(
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case 'webkit':
                        browser: PlaywrightBrowser = pwr.webkit.launch(
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case _:
                        raise ValueError(f'错误的 browser_type: {browser_type}')

                __browser = browser
                __browser_launched = True

        return __browser


async def launch_persistent_browser(
    user_data_dir: StrOrPath,
    executable_path: StrOrPath,
    browser_type: Literal['chromium', 'firefox', 'webkit'] = 'chromium',
    show_browser: bool = False,
    **kwargs,
) -> PlaywrightBrowserContext:
    """启动持久化浏览器"""
    global __persistent_browser
    global __browser_launched

    async with __lock:
        if __browser_launched is True and __persistent_browser is None:
            raise _BrowserLaunchedError('不要在已经启动了非持久化浏览器的情况下启动持久化浏览器')

        if __browser_launched is False:
            kwargs['headless'] = not show_browser
            async with _async_playwright() as pwr:
                match browser_type:
                    case 'chromium':
                        browser_context: PlaywrightBrowserContext = pwr.chromium.launch_persistent_context(
                            user_data_dir=user_data_dir,
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case 'firefox':
                        browser_context: PlaywrightBrowserContext = pwr.firefox.launch_persistent_context(
                            user_data_dir=user_data_dir,
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case 'webkit':
                        browser_context: PlaywrightBrowserContext = pwr.webkit.launch_persistent_context(
                            user_data_dir=user_data_dir,
                            executable_path=executable_path,
                            **kwargs,
                        )
                    case _:
                        raise ValueError(f'错误的 browser_type: {browser_type}')

                __persistent_browser = browser_context
                __browser_launched = True

        return __persistent_browser


async def close_browser() -> None:
    """关闭浏览器"""
    global __browser_launched
    global __browser
    global __persistent_browser

    async with __lock:
        if __browser_launched is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        if __browser is not None:
            await __browser.close()

        if __persistent_browser is not None:
            await __persistent_browser.close()

        __browser_launched = False


async def stealth_page(
    page: PlaywrightPage,
    stealth_config: Optional[StealthConfig] = None,
) -> None:
    """防爬虫检测"""
    await _stealth_async(page, stealth_config)


async def create_new_page(
    stealth: bool = False,
    stealth_config: Optional[StealthConfig] = None,
) -> PlaywrightPage:
    """创建一个新页面"""
    if __browser_launched is False:
        raise _BrowserClosedError('浏览器已经关闭或还未启动')

    if __browser is not None:
        page: PlaywrightPage = await __browser.new_page()
    if __persistent_browser is not None:
        page: PlaywrightPage = await __persistent_browser.new_page()

    if stealth:
        await stealth_page(page=page, stealth_config=stealth_config)

    return page
