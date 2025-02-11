"""
表格相关工具
"""

from __future__ import annotations

from io import BytesIO as _BytesIO
from typing import TYPE_CHECKING
from warnings import deprecated as _deprecated

from openpyxl import load_workbook

from .file_util import (
    read_bytes as _read_bytes,
    write_bytes as _write_bytes,
)
from .text_util import is_letter as _is_letter

if TYPE_CHECKING:
    from pathlib import Path as _Path

    from openpyxl import Workbook

    StrOrPath = str | _Path


__all__ = [
    #
    'load_workbook',
    #
    'read_workbook',
    'read_workbook_async',
    'read_workbook_sync',
    #
    'write_workbook',
    'write_workbook_async',
    'write_workbook_sync',
]


@_deprecated('更推荐使用具体的 read_workbook_async 或 read_workbook_sync')
def read_workbook(
    file: StrOrPath,
    async_mode,
    read_only: bool = False,
    data_only: bool = False,
    **kwargs,
):
    """读取工作簿文件"""
    if async_mode:
        return read_workbook_async(file=file, read_only=read_only, data_only=data_only, **kwargs)
    else:
        return read_workbook_sync(file=file, read_only=read_only, data_only=data_only, **kwargs)


async def read_workbook_async(
    file: StrOrPath,
    read_only: bool = False,
    data_only: bool = False,
    **kwargs,
) -> Workbook:
    """异步读取工作簿"""
    workbook_bytes = _BytesIO(await _read_bytes(file=file, async_mode=True))
    return load_workbook(filename=workbook_bytes, read_only=read_only, data_only=data_only, **kwargs)


def read_workbook_sync(
    file: StrOrPath,
    read_only: bool = False,
    data_only: bool = False,
    **kwargs,
) -> Workbook:
    """同步读取工作簿"""
    workbook_bytes = _BytesIO(_read_bytes(file=file, async_mode=False))
    return load_workbook(filename=workbook_bytes, read_only=read_only, data_only=data_only, **kwargs)


@_deprecated('更推荐使用具体的 write_workbook_async 或 write_workbook_sync')
def write_workbook(
    file: StrOrPath,
    workbook: Workbook,
    async_mode: bool,
):
    """写入工作簿文件"""
    if async_mode:
        return write_workbook_async(file=file, workbook=workbook)
    else:
        return write_workbook_sync(file=file, workbook=workbook)


async def write_workbook_async(
    file: StrOrPath,
    workbook: Workbook,
) -> _Path:
    """异步写入工作簿"""
    workbook_bytes = _BytesIO()
    workbook.save(workbook_bytes)
    return await _write_bytes(file=file, data=workbook_bytes.getvalue(), async_mode=True)


def write_workbook_sync(
    file: StrOrPath,
    workbook: Workbook,
) -> _Path:
    """同步写入工作簿"""
    workbook_bytes = _BytesIO()
    workbook.save(workbook_bytes)
    return _write_bytes(file=file, data=workbook_bytes.getvalue(), async_mode=False)


def string_column_to_integer_column(column_name: str) -> int:
    """字母形式的列名转成数字形式的列号"""
    if not _is_letter(column_name) or len(column_name) > 3:
        raise ValueError(f'"{column_name}" 不符合列名规范')

    result = 0
    for c in column_name:
        result = result * 26 + (ord(c.upper()) - ord('A') + 1)

    if result > 16384:
        raise ValueError(f'"{column_name}" 超出列名范围 "A" <= column_name <= "XFD"')

    return result


def integer_column_to_string_column(column_index: int) -> str:
    """数字形式的列号转成字母形式的列名"""
    if 1 <= column_index <= 16384:
        result = ''
        while column_index > 0:
            column_index -= 1
            result = chr(column_index % 26 + ord('A')) + result
            column_index //= 26
        return result
    raise ValueError(f'"{column_index}" 超出列号范围 1 <= column_index <= 16384')
