"""
其它工具
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


__all__ = [
    #
    'all_none',
    'all_not_none',
    #
    'any_none',
    'any_not_none',
]


def all_none(*objs: Any) -> bool:
    """全为空"""
    return all(obj is None for obj in objs)


def all_not_none(*objs: Any) -> bool:
    """全不为空"""
    return all(obj is not None for obj in objs)


def any_none(*objs: Any) -> bool:
    """任一为空"""
    return any(obj is None for obj in objs)


def any_not_none(*objs: Any) -> bool:
    """任一不为空"""
    return any(obj is not None for obj in objs)
