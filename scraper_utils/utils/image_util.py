"""
图片相关工具
"""

# TODO: 需要添加泛化的 read_image 和 write_image

from __future__ import annotations

from io import BytesIO as __BytesIO
from pathlib import Path as __Path
from typing import TYPE_CHECKING

from PIL import Image as __PIL_Image

from .file_util import read_bytes_async, read_bytes_sync, write_bytes_async, write_bytes_sync

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


async def read_image_async(file: str | __Path) -> PILImage:
    """异步读取图片文件"""
    file_bytes = await read_bytes_async(file=file)
    return __PIL_Image.open(__BytesIO(file_bytes))


def read_image_sync(file: str | __Path) -> PILImage:
    """同步读取图片文件"""
    file_bytes = read_bytes_sync(file=file)
    return __PIL_Image.open(__BytesIO(file_bytes))


async def write_image_async(file: str | __Path, image: PILImage) -> __Path:
    """异步写入图片文件"""
    file = __Path(file)

    image_format = file.suffix[1:].upper()
    if image_format == 'JPG':
        image_format = 'JPEG'

    image_bytes_fp = __BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return await write_bytes_async(file=file, data=image_bytes_fp.getvalue(), replace=True)


def write_image_sync(file: str | __Path, image: PILImage) -> __Path:
    """同步写入图片文件"""
    file = __Path(file)

    image_format = file.suffix[1:].upper()
    if image_format == 'JPG':
        image_format = 'JPEG'

    image_bytes_fp = __BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return write_bytes_sync(file=file, data=image_bytes_fp.getvalue(), replace=True)
