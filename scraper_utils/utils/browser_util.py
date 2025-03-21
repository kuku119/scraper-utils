"""
Playwright 浏览器相关工具
"""

from __future__ import annotations

from asyncio import Lock as _Lock
from pathlib import Path as _Path
from time import perf_counter
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
    from re import Pattern
    from typing import Optional, Literal, Sequence, Self

    from playwright._impl._api_structures import ClientCertificate
    from playwright.async_api import (
        BrowserContext as PlaywrightBrowserContext,
        Browser as PlaywrightBrowser,
        Page as PlaywrightPage,
        Locator,
        Playwright,
        ProxySettings,
        ViewportSize,
        HttpCredentials,
        Geolocation,
        StorageState,
    )

    type StrOrPath = str | _Path
    type StrOrPattern = str | Pattern[str]


"""
可以通过多个 async_playwright().start() 同时启动多个 playwright 实例

在一个 playwright 实例下，
launch() 和 launch_persistent_context() 均可通过相同 executable_path 启动多个浏览器实例。
但需注意：
一个 user_data_dir 只能拿来启动一个持久化上下文，若使用一个 user_data_dir 启动多个持久化上下文，程序会崩溃
"""

# TODO 需要为浏览器各种事件（例如浏览器关闭、程序崩溃等）添加回调处理


__all__ = [
    'MS1000',
    'ResourceType',
    'BrowserManager',
    'PersistentContextManager',
    'stealth',
    'abort_resources',
    'wait_for_locator',
]


