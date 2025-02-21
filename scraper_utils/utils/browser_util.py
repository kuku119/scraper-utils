"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright as _async_playwright
from playwright_stealth import stealth_async as _stealth_async

from ..constants.time_constant import MS1000
from ..enums.browser_enum import ResourceType
from ..exceptions.browser_exception import (
    BrowserLaunchedError as _BrowserLaunchedError,
    BrowserClosedError as _BrowserClosedError,
    StealthError as _StealthError,
)

if TYPE_CHECKING:
    from typing import (
        Optional,
        Literal,
        Iterable,
        Sequence,
    )

    from playwright.async_api import (
        BrowserContext as PlaywrightBrowserContext,
        Browser as PlaywrightBrowser,
        Page as PlaywrightPage,
        Playwright,
    )
    from playwright._impl._api_structures import ProxySettings

    StrOrPath = str | Path


"""
可以通过多个 async_playwright().start() 同时启动多个 playwright 实例

在一个 playwright 实例下，
launch() 和 launch_persistent_context() 均可通过相同 executable_path 启动多个浏览器实例。
但需注意：
一个 user_data_dir 只能拿来启动一个持久化上下文，若使用同一 user_data_dir 启动多个持久化上下文，程序会崩溃
"""


__all__ = [
    'MS1000',
    'ResourceType',
    'BrowserManager',
    'PersistentContextManager',
    'stealth',
    'abort_resources',
]


class BrowserManager(AbstractAsyncContextManager):
    """
    启动非持久化浏览器

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

    `kwargs` 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch
    """

    def __init__(
        self,
        *,
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
    ):
        self.__executable_path = executable_path
        self.__channel = channel
        self.__headless = headless
        self.__slow_mo = slow_mo
        self.__timeout = timeout
        self.__args = args
        self.__ignore_default_args = ignore_default_args
        self.__proxy = proxy
        self.__chromium_sandbox = chromium_sandbox
        self.__kwargs = kwargs

        self.__playwright: Optional[Playwright] = None
        self.__browser: Optional[PlaywrightBrowser] = None

    async def start(self):
        self.__playwright = await _async_playwright().start()
        self.__browser = await self.__playwright.chromium.launch(
            executable_path=self.__executable_path,
            channel=self.__channel,
            headless=self.__headless,
            slow_mo=self.__slow_mo,
            timeout=self.__timeout,
            args=self.__args,
            ignore_default_args=self.__ignore_default_args,
            proxy=self.__proxy,
            chromium_sandbox=self.__chromium_sandbox,
            **self.__kwargs,
        )

        return self

    async def close(self):
        if self.__playwright is not None and self.__browser is not None:
            await self.__browser.close()
            self.__browser = None

            await self.__playwright.stop()
            self.__playwright = None

    @property
    def browser(self):
        """获取包含的浏览器实例，如果浏览器还未启动会报错"""
        if self.__browser is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        return self.__browser

    async def new_context(self) -> PlaywrightBrowserContext:
        """创建新的浏览器上下文"""
        # TODO
        if self.__browser is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        context = await self.__browser.new_context()
        return context

    async def new_page(self) -> PlaywrightPage:
        """创建新页面"""
        # TODO
        if self.__browser is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        page = await self.__browser.new_page()
        return page

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


