"""
文件相关工具
"""

from __future__ import annotations

from pathlib import Path as _Path
from tkinter.filedialog import (
    askopenfilename as _askopenfilename,
    askopenfilenames as _askopenfilenames,
)
from typing import TYPE_CHECKING
from warnings import deprecated as _deprecated

from aiofiles import open as async_open

from ..exceptions.file_exception import NoSelectedFileError as _NoSelectedFileError

if TYPE_CHECKING:
    from typing import Optional, Iterable, Generator, Literal

    StrOrPath = str | _Path


__all__ = [
    #
    'path_exists',
    #
    'async_open',
    'sync_open',
    #
    'read_file',
    #
    'read_bytes',
    'read_bytes_async',
    'read_bytes_sync',
    #
    'read_str',
    'read_str_async',
    'read_str_sync',
    #
    'write_file',
    #
    'write_bytes',
    'write_bytes_async',
    'write_bytes_sync',
    #
    'write_str',
    'write_str_async',
    'write_str_sync',
    #
    'select_file_dialog',
    'select_files_dialog',
]


sync_open = open


def path_exists(
    path: StrOrPath,
    follow_symlinks: bool = True,
) -> bool:
    """路径是否存在"""
    if isinstance(path, _Path):
        return path.exists(follow_symlinks=follow_symlinks)
    return _Path(path).exists(follow_symlinks=follow_symlinks)


def _check_before_read(file: StrOrPath) -> _Path:
    """读取文件前的检查"""
    if isinstance(file, str):
        file = _Path(file)

    if not file.exists():
        raise FileNotFoundError(f'{file} 目标文件不存在')

    if not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    return file


def _check_before_write(file: StrOrPath) -> _Path:
    """写入文件前的检查"""
    if isinstance(file, str):
        file = _Path(file)

    if file.exists() and not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    file.parent.mkdir(exist_ok=True)

    return file


@_deprecated('更推荐使用具体的 read_XXX_async 或 read_XXX_sync')
def read_file(
    file: StrOrPath,
    read_mode: Literal['bytes', 'str'],
    async_mode: bool,
    encoding: str = 'utf-8',
):
    """
    读取文件

    通用的读取文件方法，可选择读取字节还是字符、同步还是异步

    ---

    1. `file`: 目标文件
    2. `read_mode`: 读取字节还是字符
    3. `async_mode`: 是否异步
    4. `encoding`: 文件编码（仅读取字符时需要）
    """
    match read_mode:
        case 'bytes':
            return read_bytes(file=file, async_mode=async_mode)
        case 'str':
            return read_str(file=file, async_mode=async_mode, encoding=encoding)


@_deprecated('更推荐使用具体的 read_bytes_async 或 read_bytes_sync')
def read_bytes(
    file: StrOrPath,
    async_mode: bool,
):
    """
    读取文件字节

    通用的读取文件字节方法，可选择同步还是异步
    """
    if async_mode:
        return read_bytes_async(file=file)
    else:
        return read_bytes_sync(file=file)


@_deprecated('更推荐使用具体的 read_str_async 或 read_str_sync')
def read_str(file: StrOrPath, async_mode: bool, encoding: str = 'utf-8'):
    """
    读取文件字符

    通用的读取文件字符方法，可选择同步还是异步
    """
    if async_mode:
        return read_str_async(file=file, encoding=encoding)
    else:
        return read_str_sync(file=file, encoding=encoding)


async def read_bytes_async(file: StrOrPath) -> bytes:
    """异步读取文件字节"""
    file = _check_before_read(file=file)
    async with async_open(file, 'rb') as fp:
        return await fp.read()


async def read_str_async(
    file: StrOrPath,
    encoding: str = 'utf-8',
) -> str:
    """异步读取文件字符"""
    file = _check_before_read(file=file)
    async with async_open(file, 'r', encoding=encoding) as fp:
        return await fp.read()


def read_bytes_sync(file: StrOrPath) -> bytes:
    """同步读取文件字节"""
    file = _check_before_read(file=file)
    with sync_open(file, 'rb') as fp:
        return fp.read()


