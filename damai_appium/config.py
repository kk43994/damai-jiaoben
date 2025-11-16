# -*- coding: UTF-8 -*-
"""
__Author__ = "WECENG"
__Version__ = "1.0.0"
__Description__ = "配置类"
__Created__ = 2023/10/27 09:54
"""
import json
import os


class Config:
    def __init__(self, server_url, keyword, users, city, date, price, price_index, if_commit_order, adb_port=None):
        self.server_url = server_url
        self.keyword = keyword
        self.users = users
        self.city = city
        self.date = date
        self.price = price
        self.price_index = price_index
        self.if_commit_order = if_commit_order
        self.adb_port = adb_port or "62001"  # 默认端口

    @staticmethod
    def load_config():
        # 尝试多个可能的配置文件路径
        possible_paths = [
            'config.jsonc',  # 当前目录
            'damai_appium/config.jsonc',  # 项目根目录
            os.path.join(os.path.dirname(__file__), 'config.jsonc'),  # 脚本所在目录
        ]

        config_path = None
        for path in possible_paths:
            if os.path.exists(path):
                config_path = path
                break

        if not config_path:
            raise FileNotFoundError(f"找不到config.jsonc文件，尝试了以下路径: {possible_paths}")

        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
        return Config(config['server_url'],
                      config['keyword'],
                      config['users'],
                      config['city'],
                      config['date'],
                      config['price'],
                      config['price_index'],
                      config['if_commit_order'],
                      config.get('adb_port', '62001'))  # 兼容旧配置文件