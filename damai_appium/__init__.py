# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG & BlueCestbon"
__Version__ = "2.0.0"
__Description__ = "大麦app抢票自动化"
__Created__ = 2023/10/26 10:20
__Updated__ = 2025/11/17
"""

# 导出主要类和模块 (v2.0)
from .config import Config
from .damai_app_v2 import DamaiBot, BotLogger

__all__ = [
    'DamaiBot',
    'BotLogger',
    'Config',
]

__version__ = '2.0.0'
