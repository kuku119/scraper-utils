"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

from asyncio import Lock as _Lock
from pathlib import Path as _Path
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright as _async_playwright
from playwright_stealth import stealth_async as _stealth_async

from ..constants.time_constant import MS1000
from ..enums.browser_enum import ResourceType
from ..exceptions.browser_exception import (
    BrowserClosedError as _BrowserClosedError,
    BrowserLaunchedError as _BrowserLaunchedError,
    StealthError as _StealthError,
    PlaywrightError as _PlaywrightError,
)

if TYPE_CHECKING:
    from typing import (
        Optional,
        Literal,
        Iterable,
        Sequence,
        Self,
    )

    from playwright.async_api import (
        BrowserContext as PlaywrightBrowserContext,
        Browser as PlaywrightBrowser,
        Page as PlaywrightPage,
        Playwright,
    )
    from playwright.async_api import ProxySettings

    StrOrPath = str | _Path


"""
可以通过多个 async_playwright().start() 同时启动多个 playwright 实例

在一个 playwright 实例下，
launch() 和 launch_persistent_context() 均可通过相同 executable_path 启动多个浏览器实例。
但需注意：
一个 user_data_dir 只能拿来启动一个持久化上下文，若使用一个 user_data_dir 启动多个持久化上下文，程序会崩溃
"""

# TODO 需要为各种事件（例如浏览器关闭、程序崩溃等）添加回调处理


__all__ = [
    'MS1000',
    'ResourceType',
    'BrowserManager',
    'PersistentContextManager',
    'stealth',
    'abort_resources',
]


