"""
文件相关工具
"""

from __future__ import annotations

from pathlib import Path
from tkinter.filedialog import askopenfilename, askopenfilenames
from typing import TYPE_CHECKING
from warnings import deprecated


from ..exceptions.file_exception import NoSelectedFileError

if TYPE_CHECKING:
    from typing import Optional, Iterable, Generator, Literal

    StrOrPath = str | Path


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


from aiofiles import open as async_open

sync_open = open


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


@deprecated('更推荐使用具体的 read_XXX_async 或 read_XXX_sync')
def read_file(
    file: StrOrPath,
    read_mode: Literal['bytes', 'str'],
    async_mode: bool,
    encoding: str = 'utf-8',
):
    """读取文件"""
    match read_mode:
        case 'bytes':
            return read_bytes(file=file, async_mode=async_mode)
        case 'str':
            return read_str(file=file, async_mode=async_mode, encoding=encoding)


@deprecated('更推荐使用具体的 read_bytes_async 或 read_bytes_sync')
def read_bytes(file: StrOrPath, async_mode: bool):
    """读取文件字节"""
    if async_mode:
        return read_bytes_async(file=file)
    else:
        return read_bytes_sync(file=file)


@deprecated('更推荐使用具体的 read_str_async 或 read_str_sync')
def read_str(file: StrOrPath, async_mode: bool, encoding: str = 'utf-8'):
    """读取文件字符"""
    if async_mode:
        return read_str_async(file=file, encoding=encoding)
    else:
        return read_str_sync(file=file, encoding=encoding)


async def read_bytes_async(file: StrOrPath) -> bytes:
    """异步读取文件字节"""
    file = __check_before_read(file=file)
    async with async_open(file, 'rb') as fp:
        return await fp.read()


async def read_str_async(file: StrOrPath, encoding: str = 'utf-8') -> str:
    """异步读取文件字符"""
    file = __check_before_read(file=file)
    async with async_open(file, 'r', encoding=encoding) as fp:
        return await fp.read()


def read_bytes_sync(file: StrOrPath) -> bytes:
    """同步读取文件字节"""
    file = __check_before_read(file=file)
    with sync_open(file, 'rb') as fp:
        return fp.read()


def read_str_sync(file: StrOrPath, encoding: str = 'utf-8') -> str:
    """同步读取文件字符"""
    file = __check_before_read(file=file)
    with sync_open(file, 'r', encoding=encoding) as fp:
        return fp.read()


@deprecated('更推荐使用具体的 write_XXX_async 或 write_XXX_sync')
def write_file(
    file: StrOrPath,
    data: bytes | str,
    write_mode: Literal['bytes', 'str'],
    async_mode: bool,
    replace: bool = True,
    encoding: str = 'utf-8',
):
    """读取文件"""
    match write_mode:
        case 'bytes':
            return write_bytes(file=file, data=data, async_mode=async_mode, replace=replace)
        case 'str':
            return write_str(file=file, data=data, async_mode=async_mode, replace=replace, encoding=encoding)


@deprecated('更推荐使用具体的 write_bytes_async 或 write_bytes_sync')
def write_bytes(
    file: StrOrPath,
    data: bytes,
    async_mode: bool,
    replace: bool = True,
):
    """写入文件字节"""
    if async_mode:
        return write_bytes_async(file=file, data=data, replace=replace)
    else:
        return write_bytes_sync(file=file, data=data, replace=replace)


@deprecated('更推荐使用具体的 write_str_async 或 write_str_sync')
def write_str(
    file: StrOrPath,
    data: bytes,
    async_mode: bool,
    replace: bool = True,
    encoding: str = 'utf-8',
):
    """写入文件字符"""
    if async_mode:
        return write_str_async(file=file, data=data, replace=replace, encoding=encoding)
    else:
        return write_str_sync(file=file, data=data, replace=replace, encoding=encoding)


async def write_bytes_async(file: StrOrPath, data: bytes, replace: bool = True) -> Path:
    """异步写入文件字节"""
    if not isinstance(data, bytes):
        raise TypeError('data 应为 bytes')

    file = __check_before_write(file=file)
    if replace:
        async with async_open(file, 'wb') as fp:
            await fp.write(data)
    else:
        async with async_open(file, 'ab') as fp:
            await fp.write(data)

    return file


async def write_str_async(file: StrOrPath, data: str, replace: bool = True, encoding: str = 'utf-8') -> Path:
    """异步写入文件字符"""
    if not isinstance(data, str):
        raise TypeError('data 应为 str')

    file = __check_before_write(file=file)
    if replace:
        async with async_open(file, 'w', encoding=encoding) as fp:
            await fp.write(data)
    else:
        async with async_open(file, 'a', encoding=encoding) as fp:
            await fp.write(data)

    return file


def write_bytes_sync(file: StrOrPath, data: bytes, replace: bool = True) -> Path:
    """同步写入文件字节"""
    if not isinstance(data, bytes):
        raise TypeError('data 应为 bytes')

    file = __check_before_write(file=file)
    if replace:
        with sync_open(file, 'wb') as fp:
            fp.write(data)
    else:
        with sync_open(file, 'ab') as fp:
            fp.write(data)

    return file


def write_str_sync(file: StrOrPath, data: str, replace: bool = True, encoding: str = 'utf-8') -> Path:
    """同步写入文件字符"""
    if not isinstance(data, str):
        raise TypeError('data 应为 str')

    file = __check_before_write(file=file)
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
    filetypes: Optional[Iterable[tuple[str, str]]] = None,  # like: [('EXE File', '*.exe'), ('Python File', '*.py')]
) -> Path:
    """打开文件对话框，选取单个文件，返回所选取文件的绝对路径"""
    if filetypes is None:
        result = askopenfilename(title=title, initialdir=initialdir)
    else:
        result = askopenfilename(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(result) == 0:
        raise NoSelectedFileError('未选择目标文件')

    return Path(result)


def select_files_dialog(
    title: str = '请选择文件',
    initialdir: Optional[StrOrPath] = None,
    filetypes: Optional[Iterable[tuple[str, str]]] = None,  # like: [('EXE File', '*.exe'), ('Python File', '*.py')]
) -> Generator[Path, None, None]:
    """打开文件对话框，选取多个文件，生成所选取文件的绝对路径"""
    if filetypes is None:
        results = askopenfilenames(title=title, initialdir=initialdir)
    else:
        results = askopenfilenames(title=title, initialdir=initialdir, filetypes=filetypes)

    if len(results) == 0:
        raise NoSelectedFileError('未选择目标文件')

    for r in results:
        yield Path(r)
