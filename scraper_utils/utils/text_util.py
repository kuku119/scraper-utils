"""
文本相关工具
"""

import re as _re

__all__ = [
    'is_number',
    'is_letter',
    'is_lower_letter',
    'is_upper_letter',
]


pattern_number = _re.compile(r'^\d+(\.\d+)?$')  # 数字格式

pattern_upper_letter = _re.compile(r'^[A-Z]+$')  # 全为小写拉丁字母
pattern_lower_letter = _re.compile(r'^[a-z]+$')  # 全为大写拉丁字母
pattern_letter = _re.compile(r'^[a-zA-Z]+$')  # 全为大小写拉丁字母


def is_number(s: str) -> bool:
    """是否为数字格式的字符串"""
    if len(s) == 0:
        return False
    return pattern_number.match(s) is not None


def is_lower_letter(s: str) -> bool:
    """是否全为小写拉丁字母的字符串"""
    if len(s) == 0:
        return False
    return len(s) != 0 and pattern_lower_letter.match(s) is not None


def is_upper_letter(s: str) -> bool:
    """是否全为大写拉丁字母的字符串"""
    if len(s) == 0:
        return False
    return pattern_upper_letter.match(s) is not None


def is_letter(s: str) -> bool:
    """是否全为大小写拉丁字母的字符串"""
    if len(s) == 0:
        return False
    return pattern_letter.match(s) is not None
