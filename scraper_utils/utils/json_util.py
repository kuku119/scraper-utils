"""
JSON 相关工具
"""

from __future__ import annotations

from json import loads as json_loads, dumps as json_dumps
from typing import TYPE_CHECKING
from warnings import deprecated as _deprecated

from .file_util import (
    read_str as _read_str,
    write_str as _write_str,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Optional, Callable

    StrOrPath = str | Path


__all__ = [
    #
    'json_loads',
    'json_dumps',
    #
    'read_json',
    'read_json_async',
    'read_json_sync',
    #
    'write_json',
    'write_json_async',
    'write_json_sync',
]


@_deprecated('更推荐使用具体的 read_json_async 或 read_json_sync')
def read_json(
    file: StrOrPath,
    async_mode: bool,
    encoding: str = 'utf-8',
):
    """读取 JSON 文件"""
    if async_mode:
        return read_json_async(file=file, encoding=encoding)
    else:
        return read_json_sync(file=file, encoding=encoding)


async def read_json_async(
    file: StrOrPath,
    encoding: str = 'utf-8',
) -> Any:
    """异步读取 JSON"""
    return json_loads(await _read_str(file=file, encoding=encoding, async_mode=True))


def read_json_sync(
    file: StrOrPath,
    encoding: str = 'utf-8',
) -> Any:
    """同步读取 JSON"""
    return json_loads(_read_str(file=file, encoding=encoding, async_mode=False))


@_deprecated('更推荐使用具体的 write_json_async 或 write_json_sync')
def write_json(
    file: StrOrPath,
    data: Any,
    async_mode: bool,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: int | str = 4,
    sort_keys: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
):
    """写入 JSON 文件"""
    if async_mode:
        return write_json_async(
            file=file,
            data=data,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            default=default,
        )
    else:
        return write_json_sync(
            file=file,
            data=data,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
            sort_keys=sort_keys,
            default=default,
        )


async def write_json_async(
    file: StrOrPath,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    sort_keys: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
) -> Path:
    """异步写入 JSON"""
    json_str = json_dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        default=default,
        ensure_ascii=ensure_ascii,
    )
    return await _write_str(file=file, data=json_str, encoding=encoding, replace=True, async_mode=True)


def write_json_sync(
    file: StrOrPath,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: Optional[int | str] = None,
    sort_keys: bool = False,
    default: Optional[Callable[[Any], Any]] = None,
) -> Path:
    """同步写入 JSON"""
    json_str = json_dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        default=default,
        ensure_ascii=ensure_ascii,
    )
    return _write_str(file=file, data=json_str, encoding=encoding, replace=True, async_mode=False)
