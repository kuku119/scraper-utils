"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

import asyncio as _asyncio
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright as _async_playwright
from playwright_stealth import stealth_async as _stealth_async

from ..constants.time_constant import MS1000
from ..enums.browser_enum import ResourceType
from ..exceptions.browser_exception import (
    BrowserLaunchedError as _BrowserLaunchedError,
    BrowserClosedError as _BrowserClosedError,
    StealthError as _StealthError,
    PlaywrightError as _PlaywrightError,
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
    'MS1000',
    'ResourceType',
    'launch_browser',
    'launch_persistent_browser',
    'close_browser',
    'create_new_page',
    'stealth_page',
    'open_url',
]

__lock = _asyncio.Lock()

__browser_launched = False

__playwright: Optional[Playwright] = None
__browser: Optional[PlaywrightBrowser] = None  # 非持久浏览器
__persistent_browser: Optional[PlaywrightBrowserContext] = None  # 持久浏览器上下文


async def launch_browser(
    executable_path: StrOrPath,
    channel: Literal['chromium', 'chrome', 'msedge'],
    headless: bool = True,
    slow_mo: float = 0,
    timeout: float = 30_000,
    args: Optional[Sequence[str]] = None,
    ignore_default_args: Sequence[str] = ('--enable-automation',),
    proxy: Optional[ProxySettings] = None,
    chromium_sandbox: bool = False,
    **kwargs,
) -> PlaywrightBrowser:
    """
    启动非持久化浏览器（浏览器为全局单例）

    <b>程序结束前记得调用 `close_browser()` 关闭浏览器</b>

    ---

    1. `executable_path`: 浏览器可执行文件路径
    2. `channel`: 浏览器类型
    3. `headless`: 是否隐藏浏览器界面
    4. `slow_mo`: 浏览器各项操作的时间间隔（毫秒）
    5. `timeout`: 各项操作的超时时间（毫秒）
    6. `args`: 浏览器启动参数，chrome 参照：
    https://peter.sh/experiments/chromium-command-line-switches
    7. `ignore_default_args`: 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-option-ignore-default-args
    8. `proxy`: 代理
    9. `chromium_sandbox`: 是否启用 chromium 沙箱模式

    其余参数参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch

    ---

    如果已经启动其它浏览器，将会抛出 `BrowserLaunchedError` 异常
    """
    global __browser_launched
    global __browser
    global __playwright

    async with __lock:
        # 在浏览器已经启动就抛出异常
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
                chromium_sandbox=chromium_sandbox,
                **kwargs,
            )

            __playwright = pwr
            __browser = browser
            __browser_launched = True

            return __browser
        else:
            raise _BrowserLaunchedError('不要在已经启动浏览器的情况下再次启动')


async def launch_persistent_browser(
    user_data_dir: StrOrPath,
    executable_path: StrOrPath,
    channel: Literal['chromium', 'chrome', 'msedge'],
    stealth: bool = False,
    abort_resources: Optional[Sequence[ResourceType]] = None,
    args: Optional[Sequence[str]] = None,
    ignore_default_args: Sequence[str] = ('--enable-automation',),
    slow_mo: float = 0,
    timeout: float = 30_000,
    headless: bool = True,
    proxy: Optional[ProxySettings] = None,
    no_viewport: bool = True,
    user_agent: Optional[str] = None,
    chromium_sandbox: bool = False,
    **kwargs,
) -> PlaywrightBrowserContext:
    """
    启动持久化浏览器（浏览器为全局单例）

    <b>程序结束前记得调用 `close_browser()` 关闭浏览器</b>

    ---

    1. `user_data_dir`:
    用户资料所在文件夹（如果设置的是相对路径，那是相对浏览器 exe 的路径，而不是相对当前工作目录）
    2. `executable_path`: 浏览器可执行文件路径
    3. `channel`: 浏览器类型
    4. `stealth`: 是否需要防爬虫检测
    5. `abort_resources`: 要屏蔽的资源
    6. `args`: 浏览器启动参数，chrome 参照：
    https://peter.sh/experiments/chromium-command-line-switches
    7. `ignore_default_args`: 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context-option-ignore-default-args
    8. `slow_mo`: 浏览器各项操作的时间间隔（毫秒）
    9. `timeout`: 各项操作的超时时间（毫秒）
    10. `headless`: 是否隐藏浏览器界面
    11. `proxy`: 代理
    12. `no_viewport：参照：`
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context-option-no-viewport
    13. `user_agent`: User-Agent
    14. `chromium_sandbox`: 是否启用 chromium 沙箱模式

    其余参数参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context

    ---

    如果已经启动其它浏览器，将会抛出 `BrowserLaunchedError` 异常
    """
    global __browser_launched
    global __persistent_browser
    global __playwright

    async with __lock:
        # 在浏览器已经启动就抛出异常
        if __browser_launched is False:
            pwr = await _async_playwright().start()
            browser: PlaywrightBrowserContext = await pwr.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=executable_path,
                channel=channel,
                args=args,
                ignore_default_args=ignore_default_args,
                timeout=timeout,
                headless=headless,
                proxy=proxy,
                slow_mo=slow_mo,
                no_viewport=no_viewport,
                user_agent=user_agent,
                chromium_sandbox=chromium_sandbox,
                **kwargs,
            )

            if stealth:  # 防爬虫检测
                await _stealth_async(page=browser)
                browser.stealthed = True
            else:
                browser.stealthed = False

            if abort_resources is not None:  # 屏蔽特定资源
                await browser.route(
                    '**/*',
                    lambda r: (
                        r.abort() if r.request.resource_type in abort_resources else r.continue_()
                    ),
                )

            __playwright = pwr
            __persistent_browser = browser
            __browser_launched = True

            return __persistent_browser

        raise _BrowserLaunchedError('不要在已经启动浏览器的情况下再次启动')


