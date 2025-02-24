"""
文件相关工具
"""

from __future__ import annotations

from pathlib import Path as _Path
from tkinter.filedialog import (
    askopenfilename as _askopenfilename,
    askopenfilenames as _askopenfilenames,
)
from typing import TYPE_CHECKING, overload

from aiofiles import open as _async_open

from ..exceptions.file_exception import NoSelectedFileError as _NoSelectedFileError

if TYPE_CHECKING:
    from typing import Awaitable, Generator, Iterable, Literal, Optional

    StrOrPath = str | _Path


__all__ = [
    'path_exists',
    'read_file',
    'write_file',
    'write_file',
    'select_file_dialog',
    'select_files_dialog',
]


_sync_open = open


def path_exists(
    path: StrOrPath,
    follow_symlinks: bool = True,
) -> bool:
    """路径是否存在"""
    if isinstance(path, _Path):
        return path.exists(follow_symlinks=follow_symlinks)
    return _Path(path).exists(follow_symlinks=follow_symlinks)


########## 读取文件 ##########


def _check_before_read(file: StrOrPath) -> _Path:
    """读取文件前的检查"""
    if isinstance(file, str):
        file = _Path(file)

    if not file.exists():
        raise FileNotFoundError(f'{file} 目标文件不存在')

    if not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    return file


@overload
async def read_file(file: StrOrPath, mode: Literal['bytes'], async_mode: Literal[True]) -> bytes:
    """异步读取文件字节"""


@overload
def read_file(file: StrOrPath, mode: Literal['bytes'], async_mode: Literal[False]) -> bytes:
    """同步读取文件字节"""


@overload
async def read_file(file: StrOrPath, mode: Literal['str'], async_mode: Literal[True], encoding: str = 'utf-8') -> str:
    """异步读取文件字符"""


@overload
def read_file(file: StrOrPath, mode: Literal['str'], async_mode: Literal[False], encoding: str = 'utf-8') -> str:
    """同步读取文件字符"""


def read_file(
    file: StrOrPath,
    mode: Literal['bytes', 'str'],
    async_mode: bool,
    encoding: Optional[str] = None,
) -> bytes | str | Awaitable[bytes] | Awaitable[str]:
    """读取文件"""
    if async_mode:
        return read_file_async(file=file, mode=mode, encoding=encoding)
    else:
        return read_file_sync(file=file, mode=mode, encoding=encoding)


@overload
async def read_file_async(file: StrOrPath, mode: Literal['bytes'], encoding: Optional[str] = None) -> bytes:
    """异步读取文件字节"""


@overload
async def read_file_async(file: StrOrPath, mode: Literal['str'], encoding: Optional[str] = None) -> str:
    """异步读取文件字符"""


async def read_file_async(
    file: StrOrPath,
    mode: Literal['bytes', 'str'],
    encoding: Optional[str] = None,
) -> bytes | str:
    """异步读取文件字节或字符"""
    file = _check_before_read(file=file)
    match mode:
        case 'bytes':
            async with _async_open(file, 'rb') as fp:
                return await fp.read()
        case 'str':
            async with _async_open(
                file,
                'r',
                encoding='utf-8' if encoding is None else encoding,
            ) as fp:
                return await fp.read()
        case _:
            raise ValueError(f'错误的读取模式 "{mode}"')


@overload
def read_file_sync(file: StrOrPath, mode: Literal['bytes'], encoding: Optional[str] = None) -> bytes:
    """同步读取文件字节"""


@overload
def read_file_sync(file: StrOrPath, mode: Literal['str'], encoding: Optional[str] = None) -> str:
    """同步读取文件字符"""


def read_file_sync(
    file: StrOrPath,
    mode: Literal['bytes', 'str'],
    encoding: Optional[str] = None,
) -> bytes | str:
    """同步读取文件字节或字符"""
    file = _check_before_read(file=file)
    match mode:
        case 'bytes':
            with _sync_open(file, 'rb') as fp:
                return fp.read()
        case 'str':
            with _sync_open(
                file,
                'r',
                encoding='utf-8' if encoding is None else encoding,
            ) as fp:
                return fp.read()
        case _:
            raise ValueError(f'错误的读取模式 "{mode}"')


