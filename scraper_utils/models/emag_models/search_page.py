"""
搜索页的数据模型
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ...utils.emag_url_util import (
    build_product_url,
    clean_product_image_url,
    validate_pnk,
)

if TYPE_CHECKING:
    from typing import Optional

# 获取图片拓展名用的正则表达式
_product_image_ext_pattern = re.compile(r'/images/[0-9a-z_]+\.([a-z]+)')


class CardItem:
    """单个 item-card 包含的产品信息"""

    def __init__(
        self,
        pnk: str,
        title: str,
        image_url: Optional[str] = None,
        review_count: Optional[int] = None,
        rating: Optional[float] = None,
        price: Optional[float] = None,
    ):
        if not validate_pnk(pnk=pnk):
            raise ValueError(f'"{pnk}" 不符合 pnk 格式')
        self.pnk = pnk  # 产品编号
        self.title = title  # 产品名
        self.image_url = image_url  # 产品图链接（可能是略缩图）
        self.review_count = review_count  # 评价数
        self.rating = rating  # 星级
        self.price = price  # 价格

        #
        self.__url: Optional[str] = None
        self.__origin_image_url: Optional[str] = None
        self.__image_ext: Optional[str] = None

    @property
    def url(self) -> str:
        """产品的详情页链接"""
        if self.__url is None:
            self.__url = build_product_url(pnk=self.pnk)
        return self.__url

    @property
    def origin_image_url(self) -> Optional[str]:
        """产品图的原图链接"""
        if self.image_url is None:
            return None

        if self.__origin_image_url is None:
            self.__origin_image_url = clean_product_image_url(url=self.image_url)
        return self.__origin_image_url

    @property
    def image_ext(self) -> Optional[str]:
        """产品图的后缀名"""
        if self.image_url is None:
            return None

        if self.__image_ext is None:
            image_ext_match = _product_image_ext_pattern.search(self.image_url)
            if image_ext_match is None:
                return None
            self.__image_ext: str = image_ext_match.group(1)
        return self.__image_ext

    def as_dict(self) -> dict[str, str | int | float | None]:
        """转成字典"""
        return {
            'pnk': self.pnk,
            'url': self.url,
            'title': self.title,
            'image_url': self.image_url,
            'origin_image_url': self.origin_image_url,
            'image_ext': self.image_ext,
            'review_count': self.review_count,
            'rating': self.rating,
            'price': self.price,
        }

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.pnk}", "{self.title}", "{self.url}")'

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.pnk == other.pnk

    def __hash__(self):
        return hash(self.pnk)


class KeywordResults:
    """单个关键词包含的信息"""

    def __init__(
        self,
        keyword: str,
        url: str,
        items: Optional[list[CardItem]] = None,
    ):
        self.keyword = keyword  # 关键词
        self.url = url  # 搜索页 url

        # 包含的 card-item
        self.items: list[CardItem] = list() if items is None else items
        self.items = list(dict.fromkeys(self.items))  # 去除重复值

    def __add__(self, other):
        """合并两个结果，并去除其中的重复产品（返回新对象）"""
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f'无法将 {self.__class__} 和 {type(other)} 进行合并')

        if self.keyword != other.keyword:
            raise ValueError('两者的关键词不同，无法合并')

        return self.__class__(
            keyword=self.keyword,
            url=self.url,
            items=self.items + other.items,
        )

    def __iadd__(self, other):
        """合并两个结果，并去除其中的重复产品（修改`self.items`）"""
        if not isinstance(other, self.__class__):
            raise NotImplementedError(f'无法将 {self.__class__} 和 {type(other)} 进行合并')

        if self.keyword != other.keyword:
            raise ValueError('两者的关键词不同，无法合并')

        self.items = list(dict.fromkeys(self.items + other.items))
        return self

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.keyword}", "{self.url}", {len(self)} items)'
