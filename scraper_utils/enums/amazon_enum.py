"""
亚马逊站点相关枚举
"""

from __future__ import annotations

from enum import Enum as _Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator


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
    """

    US = 'https://www.amazon.com'
    UK = 'https://www.amazon.co.uk'
    DE = 'https://www.amazon.de'
    FR = 'https://www.amazon.fr'
    IT = 'https://www.amazon.it'
    ES = 'https://www.amazon.es'

    @property
    def url(self):
        """站点对应的 url"""
        return self.value

    @classmethod
    def get_site(cls, site: str):
        """根据 site 获取对应的站点"""
        site = site.upper()
        if any(site == s.name for s in cls.supported_sites()):
            return AmazonSite[site]
        else:
            raise ValueError(f'不支持的站点 "{site}"')

    @classmethod
    def get_url(cls, site: str) -> str:
        """根据 site 获取对应的 url"""
        return cls.get_site(site=site).url

    @classmethod
    def supported_sites(cls) -> Generator['AmazonSite']:
        """支持的站点"""
        for site in cls:
            yield site