async def close_browser() -> None:
    """关闭浏览器"""
    global __browser_launched
    global __browser
    global __persistent_browser
    global __playwright

    async with __lock:
        try:
            if __browser_launched is False:
                raise _BrowserClosedError('浏览器已经关闭或还未启动')

            if __browser is not None:
                await __browser.close()

            if __persistent_browser is not None:
                await __persistent_browser.close()

            if __playwright is not None:
                await __playwright.stop()
        except _PlaywrightError:
            pass
        finally:
            __browser_launched = False


async def stealth_page(
    page: PlaywrightPage,
    stealth_config: Optional[StealthConfig] = None,
) -> PlaywrightPage:
    """
    防爬虫检测

    ---

    1. `page`: 浏览器页面
    2. `stealth_config`: 防爬虫检测的相关设置
    """

    if getattr(page, 'stealthed', False) is True:
        raise _StealthError('该页面已经隐藏')
    else:
        await _stealth_async(page, stealth_config)
        page.stealthed = True

    return page


async def create_new_page(
    stealth: bool = False,
    stealth_config: Optional[StealthConfig] = None,
    abort_resources: Optional[Sequence[ResourceType]] = None,
    no_viewport: bool = True,
    **page_kwargs,
) -> PlaywrightPage:
    """
    创建一个新页面

    ---

    1. `stealth`: 页面是否需要防爬虫检测
    2. `stealth_config`: 防爬虫检测的相关设置
    3. `abort_resources`: 页面需要屏蔽的资源，参照 `enums.browser_enum.ResourceType`
    4. `no_viewport`: 非持久浏览器才有效

    `page_kwargs` 仅在非持久浏览器才有效

    其余参数参照：
    https://playwright.dev/python/docs/api/class-browser#browser-new-page
    """
    if __browser_launched is False:
        raise _BrowserClosedError('浏览器已经关闭或还未启动')

    # 判断当前启动的是持久浏览器还是非持久浏览器
    if __browser is not None:
        page: PlaywrightPage = await __browser.new_page(
            no_viewport=no_viewport,
            **page_kwargs,
        )
    elif __persistent_browser is not None:
        page: PlaywrightPage = await __persistent_browser.new_page()
    else:
        raise _BrowserClosedError('没有已经启动的浏览器')

    if stealth is True:  # 防爬虫检测
        await stealth_page(page=page, stealth_config=stealth_config)

    if abort_resources is not None:  # 屏蔽特定资源
        await page.route(
            '**/*',
            lambda r: r.abort() if r.request.resource_type in abort_resources else r.continue_(),
        )

    return page


async def open_url(page: PlaywrightPage, url: str):
    """
    打开目标 url

    ---

    # TODO 1. 超时重试 2. 检测响应是否正常
    """
