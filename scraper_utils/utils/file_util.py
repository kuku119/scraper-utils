"""
文件相关工具
"""

from __future__ import annotations

from pathlib import Path
from tkinter.filedialog import (
    askopenfilename as __ask_open_filename,
    askopenfilenames as __ask_open_filenames,
)
from typing import TYPE_CHECKING

from aiofiles import open as __async_open

from ..exceptions.file_exception import NoSelectedFileError as __NoSelectedFileError

if TYPE_CHECKING:
    from typing import Optional, Iterable, Generator

    StrOrPath = str | Path

__sync_open = open


def path_exists(path: StrOrPath, follow_symlinks: bool = True) -> bool:
    """路径是否存在"""
    if isinstance(path, Path):
        return path.exists(follow_symlinks=follow_symlinks)
    return Path(path).exists(follow_symlinks=follow_symlinks)


def __check_before_read(file: StrOrPath) -> Path:
    """读取文件前的检查"""
    if isinstance(file, str):
        file = Path(file)

    if not file.exists():
        raise FileNotFoundError(f'{file} 目标文件不存在')

    if not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    return file


def __check_before_write(file: StrOrPath) -> Path:
    """写入文件前的检查"""
    if isinstance(file, str):
        file = Path(file)

    if file.exists() and not file.is_file():
        raise IOError(f'{file} 目标不是文件')

    file.parent.mkdir(exist_ok=True)

    return file


async def read_bytes_async(file: StrOrPath) -> bytes:
    """异步读取文件字节"""
    file = __check_before_read(file=file)
    async with __async_open(file, 'rb') as fp:
        return await fp.read()


async def read_str_async(file: StrOrPath, encoding: str = 'utf-8') -> str:
    """异步读取文件字符"""
    file = __check_before_read(file=file)
    async with __async_open(file, 'r', encoding=encoding) as fp:
        return await fp.read()


def read_bytes_sync(file: StrOrPath) -> bytes:
    """同步读取文件字节"""
    file = __check_before_read(file=file)
    with __sync_open(file, 'rb') as fp:
        return fp.read()


def read_str_sync(file: StrOrPath, encoding: str = 'utf-8') -> str:
    """同步读取文件字符"""
    file = __check_before_read(file=file)
    with __sync_open(file, 'r', encoding=encoding) as fp:
        return fp.read()


async def write_bytes_async(file: StrOrPath, data: bytes, replace: bool = True) -> Path:
    """异步写入文件字节"""
    file = __check_before_write(file=file)
    if replace:
        async with __async_open(file, 'wb') as fp:
            await fp.write(data)
    else:
        async with __async_open(file, 'ab') as fp:
            await fp.write(data)

    return file


async def write_str_async(file: StrOrPath, data: str, replace: bool = True, encoding: str = 'utf-8') -> Path:
    """异步写入文件字符"""
    file = __check_before_write(file=file)
    if replace:
        async with __async_open(file, 'w', encoding=encoding) as fp:
            await fp.write(data)
    else:
        async with __async_open(file, 'a', encoding=encoding) as fp:
            await fp.write(data)

    return file


def write_bytes_sync(file: StrOrPath, data: bytes, replace: bool = True) -> Path:
    """同步写入文件字节"""
    file = __check_before_write(file=file)
    if replace:
        with __sync_open(file, 'wb') as fp:
            fp.write(data)
    else:
        with __sync_open(file, 'ab') as fp:
            fp.write(data)

    return file


def write_str_sync(file: StrOrPath, data: str, replace: bool = True, encoding: str = 'utf-8') -> Path:
    """同步写入文件字符"""
    file = __check_before_write(file=file)
    if replace:
        with __sync_open(file, 'w', encoding=encoding) as fp:
            fp.write(data)
    else:
        with __sync_open(file, 'a', encoding=encoding) as fp:
            fp.write(data)

    return file


def select_file_dialog(
    title: str = '请选择文件',
    initialdir: Optional[StrOrPath] = None,
    filetypes: Optional[Iterable[tuple[str, str | list[str] | tuple[str, ...]]]] = None,
) -> Path:
    """打开文件对话框，选取单个文件，返回所选取文件的绝对路径"""
    if filetypes is None:
        result = __ask_open_filename(title=title, initialdir=initialdir)
    else:
        result = __ask_open_filename(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(result) == 0:
        raise __NoSelectedFileError('未选择目标文件')

    return Path(result)


def select_files_dialog(
    title: str = '请选择文件',
    initialdir: Optional[StrOrPath] = None,
    filetypes: Optional[Iterable[tuple[str, str | list[str] | tuple[str, ...]]]] = None,
) -> Generator[Path, None, None]:
    """打开文件对话框，选取多个文件，返回所选取文件的绝对路径"""
    if filetypes is None:
        results = __ask_open_filenames(title=title, initialdir=initialdir)
    else:
        results = __ask_open_filenames(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(results) == 0:
        raise __NoSelectedFileError('未选择目标文件')

    for r in results:
        yield Path(r)
