#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
环境检测和自动修复模块
提供完整的环境检测、诊断和自动修复功能
"""

import subprocess
import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class CheckResult:
    """检测结果数据类"""
    status: str  # 'ok', 'warning', 'error'
    message: str
    details: str = ""
    fix_available: bool = False
    fix_type: str = "manual"  # 'auto', 'manual', 'none'
    fix_action: Optional[str] = None


class EnvironmentChecker:
    """环境检测器 - 检测所有必需的环境组件"""

    def __init__(self):
        self.adb_path = self._find_adb()
        self.results = {}

    def _find_adb(self) -> Path:
        """查找ADB工具路径"""
        # 标准Android SDK路径
        sdk_path = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools"
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

    def check_adb_tool(self) -> CheckResult:
        """检测ADB工具是否可用"""
        try:
            result = subprocess.run(
                f'"{self.adb_path}" version',
                capture_output=True,
                text=True,
                shell=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.split('\n')[0] if result.stdout else "未知版本"
                return CheckResult(
                    status='ok',
                    message='ADB工具可用',
                    details=f'路径: {self.adb_path}\n版本: {version}',
                    fix_available=False
                )
            else:
                return CheckResult(
                    status='error',
                    message='ADB工具不可用',
                    details='ADB命令执行失败',
                    fix_available=True,
                    fix_type='manual',
                    fix_action='请安装Android SDK Platform Tools'
                )

        except FileNotFoundError:
            return CheckResult(
                status='error',
                message='ADB工具未找到',
                details=f'路径不存在: {self.adb_path}',
                fix_available=True,
                fix_type='manual',
                fix_action='请安装Android SDK或配置ADB环境变量'
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                status='warning',
                message='ADB工具响应超时',
                details='命令执行超过5秒',
                fix_available=False
            )
        except Exception as e:
            return CheckResult(
                status='error',
                message='ADB检测异常',
                details=str(e),
                fix_available=False
            )

    def check_adb_device(self) -> Tuple[CheckResult, List[str]]:
        """检测ADB设备连接状态"""
        try:
            result = subprocess.run(
                f'"{self.adb_path}" devices',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            if result.returncode != 0:
                return CheckResult(
                    status='error',
                    message='无法获取设备列表',
                    details=result.stderr,
                    fix_available=False
                ), []

            # 解析设备列表
            lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
            devices = []

            for line in lines:
                if line.strip() and '\t' in line:
                    device_id, status = line.split('\t', 1)
                    device_id = device_id.strip()
                    status = status.strip()

                    if status == "device":
                        devices.append(device_id)

            if devices:
                device_list = '\n'.join([f'  • {d}' for d in devices])
                return CheckResult(
                    status='ok',
                    message=f'检测到 {len(devices)} 个设备',
                    details=f'已连接设备:\n{device_list}',
                    fix_available=False
                ), devices
            else:
                return CheckResult(
                    status='warning',
                    message='未检测到设备',
                    details='请确保模拟器/云手机已启动并连接ADB',
                    fix_available=True,
                    fix_type='auto',
                    fix_action='自动扫描常用端口'
                ), []

        except subprocess.TimeoutExpired:
            return CheckResult(
                status='error',
                message='ADB设备列表获取超时',
                details='命令执行超过10秒',
                fix_available=False
            ), []
        except Exception as e:
            return CheckResult(
                status='error',
                message='ADB设备检测异常',
                details=str(e),
                fix_available=False
            ), []

    def check_appium_service(self, port: int = 4723) -> CheckResult:
        """检测Appium服务是否运行"""
        try:
            # 尝试连接Appium服务
            response = requests.get(
                f'http://127.0.0.1:{port}/status',
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                build_info = data.get('value', {}).get('build', {})
                version = build_info.get('version', '未知')

                return CheckResult(
                    status='ok',
                    message='Appium服务运行正常',
                    details=f'端口: {port}\nAppium版本: {version}\n状态: Ready',
                    fix_available=False
                )
            else:
                return CheckResult(
                    status='warning',
                    message='Appium服务响应异常',
                    details=f'HTTP状态码: {response.status_code}',
                    fix_available=True,
                    fix_type='manual',
                    fix_action='尝试重启Appium服务'
                )

        except requests.exceptions.ConnectionError:
            return CheckResult(
                status='error',
                message='Appium服务未运行',
                details=f'无法连接到 http://127.0.0.1:{port}',
                fix_available=True,
                fix_type='auto',
                fix_action=f'启动Appium服务: appium --address 127.0.0.1 --port {port} --allow-cors'
            )
        except requests.exceptions.Timeout:
            return CheckResult(
                status='warning',
                message='Appium服务响应超时',
                details='服务可能正在启动或负载过高',
                fix_available=False
            )
        except Exception as e:
            return CheckResult(
                status='error',
                message='Appium检测异常',
                details=str(e),
                fix_available=False
            )

    def check_damai_app(self, device_id: Optional[str] = None) -> CheckResult:
        """检测大麦App是否安装"""
        if not device_id:
            # 尝试获取第一个可用设备
            _, devices = self.check_adb_device()
            if not devices:
                return CheckResult(
                    status='error',
                    message='无法检测大麦App',
                    details='没有可用的ADB设备',
                    fix_available=False
                )
            device_id = devices[0]

        try:
            # 检查cn.damai包是否存在
            result = subprocess.run(
                f'"{self.adb_path}" -s {device_id} shell pm list packages cn.damai',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            if result.returncode == 0 and 'cn.damai' in result.stdout:
                # 获取App版本信息
                version_result = subprocess.run(
                    f'"{self.adb_path}" -s {device_id} shell dumpsys package cn.damai | grep versionName',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=10
                )

                version = "未知版本"
                if version_result.returncode == 0 and version_result.stdout:
                    # 解析versionName
                    for line in version_result.stdout.split('\n'):
                        if 'versionName' in line:
                            version = line.split('=')[-1].strip()
                            break

                return CheckResult(
                    status='ok',
                    message='大麦App已安装',
                    details=f'设备: {device_id}\n包名: cn.damai\n版本: {version}',
                    fix_available=False
                )
            else:
                return CheckResult(
                    status='error',
                    message='大麦App未安装',
                    details=f'设备 {device_id} 上未找到cn.damai包',
                    fix_available=True,
                    fix_type='manual',
                    fix_action='请在设备上安装大麦App'
                )

        except subprocess.TimeoutExpired:
            return CheckResult(
                status='warning',
                message='大麦App检测超时',
                details='命令执行超时',
                fix_available=False
            )
        except Exception as e:
            return CheckResult(
                status='error',
                message='大麦App检测异常',
                details=str(e),
                fix_available=False
            )

    def check_uiautomator2(self, device_id: Optional[str] = None) -> CheckResult:
        """检测UiAutomator2 Server是否安装"""
        if not device_id:
            _, devices = self.check_adb_device()
            if not devices:
                return CheckResult(
                    status='error',
                    message='无法检测UiAutomator2',
                    details='没有可用的ADB设备',
                    fix_available=False
                )
            device_id = devices[0]

        try:
            # 检查io.appium.uiautomator2.server
            result = subprocess.run(
                f'"{self.adb_path}" -s {device_id} shell pm list packages io.appium.uiautomator2',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            packages = result.stdout.strip().split('\n') if result.stdout else []
            has_server = any('io.appium.uiautomator2.server' in pkg for pkg in packages)
            has_test = any('io.appium.uiautomator2.server.test' in pkg for pkg in packages)

            if has_server and has_test:
                return CheckResult(
                    status='ok',
                    message='UiAutomator2 Server已安装',
                    details=f'设备: {device_id}\n包:\n  • io.appium.uiautomator2.server\n  • io.appium.uiautomator2.server.test',
                    fix_available=False
                )
            elif has_server or has_test:
                missing = []
                if not has_server:
                    missing.append('io.appium.uiautomator2.server')
                if not has_test:
                    missing.append('io.appium.uiautomator2.server.test')

                return CheckResult(
                    status='warning',
                    message='UiAutomator2安装不完整',
                    details=f'缺少: {", ".join(missing)}',
                    fix_available=True,
                    fix_type='auto',
                    fix_action='让Appium自动安装（移除skipServerInstallation配置）'
                )
            else:
                return CheckResult(
                    status='warning',
                    message='UiAutomator2未安装',
                    details='首次运行时Appium会自动安装',
                    fix_available=True,
                    fix_type='auto',
                    fix_action='确保配置中 skipServerInstallation=False'
                )

        except subprocess.TimeoutExpired:
            return CheckResult(
                status='warning',
                message='UiAutomator2检测超时',
                details='命令执行超时',
                fix_available=False
            )
        except Exception as e:
            return CheckResult(
                status='error',
                message='UiAutomator2检测异常',
                details=str(e),
                fix_available=False
            )

    def check_python_deps(self) -> CheckResult:
        """检测Python依赖是否完整"""
        required_packages = {
            'appium-python-client': 'appium',
            'selenium': 'selenium',
            'paddleocr': 'paddleocr',
            'Pillow': 'PIL',
            'opencv-python': 'cv2',
            'requests': 'requests',
            'pyperclip': 'pyperclip'
        }

        missing = []
        installed = []

        for pkg_name, import_name in required_packages.items():
            try:
                __import__(import_name)
                installed.append(pkg_name)
            except ImportError:
                missing.append(pkg_name)

        if not missing:
            return CheckResult(
                status='ok',
                message='Python依赖完整',
                details=f'已安装 {len(installed)} 个必需包',
                fix_available=False
            )
        else:
            return CheckResult(
                status='error',
                message=f'缺少 {len(missing)} 个Python包',
                details=f'缺失包:\n' + '\n'.join([f'  • {pkg}' for pkg in missing]),
                fix_available=True,
                fix_type='auto',
                fix_action=f'pip install {" ".join(missing)}'
            )

    def check_all(self) -> Dict[str, CheckResult]:
        """执行所有检测项"""
        results = {}

        # 1. 检测ADB工具
        results['adb_tool'] = self.check_adb_tool()

        # 2. 检测ADB设备
        device_result, devices = self.check_adb_device()
        results['adb_device'] = device_result

        # 3. 检测Appium服务
        results['appium'] = self.check_appium_service()

        # 4. 检测大麦App（如果有设备）
        if devices:
            results['damai_app'] = self.check_damai_app(devices[0])
            results['uiautomator2'] = self.check_uiautomator2(devices[0])
        else:
            results['damai_app'] = CheckResult(
                status='warning',
                message='跳过大麦App检测',
                details='无可用设备',
                fix_available=False
            )
            results['uiautomator2'] = CheckResult(
                status='warning',
                message='跳过UiAutomator2检测',
                details='无可用设备',
                fix_available=False
            )

        # 5. 检测Python依赖
        results['python_deps'] = self.check_python_deps()

        self.results = results
        return results


class EnvironmentFixer:
    """环境修复器 - 自动修复检测到的问题"""

    def __init__(self, adb_path: Path):
        self.adb_path = adb_path

    def scan_common_ports(self) -> List[str]:
        """扫描常用的ADB端口"""
        common_ports = [
            # 红手指常用端口
            59700, 59701, 59702,
            # MuMu模拟器
            16384, 16416, 16448,
            # 夜神模拟器
            62001, 62025, 62026,
            # 雷电模拟器
            5555, 5557, 5559,
            # 其他常见端口
            52056, 50366, 51527, 58526, 56644
        ]

        connected_devices = []
        for port in common_ports:
            try:
                device_address = f"127.0.0.1:{port}"
                result = subprocess.run(
                    f'"{self.adb_path}" connect {device_address}',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=5
                )

                # 检查输出，忽略编码
                output = (result.stdout + result.stderr).lower()
                if "connected" in output or "已连接" in output:
                    connected_devices.append(device_address)
                    # 找到一个就可以停止
                    break

            except:
                continue

        return connected_devices

    def start_appium(self, port: int = 4723, background: bool = True) -> Tuple[bool, str]:
        """启动Appium服务"""
        try:
            cmd = f'appium --address 127.0.0.1 --port {port} --allow-cors'

            # 确保Android SDK环境变量被传递
            env = os.environ.copy()
            android_sdk_path = str(Path.home() / "AppData" / "Local" / "Android" / "Sdk")
            env['ANDROID_HOME'] = android_sdk_path
            env['ANDROID_SDK_ROOT'] = android_sdk_path

            if background:
                # 后台启动
                if sys.platform == 'win32':
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        env=env
                    )
                else:
                    subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=env
                    )

                # 等待服务启动
                time.sleep(3)

                # 验证是否启动成功
                try:
                    response = requests.get(f'http://127.0.0.1:{port}/status', timeout=5)
                    if response.status_code == 200:
                        return True, f'Appium服务已启动在端口 {port}'
                    else:
                        return False, f'Appium启动后响应异常: {response.status_code}'
                except:
                    return False, 'Appium启动后无法连接'

            else:
                # 前台启动（返回命令让用户手动执行）
                return False, cmd

        except FileNotFoundError:
            return False, 'appium命令未找到，请先安装Appium: npm install -g appium'
        except Exception as e:
            return False, f'启动Appium失败: {str(e)}'

    def sync_config_files(self, adb_port: str) -> Tuple[bool, str]:
        """同步所有配置文件的ADB端口

        Args:
            adb_port: ADB端口号(只包含数字,如"50932")

        Returns:
            (成功标志, 消息)
        """
        try:
            project_root = Path(__file__).parent
            config_jsonc = project_root / "damai_appium" / "config.jsonc"
            last_config = project_root / "last_config.json"

            updated_files = []

            # 1. 更新 config.jsonc
            if config_jsonc.exists():
                try:
                    with open(config_jsonc, 'r', encoding='utf-8') as f:
                        config = json.load(f)

                    old_port = config.get('adb_port')
                    config['adb_port'] = adb_port

                    with open(config_jsonc, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    updated_files.append(f"config.jsonc ({old_port} → {adb_port})")
                except Exception as e:
                    return False, f"更新config.jsonc失败: {e}"

            # 2. 更新 last_config.json
            try:
                if last_config.exists():
                    with open(last_config, 'r', encoding='utf-8') as f:
                        last_cfg = json.load(f)
                else:
                    last_cfg = {}

                old_port = last_cfg.get('adb_port')
                last_cfg['adb_port'] = adb_port

                with open(last_config, 'w', encoding='utf-8') as f:
                    json.dump(last_cfg, f, indent=2, ensure_ascii=False)

                updated_files.append(f"last_config.json ({old_port} → {adb_port})")
            except Exception as e:
                return False, f"更新last_config.json失败: {e}"

            return True, f"已同步配置文件: {', '.join(updated_files)}"

        except Exception as e:
            return False, f"配置同步失败: {e}"

    def test_webdriver_connection(self, adb_port: str, server_url: str = "http://127.0.0.1:4723") -> Tuple[bool, str]:
        """测试WebDriver连接

        Args:
            adb_port: ADB端口号(只包含数字,如"50932")
            server_url: Appium服务器地址

        Returns:
            (成功标志, 详细信息)
        """
        try:
            # 动态导入以避免循环依赖
            from appium import webdriver
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.udid = f"127.0.0.1:{adb_port}"
            options.app_package = "cn.damai"
            options.app_activity = "cn.damai.main.ui.MainActivity"
            options.no_reset = True
            options.new_command_timeout = 300
            options.skip_server_installation = False  # 允许自动安装UiAutomator2

            # 尝试连接
            driver = webdriver.Remote(server_url, options=options)

            # 测试基本操作
            package = driver.current_package
            activity = driver.current_activity

            # 关闭连接
            driver.quit()

            return True, f"WebDriver连接成功\n设备: 127.0.0.1:{adb_port}\n当前应用: {package}\n当前Activity: {activity}"

        except Exception as e:
            error_msg = str(e)

            # 提供更详细的错误诊断
            if "instrumentation" in error_msg.lower():
                return False, f"WebDriver连接失败: UiAutomator2服务初始化失败\n建议:\n1. 重启大麦App\n2. 重启模拟器\n3. 清除UiAutomator2缓存: adb uninstall io.appium.uiautomator2.server\n\n详细错误: {error_msg[:300]}"
            elif "session" in error_msg.lower() and "not created" in error_msg.lower():
                return False, f"WebDriver连接失败: 无法创建会话\n建议:\n1. 检查Appium服务是否正常运行\n2. 检查设备连接: adb devices\n3. 检查大麦App是否已安装\n\n详细错误: {error_msg[:300]}"
            elif "connect" in error_msg.lower() or "connection" in error_msg.lower():
                return False, f"WebDriver连接失败: 无法连接到服务器\n建议:\n1. 检查Appium服务: {server_url}/status\n2. 启动Appium: appium --address 127.0.0.1 --port 4723 --allow-cors\n\n详细错误: {error_msg[:300]}"
            else:
                return False, f"WebDriver连接失败: {error_msg[:500]}"

    def auto_fix_webdriver(self) -> Tuple[bool, str, Dict]:
        """自动修复WebDriver连接问题

        完整的修复流程:
        1. 检测ADB设备
        2. 同步配置文件
        3. 检查Appium服务
        4. 测试WebDriver连接

        Returns:
            (成功标志, 消息, 详细结果字典)
        """
        results = {
            'adb_devices': None,
            'config_sync': None,
            'appium_service': None,
            'webdriver_test': None,
            'selected_port': None
        }

        # 步骤1: 检测ADB设备
        try:
            result = subprocess.run(
                f'"{self.adb_path}" devices',
                capture_output=True,
                text=True,
                shell=True,
                timeout=10
            )

            # 解析设备列表
            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip() and '\t' in line:
                    device_id = line.split('\t', 1)[0].strip()
                    if '127.0.0.1:' in device_id:
                        port = device_id.split(':')[1]
                        devices.append(port)

            if not devices:
                results['adb_devices'] = "未检测到设备"
                return False, "未检测到ADB设备,请先连接模拟器/云手机", results

            # 使用第一个设备
            adb_port = devices[0]
            results['adb_devices'] = f"检测到 {len(devices)} 个设备"
            results['selected_port'] = adb_port

        except Exception as e:
            results['adb_devices'] = f"检测失败: {e}"
            return False, f"ADB设备检测失败: {e}", results

        # 步骤2: 同步配置文件
        success, msg = self.sync_config_files(adb_port)
        results['config_sync'] = msg
        if not success:
            return False, msg, results

        # 步骤3: 检查Appium服务
        try:
            response = requests.get('http://127.0.0.1:4723/status', timeout=3)
            if response.status_code == 200:
                results['appium_service'] = "运行正常"
            else:
                results['appium_service'] = f"响应异常: {response.status_code}"
                return False, "Appium服务响应异常", results
        except:
            # 尝试启动Appium
            success, msg = self.start_appium()
            results['appium_service'] = msg
            if not success:
                return False, f"Appium服务未运行且启动失败: {msg}", results

        # 步骤4: 测试WebDriver连接
        success, msg = self.test_webdriver_connection(adb_port)
        results['webdriver_test'] = msg

        if success:
            return True, f"WebDriver自动修复成功! 端口: {adb_port}", results
        else:
            return False, f"WebDriver连接测试失败:\n{msg}", results


def get_environment_status() -> Dict:
    """获取环境状态摘要"""
    checker = EnvironmentChecker()
    results = checker.check_all()

    status_summary = {
        'overall': 'ok',  # 'ok', 'warning', 'error'
        'checks': {},
        'issues': [],
        'fixes_available': []
    }

    error_count = 0
    warning_count = 0

    for key, result in results.items():
        status_summary['checks'][key] = {
            'status': result.status,
            'message': result.message,
            'details': result.details
        }

        if result.status == 'error':
            error_count += 1
            status_summary['issues'].append({
                'type': key,
                'message': result.message,
                'severity': 'error'
            })

        elif result.status == 'warning':
            warning_count += 1
            status_summary['issues'].append({
                'type': key,
                'message': result.message,
                'severity': 'warning'
            })

        if result.fix_available:
            status_summary['fixes_available'].append({
                'type': key,
                'action': result.fix_action,
                'fix_type': result.fix_type
            })

    # 确定总体状态
    if error_count > 0:
        status_summary['overall'] = 'error'
    elif warning_count > 0:
        status_summary['overall'] = 'warning'

    return status_summary


if __name__ == "__main__":
    # 测试环境检测
    import sys
    import io

    # 设置标准输出为UTF-8编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 70)
    print("大麦抢票环境检测")
    print("=" * 70)

    checker = EnvironmentChecker()
    results = checker.check_all()

    for name, result in results.items():
        print(f"\n[{name}]")
        print(f"  状态: {result.status.upper()}")
        print(f"  信息: {result.message}")
        if result.details:
            # 替换特殊字符以避免编码问题
            details = result.details.replace('•', '-')
            print(f"  详情: {details}")
        if result.fix_available:
            print(f"  修复: {result.fix_action}")

    print("\n" + "=" * 70)
    summary = get_environment_status()
    print(f"总体状态: {summary['overall'].upper()}")
    print(f"问题数量: {len(summary['issues'])}")
    print(f"可用修复: {len(summary['fixes_available'])}")
