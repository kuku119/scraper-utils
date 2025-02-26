"""
工作簿样式相关常量
"""

from openpyxl.styles import (
    PatternFill,
    Font,
    Alignment,
)


__all__ = [
    'TEXT_CENTER_ALIGNMENT',
    'TEXT_CENTER_WRAP_ALIGNMENT',
    'HYPERLINK_FONT',
    'RED_BOLD_FONT',
    'YELLOW_FILL',
]


# 文本居中
TEXT_CENTER_ALIGNMENT = Alignment(horizontal='center', vertical='center')
# 文本居中 + 自动换行
TEXT_CENTER_WRAP_ALIGNMENT = Alignment(horizontal='center', vertical='center', wrap_text=True)

# 链接字体
HYPERLINK_FONT = Font(color='0000FF', underline='single')

# 加粗红字
RED_BOLD_FONT = Font(color='FF0000', bold=True)

# 黄色填充
YELLOW_FILL = PatternFill(fill_type='solid', fgColor='FFFF00')
