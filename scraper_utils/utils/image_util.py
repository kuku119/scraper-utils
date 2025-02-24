"""
图片相关工具
"""

from __future__ import annotations

from io import BytesIO as _BytesIO
from pathlib import Path as _Path
from typing import TYPE_CHECKING, overload

from PIL import Image as _PillowImageModule

from .file_util import read_file as _read_file, write_file as _write_file

if TYPE_CHECKING:
    from typing import Optional, Literal, Awaitable, Annotated

    from PIL.Image import Image as PillowImage

    type StrOrPath = str | _Path


__all__ = [
    'read_image',
    'write_image',
    'resize_image',
]

########## 读取 ##########


@overload
async def read_image(
    file: StrOrPath, async_mode: Literal[True], formats: Optional[list[str] | tuple[str, ...]] = None
) -> PillowImage:
    """异步读取图片文件"""


@overload
def read_image(
    file: StrOrPath, async_mode: Literal[False], formats: Optional[list[str] | tuple[str, ...]] = None
) -> PillowImage:
    """同步读取图片文件"""


def read_image(
    file: StrOrPath, async_mode: bool, formats: Optional[list[str] | tuple[str, ...]] = None
) -> PillowImage | Awaitable[PillowImage]:
    """读取图片文件"""
    if async_mode:
        return read_image_async(file=file, formats=formats)
    else:
        return read_image_sync(file=file, formats=formats)


async def read_image_async(file: StrOrPath, formats: Optional[list[str] | tuple[str, ...]] = None) -> PillowImage:
    """异步读取图片文件"""
    file_bytes = await _read_file(file=file, mode='bytes', async_mode=True)
    return _PillowImageModule.open(_BytesIO(file_bytes), formats=formats)


def read_image_sync(file: StrOrPath, formats: Optional[list[str] | tuple[str, ...]] = None) -> PillowImage:
    """同步读取图片文件"""
    file_bytes = _read_file(file=file, mode='bytes', async_mode=False)
    return _PillowImageModule.open(_BytesIO(file_bytes), formats=formats)


########## 写入 ##########


def _write_image_format(file: StrOrPath) -> str:
    """根据保存路径获取图片的 format"""
    match file:
        case _Path():
            result = file.suffix[1:].upper()
        case str():
            result = file.split('.')[-1]
        case _:
            raise TypeError(f'传入了错误的 file "{type(file)}"')

    if result == 'JPG':
        result = 'JPEG'

    return result


@overload
async def write_image(
    file: StrOrPath, image: PillowImage, async_mode: Literal[True], image_format: Optional[str] = None
) -> _Path:
    """异步写入图片文件"""


@overload
def write_image(
    file: StrOrPath, image: PillowImage, async_mode: Literal[False], image_format: Optional[str] = None
) -> _Path:
    """同步写入图片文件"""


def write_image(
    file: StrOrPath, image: PillowImage, async_mode: bool, image_format: Optional[str] = None
) -> _Path | Awaitable[_Path]:
    """写入图片文件"""
    if async_mode:
        return write_image_async(file=file, image=image, image_format=image_format)
    else:
        return write_image_sync(file=file, image=image, image_format=image_format)


async def write_image_async(file: StrOrPath, image: PillowImage, image_format: Optional[str] = None) -> _Path:
    """异步写入图片文件"""
    if image_format is None:
        image_format = _write_image_format(file=file)

    image_bytes_fp = _BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return await _write_file(file=file, data=image_bytes_fp.getvalue(), replace=True, async_mode=True)


def write_image_sync(file: StrOrPath, image: PillowImage, image_format: Optional[str] = None) -> _Path:
    """同步写入图片文件"""
    if image_format is None:
        image_format = _write_image_format(file=file)

    image_bytes_fp = _BytesIO()
    image.save(image_bytes_fp, format=image_format)
    return _write_file(file=file, data=image_bytes_fp.getvalue(), replace=True, async_mode=False)


########## 其它 ##########


def resize_image(
    image: PillowImage,
    width: int,
    height: int,
    resample: Optional[int] = None,
    box: Optional[tuple[float, float, float, float]] = None,
    reducing_gap: Optional[float] = None,
) -> PillowImage:
    """重新设置图片大小"""
    if width <= 0:
        raise ValueError(f'宽度必须大于 0 "width={width}"')
    if height <= 0:
        raise ValueError(f'高度必须大于 0 "height={height}"')

    return image.resize(
        size=(width, height),
        resample=_PillowImageModule.Resampling.LANCZOS if resample is None else resample,
        box=box,
        reducing_gap=reducing_gap,
    )