class BrowserManager:
    """
    启动非持久化浏览器

    ---

    * `executable_path`: 浏览器可执行文件路径
    * `channel`: 浏览器类型
        * `chromium`: Chromium 无头模式
        * `chrome`: Chrome
        * `msedge`: Edge
    * `args`: 浏览器启动参数，chrome 参照：
    https://peter.sh/experiments/chromium-command-line-switches
    * `chromium_sandbox`: 是否启用 Chromium 沙箱模式
    * `downloads_path`: 下载目录，会在浏览器上下文退出时会被删除
    * `env`: 指定浏览器可见的环境变量，默认为 process.env
    * `handle_sighup`: 终端关闭时是否自动关闭浏览器
    * `handle_sigint`: 按下 `Ctrl+C` 时是否自动关闭浏览器
    * `handle_sigterm`: 程序结束或被 kill 时是否自动关闭浏览器
    * `headless`: 是否隐藏浏览器界面
    * `ignore_default_args`: 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-option-ignore-default-args
    * `launch_timeout`: 等待浏览器启动的超时时间（毫秒）
    * `proxy`: 代理
    * `slow_mo`: 浏览器各项操作的时间间隔（毫秒）
    * `traces_dir`: 跟踪的保存目录
    """

    def __init__(
        self,
        executable_path: StrOrPath,
        channel: Literal['chromium', 'chrome', 'msedge'],
        *,
        args: Optional[Sequence[str]] = None,
        chromium_sandbox: bool = False,
        downloads_path: Optional[StrOrPath] = None,
        env: Optional[dict[str, str | float | bool]] = None,
        handle_sighup: bool = True,
        handle_sigint: bool = True,
        handle_sigterm: bool = True,
        headless: bool = True,
        ignore_default_args: Sequence[str] = ('--enable-automation',),
        launch_timeout: float = 30_000,
        proxy: Optional[ProxySettings] = None,
        slow_mo: float = 0,
        traces_dir: Optional[StrOrPath] = None,
    ):
        self.__executable_path = executable_path
        self.__channel = channel
        self.__args = args
        self.__chromium_sandbox = chromium_sandbox
        self.__downloads_path = downloads_path
        self.__env = env
        self.__handle_sighup = handle_sighup
        self.__handle_sigint = handle_sigint
        self.__handle_sigterm = handle_sigterm
        self.__headless = headless
        self.__ignore_default_args = ignore_default_args
        self.__launch_timeout = launch_timeout
        self.__proxy = proxy
        self.__slow_mo = slow_mo
        self.__traces_dir = traces_dir

        # 保证启动和关闭是互斥的
        self.__start_close_lock = _Lock()

        self.__playwright: Optional[Playwright] = None
        self.__browser: Optional[PlaywrightBrowser] = None

    def is_started(self) -> bool:
        """检查浏览器是否已经启动"""
        return self.__browser is not None and self.__browser.is_connected()

    async def start(self) -> Self:
        """启动浏览器，如果已经启动会抛出异常"""
        async with self.__start_close_lock:
            if self.is_started():
                raise _BrowserLaunchedError('浏览器已经启动')

            self.__playwright = await _async_playwright().start()
            self.__browser = await self.__playwright.chromium.launch(
                executable_path=self.__executable_path,
                channel=self.__channel,
                args=self.__args,
                chromium_sandbox=self.__chromium_sandbox,
                downloads_path=self.__downloads_path,
                env=self.__env,
                handle_sighup=self.__handle_sighup,
                handle_sigint=self.__handle_sigint,
                handle_sigterm=self.__handle_sigterm,
                headless=self.__headless,
                ignore_default_args=self.__ignore_default_args,
                proxy=self.__proxy,
                slow_mo=self.__slow_mo,
                timeout=self.__launch_timeout,
                traces_dir=self.__traces_dir,
            )

            # 当浏览器被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调
            self.__browser.on('disconnected', self._on_browser_disconnected)

            return self

    async def close(self) -> None:
        """关闭浏览器"""
        async with self.__start_close_lock:
            # 如果浏览器已经关闭，就忽略
            # 不加这个判断为空也没问题
            if not self.is_started() or self.__browser is None:
                return

            try:
                await self.__browser.close()
            except _PlaywrightError:
                pass
            finally:
                self.__browser = None

    async def _on_browser_disconnected(self, browser: PlaywrightBrowser) -> None:
        """当浏览器被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调"""
        # 如果 playwright 已被关闭，就忽略
        if self.__playwright is None:
            return

        try:
            await self.__playwright.stop()
        except _PlaywrightError:
            pass
        finally:
            self.__browser = None

    @property
    def browser(self) -> PlaywrightBrowser:
        """获取包含的浏览器实例，如果还未启动会抛出异常"""
        # 不加这个判断为空也没问题
        if not self.is_started() or self.__browser is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')
        return self.__browser

    async def new_context(
        self,
        *,
        abort_res_types: Optional[Sequence[ResourceType]] = None,
        accept_downloads: bool = True,
        add_init_script: Optional[str] = None,
        base_url: Optional[str] = None,
        bypass_csp: bool = False,
        client_certificates: Optional[list[ClientCertificate]] = None,
        color_scheme: Literal['light', 'dark', 'no-preference', 'null'] = 'light',
        default_navigation_timeout: int = 30_000,
        default_timeout: int = 30_000,
        device_scale_factor: Optional[float] = None,
        extra_http_headers: Optional[dict[str, str]] = None,
        forced_colors: Literal['active', 'none', 'null'] = 'none',
        geolocation: Optional[Geolocation] = None,
        has_touch: bool = False,
        http_credentials: Optional[HttpCredentials] = None,
        ignore_https_errors: bool = False,
        is_mobile: bool = False,
        java_script_enabled: bool = True,
        locale: Optional[str] = None,
        need_stealth: bool = False,
        no_viewport: bool = True,
        offline: bool = False,
        permissions: Optional[list[str]] = None,
        proxy: Optional[ProxySettings] = None,
        record_har_content: Literal['omit', 'embed', 'attach'] = 'embed',
        record_har_mode: Literal['full', 'minimal'] = 'full',
        record_har_omit_content: bool = False,
        record_har_path: Optional[StrOrPath] = None,
        record_har_url_filter: Optional[StrOrPattern] = None,
        record_video_dir: Optional[StrOrPath] = None,
        record_video_size: Optional[ViewportSize] = None,
        reduced_motion: Literal['reduce', 'no-preference', 'null'] = 'no-preference',
        screen: Optional[ViewportSize] = None,
        service_workers: Literal['allow', 'block'] = 'allow',
        storage_state: Optional[StrOrPath | StorageState] = None,
        strict_selectors: bool = False,
        timezone_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        viewport: Optional[ViewportSize] = None,
    ) -> PlaywrightBrowserContext:
        """
        创建新的浏览器上下文

        ---

        * `abort_res_types`: 要屏蔽的资源类型
        * `accept_downloads`: 是否自动下载所有附件
        * `add_init_script`: 要注入的 JavaScript 脚本内容
        * `base_url`: 基础链接
        * `bypass_csp`: 是否绕过 Content-Security-Policy
        * `client_certificates`: 证书
        * `color_scheme`: 模拟 prefers-colors-scheme
        * `default_navigation_timeout`: 导航相关的默认超时时间
        * `default_timeout`: 所有操作的默认超时时间
        * `device_scale_factor`: 缩放比例
        * `extra_http_headers`: 额外 HTTP 请求头
        * `forced_colors`: 模拟 forced-colors
        * `geolocation`: 地理位置
        * `has_touch`: 是否为触摸屏
        * `http_credentials`: HTTP 验证凭据
        * `ignore_https_errors`: 发送网络请求时是否忽略 HTTPS 错误
        * `is_mobile`: 是否为移动设备
        * `java_script_enabled`: 是否启用 JavaScript
        * `locale`: 语言
        * `need_stealth`: 是否需要隐藏
        * `no_viewport`: 是否不固定视区小大
        * `offline`: 是否为离线模式
        * `permissions`: 权限
        * `proxy`: 代理
        * `record_har_content`: HAR
        * `record_har_mode`: HAR
        * `record_har_omit_content`: HAR
        * `record_har_path`: HAR
        * `record_har_url_filter`: HAR
        * `record_video_dir`: 启用指定目录中所有页面的视频录制
        * `record_video_size`: 录制视频的尺寸
        * `reduced_motion`: 模拟 prefers-reduced-motion
        * `screen`: 窗口大小
        * `service_workers`: 是否允许站点注册 Service worker
        * `storage_state`: 使用给定的存储状态填充上下文
        * `strict_selectors`: 是否启用选择器的严格模式
        * `timezone_id`: 时区
        * `user_agent`: User-Agent
        * `viewport`: 视区小大
        """
        # 不加这个判断为空也没问题
        if not self.is_started() or self.__browser is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        context = await self.__browser.new_context(
            accept_downloads=accept_downloads,
            base_url=base_url,
            bypass_csp=bypass_csp,
            client_certificates=client_certificates,
            color_scheme=color_scheme,
            device_scale_factor=device_scale_factor,
            extra_http_headers=extra_http_headers,
            forced_colors=forced_colors,
            geolocation=geolocation,
            has_touch=has_touch,
            http_credentials=http_credentials,
            ignore_https_errors=ignore_https_errors,
            is_mobile=is_mobile,
            java_script_enabled=java_script_enabled,
            locale=locale,
            no_viewport=no_viewport,
            offline=offline,
            permissions=permissions,
            proxy=proxy,
            record_har_content=record_har_content,
            record_har_mode=record_har_mode,
            record_har_omit_content=record_har_omit_content,
            record_har_path=record_har_path,
            record_har_url_filter=record_har_url_filter,
            record_video_dir=record_video_dir,
            record_video_size=record_video_size,
            reduced_motion=reduced_motion,
            screen=screen,
            service_workers=service_workers,
            storage_state=storage_state,
            strict_selectors=strict_selectors,
            timezone_id=timezone_id,
            user_agent=user_agent,
            viewport=viewport,
        )

        # 设置默认超时时间
        # 所有操作的默认超时时间
        context.set_default_timeout(default_timeout)
        # 导航相关的默认超时时间
        context.set_default_navigation_timeout(default_navigation_timeout)

        # 注入 JavaScript 脚本
        if add_init_script is not None:
            await context.add_init_script(script=add_init_script)

        # 隐藏浏览器上下文
        if need_stealth:
            await stealth(context_page=context)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=context, res_types=abort_res_types)

        return context

    async def new_page(
        self,
        *,
        abort_res_types: Optional[Sequence[ResourceType]] = None,
        accept_downloads: bool = True,
        add_init_script: Optional[str] = None,
        base_url: Optional[str] = None,
        bypass_csp: bool = False,
        client_certificates: Optional[list[ClientCertificate]] = None,
        color_scheme: Literal['light', 'dark', 'no-preference', 'null'] = 'light',
        default_navigation_timeout: int = 30_000,
        default_timeout: int = 30_000,
        device_scale_factor: Optional[float] = None,
        extra_http_headers: Optional[dict[str, str]] = None,
        forced_colors: Literal['active', 'none', 'null'] = 'none',
        geolocation: Optional[Geolocation] = None,
        has_touch: bool = False,
        http_credentials: Optional[HttpCredentials] = None,
        ignore_https_errors: bool = False,
        is_mobile: bool = False,
        java_script_enabled: bool = True,
        locale: Optional[str] = None,
        need_stealth: bool = False,
        no_viewport: bool = True,
        offline: bool = False,
        permissions: Optional[list[str]] = None,
        proxy: Optional[ProxySettings] = None,
        record_har_content: Literal['omit', 'embed', 'attach'] = 'embed',
        record_har_mode: Literal['full', 'minimal'] = 'full',
        record_har_omit_content: bool = False,
        record_har_path: Optional[StrOrPath] = None,
        record_har_url_filter: Optional[StrOrPattern] = None,
        record_video_dir: Optional[StrOrPath] = None,
        record_video_size: Optional[ViewportSize] = None,
        reduced_motion: Literal['reduce', 'no-preference', 'null'] = 'no-preference',
        screen: Optional[ViewportSize] = None,
        service_workers: Literal['allow', 'block'] = 'allow',
        storage_state: Optional[StrOrPath | StorageState] = None,
        strict_selectors: bool = False,
        timezone_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        viewport: Optional[ViewportSize] = None,
    ) -> PlaywrightPage:
        """
        创建新页面

        ---

        * `abort_res_types`: 要屏蔽的资源类型
        * `accept_downloads`: 是否自动下载所有附件
        * `add_init_script`: 要注入的 JavaScript 脚本内容
        * `base_url`: 基础链接
        * `bypass_csp`: 是否绕过 Content-Security-Policy
        * `client_certificates`: 证书
        * `color_scheme`: 模拟 prefers-colors-scheme
        * `default_navigation_timeout`: 导航相关的默认超时时间
        * `default_timeout`: 所有操作的默认超时时间
        * `device_scale_factor`: 缩放比例
        * `extra_http_headers`: 额外 HTTP 请求头
        * `forced_colors`: 模拟 forced-colors
        * `geolocation`: 地理位置
        * `has_touch`: 是否为触摸屏
        * `http_credentials`: HTTP 验证凭据
        * `ignore_https_errors`: 发送网络请求时是否忽略 HTTPS 错误
        * `is_mobile`: 是否为移动设备
        * `java_script_enabled`: 是否启用 JavaScript
        * `locale`: 语言
        * `need_stealth`: 是否需要隐藏
        * `no_viewport`: 是否不固定视区小大
        * `offline`: 是否为离线模式
        * `permissions`: 权限
        * `proxy`: 代理
        * `record_har_content`: HAR
        * `record_har_mode`: HAR
        * `record_har_omit_content`: HAR
        * `record_har_path`: HAR
        * `record_har_url_filter`: HAR
        * `record_video_dir`: 启用指定目录中所有页面的视频录制
        * `record_video_size`: 录制视频的尺寸
        * `reduced_motion`: 模拟 prefers-reduced-motion
        * `screen`: 窗口大小
        * `service_workers`: 是否允许站点注册 Service worker
        * `storage_state`: 使用给定的存储状态填充上下文
        * `strict_selectors`: 是否启用选择器的严格模式
        * `timezone_id`: 时区
        * `user_agent`: User-Agent
        * `viewport`: 视区小大
        """

        context = await self.new_context(
            abort_res_types=abort_res_types,
            accept_downloads=accept_downloads,
            add_init_script=add_init_script,
            base_url=base_url,
            bypass_csp=bypass_csp,
            client_certificates=client_certificates,
            color_scheme=color_scheme,
            default_navigation_timeout=default_navigation_timeout,
            default_timeout=default_timeout,
            device_scale_factor=device_scale_factor,
            extra_http_headers=extra_http_headers,
            forced_colors=forced_colors,
            geolocation=geolocation,
            has_touch=has_touch,
            http_credentials=http_credentials,
            ignore_https_errors=ignore_https_errors,
            is_mobile=is_mobile,
            java_script_enabled=java_script_enabled,
            locale=locale,
            need_stealth=need_stealth,
            no_viewport=no_viewport,
            offline=offline,
            permissions=permissions,
            proxy=proxy,
            record_har_content=record_har_content,
            record_har_mode=record_har_mode,
            record_har_omit_content=record_har_omit_content,
            record_har_path=record_har_path,
            record_har_url_filter=record_har_url_filter,
            record_video_dir=record_video_dir,
            record_video_size=record_video_size,
            reduced_motion=reduced_motion,
            screen=screen,
            service_workers=service_workers,
            storage_state=storage_state,
            strict_selectors=strict_selectors,
            timezone_id=timezone_id,
            user_agent=user_agent,
            viewport=viewport,
        )
        page = await context.new_page()

        # 设置默认超时时间
        # 所有操作的默认超时时间
        page.set_default_timeout(default_timeout)
        # 导航相关的默认超时时间
        page.set_default_navigation_timeout(default_navigation_timeout)

        # 注入 JavaScript 脚本
        if add_init_script is not None:
            await page.add_init_script(script=add_init_script)

        # 隐藏页面
        if need_stealth:
            await stealth(context_page=page)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=page, res_types=abort_res_types)

        return page

    async def __aenter__(self) -> Self:
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()


