"""
图片相关工具
"""

from __future__ import annotations

from io import BytesIO as _BytesIO
from pathlib import Path as _Path
from typing import TYPE_CHECKING
from warnings import deprecated as _deprecated

from PIL import Image as _PillowImageModule

from .file_util import (
    read_bytes as _read_bytes,
    write_bytes as _write_bytes,
)

if TYPE_CHECKING:
    from typing import Optional
    from PIL.Image import Image as PillowImage

    StrOrPath = str | _Path


__all__ = [
    #
    'read_image',
    'read_image_async',
    'read_image_sync',
    #
    'write_image',
    'write_image_async',
    'write_image_sync',
    #
    'resize_image',
]


@_deprecated('更推荐使用具体的 read_image_async 或 read_image_sync')
def read_image(
    file: StrOrPath,
    async_mode: bool,
):
    """
    读取图片文件

    通用的读取图片文件的方法，可选择同步还是异步
    """
    if async_mode:
        return read_image_async(file=file)
    else:
        return read_image(file=file)


async def read_image_async(file: StrOrPath) -> PillowImage:
    """异步读取图片文件"""
    file_bytes = await _read_bytes(file=file, async_mode=True)
    return _PillowImageModule.open(_BytesIO(file_bytes))


def read_image_sync(file: StrOrPath) -> PillowImage:
    """同步读取图片文件"""
    file_bytes = _read_bytes(file=file, async_mode=False)
    return _PillowImageModule.open(_BytesIO(file_bytes))


@_deprecated('更推荐使用具体的 write_image_async 或 write_image_sync')
def write_image(
    file: StrOrPath,
    image: PillowImage,
    async_mode: bool,
):
    """
    写入图片文件

    通用的写入图片文件的方法，可选择同步还是异步
    """
    if async_mode:
        return write_image_async(file=file, image=image)
    else:
        return write_image_sync(file=file, image=image)


async def write_image_async(
    file: StrOrPath,
    image: PillowImage,
) -> _Path:
    """异步写入图片文件"""
    file = _Path(file)

    image_format = file.suffix[1:].upper()
    if image_format == 'JPG':
        image_format = 'JPEG'

    image_bytes_fp = _BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return await _write_bytes(file=file, data=image_bytes_fp.getvalue(), replace=True, async_mode=True)


def write_image_sync(
    file: StrOrPath,
    image: PillowImage,
) -> _Path:
    """同步写入图片文件"""
    file = _Path(file)

    image_format = file.suffix[1:].upper()
    if image_format == 'JPG':
        image_format = 'JPEG'

    image_bytes_fp = _BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return _write_bytes(file=file, data=image_bytes_fp.getvalue(), replace=True, async_mode=False)


def resize_image(
    image: PillowImage,
    width: int,
    height: int,
    resample: Optional[int] = None,
    box: Optional[tuple[float, float, float, float]] = None,
    reducing_gap: Optional[float] = None,
) -> PillowImage:
    """重新设置图片大小"""
    if width <= 0 or height <= 0:
        raise ValueError('图片的宽度和高度都必须大于 0')
    return image.resize(
        size=(width, height),
        resample=_PillowImageModule.Resampling.LANCZOS if resample is None else resample,
        box=box,
        reducing_gap=reducing_gap,
    )
