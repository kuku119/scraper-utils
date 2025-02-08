"""
时间相关工具
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import tzinfo
    from typing import Optional


__all__ = [
    'now',
    'now_str',
]


def now(tz: Optional[tzinfo] = None) -> datetime:
    """获取特定时区的当前时间，默认为本地时区"""
    return datetime.now(tz=tz)


def now_str(formatter: str = '%Y-%m-%d %H:%M:%S', tz: Optional[tzinfo] = None) -> str:
    """按照 formatter 获取当前时间字符串"""
    return now(tz=tz).strftime(formatter)
