"""
测试 file_util 中的读取功能
"""

from pathlib import Path
import pytest

from scraper_utils.utils.file_util import read_file


@pytest.fixture(scope='session')
def cwd() -> Path:
    return Path.cwd()


async def test_async_1(cwd):
    data = await read_file(file=cwd.joinpath('./LICENSE'), mode='bytes', async_mode=True)
    assert len(data) > 0
    assert 'MIT License' in data.decode()


async def test_async_2(cwd):
    data = await read_file(file=cwd.joinpath('./LICENSE'), mode='str', async_mode=True)
    assert len(data) > 0
    assert 'MIT License' in data


def test_sync_1(cwd):
    data = read_file(file=cwd.joinpath('./LICENSE'), mode='bytes', async_mode=False)
    assert len(data) > 0
    assert 'MIT License' in data.decode()


def test_sync_2(cwd):
    data = read_file(file=cwd.joinpath('./LICENSE'), mode='str', async_mode=False)
    assert len(data) > 0
    assert 'MIT License' in data