# 保证一个时刻只能启动一个持久化上下文
_persistent_context_start_lock = _Lock()


class PersistentContextManager:
    """
    启动持久化浏览器上下文

    ---

    * `user_data_dir`:
    用户资料所在文件夹（如果传入的是相对路径，那会尝试解析成绝对路径）
    * `executable_path`: 浏览器可执行文件路径
    * `channel`: 浏览器类型
        * `chromium`: Chromium 无头模式
        * `chrome`: Chrome
        * `msedge`: Edge
    * `abort_res_types`: 要屏蔽的资源类型
    * `accept_downloads`: 是否自动下载所有附件
    * `add_init_script`: 要注入的 JavaScript 脚本内容
    * `args`: 浏览器启动参数，chrome 参照：
    * `base_url`: 基础链接
    * `bypass_csp`: 是否绕过 Content-Security-Policy
    https://peter.sh/experiments/chromium-command-line-switches
    * `chromium_sandbox`: 是否启用 Chromium 沙箱模式
    * `client_certificates`: 证书
    * `color_scheme`: 模拟 prefers-colors-scheme
    * `default_navigation_timeout`: 导航相关的默认超时时间
    * `default_timeout`: 所有操作的默认超时时间
    * `device_scale_factor`: 缩放比例
    * `downloads_path`: 下载目录，会在浏览器上下文退出时会被删除
    * `env`: 指定浏览器可见的环境变量，默认为 process.env
    * `extra_http_headers`: 额外 HTTP 请求头
    * `forced_colors`: 模拟 forced-colors
    * `geolocation`: 地理位置
    * `handle_sighup`: 终端关闭时是否自动关闭浏览器
    * `handle_sigint`: 按下 `Ctrl+C` 时是否自动关闭浏览器
    * `handle_sigterm`: 程序结束或被 kill 时是否自动关闭浏览器
    * `has_touch`: 是否为触摸屏
    * `headless`: 是否隐藏浏览器界面
    * `http_credentials`: HTTP 验证凭据
    * `ignore_default_args`: 参照：
    https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-option-ignore-default-args
    * `ignore_https_errors`: 发送网络请求时是否忽略 HTTPS 错误
    * `is_mobile`: 是否为移动设备
    * `java_script_enabled`: 是否启用 JavaScript
    * `launch_timeout`: 等待浏览器启动的超时时间（毫秒）
    * `locale`: 语言
    * `need_stealth`: 是否需要隐藏
    * `no_viewport`: 是否不固定视区小大
    * `offline`: 是否为离线模式
    * `permissions`: 权限
    * `proxy`: 代理
    * `record_har_content`: HAR
    * `record_har_mode`: HAR
    * `record_har_omit_content`: HAR
    * `record_har_path`: HAR
    * `record_har_url_filter`: HAR
    * `record_video_dir`: 启用指定目录中所有页面的视频录制
    * `record_video_size`: 录制视频的尺寸
    * `reduced_motion`: 模拟 prefers-reduced-motion
    * `screen`: 窗口大小
    * `service_workers`: 是否允许站点注册 Service worker
    * `slow_mo`: 浏览器各项操作的时间间隔（毫秒）
    * `strict_selectors`: 是否启用选择器的严格模式
    * `timezone_id`: 时区
    * `traces_dir`: 跟踪的保存目录
    * `user_agent`: User-Agent
    * `viewport`: 视区小大
    """

    # 持久化上下文们正在使用的 user_data_dir，保证一个 user_data_dir 只能被用于一个持久化上下文
    __used_user_data_dirs: set[_Path] = set()

    def __init__(
        self,
        executable_path: StrOrPath,
        user_data_dir: StrOrPath,
        channel: Literal['chromium', 'chrome', 'msedge'],
        *,
        abort_res_types: Optional[Sequence[ResourceType]] = None,
        accept_downloads: bool = True,
        add_init_script: Optional[str] = None,
        args: Optional[Sequence[str]] = None,
        base_url: Optional[str] = None,
        bypass_csp: bool = False,
        chromium_sandbox: bool = False,
        client_certificates: Optional[list[ClientCertificate]] = None,
        color_scheme: Literal['light', 'dark', 'no-preference', 'null'] = 'light',
        default_navigation_timeout: int = 30_000,
        default_timeout: int = 30_000,
        device_scale_factor: Optional[float] = None,
        downloads_path: Optional[StrOrPath] = None,
        env: Optional[dict[str, str | float | bool]] = None,
        extra_http_headers: Optional[dict[str, str]] = None,
        forced_colors: Literal['active', 'none', 'null'] = 'none',
        geolocation: Optional[Geolocation] = None,
        handle_sighup: bool = True,
        handle_sigint: bool = True,
        handle_sigterm: bool = True,
        has_touch: bool = False,
        headless: bool = True,
        http_credentials: Optional[HttpCredentials] = None,
        ignore_default_args: Sequence[str] = ('--enable-automation',),
        ignore_https_errors: bool = False,
        is_mobile: bool = False,
        java_script_enabled: bool = True,
        launch_timeout: int = 30_000,
        locale: Optional[str] = None,
        need_stealth: bool = False,
        no_viewport: bool = True,
        offline: bool = False,
        permissions: Optional[list[str]] = None,
        proxy: Optional[ProxySettings] = None,
        record_har_content: Literal['omit', 'embed', 'attach'] = 'embed',
        record_har_mode: Literal['full', 'minimal'] = 'full',
        record_har_omit_content: bool = False,
        record_har_path: Optional[StrOrPath] = None,
        record_har_url_filter: Optional[StrOrPattern] = None,
        record_video_dir: Optional[StrOrPath] = None,
        record_video_size: Optional[ViewportSize] = None,
        reduced_motion: Literal['reduce', 'no-preference', 'null'] = 'no-preference',
        screen: Optional[ViewportSize] = None,
        service_workers: Literal['allow', 'block'] = 'allow',
        slow_mo: float = 0,
        strict_selectors: bool = False,
        timezone_id: Optional[str] = None,
        traces_dir: Optional[StrOrPath] = None,
        user_agent: Optional[str] = None,
        viewport: Optional[ViewportSize] = None,
    ):
        self.__user_data_dir = _Path(user_data_dir).resolve()
        self.__executable_path = executable_path
        self.__channel = channel
        self.__abort_res_types = abort_res_types
        self.__accept_downloads = accept_downloads
        self.__add_init_script = add_init_script
        self.__args = args
        self.__base_url = base_url
        self.__bypass_csp = bypass_csp
        self.__chromium_sandbox = chromium_sandbox
        self.__client_certificates = client_certificates
        self.__color_scheme: Literal['light', 'dark', 'no-preference', 'null'] = color_scheme
        self.__default_navigation_timeout = default_navigation_timeout
        self.__default_timeout = default_timeout
        self.__device_scale_factor = device_scale_factor
        self.__downloads_path = downloads_path
        self.__env = env
        self.__extra_http_headers = extra_http_headers
        self.__forced_colors: Literal['active', 'none', 'null'] = forced_colors
        self.__geolocation = geolocation
        self.__handle_sighup = handle_sighup
        self.__handle_sigint = handle_sigint
        self.__handle_sigterm = handle_sigterm
        self.__has_touch = has_touch
        self.__headless = headless
        self.__http_credentials = http_credentials
        self.__ignore_default_args = ignore_default_args
        self.__ignore_https_errors = ignore_https_errors
        self.__is_mobile = is_mobile
        self.__java_script_enabled = java_script_enabled
        self.__launch_timeout = launch_timeout
        self.__locale = locale
        self.__need_stealth = need_stealth
        self.__no_viewport = no_viewport
        self.__offline = offline
        self.__permissions = permissions
        self.__proxy = proxy
        self.__record_har_content: Literal['omit', 'embed', 'attach'] = record_har_content
        self.__record_har_mode: Literal['full', 'minimal'] = record_har_mode
        self.__record_har_omit_content = record_har_omit_content
        self.__record_har_path = record_har_path
        self.__record_har_url_filter = record_har_url_filter
        self.__record_video_dir = record_video_dir
        self.__record_video_size = record_video_size
        self.__reduced_motion: Literal['reduce', 'no-preference', 'null'] = reduced_motion
        self.__screen = screen
        self.__service_workers: Literal['allow', 'block'] = service_workers
        self.__slow_mo = slow_mo
        self.__strict_selectors = strict_selectors
        self.__timezone_id = timezone_id
        self.__traces_dir = traces_dir
        self.__user_agent = user_agent
        self.__viewport = viewport

        # 保证启动和关闭是互斥的
        self.__start_close_lock = _Lock()

        self.__playwright: Optional[Playwright] = None
        self.__persistent_context: Optional[PlaywrightBrowserContext] = None

    def is_started(self) -> bool:
        """检查是否已经启动"""
        return self.__persistent_context is not None

    async def start(self) -> Self:
        """启动持久化上下文，如果已经启动或者 user_data_dir 被用于其它持久化上下文会抛出异常"""
        async with self.__start_close_lock:
            if self.is_started():
                raise _BrowserLaunchedError('持久化上下文已经启动')

            # 检查当前的 user_data_dir 是否未被用于其它持久化上下文
            if self.__user_data_dir in self.__used_user_data_dirs:
                raise _BrowserLaunchedError(f'"{self.__user_data_dir}" 已被用于启动其它持久上下文')

            async with _persistent_context_start_lock:
                # 再次检查当前的 user_data_dir 是否未被用于其它持久化上下文
                if self.__user_data_dir in self.__used_user_data_dirs:
                    raise _BrowserLaunchedError(f'"{self.__user_data_dir}" 已被用于启动其它持久上下文')

                self.__used_user_data_dirs.add(self.__user_data_dir)

                try:
                    self.__playwright = await _async_playwright().start()
                    self.__persistent_context = await self.__playwright.chromium.launch_persistent_context(
                        user_data_dir=self.__user_data_dir,
                        executable_path=self.__executable_path,
                        channel=self.__channel,
                        accept_downloads=self.__accept_downloads,
                        args=self.__args,
                        bypass_csp=self.__bypass_csp,
                        base_url=self.__base_url,
                        chromium_sandbox=self.__chromium_sandbox,
                        client_certificates=self.__client_certificates,
                        color_scheme=self.__color_scheme,
                        device_scale_factor=self.__device_scale_factor,
                        downloads_path=self.__downloads_path,
                        env=self.__env,
                        extra_http_headers=self.__extra_http_headers,
                        forced_colors=self.__forced_colors,
                        geolocation=self.__geolocation,
                        handle_sighup=self.__handle_sighup,
                        handle_sigint=self.__handle_sigint,
                        handle_sigterm=self.__handle_sigterm,
                        has_touch=self.__has_touch,
                        headless=self.__headless,
                        http_credentials=self.__http_credentials,
                        ignore_default_args=self.__ignore_default_args,
                        ignore_https_errors=self.__ignore_https_errors,
                        is_mobile=self.__is_mobile,
                        java_script_enabled=self.__java_script_enabled,
                        locale=self.__locale,
                        no_viewport=self.__no_viewport,
                        offline=self.__offline,
                        permissions=self.__permissions,
                        proxy=self.__proxy,
                        record_har_content=self.__record_har_content,
                        record_har_mode=self.__record_har_mode,
                        record_har_omit_content=self.__record_har_omit_content,
                        record_har_path=self.__record_har_path,
                        record_har_url_filter=self.__record_har_url_filter,
                        record_video_dir=self.__record_video_dir,
                        record_video_size=self.__record_video_size,
                        reduced_motion=self.__reduced_motion,
                        screen=self.__screen,
                        service_workers=self.__service_workers,
                        slow_mo=self.__slow_mo,
                        strict_selectors=self.__strict_selectors,
                        timeout=self.__launch_timeout,
                        timezone_id=self.__timezone_id,
                        traces_dir=self.__traces_dir,
                        user_agent=self.__user_agent,
                        viewport=self.__viewport,
                    )

                    # 当持久化上下文被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调
                    self.__persistent_context.on('close', self._on_context_close)

                    # 设置默认超时时间
                    # 所有操作的默认超时时间
                    self.__persistent_context.set_default_timeout(self.__default_timeout)
                    # 导航相关的默认超时时间
                    self.__persistent_context.set_default_navigation_timeout(self.__default_navigation_timeout)

                    # 注入 JavaScript 脚本
                    if self.__add_init_script is not None:
                        await self.__persistent_context.add_init_script(script=self.__add_init_script)

                    # 隐藏上下文
                    if self.__need_stealth:
                        await stealth(context_page=self.__persistent_context)

                    # 屏蔽特定资源
                    if self.__abort_res_types is not None:
                        await abort_resources(context_page=self.__persistent_context, res_types=self.__abort_res_types)

                    return self

                except _PlaywrightError as pe:
                    # 如果在启动时失败了就移除当前的 user_data_dir
                    self.__playwright = None
                    self.__persistent_context = None
                    self.__used_user_data_dirs.discard(self.__user_data_dir)
                    raise _BrowserClosedError(f'启动浏览器失败\n{pe}')

    async def close(self) -> None:
        """关闭持久化上下文"""
        # 如果已经关闭，就忽略
        # 不加这个判断为空也没问题
        if not self.is_started() or self.__persistent_context is None:
            return

        async with self.__start_close_lock:
            # 再次判断，如果已经关闭，就忽略
            # 不加这个判断为空也没问题
            if not self.is_started() or self.__persistent_context is None:
                return

            try:
                await self.__persistent_context.close()
            except _PlaywrightError:
                pass
            finally:
                self.__persistent_context = None

    async def _on_context_close(self, context: PlaywrightBrowserContext) -> None:
        """当持久化上下文被关闭时（可能是正常退出，也可能是程序崩溃）触发的回调"""
        # 如果已经关闭，就忽略
        if self.__playwright is None:
            return

        try:
            await self.__playwright.stop()
        except _PlaywrightError:
            pass
        finally:
            self.__playwright = None
            self.__used_user_data_dirs.discard(self.__user_data_dir)

    @property
    def context(self) -> PlaywrightBrowserContext:
        """获取包含的持久化上下文实例，如果还未启动会抛出异常"""
        # 不加这个判断为空也没问题
        if self.is_started() is False or self.__persistent_context is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        return self.__persistent_context

    async def new_page(
        self,
        need_stealth: bool = False,
        abort_res_types: Optional[Sequence[ResourceType]] = None,
    ) -> PlaywrightPage:
        """创建持久化上下文的新页面"""
        # 不加这个判断为空也没问题
        if not self.is_started() or self.__persistent_context is None:
            raise _BrowserClosedError('浏览器已经关闭或还未启动')

        page = await self.__persistent_context.new_page()

        # 隐藏页面
        if need_stealth:
            await stealth(context_page=page)

        # 屏蔽特定资源
        if abort_res_types is not None:
            await abort_resources(context_page=page, res_types=abort_res_types)

        return page

    async def __aenter__(self) -> Self:
        return await self.start()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()


async def stealth(context_page: PlaywrightBrowserContext | PlaywrightPage, ignore_stealthed: bool = False) -> None:
    """隐藏浏览器上下文或页面"""
    # 如果浏览器上下文或页面已被隐藏会抛出异常
    if getattr(context_page, 'stealthed', None):
        # 可以忽略已被隐藏
        if ignore_stealthed:
            return
        raise _StealthError('该浏览器上下文或页面已经隐藏')

    await _stealth_async(context_page)  # type: ignore
    setattr(context_page, 'stealthed', True)


async def abort_resources(
    context_page: PlaywrightBrowserContext | PlaywrightPage, res_types: Sequence[ResourceType]
) -> None:
    """屏蔽特定资源的请求"""
    await context_page.route(
        '**/*',
        lambda r: (r.abort() if r.request.resource_type in res_types else r.continue_()),
    )


async def wait_for_locator(
    page: PlaywrightPage, locator: Locator, timeout: int = 30_000, interval: int = 1_000
) -> bool:
    """在超时事件内定期检查页面中有无特定元素。"""
    start_time = perf_counter()
    while True:
        if (perf_counter() - start_time) > (timeout / 1000):
            return False
        if await locator.count() > 0:
            return True
        await page.wait_for_timeout(interval)