def read_str_sync(
    file: StrOrPath,
    encoding: str = 'utf-8',
) -> str:
    """同步读取文件字符"""
    file = _check_before_read(file=file)
    with sync_open(file, 'r', encoding=encoding) as fp:
        return fp.read()


@_deprecated('更推荐使用具体的 write_XXX_async 或 write_XXX_sync')
def write_file(
    file: StrOrPath,
    data: bytes | str,
    write_mode: Literal['bytes', 'str'],
    async_mode: bool,
    replace: bool = True,
    encoding: str = 'utf-8',
):
    """
    读取文件

    通用的写入文件方法，可选择写入字节还是字符、同步还是异步、覆盖还是追加

    ---

    1. `file`: 目标文件
    2. `data`: 要写入的数据
    3. `write_mode`: 写入字节还是字符
    4. `async_mode`: 是否异步
    5. `replace`: 是否覆盖
    6. `encoding`: 文件编码（仅写入字符时需要）
    """
    match write_mode:
        case 'bytes':
            return write_bytes(file=file, data=data, async_mode=async_mode, replace=replace)
        case 'str':
            return write_str(file=file, data=data, async_mode=async_mode, replace=replace, encoding=encoding)


@_deprecated('更推荐使用具体的 write_bytes_async 或 write_bytes_sync')
def write_bytes(
    file: StrOrPath,
    data: bytes,
    async_mode: bool,
    replace: bool = True,
):
    """
    写入文件字节

    通用的写入文件字节的方法，可选择同步还是异步、追加还是覆盖
    """
    if async_mode:
        return write_bytes_async(file=file, data=data, replace=replace)
    else:
        return write_bytes_sync(file=file, data=data, replace=replace)


@_deprecated('更推荐使用具体的 write_str_async 或 write_str_sync')
def write_str(
    file: StrOrPath,
    data: str,
    async_mode: bool,
    replace: bool = True,
    encoding: str = 'utf-8',
):
    """
    写入文件字符

    通用的写入文件字符的方法，可选择同步还是异步、追加还是覆盖
    """
    if async_mode:
        return write_str_async(file=file, data=data, replace=replace, encoding=encoding)
    else:
        return write_str_sync(file=file, data=data, replace=replace, encoding=encoding)


async def write_bytes_async(file: StrOrPath, data: bytes, replace: bool = True) -> _Path:
    """异步写入文件字节"""
    if not isinstance(data, bytes):
        raise TypeError('data 应为 bytes')

    file = _check_before_write(file=file)
    if replace:
        async with async_open(file, 'wb') as fp:
            await fp.write(data)
    else:
        async with async_open(file, 'ab') as fp:
            await fp.write(data)

    return file


async def write_str_async(
    file: StrOrPath,
    data: str,
    replace: bool = True,
    encoding: str = 'utf-8',
) -> _Path:
    """异步写入文件字符"""
    if not isinstance(data, str):
        raise TypeError('data 应为 str')

    file = _check_before_write(file=file)
    if replace:
        async with async_open(file, 'w', encoding=encoding) as fp:
            await fp.write(data)
    else:
        async with async_open(file, 'a', encoding=encoding) as fp:
            await fp.write(data)

    return file


def write_bytes_sync(
    file: StrOrPath,
    data: bytes,
    replace: bool = True,
) -> _Path:
    """同步写入文件字节"""
    if not isinstance(data, bytes):
        raise TypeError('data 应为 bytes')

    file = _check_before_write(file=file)
    if replace:
        with sync_open(file, 'wb') as fp:
            fp.write(data)
    else:
        with sync_open(file, 'ab') as fp:
            fp.write(data)

    return file


def write_str_sync(
    file: StrOrPath,
    data: str,
    replace: bool = True,
    encoding: str = 'utf-8',
) -> _Path:
    """同步写入文件字符"""
    if not isinstance(data, str):
        raise TypeError('data 应为 str')

    file = _check_before_write(file=file)
    if replace:
        with sync_open(file, 'w', encoding=encoding) as fp:
            fp.write(data)
    else:
        with sync_open(file, 'a', encoding=encoding) as fp:
            fp.write(data)

    return file


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
) -> Generator[_Path, None, None]:
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
