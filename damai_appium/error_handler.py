# -*- coding: UTF-8 -*-
"""
全局异常处理系统 - 提升系统稳定性
支持：异常分类、自动恢复、错误统计
"""

import time
import traceback
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps


class ErrorCategory(Enum):
    """错误类别枚举"""
    NETWORK = "network"  # 网络错误
    ELEMENT_NOT_FOUND = "element_not_found"  # 元素未找到
    TIMEOUT = "timeout"  # 超时错误
    SYSTEM = "system"  # 系统错误
    APPIUM = "appium"  # Appium相关错误
    UNKNOWN = "unknown"  # 未知错误


@dataclass
class ErrorRecord:
    """错误记录"""
    category: ErrorCategory
    error_type: str
    error_message: str
    timestamp: datetime
    traceback_info: str = ""
    auto_recovered: bool = False
    recovery_attempts: int = 0


class ErrorStatistics:
    """错误统计"""

    def __init__(self):
        self.records: list[ErrorRecord] = []
        self.category_counts: Dict[ErrorCategory, int] = {
            category: 0 for category in ErrorCategory
        }
        self.recovery_success_count = 0
        self.recovery_fail_count = 0

    def add_record(self, record: ErrorRecord):
        """添加错误记录"""
        self.records.append(record)
        self.category_counts[record.category] += 1

        if record.auto_recovered:
            self.recovery_success_count += 1
        elif record.recovery_attempts > 0:
            self.recovery_fail_count += 1

    def get_summary(self) -> Dict[str, Any]:
        """获取统计摘要"""
        total_errors = len(self.records)

        return {
            "total_errors": total_errors,
            "category_breakdown": {
                cat.value: count for cat, count in self.category_counts.items()
            },
            "auto_recovery_success": self.recovery_success_count,
            "auto_recovery_fail": self.recovery_fail_count,
            "recovery_rate": (
                self.recovery_success_count / (self.recovery_success_count + self.recovery_fail_count) * 100
                if (self.recovery_success_count + self.recovery_fail_count) > 0 else 0
            )
        }

    def print_summary(self, logger=None):
        """打印统计摘要"""
        summary = self.get_summary()

        def log(msg):
            if logger:
                logger.info(msg)
            else:
                print(msg)

        log("=" * 60)
        log("错误统计报告")
        log("=" * 60)
        log(f"总错误数: {summary['total_errors']}")
        log(f"自动恢复成功: {summary['auto_recovery_success']}")
        log(f"自动恢复失败: {summary['auto_recovery_fail']}")
        log(f"恢复成功率: {summary['recovery_rate']:.1f}%")
        log("-" * 60)
        log("错误分类:")
        for category, count in summary['category_breakdown'].items():
            if count > 0:
                log(f"  {category}: {count}")
        log("=" * 60)


