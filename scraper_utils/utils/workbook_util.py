"""
表格相关工具
"""

# TODO

from __future__ import annotations

from io import BytesIO as __BytesIO
from pathlib import Path as __Path
from typing import TYPE_CHECKING

from openpyxl import load_workbook as __load_workbook

from .file_util import (
    read_bytes_sync as __rbs,
    read_bytes_async as __rba,
    write_bytes_sync as __wbs,
    write_bytes_async as __wba,
)

if TYPE_CHECKING:
    from openpyxl import Workbook


async def read_workbook_async(
    file: str | __Path,
    read_only: bool = False,
    data_only: bool = False,
    **kwargs,
) -> Workbook:
    """异步读取工作簿"""
    workbook_bytes = __BytesIO(await __rba(file=file))
    return __load_workbook(filename=workbook_bytes, read_only=read_only, data_only=data_only, **kwargs)


def read_workbook_sync(
    file: str | __Path,
    read_only: bool = False,
    data_only: bool = False,
    **kwargs,
) -> Workbook:
    """同步读取工作簿"""
    workbook_bytes = __BytesIO(__rbs(file=file))
    return __load_workbook(filename=workbook_bytes, read_only=read_only, data_only=data_only, **kwargs)


async def write_workbook_async(file: str | __Path, workbook: Workbook) -> __Path:
    """异步写入工作簿"""
    workbook_bytes = __BytesIO()
    workbook.save(workbook_bytes)
    return await __wba(file=file, data=workbook_bytes.getvalue())


def write_workbook_sync(file: str | __Path, workbook: Workbook) -> __Path:
    """同步写入工作簿"""
    workbook_bytes = __BytesIO()
    workbook.save(workbook_bytes)
    return __wbs(file=file, data=workbook_bytes.getvalue())
