"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

import asyncio as _asyncio
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright as _async_playwright
from playwright_stealth import stealth_async as _stealth_async

from ..constants.time_constant import MS1000
from ..exceptions.browser_exception import (
    BrowserLaunchedError as _BrowserLaunchedError,
    BrowserClosedError as _BrowserClosedError,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import (
        Optional,
        Literal,
        Sequence,
    )

    from playwright.async_api import (
        BrowserContext as PlaywrightBrowserContext,
        Browser as PlaywrightBrowser,
        Page as PlaywrightPage,
        Playwright,
    )
    from playwright._impl._api_structures import ProxySettings
    from playwright_stealth import StealthConfig

    StrOrPath = str | Path


__all__ = [
    #
    'MS1000',
    #
    'launch_browser',
    'launch_persistent_browser',
    #
    'close_browser',
    #
    'create_new_page',
    #
    'stealth_page',
]

__lock = _asyncio.Lock()

__browser_launched = False

__playwright: Optional[Playwright] = None
__browser: Optional[PlaywrightBrowser] = None
__persistent_browser: Optional[PlaywrightBrowserContext] = None


async def launch_browser(
    executable_path: StrOrPath,
    channel: Literal['chromium', 'chrome', 'msedge'],
    headless: bool = True,
    slow_mo: float = 0,
    timeout: float = 30_000,
    args: Optional[Sequence[str]] = None,
    ignore_default_args: Sequence[str] = ('--enable-automation',),
    proxy: Optional[ProxySettings] = None,
    **kwargs,
) -> PlaywrightBrowser:
    """
    启动非持久化浏览器
    """
    global __browser_launched
    global __browser
    global __playwright

    async with __lock:
        if __browser_launched is True and __browser is None:
            raise _BrowserLaunchedError('不要在已经启动了持久化浏览器的情况下启动非持久化浏览器')

        if __browser_launched is False:
            pwr = await _async_playwright().start()
            browser: PlaywrightBrowser = await pwr.chromium.launch(
                args=args,
                channel=channel,
                executable_path=executable_path,
                headless=headless,
                ignore_default_args=ignore_default_args,
                proxy=proxy,
                slow_mo=slow_mo,
                timeout=timeout,
                **kwargs,
            )

            __playwright = pwr
            __browser = browser
            __browser_launched = True

        return __browser


async def launch_persistent_browser(
    user_data_dir: StrOrPath,
    executable_path: StrOrPath,
    channel: Literal['chromium', 'chrome', 'msedge'],
    args: Optional[Sequence[str]] = None,
    ignore_default_args: Sequence[str] = ('--enable-automation',),
    slow_mo: float = 0,
    timeout: float = 30_000,
    headless: bool = True,
    proxy: Optional[ProxySettings] = None,
    no_viewport: bool = True,
    user_agent: Optional[str] = None,
    **kwargs,
) -> PlaywrightBrowserContext:
    """
    启动持久化浏览器
    """
    global __browser_launched
    global __persistent_browser
    global __playwright

    async with __lock:
        if __browser_launched is True and __persistent_browser is None:
            raise _BrowserLaunchedError('不要在已经启动了非持久化浏览器的情况下启动持久化浏览器')

        if __browser_launched is False:
            pwr = await _async_playwright().start()
            browser: PlaywrightBrowserContext = await pwr.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=executable_path,
                channel=channel,
                # args=args,
                ignore_default_args=ignore_default_args,
                timeout=timeout,
                headless=headless,
                proxy=proxy,
                slow_mo=slow_mo,
                no_viewport=no_viewport,
                user_agent=user_agent,
                **kwargs,
            )

            __playwright = pwr
            __persistent_browser = browser
            __browser_launched = True

        return __persistent_browser


async def close_browser() -> None:
    """关闭浏览器"""
    global __browser_launched
    global __browser
    global __persistent_browser
    global __playwright

    async with __lock:
        if __browser_launched is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        if __browser is not None:
            await __browser.close()

        if __persistent_browser is not None:
            await __persistent_browser.close()

        if __playwright is not None:
            await __playwright.stop()

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
    abort_resources: Optional[Sequence[str]] = None,
    no_viewport: bool = True,
    **page_kwargs,
) -> PlaywrightPage:
    """创建一个新页面"""
    if __browser_launched is False:
        raise _BrowserClosedError('浏览器已经关闭或还未启动')

    if __browser is not None:
        page: PlaywrightPage = await __browser.new_page(
            no_viewport=no_viewport,
            **page_kwargs,
        )
    elif __persistent_browser is not None:
        page: PlaywrightPage = await __persistent_browser.new_page()
    else:
        raise _BrowserClosedError('没有已经启动的浏览器')

    if stealth is True:
        await stealth_page(page=page, stealth_config=stealth_config)

    if abort_resources is not None:
        for res in abort_resources:
            await page.route(res, lambda r: r.abort())

    return page
