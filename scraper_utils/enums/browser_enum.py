"""
浏览器相关枚举
"""

from enum import StrEnum as _StrEnum


__all__ = [
    'ResourceType',
]


class ResourceType(_StrEnum):
    """浏览器接受的资源类型"""

    DOCUMENT = 'document'
    STYLESHEET = 'stylesheet'
    IMAGE = 'image'
    MEDIA = 'media'
    FONT = 'font'
    SCRIPT = 'script'
    TEXTTRACK = 'texttrack'
    XHR = 'xhr'
    FETCH = 'fetch'
    EVENTSOURCE = 'eventsource'
    WEBSOCKET = 'websocket'
    MANIFEST = 'manifest'
    OTHER = 'other'