########## 写入文件 ##########


def _check_before_write(file: StrOrPath) -> _Path:
    """写入文件前的检查"""
    if isinstance(file, str):
        file = _Path(file)

    if file.exists() and not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    file.parent.mkdir(exist_ok=True)

    return file


@overload
async def write_file(file: StrOrPath, data: bytes, async_mode: Literal[True], replace: bool = True) -> _Path:
    """异步写入文件字节"""


@overload
def write_file(file: StrOrPath, data: bytes, async_mode: Literal[False], replace: bool = True) -> _Path:
    """同步写入文件字节"""


@overload
async def write_file(
    file: StrOrPath, data: str, async_mode: Literal[True], replace: bool = True, encoding: str = 'utf-8'
) -> _Path:
    """异步写入文件字符"""


@overload
def write_file(
    file: StrOrPath, data: str, async_mode: Literal[False], replace: bool = True, encoding: str = 'utf-8'
) -> _Path:
    """同步写入文件字符"""


def write_file(
    file: StrOrPath,
    data: bytes | str,
    async_mode: bool,
    replace: bool = True,
    encoding: str = 'utf-8',
) -> Awaitable[_Path] | _Path:
    """写入文件"""
    if async_mode:
        return write_file_async(file=file, data=data, replace=replace, encoding=encoding)
    else:
        return write_file_sync(file=file, data=data, replace=replace, encoding=encoding)


async def write_file_async(
    file: StrOrPath, data: bytes | str, replace: bool = True, encoding: Optional[str] = None
) -> _Path:
    """异步写入文件字节或字符"""
    file = _check_before_write(file=file)

    match data:
        case bytes():
            async with _async_open(file, 'wb' if replace else 'ab') as fp:
                await fp.write(data)
            return file
        case str():
            async with _async_open(
                file,
                'w' if replace else 'a',
                encoding='utf-8' if encoding is None else encoding,
            ) as fp:
                await fp.write(data)
            return file
        case _:
            raise TypeError(f'错误的 data 类型 "{type(data)}"')


def write_file_sync(file: StrOrPath, data: bytes | str, replace: bool = True, encoding: str = 'utf-8') -> _Path:
    """同步写入文件字节或字符"""
    file = _check_before_write(file=file)

    match data:
        case bytes():
            with _sync_open(file, 'wb' if replace else 'ab') as fp:
                fp.write(data)
            return file
        case str():
            with _sync_open(
                file,
                'w' if replace else 'a',
                encoding='utf-8' if encoding is None else encoding,
            ) as fp:
                fp.write(data)
            return file
        case _:
            raise TypeError(f'错误的 data 类型 "{type(data)}"')


########## 文件选择对话框 ##########


def select_file_dialog(
    title: str = '请选择文件',
    initialdir: Optional[StrOrPath] = None,
    filetypes: Optional[Iterable[tuple[str, str]]] = None,
) -> _Path:
    """
    打开文件对话框，选取单个文件，返回所选取文件的绝对路径

    ---

    1. `title`: 窗口标题
    2. `initialdir`: 打开时的初始目录
    3. `filetypes`: 可被选取的文件种类
    例如：[('EXE File', '*.exe'), ('Python File', '*.py')]
    """
    if filetypes is None:
        result = _askopenfilename(title=title, initialdir=initialdir)
    else:
        result = _askopenfilename(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(result) == 0:
        raise _NoSelectedFileError('未选择目标文件')

    return _Path(result)


def select_files_dialog(
    title: str = '请选择文件',
    initialdir: Optional[StrOrPath] = None,
    filetypes: Optional[Iterable[tuple[str, str]]] = None,
) -> Generator[_Path]:
    """
    打开文件对话框，选取多个文件，生成所选取文件的绝对路径

    ---

    1. `title`: 窗口标题
    2. `initialdir`: 打开时的初始目录
    3. `filetypes`: 可被选取的文件种类
    例如：[('EXE File', '*.exe'), ('Python File', '*.py')]
    """
    if filetypes is None:
        results = _askopenfilenames(title=title, initialdir=initialdir)
    else:
        results = _askopenfilenames(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(results) == 0:
        raise _NoSelectedFileError('未选择目标文件')

    for r in results:
        yield _Path(r)
