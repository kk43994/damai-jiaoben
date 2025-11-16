# -*- coding: UTF-8 -*-
"""
WebDriver健康监控和自动重连系统
解决WebDriver连接不稳定导致的会话中断问题
"""

import time
import threading
from typing import Optional, Callable, Any
from datetime import datetime
from appium import webdriver
from appium.options.common.base import AppiumOptions
from selenium.common.exceptions import (
    WebDriverException,
    InvalidSessionIdException,
    NoSuchWindowException,
    TimeoutException
)


class SessionState:
    """WebDriver会话状态"""
    def __init__(self):
        self.is_alive = True
        self.last_check_time = time.time()
        self.reconnect_count = 0
        self.total_failures = 0
        self.last_error = None
        self.session_start_time = time.time()

    def mark_failed(self, error: Exception):
        """标记失败"""
        self.is_alive = False
        self.total_failures += 1
        self.last_error = str(error)
        self.last_check_time = time.time()

    def mark_alive(self):
        """标记存活"""
        self.is_alive = True
        self.last_check_time = time.time()

    def reset_reconnect(self):
        """重置重连计数"""
        self.reconnect_count = 0
        self.session_start_time = time.time()


class WebDriverHealthMonitor:
    """
    WebDriver健康监控器

    功能：
    1. 自动检测WebDriver会话健康状态
    2. 会话失败时自动重连
    3. 支持重连重试和指数退避
    4. 保留会话状态（当前Activity等）
    5. 提供详细的健康报告
    """

    def __init__(
        self,
        driver_factory: Callable[[], webdriver.Remote],
        logger=None,
        health_check_interval: int = 30,  # 健康检查间隔（秒）
        max_reconnect_attempts: int = 3,  # 最大重连次数
        reconnect_timeout: int = 60,  # 重连超时（秒）
        auto_monitor: bool = True  # 是否自动启动监控
    ):
        """
        初始化健康监控器

        Args:
            driver_factory: 创建WebDriver的工厂函数
            logger: 日志记录器
            health_check_interval: 健康检查间隔（秒）
            max_reconnect_attempts: 最大重连尝试次数
            reconnect_timeout: 单次重连超时时间（秒）
            auto_monitor: 是否自动启动后台监控
        """
        self.driver_factory = driver_factory
        self.logger = logger
        self.health_check_interval = health_check_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_timeout = reconnect_timeout

        self.driver: Optional[webdriver.Remote] = None
        self.state = SessionState()
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor = threading.Event()
        self._reconnect_lock = threading.Lock()

        if auto_monitor:
            self.start_monitoring()

    def _log(self, message: str, level: str = "INFO"):
        """内部日志方法"""
        if self.logger:
            if hasattr(self.logger, level.lower()):
                getattr(self.logger, level.lower())(message)
            elif hasattr(self.logger, 'log'):
                self.logger.log(message, level)
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def initialize_driver(self) -> bool:
        """
        初始化WebDriver

        Returns:
            是否初始化成功
        """
        try:
            self._log("正在初始化WebDriver...", "INFO")
            self.driver = self.driver_factory()
            self.state.mark_alive()
            self.state.reset_reconnect()
            self._log("✓ WebDriver初始化成功", "SUCCESS")
            return True
        except Exception as e:
            self._log(f"✗ WebDriver初始化失败: {e}", "ERROR")
            self.state.mark_failed(e)
            return False

    def check_health(self, quick: bool = False) -> bool:
        """
        检查WebDriver健康状态

        Args:
            quick: 是否快速检查（仅检查session_id）

        Returns:
            是否健康
        """
        if self.driver is None:
            self.state.mark_failed(Exception("Driver未初始化"))
            return False

        try:
            # 快速检查：检查session_id
            if self.driver.session_id is None:
                self.state.mark_failed(Exception("Session ID为空"))
                return False

            if not quick:
                # 完整检查：尝试获取当前Activity（仅Android）
                _ = self.driver.current_activity

            self.state.mark_alive()
            return True

        except InvalidSessionIdException as e:
            self._log("检测到无效的Session ID", "WARNING")
            self.state.mark_failed(e)
            return False

        except NoSuchWindowException as e:
            self._log("检测到窗口已关闭", "WARNING")
            self.state.mark_failed(e)
            return False

        except WebDriverException as e:
            error_msg = str(e).lower()
            if "invalid session id" in error_msg or "session not found" in error_msg:
                self._log("检测到会话已失效", "WARNING")
                self.state.mark_failed(e)
                return False
            elif "timeout" in error_msg:
                self._log("检测到通信超时", "WARNING")
                self.state.mark_failed(e)
                return False
            else:
                # 其他WebDriver异常，可能是临时性问题
                self._log(f"WebDriver通信异常: {e}", "WARNING")
                return True  # 不标记为失败，可能恢复

        except Exception as e:
            self._log(f"健康检查异常: {e}", "WARNING")
            return True  # 未知异常，保守处理

    def reconnect(self, preserve_state: bool = True) -> bool:
        """
        重新连接WebDriver

        Args:
            preserve_state: 是否尝试恢复之前的状态

        Returns:
            是否重连成功
        """
        with self._reconnect_lock:
            self._log("", "INFO")
            self._log("="*60, "INFO")
            self._log("🔄 开始WebDriver重连流程", "WARNING")
            self._log("="*60, "INFO")

            # 保存当前状态
            previous_activity = None
            if preserve_state and self.driver:
                try:
                    previous_activity = self.driver.current_activity
                    self._log(f"保存当前Activity: {previous_activity}", "INFO")
                except:
                    pass

            # 关闭旧连接
            if self.driver:
                try:
                    self._log("正在关闭旧的WebDriver会话...", "INFO")
                    self.driver.quit()
                    self._log("✓ 旧会话已关闭", "SUCCESS")
                except:
                    self._log("旧会话关闭失败（可能已断开）", "WARNING")

            # 重连重试
            for attempt in range(1, self.max_reconnect_attempts + 1):
                self._log(f"", "INFO")
                self._log(f"[尝试 {attempt}/{self.max_reconnect_attempts}] 正在重新连接...", "INFO")

                try:
                    # 指数退避
                    if attempt > 1:
                        wait_time = min(2 ** (attempt - 1), 10)  # 最多等待10秒
                        self._log(f"等待 {wait_time} 秒后重试...", "INFO")
                        time.sleep(wait_time)

                    # 创建新连接
                    start_time = time.time()
                    self.driver = self.driver_factory()
                    connect_time = time.time() - start_time

                    # 验证连接
                    if self.check_health(quick=True):
                        self.state.mark_alive()
                        self.state.reconnect_count += 1
                        self._log(f"✓ WebDriver重连成功! (耗时: {connect_time:.2f}秒)", "SUCCESS")

                        # 尝试恢复状态
                        if preserve_state and previous_activity:
                            self._log(f"尝试恢复到之前的Activity: {previous_activity}", "INFO")
                            # 注意：这里只是记录，实际恢复需要应用层逻辑

                        self._log("="*60, "INFO")
                        return True
                    else:
                        self._log(f"✗ 连接成功但健康检查失败", "ERROR")

                except Exception as e:
                    self._log(f"✗ 重连失败: {e}", "ERROR")
                    if attempt < self.max_reconnect_attempts:
                        self._log(f"将进行第 {attempt + 1} 次尝试...", "WARNING")

            # 所有重试失败
            self._log("", "ERROR")
            self._log("="*60, "ERROR")
            self._log(f"❌ WebDriver重连失败（已尝试{self.max_reconnect_attempts}次）", "ERROR")
            self._log("="*60, "ERROR")
            self.state.mark_failed(Exception("重连失败"))
            return False

    def _monitor_loop(self):
        """后台监控循环"""
        self._log("✓ WebDriver健康监控已启动", "INFO")
        self._log(f"  - 检查间隔: {self.health_check_interval}秒", "INFO")
        self._log(f"  - 自动重连: 已启用（最多{self.max_reconnect_attempts}次）", "INFO")

        while not self._stop_monitor.is_set():
            try:
                # 等待指定间隔
                if self._stop_monitor.wait(self.health_check_interval):
                    break  # 收到停止信号

                # 执行健康检查
                if not self.check_health():
                    self._log("⚠️ 检测到WebDriver会话异常", "WARNING")
                    self._log(f"上次错误: {self.state.last_error}", "WARNING")

                    # 尝试自动重连
                    self._log("触发自动重连机制...", "WARNING")
                    if self.reconnect(preserve_state=True):
                        self._log("✓ 自动重连成功，会话已恢复", "SUCCESS")
                    else:
                        self._log("❌ 自动重连失败，需要手动处理", "ERROR")
                        # 暂停监控，避免无限重试
                        self._log("健康监控已暂停（会话失效）", "WARNING")
                        break

            except Exception as e:
                self._log(f"监控循环异常: {e}", "ERROR")

        self._log("WebDriver健康监控已停止", "INFO")

    def start_monitoring(self):
        """启动后台健康监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._log("健康监控已在运行中", "WARNING")
            return

        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="WebDriverHealthMonitor"
        )
        self._monitor_thread.start()

    def stop_monitoring(self):
        """停止后台健康监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._log("正在停止健康监控...", "INFO")
            self._stop_monitor.set()
            self._monitor_thread.join(timeout=5)
            self._log("✓ 健康监控已停止", "SUCCESS")

    def get_health_report(self) -> dict:
        """
        获取健康报告

        Returns:
            包含健康状态的字典
        """
        session_uptime = time.time() - self.state.session_start_time

        return {
            "is_alive": self.state.is_alive,
            "has_driver": self.driver is not None,
            "session_id": self.driver.session_id if self.driver else None,
            "last_check_time": self.state.last_check_time,
            "time_since_last_check": time.time() - self.state.last_check_time,
            "reconnect_count": self.state.reconnect_count,
            "total_failures": self.state.total_failures,
            "last_error": self.state.last_error,
            "session_uptime_seconds": session_uptime,
            "session_uptime_formatted": self._format_uptime(session_uptime),
            "monitoring_active": self._monitor_thread and self._monitor_thread.is_alive()
        }

    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}小时{minutes}分{secs}秒"
        elif minutes > 0:
            return f"{minutes}分{secs}秒"
        else:
            return f"{secs}秒"

    def shutdown(self):
        """关闭监控器和WebDriver"""
        self._log("正在关闭WebDriver健康监控器...", "INFO")

        # 停止监控
        self.stop_monitoring()

        # 关闭WebDriver
        if self.driver:
            try:
                self.driver.quit()
                self._log("✓ WebDriver已关闭", "SUCCESS")
            except:
                self._log("WebDriver关闭失败（可能已断开）", "WARNING")

        self._log("✓ 健康监控器已关闭", "SUCCESS")

    def __enter__(self):
        """上下文管理器入口"""
        if not self.driver:
            self.initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()


# 辅助函数：创建健康监控器
def create_health_monitor(
    server_url: str,
    capabilities: dict,
    logger=None,
    **monitor_kwargs
) -> WebDriverHealthMonitor:
    """
    创建WebDriver健康监控器的便捷方法

    Args:
        server_url: Appium服务器URL
        capabilities: WebDriver capabilities
        logger: 日志记录器
        **monitor_kwargs: 传递给WebDriverHealthMonitor的其他参数

    Returns:
        WebDriverHealthMonitor实例
    """
    def driver_factory():
        options = AppiumOptions()
        options.load_capabilities(capabilities)
        return webdriver.Remote(server_url, options=options)

    return WebDriverHealthMonitor(
        driver_factory=driver_factory,
        logger=logger,
        **monitor_kwargs
    )
