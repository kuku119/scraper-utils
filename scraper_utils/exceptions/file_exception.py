"""
文件相关异常
"""

__all__ = [
    'NoSelectedFileError',
]


class NoSelectedFileError(Exception):
    """没有选择文件时抛出该异常"""
