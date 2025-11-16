# -*- coding: UTF-8 -*-
"""
简化版设备管理器 - 仅供GUI使用
"""

import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class Device:
    """设备信息"""
    name: str
    address: str
    type: str = "adb"  # adb, redhand, emulator


class DeviceManager:
    """简化版设备管理器"""

    def __init__(self, config_file: str = "devices.json"):
        self.config_file = Path(config_file)
        self.devices: List[Device] = []
        self.load_devices()

    def load_devices(self):
        """加载设备列表"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.devices = [Device(**d) for d in data]
            except Exception:
                self.devices = []
        else:
            self.devices = []

    def save_devices(self):
        """保存设备列表"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(d) for d in self.devices], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def list_devices(self) -> List[Device]:
        """列出所有设备"""
        return self.devices

    def add_device(self, name: str, address: str, device_type: str = "adb"):
        """添加设备"""
        # 检查是否已存在
        for device in self.devices:
            if device.name == name:
                raise ValueError(f"设备 '{name}' 已存在")

        device = Device(name=name, address=address, type=device_type)
        self.devices.append(device)
        self.save_devices()

    def remove_device(self, name: str):
        """删除设备"""
        self.devices = [d for d in self.devices if d.name != name]
        self.save_devices()

    def auto_detect_devices(self) -> List[Device]:
        """自动检测ADB设备"""
        new_devices = []
        try:
            result = subprocess.run(['adb', 'devices'],
                                  capture_output=True,
                                  text=True,
                                  timeout=5)

            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行

            for line in lines:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]

                    # 检查是否已存在
                    exists = any(d.address == device_id for d in self.devices)
                    if not exists:
                        name = f"ADB-{device_id[:8]}"
                        device = Device(name=name, address=device_id, type="adb")
                        self.devices.append(device)
                        new_devices.append(device)

            if new_devices:
                self.save_devices()
        except Exception:
            pass

        return new_devices
