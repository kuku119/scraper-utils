"""
测试列名、列号转换
"""

from openpyxl.utils import (
    column_index_from_string as s2i_openpyxl,
    get_column_letter as i2s_openpyxl,
)
import pytest

from scraper_utils.utils.workbook_util import (
    string_column_to_integer_column as s2i,
    integer_column_to_string_column as i2s,
)


def test_s2i():
    for i in range(1, 16385):
        column_name = i2s_openpyxl(i)
        assert s2i(column_name=column_name) == s2i_openpyxl(column_name)


def test_i2s():
    for i in range(1, 16385):
        assert i2s(column_index=i) == i2s_openpyxl(i)


def test_s2i_range():
    s2i(column_name='A')
    s2i(column_name='XFD')
    with pytest.raises(ValueError):
        s2i(column_name='')
    with pytest.raises(ValueError):
        s2i(column_name='1')
    with pytest.raises(ValueError):
        s2i(column_name='XFE')


def test_i2s_range():
    i2s(1)
    i2s(16384)
    with pytest.raises(ValueError):
        i2s(0)
    with pytest.raises(ValueError):
        i2s(16385)