class BrowserManager:
    """
    启动非持久化浏览器

    ---

    既可以通过
    ```python
    async with BrowserManager(...) as bm:
        pass
    ```
    来使用，也可以通过
    ```python
    bm = await BrowserManager(...).start()
    pass
    await bm.close()
    ```
    来使用

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
        self.__kwargs = kwargs

        # 保证启动和关闭是互斥的
        self.__start_close_lock = _Lock()

        self.__playwright: Optional[Playwright] = None
        self.__browser: Optional[PlaywrightBrowser] = None

    async def start(self) -> Self:
        """启动浏览器，如果已经启动会抛出异常"""
        async with self.__start_close_lock:
            if self.started() is True:
                raise _BrowserLaunchedError('浏览器已经启动')

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
                **self.__kwargs,
            )

            # TODO 在浏览器被关闭时添加事件，让 BrowserManager 能收到浏览器已被关闭的信息
            # self.__browser.on('disconnected')

            return self

    async def close(self) -> None:
        """关闭浏览器，如果还未启动会抛出异常"""
        async with self.__start_close_lock:
            if self.started() is False:
                raise _BrowserClosedError('Playwright 实例或浏览器还未启动')

            try:
                await self.__browser.close()
                await self.__playwright.stop()
            except _PlaywrightError:
                pass
            finally:
                self.__browser = None
                self.__playwright = None

    async def _browser_close_callback(self):
        """当浏览器被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调"""
        # TODO

    def started(self) -> bool:
        """检查是否已经启动"""
        # TODO

    @property
    def browser(self) -> PlaywrightBrowser:
        """获取包含的浏览器实例，如果还未启动会抛出异常"""
        if self.started() is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        return self.__browser

    async def new_context(
        self,
        need_stealth: bool = False,
        abort_res_types: Optional[Iterable[ResourceType]] = None,
    ) -> PlaywrightBrowserContext:
        """创建新的浏览器上下文"""
        # TODO 创建上下文时的参数要怎么办
        if self.started() is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        context = await self.__browser.new_context()

        # 隐藏浏览器上下文
        if need_stealth is True:
            await stealth(context_page=context)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=context, res_types=abort_res_types)

        context = await self.__browser.new_context()
        return context

    async def _context_close_callback(self):
        """当创建的上下文被关闭时会触发的回调"""
        # TODO

    async def new_page(
        self,
        need_stealth: bool = False,
        abort_res_types: Optional[Iterable[ResourceType]] = None,
        **kwargs,
    ) -> PlaywrightPage:
        """创建新页面"""
        # TODO 创建页面时的参数要怎么办？
        if self.started() is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        page = await self.__browser.new_page(**kwargs)

        # 隐藏页面
        if need_stealth is True:
            await stealth(context_page=page)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=page, res_types=abort_res_types)

        return page

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


# 保证一个时刻只能启动一个持久化上下文
_persistent_context_start_lock = _Lock()


class PersistentContextManager:
    """
        启动持久化浏览器上下文

        ---

        1. `user_data_dir`:
        用户资料所在文件夹（如果传入的是相对路径，那会尝试解析成绝对路径）
        2. `executable_path`: 浏览器可执行文件路径
        3. `channel`: 浏览器类型
        4. `need_stealth`: 是否需要防爬虫检测
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
    n
        `kwargs` 参照：
        https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context
    """

    # 持久化上下文们正在使用的 user_data_dir
    __used_user_data_dirs: set[_Path] = {}

    def __init__(
        self,
        *,
        user_data_dir: StrOrPath,
        executable_path: StrOrPath,
        channel: Literal['chromium', 'chrome', 'msedge'],
        need_stealth: bool = False,
        abort_res_types: Optional[Iterable[ResourceType]] = None,
        args: Optional[Sequence[str]] = None,
        ignore_default_args: Sequence[str] = ('--enable-automation',),
        slow_mo: float = 0,
        timeout: float = 30_000,
        headless: bool = True,
        proxy: Optional[ProxySettings] = None,
        no_viewport: bool = True,
        **kwargs,
    ):
        self.__user_data_dir = _Path(user_data_dir).resolve()
        self.__executable_path = executable_path
        self.__channel = channel
        self.__need_stealth = need_stealth
        self.__abort_res_types = abort_res_types
        self.__args = args
        self.__ignore_default_args = ignore_default_args
        self.__slow_mo = slow_mo
        self.__timeout = timeout
        self.__headless = headless
        self.__proxy = proxy
        self.__no_viewport = no_viewport
        self.__kwargs = kwargs

        # 保证启动和关闭是互斥的
        self.__start_close_lock = _Lock()

        self.__playwright: Optional[Playwright] = None
        self.__persistent_context: Optional[PlaywrightBrowserContext] = None

    async def start(self) -> Self:
        """启动持久化上下文，如果已经启动或者 user_data_dir 被用于其它持久化上下文会抛出异常"""
        async with self.__start_close_lock:
            if self.started() is True:
                raise _BrowserLaunchedError('持久化上下文已经启动')

            # 检查当前的 user_data_dir 是否未被用于其它持久化上下文
            if self.__user_data_dir in self.__used_user_data_dirs:
                raise _BrowserLaunchedError(f'"{self.__user_data_dir}" 已被用于启动其它持久上下文')

            async with _persistent_context_start_lock:
                # 再次检查当前的 user_data_dir 是否未被用于其它持久化上下文
                if self.__user_data_dir in self.__used_user_data_dirs:
                    raise _BrowserLaunchedError(f'"{self.__user_data_dir}" 已被用于启动其它持久上下文')

                try:
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
                        **self.__kwargs,
                    )

                    # TODO 在持久化上下文被关闭时添加事件，让 PersistentContextManager 能接收到持久化上下文被关闭的消息
                    # self.__persistent_context.on('close')

                    self.__used_user_data_dirs.add(self.__user_data_dir)

                    # 防爬虫检测
                    if self.__need_stealth is True:
                        await stealth(context_page=self.__persistent_context)

                    # 屏蔽特定资源
                    if self.__abort_res_types is not None:
                        await abort_resources(context_page=self.__persistent_context, res_types=self.__abort_res_types)

                    return self

                except _PlaywrightError as pe:  # 如果在启动时失败了就移除当前的 user_data_dir
                    self.__used_user_data_dirs.discard(self.__user_data_dir)
                    raise _BrowserClosedError(f'启动浏览器失败\n{pe}')

    async def close(self) -> None:
        """关闭持久化上下文，如果还未启动会报错"""
        async with self.__start_close_lock:
            if self.started() is False:
                raise _BrowserClosedError('Playwright 实例或持久化上下文还未启动')

            try:
                await self.__persistent_context.close()
                await self.__playwright.stop()
            except _PlaywrightError:
                pass
            finally:
                self.__persistent_context = None
                self.__playwright = None
                self.__used_user_data_dirs.discard(self.__user_data_dir)

    async def _context_close_callback(self):
        """当持久化上下文被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调"""
        # TODO

    def started(self) -> bool:
        """检查是否已经启动"""
        # TODO

    @property
    def context(self) -> PlaywrightBrowserContext:
        """获取包含的持久化上下文实例，如果还未启动会抛出异常"""
        if self.started() is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        return self.__persistent_context

    async def new_page(
        self,
        need_stealth: bool = False,
        abort_res_types: Optional[Iterable[ResourceType]] = None,
    ) -> PlaywrightPage:
        """创建持久化上下文的新页面"""
        if self.started() is False:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        page = await self.__persistent_context.new_page()

        # 隐藏页面
        if need_stealth is True:
            await stealth(context_page=page)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=page, res_types=abort_res_types)

        return page

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()


async def stealth(
    context_page: PlaywrightBrowserContext | PlaywrightPage,
    ignore_stealthed: bool = False,
) -> None:
    """隐藏浏览器上下文或页面"""
    # # 如果该页面的父上下文已被隐藏会跳过
    # if isinstance(context_page, PlaywrightPage):
    #     if getattr(context_page.context, 'stealthed', None) is True:
    #         return

    # 如果浏览器上下文或页面已被隐藏会抛出异常
    if getattr(context_page, 'stealthed', None) is True:
        # 可以忽略已被隐藏
        if ignore_stealthed is True:
            return
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
