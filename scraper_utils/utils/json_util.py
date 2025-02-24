"""
JSON 相关工具
"""

from __future__ import annotations

from json import loads as json_loads, dumps as json_dumps
from typing import TYPE_CHECKING, overload

from .file_util import read_file as _read_file, write_file as _write_file

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Awaitable, Optional, Literal

    type StrOrPath = str | Path


__all__ = [
    'json_loads',
    'json_dumps',
    'read_json',
    'write_json',
]

########## 读取 ##########


@overload
async def read_json(file: StrOrPath, async_mode: Literal[True], encoding: str = 'utf-8') -> Any:
    """异步读取 JSON"""


@overload
def read_json(file: StrOrPath, async_mode: Literal[False], encoding: str = 'utf-8') -> Any:
    """同步读取 JSON"""


def read_json(file: StrOrPath, async_mode: bool, encoding: str = 'utf-8') -> Awaitable[Any] | Any:
    """读取 JSON"""
    if async_mode:
        return read_json_async(file=file, encoding=encoding)
    else:
        return read_json_sync(file=file, encoding=encoding)


async def read_json_async(file: StrOrPath, encoding: str = 'utf-8') -> Any:
    """异步读取 JSON"""
    return json_loads(await _read_file(file=file, mode='str', async_mode=True, encoding=encoding))


def read_json_sync(file: StrOrPath, encoding: str = 'utf-8') -> Any:
    """同步读取 JSON"""
    return json_loads(_read_file(file=file, mode='str', async_mode=False, encoding=encoding))


########## 读取 ##########


@overload
async def write_json(
    file: StrOrPath,
    data: Any,
    async_mode: Literal[True],
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    **kwargs,
) -> Path:
    """异步写入 JSON"""


@overload
def write_json(
    file: StrOrPath,
    data: Any,
    async_mode: Literal[False],
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    **dump_kwargs,
) -> Path:
    """同步写入 JSON"""


def write_json(
    file: StrOrPath,
    data: Any,
    async_mode: bool,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    **dump_kwargs,
) -> Path | Awaitable[Path]:
    """写入 JSON"""
    if async_mode:
        return write_json_async(
            file=file,
            data=data,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
            **dump_kwargs,
        )
    else:
        return write_json_sync(
            file=file,
            data=data,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
            **dump_kwargs,
        )


async def write_json_async(
    file: StrOrPath,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    **dump_kwargs,
) -> Path:
    """异步写入 JSON"""
    json_str = json_dumps(data, indent=indent, ensure_ascii=ensure_ascii, **dump_kwargs)
    return await _write_file(file=file, data=json_str, encoding=encoding, replace=True, async_mode=True)


def write_json_sync(
    file: StrOrPath,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    **dump_kwargs,
) -> Path:
    """同步写入 JSON"""
    json_str = json_dumps(data, indent=indent, ensure_ascii=ensure_ascii, **dump_kwargs)
    return _write_file(file=file, data=json_str, encoding=encoding, replace=True, async_mode=False)
