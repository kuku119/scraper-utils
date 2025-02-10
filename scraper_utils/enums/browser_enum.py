"""
浏览器相关枚举
"""

from enum import (
    StrEnum as _StrEnum,
    auto as _auto,
)


__all__ = [
    'ResourceType',
]


class ResourceType(_StrEnum):
    DOCUMENT = _auto()
    STYLESHEET = _auto()
    IMAGE = _auto()
    MEDIA = _auto()
    FONT = _auto()
    SCRIPT = _auto()
    TEXTTRACK = _auto()
    XHR = _auto()
    FETCH = _auto()
    EVENTSOURCE = _auto()
    WEBSOCKET = _auto()
    MANIFEST = _auto()
    OTHER = _auto()
