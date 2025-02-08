"""
JSON 相关工具
"""

from __future__ import annotations

from json import loads as json_loads, dumps as json_dumps
from typing import TYPE_CHECKING

from .file_util import read_str_async, read_str_sync, write_str_async, write_str_sync

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Optional, Callable


async def read_json_async(file: str | Path, encoding: str = 'utf-8') -> Any:
    """异步读取 JSON"""
    return json_loads(await read_str_async(file=file, encoding=encoding))


def read_json_sync(file: str | Path, encoding: str = 'utf-8') -> Any:
    """同步读取 JSON"""
    return json_loads(read_str_sync(file=file, encoding=encoding))


async def write_json_async(
    file: str | Path,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: int | str = 4,
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
    return await write_str_async(file=file, data=json_str, encoding=encoding, replace=True)


def write_json_sync(
    file: str | Path,
    data: Any,
    encoding: str = 'utf-8',
    ensure_ascii: bool = False,
    indent: int | str = 4,
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
    return write_str_sync(file=file, data=json_str, encoding=encoding, replace=True)
