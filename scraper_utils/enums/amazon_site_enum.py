"""
亚马逊站点枚举
"""

from __future__ import annotations

from enum import Enum as __Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator


class AmazonSite(__Enum):
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

    US = 'https://www.amazon.com'  # 美国
    UK = 'https://www.amazon.co.uk'  # 英国
    DE = 'https://www.amazon.de'  # 德国
    FR = 'https://www.amazon.fr'  # 法国
    IT = 'https://www.amazon.it'  # 意大利
    ES = 'https://www.amazon.es'  # 西班牙

    @property
    def url(self):
        """站点对应的 url"""
        return self.value

    @property
    def cn_description(self):
        """站点的中文描述"""
        match self:
            case AmazonSite.US:
                return '美国'
            case AmazonSite.UK:
                return '英国'
            case AmazonSite.DE:
                return '德国'
            case AmazonSite.FR:
                return '法国'
            case AmazonSite.IT:
                return '意大利'
            case AmazonSite.ES:
                return '西班牙'

    @classmethod
    def get_site(cls, site: str) -> 'AmazonSite':
        """根据 site 获取对应的站点"""
        site = site.upper()
        if site in (s.name for s in cls.supported_sites()):
            return AmazonSite[site]
        else:
            raise ValueError(f'Site {site} not supported')

    @classmethod
    def get_url(cls, site: str) -> str:
        """根据 site 获取对应的 url"""
        return cls.get_site(site=site).url

    @classmethod
    def supported_sites(cls) -> Generator['AmazonSite', None, None]:
        """支持哪些站点"""
        for site in cls:
            yield site

    @classmethod
    def supported_urls(cls) -> Generator[str, None, None]:
        """支持哪些 url"""
        for site in cls:
            yield site.url