class PersistentContextManager(AbstractAsyncContextManager):
    """
    启动持久化浏览器上下文

    ---

    1. `user_data_dir`:
    用户资料所在文件夹（如果设置的是相对路径，那是相对浏览器 exe 的路径，而不是相对当前工作目录）
    2. `executable_path`: 浏览器可执行文件路径
    3. `channel`: 浏览器类型
    4. `stealth`: 是否需要防爬虫检测
    5. `abort_res_types`: 要屏蔽的资源类型
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

    `kwargs` 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
    """

    # 持久化上下文们正在使用的 user_data_dir
    _used_user_data_dirs: list[Path] = []
    # TODO 未完善

    def __new__(cls, user_data_dir: StrOrPath, **kwargs):
        # 一个 user_data_dir 只能用来启动一个持久化上下文
        if any(p.samefile(user_data_dir) for p in cls._used_user_data_dirs):
            raise _BrowserLaunchedError(f'"{user_data_dir}" 已用于启动一个持久化上下文 ')
        return super().__new__(cls, user_data_dir=user_data_dir, **kwargs)

    def __init__(
        self,
        *,
        user_data_dir: StrOrPath,
        executable_path: StrOrPath,
        channel: Literal['chromium', 'chrome', 'msedge'],
        stealth: bool = False,
        abort_res_types: Optional[Iterable[ResourceType]] = None,
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
    ):
        self.__user_data_dir = user_data_dir
        self.__executable_path = executable_path
        self.__channel = channel
        self.__stealth = stealth
        self.__abort_res_types = abort_res_types
        self.__args = args
        self.__ignore_default_args = ignore_default_args
        self.__slow_mo = slow_mo
        self.__timeout = timeout
        self.__headless = headless
        self.__proxy = proxy
        self.__no_viewport = no_viewport
        self.__user_agent = user_agent
        self.__chromium_sandbox = chromium_sandbox
        self.__kwargs = kwargs

        self.__playwright: Optional[Playwright] = None
        self.__persistent_context: Optional[PlaywrightBrowserContext] = None

    async def start(self):
        self.__playwright = await _async_playwright().start()
        self.__persistent_context = await self.__playwright.chromium.launch_persistent_context(
            user_data_dir=self.__user_data_dir,
            executable_path=self.__executable_path,
            channel=self.__channel,
            args=self.__args,
            ignore_default_args=self.__ignore_default_args,
            slow_mo=self.__slow_mo,
            timeout=self.__timeout,
            headless=self.__headless,
            proxy=self.__proxy,
            no_viewport=self.__no_viewport,
            user_agent=self.__user_agent,
            chromium_sandbox=self.__chromium_sandbox,
            **self.__kwargs,
        )
        self._used_user_data_dirs.append(Path(self.__user_data_dir))

        # 防爬虫检测
        if self.__stealth is True:
            await stealth(context_page=self.__persistent_context)

        # 屏蔽特定资源
        if self.__abort_res_types is not None:
            await abort_resources(
                context_page=self.__persistent_context,
                res_types=self.__abort_res_types,
            )

        return self

    async def close(self):
        if self.__playwright is not None and self.__persistent_context is not None:
            await self.__persistent_context.close()
            self.__persistent_context = None

            await self.__playwright.stop()
            self.__playwright = None

            self._used_user_data_dirs.remove(self.__user_data_dir)

    @property
    def context(self):
        """获取包含的持久化上下文实例，如果浏览器还未启动会报错"""
        if self.__persistent_context is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        return self.__persistent_context

    async def new_page(self) -> PlaywrightPage:
        """创建新页面"""
        # TODO
        if self.__persistent_context is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        page = await self.__persistent_context.new_page()
        page.stealthed = self.__stealth
        return page

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


async def stealth(context_page: PlaywrightBrowserContext | PlaywrightPage) -> None:
    """防爬虫检测"""
    if getattr(context_page, 'stealthed', None) is True:
        raise _StealthError('该浏览器上下文或页面已经隐藏')
    await _stealth_async(context_page)
    context_page.stealthed = True


async def abort_resources(
    context_page: PlaywrightBrowserContext | PlaywrightPage,
    res_types: Iterable[ResourceType],
) -> None:
    """屏蔽特定资源的请求"""
    await context_page.route(
        '**/*',
        lambda r: (r.abort() if r.request.resource_type in res_types else r.continue_()),
    )


async def open_url(page: PlaywrightPage, url: str):
    """打开目标 url"""
    # TODO
