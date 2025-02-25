"""
爬取 Temu 的关键词搜索页面
"""

import asyncio
from pathlib import Path
from sys import stderr

from loguru import logger

from scraper_utils.utils.browser_util import PersistentContextManager

# 当前工作目录
cwd = Path.cwd()

# 日志
logger.remove()
logger.add(
    stderr,
    format=(
        '[<green>{time:HH:mm:ss}</green>] [<level>{level:.3}</level>] '
        '[<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>] >>> '
        '<level>{message}</level>'
    ),
)


async def start_scrape():
    """"""
    # TODO


if __name__ == '__main__':

    async def main():
        """"""
        # TODO

    asyncio.run(main())
