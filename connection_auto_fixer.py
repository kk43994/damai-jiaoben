#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
连接自动修复模块 - 整合 Appium、ADB 和 WebDriver 的自动检测和修复
提供一键修复功能
"""

import subprocess
import time
import requests
from pathlib import Path
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class ConnectionStatus:
    """连接状态"""
    appium_running: bool = False
    adb_connected: bool = False
    webdriver_healthy: bool = False
    device_udid: Optional[str] = None
    error_messages: List[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []

    @property
    def is_ready(self) -> bool:
        """是否准备就绪"""
        return self.appium_running and self.adb_connected


class ConnectionAutoFixer:
    """连接自动修复器 - 一键修复所有连接问题"""

    def __init__(self, logger=None, adb_port: str = "59700"):
        """
        初始化连接自动修复器

        Args:
            logger: 日志记录器（需要有 info, warning, error, success 方法）
            adb_port: ADB端口号
        """
        self.logger = logger
        self.adb_port = adb_port
        self.adb_path = self._find_adb()
        self.appium_url = "http://127.0.0.1:4723"

    def _find_adb(self) -> Path:
        """查找ADB工具路径"""
        # 标准Android SDK路径
        sdk_path = Path.home() / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools"
        adb_exe = sdk_path / "adb.exe"

        if adb_exe.exists():
            return adb_exe

        # 检查PATH中的adb
        try:
            result = subprocess.run("where adb", capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return Path(result.stdout.strip().split('\n')[0])
        except:
            pass

        return Path("adb")

    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        if self.logger:
            log_method = getattr(self.logger, level.lower(), None)
            if log_method:
                log_method(message)
            else:
                print(f"[{level}] {message}")
        else:
            print(f"[{level}] {message}")

    def check_appium_service(self) -> bool:
        """检查Appium服务是否运行"""
        try:
            response = requests.get(f"{self.appium_url}/status", timeout=3)
            if response.status_code == 200:
                self._log("✓ Appium服务运行正常", "INFO")
                return True
        except requests.exceptions.ConnectionError:
            self._log("✗ Appium服务未运行", "WARNING")
        except Exception as e:
            self._log(f"✗ Appium检测失败: {e}", "ERROR")
        return False

    def start_appium_service(self) -> bool:
        """启动Appium服务（后台运行）"""
        self._log("正在启动Appium服务...", "INFO")

        try:
            # 方法1: 使用start_appium.bat（如果存在）
            bat_file = Path(__file__).parent / "start_appium.bat"
            if bat_file.exists():
                self._log("使用 start_appium.bat 启动", "INFO")
                subprocess.Popen(
                    str(bat_file),
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # 方法2: 直接启动appium
                self._log("直接启动 appium 命令", "INFO")
                subprocess.Popen(
                    ["appium", "--address", "127.0.0.1", "--port", "4723", "--allow-cors"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            # 等待服务启动（最多30秒）
            for i in range(30):
                time.sleep(1)
                if self.check_appium_service():
                    self._log(f"✓ Appium服务启动成功 (耗时 {i+1} 秒)", "SUCCESS")
                    return True
                if i % 5 == 0:
                    self._log(f"等待Appium启动... ({i+1}/30秒)", "INFO")

            self._log("✗ Appium服务启动超时", "ERROR")
            return False

        except FileNotFoundError:
            self._log("✗ Appium命令未找到，请确认已安装Appium", "ERROR")
            return False
        except Exception as e:
            self._log(f"✗ 启动Appium失败: {e}", "ERROR")
            return False

    def check_adb_device(self, udid: str, check_offline: bool = False) -> bool:
        """
        检查ADB设备是否已连接

        Args:
            udid: 设备UDID
            check_offline: 如果为True，返回设备是否为offline状态

        Returns:
            如果check_offline=True: 返回设备是否离线
            如果check_offline=False: 返回设备是否正常连接
        """
        try:
            result = subprocess.run(
                f'"{self.adb_path}" devices',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            if result.returncode == 0:
                output = result.stdout
                # 检查设备是否在列表中且状态正常
                for line in output.split('\n'):
                    if udid in line:
                        if '\tdevice' in line or ' device' in line:
                            if not check_offline:
                                self._log(f"✓ ADB设备已连接: {udid}", "INFO")
                            return False if check_offline else True
                        elif 'offline' in line:
                            if check_offline:
                                return True
                            else:
                                self._log(f"✗ ADB设备离线: {udid}", "WARNING")
                                return False
                        elif 'unauthorized' in line:
                            self._log(f"✗ ADB设备未授权: {udid}", "WARNING")
                            return False

                if not check_offline:
                    self._log(f"✗ ADB设备未找到: {udid}", "WARNING")
                return False

            return False

        except Exception as e:
            self._log(f"✗ ADB设备检测失败: {e}", "ERROR")
            return False

    def clear_zombie_connections(self, max_retries: int = 3) -> bool:
        """
        清除ADB僵尸连接（智能版）

        清理策略：
        1. 先检测是否有僵尸连接
        2. 如果有，才执行清理：断开所有ADB连接
        3. 重启ADB服务器
        4. 等待网络连接完全释放

        Args:
            max_retries: 最大重试次数

        Returns:
            是否成功清除
        """
        self._log("开始清除ADB僵尸连接...", "INFO")

        # 优化：先检测是否真的有僵尸连接
        try:
            result = subprocess.run(
                f'"{self.adb_path}" devices',
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )

            offline_count = 0
            unauthorized_count = 0
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.split('\n'):
                    if 'offline' in line:
                        offline_count += 1
                    elif 'unauthorized' in line:
                        unauthorized_count += 1

            if offline_count == 0 and unauthorized_count == 0:
                self._log("✓ 未检测到僵尸连接，跳过清理", "INFO")
                return True

            self._log(f"检测到 {offline_count + unauthorized_count} 个异常连接（离线:{offline_count}, 未授权:{unauthorized_count}），开始清理...", "INFO")
        except Exception as e:
            self._log(f"检测异常连接时出错: {e}，继续执行清理", "WARNING")

        try:
            for attempt in range(max_retries):
                if attempt > 0:
                    self._log(f"  重试 {attempt + 1}/{max_retries}...", "INFO")

                # 1. 断开所有设备
                self._log("  [1/3] 断开所有ADB设备...", "INFO")
                result = subprocess.run(
                    f'"{self.adb_path}" devices',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=10
                )

                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.split('\n'):
                        if '127.0.0.1:' in line:
                            parts = line.split()
                            if parts:
                                device_id = parts[0]
                                subprocess.run(
                                    f'"{self.adb_path}" disconnect {device_id}',
                                    capture_output=True,
                                    shell=True,
                                    timeout=5
                                )

                time.sleep(1)

                # 2. 重启ADB服务器
                self._log("  [2/3] 重启ADB服务器...", "INFO")
                subprocess.run(
                    f'"{self.adb_path}" kill-server',
                    capture_output=True,
                    shell=True,
                    timeout=10
                )
                time.sleep(2)

                # 启动服务器
                subprocess.run(
                    f'"{self.adb_path}" start-server',
                    capture_output=True,
                    shell=True,
                    timeout=10
                )
                time.sleep(1)

                # 3. 验证清理结果
                self._log("  [3/3] 验证清理结果...", "INFO")
                result = subprocess.run(
                    f'"{self.adb_path}" devices',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=10
                )

                # 检查是否还有设备连接
                connected_devices = 0
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.split('\n'):
                        if '127.0.0.1:' in line and 'device' in line:
                            connected_devices += 1

                if connected_devices == 0:
                    self._log("✓ ADB僵尸连接已清除", "SUCCESS")
                    return True
                else:
                    self._log(f"  仍有 {connected_devices} 个设备连接", "WARNING")
                    time.sleep(2)

            self._log("✗ 清除僵尸连接失败（达到最大重试次数）", "ERROR")
            return False

        except Exception as e:
            self._log(f"✗ 清除僵尸连接时出错: {e}", "ERROR")
            return False

    def fix_offline_device(self, udid: str) -> bool:
        """修复离线的ADB设备（优化版）"""
        self._log(f"检测到设备离线，尝试修复: {udid}", "WARNING")

        # 优化：先检查端口可达性，避免浪费时间
        if ':' in udid:
            host, port_str = udid.split(':')
            port = int(port_str)
            reachable, reason = self._test_port_reachable(host, port, timeout=2)
            if not reachable:
                self._log(f"✗ 端口 {port} 不可达: {reason}", "ERROR")
                self._log("", "ERROR")
                self._log("⚠️  设备可能处于以下状态:", "ERROR")
                self._log("  • 红手指云手机未启动或离线", "ERROR")
                self._log("  • 端口号配置错误", "ERROR")
                self._log("  • 网络连接问题", "ERROR")
                self._log("", "ERROR")
                self._show_port_check_guide(port_str)
                return False  # 提前返回，不浪费时间执行修复流程

        try:
            # 1. 先尝试清除僵尸连接
            self._log("  [1/4] 清除僵尸连接...", "INFO")
            self.clear_zombie_connections(max_retries=2)

            # 2. 断开连接
            self._log("  [2/4] 断开设备连接...", "INFO")
            subprocess.run(
                f'"{self.adb_path}" disconnect {udid}',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )
            time.sleep(1)

            # 3. 杀死ADB服务器
            self._log("  [3/4] 重启ADB服务器...", "INFO")
            subprocess.run(
                f'"{self.adb_path}" kill-server',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )
            time.sleep(2)

            # 4. 重新连接
            self._log("  [4/4] 重新连接设备...", "INFO")
            if self.connect_adb_device(udid):
                self._log(f"✓ 设备修复成功: {udid}", "SUCCESS")
                return True
            else:
                self._log(f"✗ 设备修复失败: {udid}", "ERROR")
                return False

        except Exception as e:
            self._log(f"✗ 修复设备时出错: {e}", "ERROR")
            return False

    def _show_port_check_guide(self, port: str):
        """显示红手指连接排查指南"""
        self._log("="*60, "INFO")
        self._log("🔧 红手指连接排查指南", "INFO")
        self._log("="*60, "INFO")
        self._log("", "INFO")
        self._log("请按以下步骤检查:", "INFO")
        self._log("", "INFO")
        self._log("1️⃣  打开红手指客户端", "INFO")
        self._log("   - 确认云手机状态显示为'在线'（绿色）", "INFO")
        self._log("   - 如果离线，请点击'启动'按钮", "INFO")
        self._log("", "INFO")
        self._log("2️⃣  查看ADB端口号", "INFO")
        self._log("   - 在云手机卡片上找到端口号显示", "INFO")
        self._log(f"   - 当前配置端口: {port}", "INFO")
        self._log("   - 如果不一致，请在GUI中修改端口号", "INFO")
        self._log("", "INFO")
        self._log("3️⃣  确保ADB调试已开启", "INFO")
        self._log("   - 打开云手机的'设置' → '开发者选项'", "INFO")
        self._log("   - 确保'USB调试'已开启", "INFO")
        self._log("", "INFO")
        self._log("4️⃣  尝试重启", "INFO")
        self._log("   - 重启红手指客户端", "INFO")
        self._log("   - 或重启云手机", "INFO")
        self._log("", "INFO")
        self._log("="*60, "INFO")

    def _test_port_reachable(self, host: str, port: int, timeout: float = 2) -> Tuple[bool, str]:
        """
        测试端口是否可达（增强版）

        Args:
            host: 主机地址
            port: 端口号
            timeout: 超时时间（秒）

        Returns:
            (可达性, 详细信息)
        """
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return True, "端口可达"
            elif result == 10061:  # Windows: Connection refused
                return False, "端口拒绝连接（设备可能未启动ADB服务）"
            elif result == 10060:  # Windows: Connection timeout
                return False, "连接超时（网络不可达或防火墙阻止）"
            else:
                return False, f"连接失败（错误代码: {result}）"
        except socket.timeout:
            return False, "连接超时（网络延迟过高或设备离线）"
        except Exception as e:
            return False, f"检测失败: {str(e)}"

    def connect_adb_device(self, udid: str) -> bool:
        """连接ADB设备"""
        self._log(f"正在连接ADB设备: {udid}...", "INFO")

        # 快速检查端口可达性（优化：返回详细原因）
        if ':' in udid:
            host, port_str = udid.split(':')
            port = int(port_str)
            reachable, reason = self._test_port_reachable(host, port)
            if not reachable:
                self._log(f"✗ 端口 {port} 不可达: {reason}", "WARNING")
                # 继续尝试连接，因为有时socket检测不准确

        try:
            result = subprocess.run(
                f'"{self.adb_path}" connect {udid}',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10  # 优化: 从30秒降低到10秒，快速失败
            )

            if result.returncode == 0:
                # 修复：安全处理 stdout，避免 NoneType 错误
                output = (result.stdout or "").lower()
                if 'connected' in output or 'already connected' in output:
                    self._log(f"✓ ADB连接成功: {udid}", "SUCCESS")
                    time.sleep(2)  # 等待连接稳定
                    return self.check_adb_device(udid)
                else:
                    self._log(f"✗ ADB连接失败: {result.stdout or '(无输出)'}", "ERROR")
                    return False
            else:
                self._log(f"✗ ADB连接命令失败: {result.stderr or '(无输出)'}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self._log("✗ ADB连接超时（30秒）", "ERROR")
            return False
        except Exception as e:
            self._log(f"✗ ADB连接失败: {e}", "ERROR")
            return False

    def auto_scan_adb_ports(self) -> Optional[str]:
        """自动扫描常用ADB端口"""
        self._log("开始扫描常用ADB端口...", "INFO")

        common_ports = [
            # 红手指常用端口
            59700, 59701, 59702, 53709,
            # MuMu模拟器
            16384, 16416, 16448,
            # 夜神模拟器
            62001, 62025, 62026,
            # 雷电模拟器
            5555, 5557, 5559,
        ]

        for port in common_ports:
            device_address = f"127.0.0.1:{port}"
            self._log(f"  尝试端口 {port}...", "INFO")

            if self.connect_adb_device(device_address):
                self._log(f"✓ 找到可用设备: {device_address}", "SUCCESS")
                return device_address

        self._log("✗ 未找到可用的ADB设备", "WARNING")
        return None

    def check_all(self, udid: Optional[str] = None) -> ConnectionStatus:
        """
        检查所有连接状态

        Args:
            udid: 设备UDID，如果为None则使用self.adb_port

        Returns:
            ConnectionStatus对象
        """
        if udid is None:
            udid = f"127.0.0.1:{self.adb_port}"

        status = ConnectionStatus()

        # 1. 检查Appium
        self._log("="*60, "INFO")
        self._log("开始连接状态检测", "INFO")
        self._log("="*60, "INFO")

        status.appium_running = self.check_appium_service()
        if not status.appium_running:
            status.error_messages.append("Appium服务未运行")

        # 2. 检查ADB设备
        status.adb_connected = self.check_adb_device(udid)
        status.device_udid = udid if status.adb_connected else None
        if not status.adb_connected:
            status.error_messages.append(f"ADB设备未连接: {udid}")

        # 3. 总结
        self._log("="*60, "INFO")
        if status.is_ready:
            self._log("✓ 所有连接检测通过，可以开始抢票", "SUCCESS")
        else:
            self._log("✗ 检测到连接问题，需要修复", "WARNING")
            for msg in status.error_messages:
                self._log(f"  • {msg}", "WARNING")
        self._log("="*60, "INFO")

        return status

    def auto_fix_all(self, udid: Optional[str] = None, auto_scan: bool = True) -> bool:
        """
        自动修复所有连接问题

        Args:
            udid: 设备UDID，如果为None则使用self.adb_port
            auto_scan: 如果连接失败是否自动扫描端口

        Returns:
            是否修复成功
        """
        if udid is None:
            udid = f"127.0.0.1:{self.adb_port}"

        self._log("="*60, "INFO")
        self._log("开始自动修复连接", "INFO")
        self._log("="*60, "INFO")

        # 1. 修复Appium服务
        self._log("[1/2] 检测Appium服务...", "INFO")
        if not self.check_appium_service():
            self._log("Appium服务未运行，尝试启动...", "WARNING")
            if not self.start_appium_service():
                self._log("✗ Appium服务启动失败", "ERROR")
                return False
        else:
            self._log("✓ Appium服务运行正常", "SUCCESS")

        # 2. 修复ADB连接
        self._log("[2/2] 检测ADB设备连接...", "INFO")

        # 首先检查设备是否离线
        if self.check_adb_device(udid, check_offline=True):
            # 设备离线，尝试修复
            if not self.fix_offline_device(udid):
                self._log("✗ 设备离线修复失败", "ERROR")
                return False
        elif not self.check_adb_device(udid):
            # 设备未连接，尝试连接
            self._log(f"ADB设备未连接，尝试连接 {udid}...", "WARNING")
            if not self.connect_adb_device(udid):
                # 如果连接失败且启用自动扫描
                if auto_scan:
                    self._log("当前端口连接失败，尝试自动扫描其他端口...", "INFO")
                    found_udid = self.auto_scan_adb_ports()
                    if found_udid:
                        self.adb_port = found_udid.split(':')[1]
                        udid = found_udid
                    else:
                        self._log("✗ 未找到可用的ADB设备", "ERROR")
                        self._log("请检查:", "ERROR")
                        self._log("  1. 红手指云手机是否在线", "ERROR")
                        self._log("  2. 端口号是否正确", "ERROR")
                        self._log("  3. 云手机是否允许ADB调试", "ERROR")
                        return False
                else:
                    # 手动指定端口模式 - 不扫描其他端口
                    self._log(f"✗ 无法连接到指定端口: {udid}", "ERROR")
                    self._log("请检查:", "ERROR")
                    self._log("  1. 红手指云手机是否在线", "ERROR")
                    self._log("  2. 端口号是否正确（查看红手指客户端显示的端口）", "ERROR")
                    self._log("  3. 云手机是否允许ADB调试", "ERROR")
                    self._log("  4. 是否需要重启红手指客户端", "ERROR")
                    return False
        else:
            self._log(f"✓ ADB设备已连接: {udid}", "SUCCESS")

        # 3. 验证修复结果
        self._log("="*60, "INFO")
        self._log("验证修复结果...", "INFO")
        status = self.check_all(udid)

        if status.is_ready:
            self._log("✓ 所有连接修复成功！", "SUCCESS")
            self._log("="*60, "INFO")
            return True
        else:
            self._log("✗ 连接修复失败", "ERROR")
            for msg in status.error_messages:
                self._log(f"  • {msg}", "ERROR")
            self._log("="*60, "INFO")
            return False


# 简单的日志记录器（如果GUI没有提供）
class SimpleLogger:
    """简单的日志记录器"""

    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def warning(msg):
        print(f"[WARN] {msg}")

    @staticmethod
    def error(msg):
        print(f"[ERROR] {msg}")

    @staticmethod
    def success(msg):
        print(f"[OK] {msg}")


# 测试代码
if __name__ == "__main__":
    logger = SimpleLogger()
    fixer = ConnectionAutoFixer(logger, adb_port="59700")

    # 检测连接状态
    status = fixer.check_all()

    # 如果有问题，尝试自动修复
    if not status.is_ready:
        print("\n检测到连接问题，开始自动修复...\n")
        success = fixer.auto_fix_all(auto_scan=True)
        if success:
            print("\n✓ 连接修复成功！")
        else:
            print("\n✗ 连接修复失败，请检查环境配置")
