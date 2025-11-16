# -*- coding: UTF-8 -*-
"""
配置模板管理系统 - 快速切换演出配置
支持：保存/加载/删除/导入/导出配置模板
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class TicketConfig:
    """抢票配置"""
    name: str  # 模板名称
    keyword: str  # 演出关键词
    city: str  # 城市
    date: str  # 日期
    price: str  # 票价
    price_index: int  # 票档索引
    users: List[str]  # 观演人
    adb_port: str  # ADB端口
    server_url: str  # Appium服务器地址
    if_commit_order: bool  # 是否提交订单
    notes: str = ""  # 备注
    created_at: str = ""  # 创建时间
    updated_at: str = ""  # 更新时间

    def __post_init__(self):
        """初始化时间戳"""
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.updated_at:
            self.updated_at = self.created_at


class ConfigTemplateManager:
    """配置模板管理器"""

    def __init__(self, templates_dir: str = "config_templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_file = self.templates_dir / "templates.json"
        self.templates: Dict[str, TicketConfig] = {}
        self.load_all_templates()

    def load_all_templates(self):
        """加载所有模板"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.templates = {
                    name: TicketConfig(**config)
                    for name, config in data.items()
                }

                print(f"[模板管理] 成功加载 {len(self.templates)} 个配置模板")
            except Exception as e:
                print(f"[模板管理] 加载模板失败: {e}")
                self.templates = {}
        else:
            self.templates = {}

    def save_all_templates(self):
        """保存所有模板"""
        try:
            data = {
                name: asdict(config)
                for name, config in self.templates.items()
            }

            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"[模板管理] 成功保存 {len(self.templates)} 个配置模板")
            return True
        except Exception as e:
            print(f"[模板管理] 保存模板失败: {e}")
            return False

    def save_template(self, config: TicketConfig, overwrite: bool = False) -> bool:
        """
        保存配置模板

        Args:
            config: 配置对象
            overwrite: 是否覆盖已存在的模板

        Returns:
            bool: 是否成功
        """
        if config.name in self.templates and not overwrite:
            print(f"[模板管理] 模板 '{config.name}' 已存在，使用 overwrite=True 覆盖")
            return False

        # 更新时间戳
        config.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.templates[config.name] = config
        return self.save_all_templates()

    def load_template(self, name: str) -> Optional[TicketConfig]:
        """
        加载配置模板

        Args:
            name: 模板名称

        Returns:
            TicketConfig: 配置对象，如果不存在返回None
        """
        if name in self.templates:
            return self.templates[name]
        else:
            print(f"[模板管理] 模板 '{name}' 不存在")
            return None

    def delete_template(self, name: str) -> bool:
        """
        删除配置模板

        Args:
            name: 模板名称

        Returns:
            bool: 是否成功
        """
        if name in self.templates:
            del self.templates[name]
            return self.save_all_templates()
        else:
            print(f"[模板管理] 模板 '{name}' 不存在")
            return False

    def list_templates(self) -> List[str]:
        """列出所有模板名称"""
        return list(self.templates.keys())

    def get_templates_info(self) -> List[Dict[str, Any]]:
        """获取所有模板信息（用于GUI显示）"""
        info_list = []
        for name, config in self.templates.items():
            info_list.append({
                "name": name,
                "keyword": config.keyword,
                "city": config.city,
                "date": config.date,
                "price": config.price,
                "notes": config.notes,
                "created_at": config.created_at,
                "updated_at": config.updated_at
            })

        # 按更新时间排序（最新的在前）
        info_list.sort(key=lambda x: x["updated_at"], reverse=True)
        return info_list

    def export_template(self, name: str, export_path: str) -> bool:
        """
        导出配置模板到JSON文件

        Args:
            name: 模板名称
            export_path: 导出路径

        Returns:
            bool: 是否成功
        """
        config = self.load_template(name)
        if not config:
            return False

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, ensure_ascii=False, indent=2)

            print(f"[模板管理] 成功导出模板 '{name}' 到 {export_path}")
            return True
        except Exception as e:
            print(f"[模板管理] 导出模板失败: {e}")
            return False

    def import_template(self, import_path: str, overwrite: bool = False) -> bool:
        """
        从JSON文件导入配置模板

        Args:
            import_path: 导入路径
            overwrite: 是否覆盖已存在的模板

        Returns:
            bool: 是否成功
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = TicketConfig(**data)
            return self.save_template(config, overwrite=overwrite)

        except Exception as e:
            print(f"[模板管理] 导入模板失败: {e}")
            return False

    def search_templates(self, keyword: str) -> List[str]:
        """
        搜索模板

        Args:
            keyword: 搜索关键词

        Returns:
            List[str]: 匹配的模板名称列表
        """
        keyword_lower = keyword.lower()
        results = []

        for name, config in self.templates.items():
            # 在名称、关键词、城市、备注中搜索
            if (keyword_lower in name.lower() or
                keyword_lower in config.keyword.lower() or
                keyword_lower in config.city.lower() or
                keyword_lower in config.notes.lower()):
                results.append(name)

        return results

    def duplicate_template(self, source_name: str, new_name: str) -> bool:
        """
        复制模板

        Args:
            source_name: 源模板名称
            new_name: 新模板名称

        Returns:
            bool: 是否成功
        """
        source_config = self.load_template(source_name)
        if not source_config:
            return False

        if new_name in self.templates:
            print(f"[模板管理] 模板 '{new_name}' 已存在")
            return False

        # 创建副本
        new_config = TicketConfig(
            name=new_name,
            keyword=source_config.keyword,
            city=source_config.city,
            date=source_config.date,
            price=source_config.price,
            price_index=source_config.price_index,
            users=source_config.users.copy(),
            adb_port=source_config.adb_port,
            server_url=source_config.server_url,
            if_commit_order=source_config.if_commit_order,
            notes=f"复制自 {source_name}"
        )

        return self.save_template(new_config)

    def create_quick_template(self,
                            name: str,
                            keyword: str,
                            city: str,
                            date: str = "",
                            price: str = "",
                            adb_port: str = "59700") -> bool:
        """
        快速创建配置模板（使用默认值）

        Args:
            name: 模板名称
            keyword: 演出关键词
            city: 城市
            date: 日期
            price: 票价
            adb_port: ADB端口

        Returns:
            bool: 是否成功
        """
        config = TicketConfig(
            name=name,
            keyword=keyword,
            city=city,
            date=date,
            price=price,
            price_index=0,
            users=[],
            adb_port=adb_port,
            server_url="http://127.0.0.1:4723",
            if_commit_order=False,
            notes=f"快速创建于 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        return self.save_template(config)


# 单例模式
_template_manager_instance = None


def get_template_manager() -> ConfigTemplateManager:
    """获取配置模板管理器单例"""
    global _template_manager_instance
    if _template_manager_instance is None:
        _template_manager_instance = ConfigTemplateManager()
    return _template_manager_instance