class GlobalErrorHandler:
    """全局错误处理器"""

    def __init__(self, logger=None):
        self.logger = logger
        self.statistics = ErrorStatistics()
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}

    def log(self, msg: str, level: str = "INFO"):
        """统一日志输出"""
        if self.logger:
            if hasattr(self.logger, level.lower()):
                getattr(self.logger, level.lower())(msg)
        else:
            print(f"[{level}] {msg}")

    def classify_error(self, exception: Exception) -> ErrorCategory:
        """错误分类"""
        error_name = type(exception).__name__
        error_msg = str(exception).lower()

        # 网络错误
        if any(keyword in error_msg for keyword in [
            'connection', 'network', 'timeout', 'unreachable', 'refused'
        ]) or error_name in ['ConnectionError', 'URLError', 'HTTPError']:
            return ErrorCategory.NETWORK

        # 元素未找到
        if any(keyword in error_msg for keyword in [
            'no such element', 'element not found', 'unable to find element'
        ]) or error_name in ['NoSuchElementException', 'ElementNotFound']:
            return ErrorCategory.ELEMENT_NOT_FOUND

        # 超时错误
        if 'timeout' in error_msg or error_name == 'TimeoutException':
            return ErrorCategory.TIMEOUT

        # Appium错误
        if any(keyword in error_msg for keyword in [
            'appium', 'webdriver', 'session'
        ]) or error_name in ['WebDriverException', 'InvalidSessionIdException']:
            return ErrorCategory.APPIUM

        # 系统错误
        if error_name in ['OSError', 'MemoryError', 'SystemError']:
            return ErrorCategory.SYSTEM

        return ErrorCategory.UNKNOWN

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """注册恢复策略"""
        self.recovery_strategies[category] = strategy
        self.log(f"注册恢复策略: {category.value}", "DEBUG")

    def handle_error(self,
                    exception: Exception,
                    context: str = "",
                    auto_recover: bool = True,
                    max_recovery_attempts: int = 2) -> bool:
        """
        处理错误

        Args:
            exception: 异常对象
            context: 上下文信息
            auto_recover: 是否自动恢复
            max_recovery_attempts: 最大恢复尝试次数

        Returns:
            bool: 是否成功恢复
        """
        category = self.classify_error(exception)
        error_type = type(exception).__name__
        error_message = str(exception)

        self.log(f"捕获错误 [{category.value}]: {error_type}: {error_message}", "ERROR")
        if context:
            self.log(f"  上下文: {context}", "ERROR")

        # 创建错误记录
        record = ErrorRecord(
            category=category,
            error_type=error_type,
            error_message=error_message,
            timestamp=datetime.now(),
            traceback_info=traceback.format_exc()
        )

        # 尝试自动恢复
        recovered = False
        if auto_recover and category in self.recovery_strategies:
            self.log(f"尝试自动恢复...", "WARNING")

            for attempt in range(max_recovery_attempts):
                record.recovery_attempts += 1

                try:
                    self.log(f"  恢复尝试 {attempt + 1}/{max_recovery_attempts}", "INFO")
                    self.recovery_strategies[category]()

                    self.log(f"✓ 自动恢复成功", "SUCCESS")
                    recovered = True
                    record.auto_recovered = True
                    break

                except Exception as e:
                    self.log(f"  恢复失败: {str(e)}", "WARNING")
                    if attempt < max_recovery_attempts - 1:
                        time.sleep(2 ** attempt)  # 指数退避

        # 记录错误
        self.statistics.add_record(record)

        return recovered

    def safe_execute(self,
                    func: Callable,
                    error_context: str = "",
                    fallback_value: Any = None,
                    raise_on_error: bool = False) -> Any:
        """
        安全执行函数（捕获所有异常）

        Args:
            func: 要执行的函数
            error_context: 错误上下文
            fallback_value: 发生错误时的返回值
            raise_on_error: 是否在错误后抛出异常

        Returns:
            函数返回值或fallback_value
        """
        try:
            return func()
        except Exception as e:
            recovered = self.handle_error(e, context=error_context, auto_recover=True)

            if not recovered and raise_on_error:
                raise

            return fallback_value


def error_handler(category: ErrorCategory = None,
                 context: str = "",
                 auto_recover: bool = True,
                 fallback_value: Any = None):
    """
    装饰器：自动处理函数异常

    用法:
        @error_handler(category=ErrorCategory.NETWORK, context="连接Appium")
        def connect():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取第一个参数（通常是self）
                handler = None
                if args and hasattr(args[0], 'error_handler'):
                    handler = args[0].error_handler

                if handler and isinstance(handler, GlobalErrorHandler):
                    recovered = handler.handle_error(
                        e,
                        context=context or func.__name__,
                        auto_recover=auto_recover
                    )

                    if not recovered:
                        if fallback_value is not None:
                            return fallback_value
                        raise
                else:
                    # 没有error_handler，直接抛出
                    raise

        return wrapper
    return decorator


# 预定义恢复策略

def restart_app_strategy(driver, package_name: str = "cn.damai"):
    """重启App恢复策略"""
    def recover():
        print("[恢复策略] 重启App...")
        driver.terminate_app(package_name)
        time.sleep(2)
        driver.activate_app(package_name)
        time.sleep(3)
        print("[恢复策略] App重启完成")
    return recover


def reconnect_driver_strategy(reconnect_func: Callable):
    """重新连接Driver恢复策略"""
    def recover():
        print("[恢复策略] 重新连接Driver...")
        reconnect_func()
        print("[恢复策略] Driver重连完成")
    return recover


def scroll_page_strategy(driver, direction: str = "down"):
    """滚动页面恢复策略（元素未找到时）"""
    def recover():
        print(f"[恢复策略] 滚动页面 ({direction})...")

        # 获取屏幕尺寸
        size = driver.get_window_size()
        width = size['width']
        height = size['height']

        if direction == "down":
            driver.swipe(width // 2, height * 0.7, width // 2, height * 0.3, 500)
        elif direction == "up":
            driver.swipe(width // 2, height * 0.3, width // 2, height * 0.7, 500)

        time.sleep(1)
        print("[恢复策略] 页面滚动完成")
    return recover
