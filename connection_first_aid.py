#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
连接急救箱 - 全面体检 + 针对性修复
整合环境诊断和一键修复功能，提供详细的诊断和修复过程
"""

import subprocess
import time
import requests
import psutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from connection_auto_fixer import ConnectionAutoFixer


class ProblemSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "严重"  # 阻止连接
    WARNING = "警告"   # 可能影响连接
    INFO = "提示"      # 优化建议


@dataclass
class DiagnosticIssue:
    """诊断问题"""
    category: str  # 问题分类（Appium/ADB/WebDriver/Network/System）
    severity: ProblemSeverity  # 严重程度
    title: str  # 问题标题
    description: str  # 详细描述
    possible_causes: List[str] = field(default_factory=list)  # 可能原因
    fix_suggestions: List[str] = field(default_factory=list)  # 修复建议
    auto_fixable: bool = False  # 是否可自动修复


@dataclass
class DiagnosticReport:
    """诊断报告"""
    issues: List[DiagnosticIssue] = field(default_factory=list)
    appium_status: Dict[str, Any] = field(default_factory=dict)
    adb_status: Dict[str, Any] = field(default_factory=dict)
    webdriver_status: Dict[str, Any] = field(default_factory=dict)
    network_status: Dict[str, Any] = field(default_factory=dict)
    system_status: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0
    end_time: float = 0

    @property
    def duration(self) -> float:
        """诊断耗时（秒）"""
        return self.end_time - self.start_time if self.end_time > 0 else 0

    @property
    def critical_issues(self) -> List[DiagnosticIssue]:
        """严重问题列表"""
        return [i for i in self.issues if i.severity == ProblemSeverity.CRITICAL]

    @property
    def warning_issues(self) -> List[DiagnosticIssue]:
        """警告问题列表"""
        return [i for i in self.issues if i.severity == ProblemSeverity.WARNING]

    @property
    def has_critical_issues(self) -> bool:
        """是否有严重问题"""
        return len(self.critical_issues) > 0

    @property
    def is_healthy(self) -> bool:
        """是否健康（无严重问题且无警告）"""
        return len(self.issues) == 0


class ConnectionFirstAid:
    """连接急救箱 - 全面体检 + 针对性修复"""

    def __init__(self, logger=None, adb_port: str = "59700", appium_url: str = "http://127.0.0.1:4723"):
        """
        初始化急救箱

        Args:
            logger: 日志记录器
            adb_port: ADB端口号
            appium_url: Appium服务地址
        """
        self.logger = logger
        self.adb_port = adb_port
        self.appium_url = appium_url
        self.adb_path = self._find_adb()
        self.auto_fixer = ConnectionAutoFixer(logger=logger, adb_port=adb_port)

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

    # ========== 体检功能 ==========

    def diagnose_all(self, udid: Optional[str] = None) -> DiagnosticReport:
        """
        全面体检 - 检测所有可能的问题

        Args:
            udid: 设备UDID，如果为None则使用self.adb_port

        Returns:
            DiagnosticReport: 详细的诊断报告
        """
        if udid is None:
            udid = f"127.0.0.1:{self.adb_port}"

        report = DiagnosticReport()
        report.start_time = time.time()

        self._log("="*80, "INFO")
        self._log("🏥 连接急救箱 - 开始全面体检", "INFO")
        self._log("="*80, "INFO")
        self._log("", "INFO")

        # 1. Appium服务诊断
        self._diagnose_appium(report)

        # 2. ADB诊断
        self._diagnose_adb(report, udid)

        # 3. WebDriver诊断（需要传入driver，这里只做基础检测）
        self._diagnose_webdriver_basic(report)

        # 4. 网络诊断
        self._diagnose_network(report, udid)

        # 5. 系统资源诊断
        self._diagnose_system(report)

        report.end_time = time.time()

        # 生成诊断摘要
        self._print_diagnostic_summary(report)

        return report

    def _diagnose_appium(self, report: DiagnosticReport):
        """诊断Appium服务"""
        self._log("━"*80, "INFO")
        self._log("[1/5] 📱 诊断 Appium 服务", "INFO")
        self._log("━"*80, "INFO")

        try:
            # 检测1: Appium服务是否运行
            self._log("  [1.1] 检测 Appium 服务运行状态...", "INFO")
            try:
                response = requests.get(f"{self.appium_url}/status", timeout=3)
                if response.status_code == 200:
                    report.appium_status['running'] = True
                    report.appium_status['response_time'] = response.elapsed.total_seconds()
                    self._log(f"    ✓ Appium 服务运行正常 (响应时间: {response.elapsed.total_seconds():.3f}秒)", "SUCCESS")

                    # 获取Appium详细信息
                    try:
                        status_data = response.json()
                        if 'value' in status_data:
                            build_info = status_data['value'].get('build', {})
                            report.appium_status['version'] = build_info.get('version', '未知')
                            self._log(f"    ℹ️ Appium 版本: {report.appium_status.get('version', '未知')}", "INFO")
                    except:
                        pass
                else:
                    report.appium_status['running'] = False
                    issue = DiagnosticIssue(
                        category="Appium",
                        severity=ProblemSeverity.CRITICAL,
                        title="Appium服务返回异常状态",
                        description=f"HTTP状态码: {response.status_code}",
                        possible_causes=["Appium服务异常", "端口冲突"],
                        fix_suggestions=["重启Appium服务", "检查端口4723是否被占用"],
                        auto_fixable=True
                    )
                    report.issues.append(issue)
                    self._log(f"    ✗ Appium 服务返回异常状态: {response.status_code}", "ERROR")
            except requests.exceptions.ConnectionError:
                report.appium_status['running'] = False
                issue = DiagnosticIssue(
                    category="Appium",
                    severity=ProblemSeverity.CRITICAL,
                    title="Appium服务未运行",
                    description="无法连接到 http://127.0.0.1:4723",
                    possible_causes=[
                        "Appium未安装",
                        "Appium未启动",
                        "Appium启动失败",
                        "端口4723被占用"
                    ],
                    fix_suggestions=[
                        "运行 start_appium.bat 启动服务",
                        "手动启动 Appium",
                        "检查端口占用: netstat -ano | findstr :4723"
                    ],
                    auto_fixable=True
                )
                report.issues.append(issue)
                self._log("    ✗ Appium 服务未运行", "ERROR")
            except requests.exceptions.Timeout:
                report.appium_status['running'] = False
                issue = DiagnosticIssue(
                    category="Appium",
                    severity=ProblemSeverity.WARNING,
                    title="Appium服务响应超时",
                    description="连接Appium超时（>3秒）",
                    possible_causes=["系统资源不足", "Appium服务负载过高"],
                    fix_suggestions=["重启Appium服务", "检查系统资源"],
                    auto_fixable=True
                )
                report.issues.append(issue)
                self._log("    ✗ Appium 服务响应超时", "WARNING")

            # 检测2: Appium端口占用检测
            self._log("  [1.2] 检测 Appium 端口占用情况...", "INFO")
            if self._check_port_in_use(4723):
                self._log("    ✓ 端口 4723 已被占用（正常，Appium正在运行）", "SUCCESS")
            elif not report.appium_status.get('running', False):
                self._log("    ⚠️ 端口 4723 未被占用，但Appium未运行", "WARNING")

        except Exception as e:
            self._log(f"  ✗ Appium诊断异常: {e}", "ERROR")
            issue = DiagnosticIssue(
                category="Appium",
                severity=ProblemSeverity.CRITICAL,
                title="Appium诊断失败",
                description=str(e),
                possible_causes=["系统异常"],
                fix_suggestions=["查看详细错误日志"],
                auto_fixable=False
            )
            report.issues.append(issue)

        self._log("", "INFO")

    def _diagnose_adb(self, report: DiagnosticReport, udid: str):
        """诊断ADB连接"""
        self._log("━"*80, "INFO")
        self._log("[2/5] 🔧 诊断 ADB 连接", "INFO")
        self._log("━"*80, "INFO")

        try:
            # 检测1: ADB工具是否存在
            self._log("  [2.1] 检测 ADB 工具...", "INFO")
            if self.adb_path.exists() or self.adb_path.name == "adb":
                self._log(f"    ✓ ADB 工具路径: {self.adb_path}", "SUCCESS")
                report.adb_status['adb_path'] = str(self.adb_path)
            else:
                issue = DiagnosticIssue(
                    category="ADB",
                    severity=ProblemSeverity.CRITICAL,
                    title="ADB工具未找到",
                    description=f"路径 {self.adb_path} 不存在",
                    possible_causes=["Android SDK未安装", "环境变量未配置"],
                    fix_suggestions=[
                        "安装 Android SDK",
                        "配置 ANDROID_HOME 环境变量",
                        "将 platform-tools 添加到 PATH"
                    ],
                    auto_fixable=False
                )
                report.issues.append(issue)
                self._log(f"    ✗ ADB 工具未找到: {self.adb_path}", "ERROR")
                return

            # 检测2: ADB服务器状态
            self._log("  [2.2] 检测 ADB 服务器状态...", "INFO")
            try:
                result = subprocess.run(
                    f'"{self.adb_path}" version',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    report.adb_status['version'] = version_line
                    self._log(f"    ✓ {version_line}", "SUCCESS")
                else:
                    self._log("    ✗ 无法获取 ADB 版本", "WARNING")
            except Exception as e:
                self._log(f"    ✗ ADB 版本检测失败: {e}", "WARNING")

            # 检测3: 设备列表
            self._log("  [2.3] 检测 ADB 设备连接...", "INFO")
            try:
                result = subprocess.run(
                    f'"{self.adb_path}" devices -l',
                    capture_output=True,
                    text=True,
                    shell=True,
                    timeout=10
                )

                if result.returncode == 0:
                    devices_output = result.stdout
                    report.adb_status['devices_output'] = devices_output

                    # 解析设备列表
                    device_lines = [line.strip() for line in devices_output.split('\n')
                                   if line.strip() and not line.startswith('List of devices')]

                    report.adb_status['device_count'] = len(device_lines)
                    report.adb_status['devices'] = []

                    target_found = False
                    offline_count = 0
                    unauthorized_count = 0

                    for line in device_lines:
                        if not line:
                            continue

                        parts = line.split()
                        if len(parts) >= 2:
                            device_id = parts[0]
                            device_state = parts[1]

                            device_info = {'id': device_id, 'state': device_state}
                            report.adb_status['devices'].append(device_info)

                            if device_id == udid:
                                target_found = True
                                if device_state == 'device':
                                    self._log(f"    ✓ 目标设备已连接: {udid} (状态: {device_state})", "SUCCESS")
                                elif device_state == 'offline':
                                    offline_count += 1
                                    issue = DiagnosticIssue(
                                        category="ADB",
                                        severity=ProblemSeverity.CRITICAL,
                                        title=f"目标设备离线: {udid}",
                                        description="设备显示为offline状态",
                                        possible_causes=[
                                            "红手指云手机未启动",
                                            "网络连接中断",
                                            "端口号错误"
                                        ],
                                        fix_suggestions=[
                                            "检查红手指客户端，确保云手机在线",
                                            "重启红手指客户端",
                                            "验证端口号是否正确"
                                        ],
                                        auto_fixable=True
                                    )
                                    report.issues.append(issue)
                                    self._log(f"    ✗ 目标设备离线: {udid}", "ERROR")
                                elif device_state == 'unauthorized':
                                    unauthorized_count += 1
                                    issue = DiagnosticIssue(
                                        category="ADB",
                                        severity=ProblemSeverity.CRITICAL,
                                        title=f"目标设备未授权: {udid}",
                                        description="设备显示为unauthorized状态",
                                        possible_causes=[
                                            "USB调试未授权",
                                            "ADB密钥未信任"
                                        ],
                                        fix_suggestions=[
                                            "在设备上允许USB调试",
                                            "重新连接设备",
                                            "清除ADB授权: adb kill-server"
                                        ],
                                        auto_fixable=True
                                    )
                                    report.issues.append(issue)
                                    self._log(f"    ✗ 目标设备未授权: {udid}", "ERROR")
                            else:
                                # 其他设备
                                if device_state == 'offline':
                                    offline_count += 1
                                elif device_state == 'unauthorized':
                                    unauthorized_count += 1

                    # 统计僵尸连接
                    if offline_count > 0 or unauthorized_count > 0:
                        issue = DiagnosticIssue(
                            category="ADB",
                            severity=ProblemSeverity.WARNING,
                            title=f"检测到僵尸连接",
                            description=f"离线设备: {offline_count}个, 未授权设备: {unauthorized_count}个",
                            possible_causes=["设备断开后未清理", "ADB服务器状态异常"],
                            fix_suggestions=["清除僵尸连接", "重启ADB服务器"],
                            auto_fixable=True
                        )
                        report.issues.append(issue)
                        self._log(f"    ⚠️ 检测到僵尸连接 (离线: {offline_count}, 未授权: {unauthorized_count})", "WARNING")

                    if not target_found:
                        issue = DiagnosticIssue(
                            category="ADB",
                            severity=ProblemSeverity.CRITICAL,
                            title=f"目标设备未连接: {udid}",
                            description="在ADB设备列表中未找到目标设备",
                            possible_causes=[
                                "设备未连接",
                                "端口号错误",
                                "红手指云手机离线"
                            ],
                            fix_suggestions=[
                                "连接设备: adb connect {udid}",
                                "验证端口号",
                                "检查红手指状态"
                            ],
                            auto_fixable=True
                        )
                        report.issues.append(issue)
                        self._log(f"    ✗ 目标设备未连接: {udid}", "ERROR")

                    self._log(f"    ℹ️ 总设备数: {len(device_lines)}", "INFO")
                else:
                    self._log("    ✗ 无法获取设备列表", "ERROR")
            except subprocess.TimeoutExpired:
                self._log("    ✗ ADB devices 命令超时", "ERROR")
            except Exception as e:
                self._log(f"    ✗ ADB 设备检测失败: {e}", "ERROR")

        except Exception as e:
            self._log(f"  ✗ ADB诊断异常: {e}", "ERROR")
            issue = DiagnosticIssue(
                category="ADB",
                severity=ProblemSeverity.CRITICAL,
                title="ADB诊断失败",
                description=str(e),
                possible_causes=["系统异常"],
                fix_suggestions=["查看详细错误日志"],
                auto_fixable=False
            )
            report.issues.append(issue)

        self._log("", "INFO")

    def _diagnose_webdriver_basic(self, report: DiagnosticReport):
        """诊断WebDriver基础状态"""
        self._log("━"*80, "INFO")
        self._log("[3/5] 🌐 诊断 WebDriver 连接", "INFO")
        self._log("━"*80, "INFO")

        # 基础检测：Appium sessions接口
        self._log("  [3.1] 检测 WebDriver 会话...", "INFO")
        try:
            response = requests.get(f"{self.appium_url}/wd/hub/sessions", timeout=3)
            if response.status_code == 200:
                sessions = response.json().get('value', [])
                report.webdriver_status['session_count'] = len(sessions)

                if len(sessions) > 0:
                    self._log(f"    ✓ 检测到 {len(sessions)} 个活动会话", "SUCCESS")
                    for i, session in enumerate(sessions):
                        session_id = session.get('id', 'unknown')[:16]
                        self._log(f"      - 会话 #{i+1}: {session_id}...", "INFO")
                else:
                    self._log("    ℹ️ 当前无活动WebDriver会话", "INFO")
                    report.webdriver_status['has_session'] = False
            else:
                self._log(f"    ⚠️ 无法获取会话信息 (HTTP {response.status_code})", "WARNING")
        except Exception as e:
            self._log(f"    ⚠️ 无法检测WebDriver会话: {e}", "WARNING")

        self._log("  ℹ️ 详细的WebDriver健康检测需要传入driver实例", "INFO")
        self._log("", "INFO")

    def _diagnose_network(self, report: DiagnosticReport, udid: str):
        """诊断网络连接"""
        self._log("━"*80, "INFO")
        self._log("[4/5] 🌐 诊断网络连接", "INFO")
        self._log("━"*80, "INFO")

        try:
            # 检测1: Appium端口可达性
            self._log("  [4.1] 检测 Appium 端口 (4723)...", "INFO")
            reachable, reason = self.auto_fixer._test_port_reachable("127.0.0.1", 4723, timeout=2)
            if reachable:
                self._log(f"    ✓ Appium端口可达: {reason}", "SUCCESS")
            else:
                self._log(f"    ✗ Appium端口不可达: {reason}", "ERROR")
                if not report.appium_status.get('running', False):
                    # 已经在Appium诊断中记录了问题，这里不重复

                    pass

            # 检测2: ADB设备端口可达性
            if ':' in udid:
                self._log(f"  [4.2] 检测 ADB 设备端口 ({udid})...", "INFO")
                host, port_str = udid.split(':')
                port = int(port_str)

                reachable, reason = self.auto_fixer._test_port_reachable(host, port, timeout=2)
                report.network_status['device_reachable'] = reachable
                report.network_status['device_reason'] = reason

                if reachable:
                    self._log(f"    ✓ 设备端口可达: {reason}", "SUCCESS")
                else:
                    self._log(f"    ✗ 设备端口不可达: {reason}", "ERROR")
                    # 检查是否已经在ADB诊断中记录过
                    already_reported = any(
                        issue.category == "ADB" and "离线" in issue.title
                        for issue in report.issues
                    )
                    if not already_reported:
                        issue = DiagnosticIssue(
                            category="Network",
                            severity=ProblemSeverity.CRITICAL,
                            title=f"设备端口不可达: {port}",
                            description=reason,
                            possible_causes=[
                                "红手指云手机未启动",
                                "网络连接问题",
                                "端口号错误"
                            ],
                            fix_suggestions=[
                                "检查红手指客户端，确保云手机在线",
                                "验证端口号是否正确",
                                "检查网络连接"
                            ],
                            auto_fixable=False
                        )
                        report.issues.append(issue)

        except Exception as e:
            self._log(f"  ✗ 网络诊断异常: {e}", "ERROR")

        self._log("", "INFO")

    def _diagnose_system(self, report: DiagnosticReport):
        """诊断系统资源"""
        self._log("━"*80, "INFO")
        self._log("[5/5] 💻 诊断系统资源", "INFO")
        self._log("━"*80, "INFO")

        try:
            # 检测1: CPU使用率
            self._log("  [5.1] 检测 CPU 使用率...", "INFO")
            cpu_percent = psutil.cpu_percent(interval=1)
            report.system_status['cpu_percent'] = cpu_percent

            if cpu_percent < 80:
                self._log(f"    ✓ CPU 使用率: {cpu_percent}%", "SUCCESS")
            elif cpu_percent < 90:
                self._log(f"    ⚠️ CPU 使用率较高: {cpu_percent}%", "WARNING")
                issue = DiagnosticIssue(
                    category="System",
                    severity=ProblemSeverity.WARNING,
                    title="CPU使用率较高",
                    description=f"当前CPU使用率: {cpu_percent}%",
                    possible_causes=["系统负载过高", "后台程序占用"],
                    fix_suggestions=["关闭不必要的程序", "检查任务管理器"],
                    auto_fixable=False
                )
                report.issues.append(issue)
            else:
                self._log(f"    ✗ CPU 使用率过高: {cpu_percent}%", "ERROR")
                issue = DiagnosticIssue(
                    category="System",
                    severity=ProblemSeverity.CRITICAL,
                    title="CPU使用率过高",
                    description=f"当前CPU使用率: {cpu_percent}%",
                    possible_causes=["系统负载过高", "程序异常"],
                    fix_suggestions=["重启计算机", "检查异常进程"],
                    auto_fixable=False
                )
                report.issues.append(issue)

            # 检测2: 内存使用率
            self._log("  [5.2] 检测内存使用率...", "INFO")
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            report.system_status['memory_percent'] = memory_percent
            report.system_status['memory_available_gb'] = memory.available / (1024**3)

            if memory_percent < 80:
                self._log(f"    ✓ 内存使用率: {memory_percent}% (可用: {memory.available / (1024**3):.1f} GB)", "SUCCESS")
            elif memory_percent < 90:
                self._log(f"    ⚠️ 内存使用率较高: {memory_percent}% (可用: {memory.available / (1024**3):.1f} GB)", "WARNING")
                issue = DiagnosticIssue(
                    category="System",
                    severity=ProblemSeverity.WARNING,
                    title="内存使用率较高",
                    description=f"当前内存使用率: {memory_percent}%",
                    possible_causes=["程序占用内存过多"],
                    fix_suggestions=["关闭不必要的程序", "增加虚拟内存"],
                    auto_fixable=False
                )
                report.issues.append(issue)
            else:
                self._log(f"    ✗ 内存使用率过高: {memory_percent}% (可用: {memory.available / (1024**3):.1f} GB)", "ERROR")
                issue = DiagnosticIssue(
                    category="System",
                    severity=ProblemSeverity.CRITICAL,
                    title="内存不足",
                    description=f"当前内存使用率: {memory_percent}%",
                    possible_causes=["内存泄漏", "程序占用过多"],
                    fix_suggestions=["重启程序", "增加物理内存"],
                    auto_fixable=False
                )
                report.issues.append(issue)

            # 检测3: 磁盘空间
            self._log("  [5.3] 检测磁盘空间...", "INFO")
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            report.system_status['disk_percent'] = disk_percent
            report.system_status['disk_free_gb'] = disk.free / (1024**3)

            if disk_percent < 90:
                self._log(f"    ✓ 磁盘使用率: {disk_percent}% (剩余: {disk.free / (1024**3):.1f} GB)", "SUCCESS")
            else:
                self._log(f"    ⚠️ 磁盘空间不足: {disk_percent}% (剩余: {disk.free / (1024**3):.1f} GB)", "WARNING")
                issue = DiagnosticIssue(
                    category="System",
                    severity=ProblemSeverity.WARNING,
                    title="磁盘空间不足",
                    description=f"磁盘使用率: {disk_percent}%",
                    possible_causes=["文件占用过多"],
                    fix_suggestions=["清理临时文件", "删除不需要的文件"],
                    auto_fixable=False
                )
                report.issues.append(issue)

        except Exception as e:
            self._log(f"  ✗ 系统资源诊断异常: {e}", "ERROR")

        self._log("", "INFO")

    def _check_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def _print_diagnostic_summary(self, report: DiagnosticReport):
        """打印诊断摘要"""
        self._log("="*80, "INFO")
        self._log("📊 诊断摘要报告", "INFO")
        self._log("="*80, "INFO")
        self._log("", "INFO")
        self._log(f"⏱️ 诊断耗时: {report.duration:.2f}秒", "INFO")
        self._log("", "INFO")

        if report.is_healthy:
            self._log("✅ 系统状态健康，未发现问题", "SUCCESS")
        else:
            critical_count = len(report.critical_issues)
            warning_count = len(report.warning_issues)
            info_count = len([i for i in report.issues if i.severity == ProblemSeverity.INFO])

            self._log(f"🔍 发现问题总数: {len(report.issues)}", "INFO")
            if critical_count > 0:
                self._log(f"   ❌ 严重问题: {critical_count} 个", "ERROR")
            if warning_count > 0:
                self._log(f"   ⚠️ 警告: {warning_count} 个", "WARNING")
            if info_count > 0:
                self._log(f"   ℹ️ 提示: {info_count} 个", "INFO")

            self._log("", "INFO")
            self._log("━"*80, "INFO")
            self._log("📝 问题详情", "INFO")
            self._log("━"*80, "INFO")

            for i, issue in enumerate(report.issues, 1):
                severity_icon = {
                    ProblemSeverity.CRITICAL: "❌",
                    ProblemSeverity.WARNING: "⚠️",
                    ProblemSeverity.INFO: "ℹ️"
                }[issue.severity]

                self._log("", "INFO")
                self._log(f"{severity_icon} 问题 #{i}: {issue.title}", issue.severity.value.upper() if issue.severity == ProblemSeverity.CRITICAL else "WARNING")
                self._log(f"   分类: {issue.category}", "INFO")
                self._log(f"   描述: {issue.description}", "INFO")

                if issue.possible_causes:
                    self._log("   可能原因:", "INFO")
                    for cause in issue.possible_causes:
                        self._log(f"     • {cause}", "INFO")

                if issue.fix_suggestions:
                    self._log("   修复建议:", "INFO")
                    for suggestion in issue.fix_suggestions:
                        self._log(f"     • {suggestion}", "INFO")

                if issue.auto_fixable:
                    self._log("   ✓ 可自动修复", "SUCCESS")
                else:
                    self._log("   ⚠️ 需要手动修复", "WARNING")

        self._log("", "INFO")
        self._log("="*80, "INFO")

    # ========== 修复功能 ==========

    def fix_all(self, report: DiagnosticReport, udid: Optional[str] = None) -> bool:
        """
        针对性修复 - 根据诊断结果修复问题

        Args:
            report: 诊断报告
            udid: 设备UDID

        Returns:
            是否全部修复成功
        """
        if udid is None:
            udid = f"127.0.0.1:{self.adb_port}"

        self._log("", "INFO")
        self._log("="*80, "INFO")
        self._log("🔧 开始针对性修复", "INFO")
        self._log("="*80, "INFO")
        self._log("", "INFO")

        # 筛选可自动修复的问题
        auto_fixable_issues = [i for i in report.critical_issues + report.warning_issues if i.auto_fixable]

        if not auto_fixable_issues:
            self._log("ℹ️ 无可自动修复的问题", "INFO")
            return True

        self._log(f"发现 {len(auto_fixable_issues)} 个可自动修复的问题，开始修复...", "INFO")
        self._log("", "INFO")

        success_count = 0
        fail_count = 0

        for i, issue in enumerate(auto_fixable_issues, 1):
            self._log(f"━"*80, "INFO")
            self._log(f"[{i}/{len(auto_fixable_issues)}] 修复: {issue.title}", "INFO")
            self._log(f"━"*80, "INFO")

            try:
                if issue.category == "Appium":
                    if "未运行" in issue.title or "异常" in issue.title:
                        success = self._fix_appium_service()
                    else:
                        success = False
                elif issue.category == "ADB":
                    if "离线" in issue.title:
                        success = self._fix_offline_device(udid)
                    elif "未连接" in issue.title:
                        success = self._fix_connect_device(udid)
                    elif "僵尸" in issue.title:
                        success = self._fix_zombie_connections()
                    else:
                        success = False
                else:
                    success = False

                if success:
                    success_count += 1
                    self._log(f"✓ 修复成功", "SUCCESS")
                else:
                    fail_count += 1
                    self._log(f"✗ 修复失败", "ERROR")
            except Exception as e:
                fail_count += 1
                self._log(f"✗ 修复异常: {e}", "ERROR")

            self._log("", "INFO")

        self._log("="*80, "INFO")
        self._log(f"修复完成: 成功 {success_count}/{len(auto_fixable_issues)}, 失败 {fail_count}/{len(auto_fixable_issues)}", "INFO")
        self._log("="*80, "INFO")

        return fail_count == 0

    def _fix_appium_service(self) -> bool:
        """修复Appium服务"""
        self._log("  正在启动Appium服务...", "INFO")
        return self.auto_fixer.start_appium_service()

    def _fix_offline_device(self, udid: str) -> bool:
        """修复离线设备"""
        self._log(f"  正在修复离线设备: {udid}...", "INFO")
        return self.auto_fixer.fix_offline_device(udid)

    def _fix_connect_device(self, udid: str) -> bool:
        """连接设备"""
        self._log(f"  正在连接设备: {udid}...", "INFO")
        return self.auto_fixer.connect_adb_device(udid)

    def _fix_zombie_connections(self) -> bool:
        """清除僵尸连接"""
        self._log("  正在清除僵尸连接...", "INFO")
        return self.auto_fixer.clear_zombie_connections()

    # ========== 完整流程 ==========

    def diagnose_and_fix(self, udid: Optional[str] = None, auto_fix: bool = True) -> Tuple[DiagnosticReport, bool]:
        """
        完整流程：先体检，后修复

        Args:
            udid: 设备UDID
            auto_fix: 是否自动修复

        Returns:
            (诊断报告, 修复是否成功)
        """
        # 1. 全面体检
        report = self.diagnose_all(udid)

        # 2. 针对性修复
        fix_success = True
        if auto_fix and (report.has_critical_issues or len(report.warning_issues) > 0):
            fix_success = self.fix_all(report, udid)
        elif not auto_fix:
            self._log("", "INFO")
            self._log("ℹ️ 自动修复已禁用，请手动修复问题", "INFO")

        return report, fix_success


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
    first_aid = ConnectionFirstAid(logger, adb_port="62336")

    print("\n" + "="*80)
    print("🏥 连接急救箱测试")
    print("="*80 + "\n")

    # 执行完整诊断和修复
    report, fix_success = first_aid.diagnose_and_fix(auto_fix=True)

    print("\n" + "="*80)
    print(f"测试完成 - 修复{'成功' if fix_success else '失败'}")
    print("="*80)
