"""
亚马逊站点相关枚举
"""

from __future__ import annotations

from enum import Enum as _Enum
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Generator, Self, Optional, TypeVar

    T = TypeVar('T')


__all__ = [
    'AmazonSite',
]


class AmazonSite(_Enum):
    """
    亚马逊站点

    ---

    目前支持的站点：

    1. US
    2. UK
    3. DE
    4. FR
    5. IT
    6. ES
    7. JP
    """

    US = 'https://www.amazon.com'
    UK = 'https://www.amazon.co.uk'
    DE = 'https://www.amazon.de'
    FR = 'https://www.amazon.fr'
    IT = 'https://www.amazon.it'
    ES = 'https://www.amazon.es'
    JP = 'https://www.amazon.co.jp'

    @property
    def url(self):
        """站点对应的 url"""
        return self.value

    @overload
    @classmethod
    def get(cls, site: str) -> Self: ...

    @overload
    @classmethod
    def get(cls, site: str, default: T) -> Self | T: ...

    @classmethod
    def get(cls, site: str, default: T = None) -> Self | T:
        """根据 site 获取对应的站点，如果不存在且 default 已设置则返回 default
        参数：
            site: 站点名称（不区分大小写）
            default: 可选参数，当站点不存在时返回的默认值
        """
        site = site.upper()
        for s in cls:
            if site == s.name:
                return s
        else:
            return default

    @overload
    @classmethod
    def get_url(cls, site: str) -> str: ...

    @overload
    @classmethod
    def get_url(cls, site: str, default: T) -> str | T: ...

    @classmethod
    def get_url(cls, site: str, default: T = None) -> str | T:
        """根据 site 获取对应的 url，如果不存在且 default 已设置则返回 default
        参数：
            site: 站点名称（不区分大小写）
            default: 可选参数，当站点不存在时返回的默认值
        """
        try:
            return cls.get(site).url
        except KeyError:
            return default

    @classmethod
    def supported_sites(cls) -> Generator[Self]:
        """支持的站点"""
        for site in cls:
            yield site


if __name__ == '__main__':
    s1 = AmazonSite.get('S')
    print(s1)
