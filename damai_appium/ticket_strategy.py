# -*- coding: UTF-8 -*-
"""
多策略抢票系统 - 提升抢票成功率
支持：坐标点击 + XPath查找 + OCR识别 + UiAutomator
"""

import time
from typing import Optional, Callable, List, Dict, Any
from enum import Enum
from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class StrategyType(Enum):
    """策略类型枚举"""
    COORDINATE = "coordinate"  # 坐标点击
    XPATH = "xpath"  # XPath查找
    UIAUTOMATOR = "uiautomator"  # UiAutomator
    OCR = "ocr"  # OCR识别
    HYBRID = "hybrid"  # 混合策略


@dataclass
class StrategyResult:
    """策略执行结果"""
    success: bool
    strategy_type: StrategyType
    error_msg: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0


class RetryConfig:
    """重试配置"""
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, backoff_factor: float = 1.5):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor  # 指数退避因子


class TicketStrategy:
    """多策略抢票管理器"""

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger
        self.retry_config = RetryConfig()
        self.strategy_stats = {
            StrategyType.COORDINATE: {"success": 0, "fail": 0},
            StrategyType.XPATH: {"success": 0, "fail": 0},
            StrategyType.UIAUTOMATOR: {"success": 0, "fail": 0},
            StrategyType.OCR: {"success": 0, "fail": 0},
        }

    def log(self, msg: str, level: str = "INFO"):
        """统一日志输出"""
        if self.logger:
            if hasattr(self.logger, level.lower()):
                getattr(self.logger, level.lower())(msg)
        else:
            print(f"[{level}] {msg}")

    def execute_with_retry(self,
                          strategies: List[Callable],
                          strategy_names: List[StrategyType],
                          task_name: str = "操作") -> StrategyResult:
        """
        执行多策略并自动重试

        Args:
            strategies: 策略函数列表（优先级从高到低）
            strategy_names: 策略名称列表
            task_name: 任务名称（用于日志）

        Returns:
            StrategyResult: 执行结果
        """
        self.log(f"开始执行任务: {task_name}", "INFO")

        for idx, (strategy_func, strategy_type) in enumerate(zip(strategies, strategy_names), 1):
            self.log(f"尝试策略 {idx}/{len(strategies)}: {strategy_type.value}", "INFO")

            # 带重试的策略执行
            result = self._execute_single_strategy_with_retry(
                strategy_func,
                strategy_type,
                task_name
            )

            if result.success:
                self.strategy_stats[strategy_type]["success"] += 1
                self.log(f"✓ 策略 {strategy_type.value} 执行成功", "SUCCESS")
                return result
            else:
                self.strategy_stats[strategy_type]["fail"] += 1
                self.log(f"✗ 策略 {strategy_type.value} 执行失败: {result.error_msg}", "WARNING")

        # 所有策略都失败
        self.log(f"所有策略均失败，任务 {task_name} 执行失败", "ERROR")
        return StrategyResult(
            success=False,
            strategy_type=StrategyType.HYBRID,
            error_msg="所有策略均失败"
        )

    def _execute_single_strategy_with_retry(self,
                                           strategy_func: Callable,
                                           strategy_type: StrategyType,
                                           task_name: str) -> StrategyResult:
        """
        执行单个策略并重试
        """
        start_time = time.time()
        retry_count = 0
        current_delay = self.retry_config.retry_delay

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                retry_count = attempt

                if attempt > 0:
                    self.log(f"  重试 {attempt}/{self.retry_config.max_retries} (延迟 {current_delay:.1f}s)", "WAIT")
                    time.sleep(current_delay)
                    current_delay *= self.retry_config.backoff_factor  # 指数退避

                # 执行策略
                strategy_func()

                execution_time = time.time() - start_time
                return StrategyResult(
                    success=True,
                    strategy_type=strategy_type,
                    retry_count=retry_count,
                    execution_time=execution_time
                )

            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"

                if attempt == self.retry_config.max_retries:
                    # 达到最大重试次数
                    execution_time = time.time() - start_time
                    return StrategyResult(
                        success=False,
                        strategy_type=strategy_type,
                        error_msg=error_msg,
                        retry_count=retry_count,
                        execution_time=execution_time
                    )

        # 不应该到达这里
        return StrategyResult(
            success=False,
            strategy_type=strategy_type,
            error_msg="未知错误"
        )

    def click_by_coordinate(self, x: int, y: int) -> Callable:
        """坐标点击策略"""
        def _click():
            self.driver.tap([(x, y)])
            time.sleep(0.5)
        return _click

    def click_by_xpath(self, xpath: str, timeout: float = 5.0) -> Callable:
        """XPath查找并点击策略"""
        def _click():
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.click()
            time.sleep(0.5)
        return _click

    def click_by_uiautomator(self, selector: str) -> Callable:
        """UiAutomator查找并点击策略"""
        def _click():
            from appium.webdriver.common.appiumby import AppiumBy
            element = self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, selector)
            element.click()
            time.sleep(0.5)
        return _click

    def click_by_text(self, text: str, partial: bool = False) -> Callable:
        """通过文字查找并点击（UiAutomator实现）"""
        if partial:
            selector = f'new UiSelector().textContains("{text}")'
        else:
            selector = f'new UiSelector().text("{text}")'
        return self.click_by_uiautomator(selector)

    def get_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        total_success = sum(stat["success"] for stat in self.strategy_stats.values())
        total_fail = sum(stat["fail"] for stat in self.strategy_stats.values())
        total = total_success + total_fail

        if total == 0:
            success_rate = 0.0
        else:
            success_rate = (total_success / total) * 100

        return {
            "total_operations": total,
            "total_success": total_success,
            "total_fail": total_fail,
            "success_rate": success_rate,
            "strategy_details": self.strategy_stats
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()
        self.log("=" * 60, "INFO")
        self.log("多策略抢票统计信息", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"总操作次数: {stats['total_operations']}", "INFO")
        self.log(f"成功次数: {stats['total_success']}", "INFO")
        self.log(f"失败次数: {stats['total_fail']}", "INFO")
        self.log(f"成功率: {stats['success_rate']:.1f}%", "INFO")
        self.log("-" * 60, "INFO")

        for strategy_type, details in stats['strategy_details'].items():
            total = details['success'] + details['fail']
            if total > 0:
                rate = (details['success'] / total) * 100
                self.log(f"{strategy_type.value}: {details['success']}/{total} ({rate:.1f}%)", "INFO")

        self.log("=" * 60, "INFO")


class StrategyPresets:
    """预设策略组合"""

    @staticmethod
    def click_button_strategies(driver, button_text: str, x: int = None, y: int = None):
        """
        点击按钮的策略组合
        优先级: 文字查找 > 坐标点击
        """
        strategy_manager = TicketStrategy(driver)

        strategies = []
        strategy_types = []

        # 策略1: 通过文字精确查找
        strategies.append(strategy_manager.click_by_text(button_text, partial=False))
        strategy_types.append(StrategyType.UIAUTOMATOR)

        # 策略2: 通过文字模糊查找
        strategies.append(strategy_manager.click_by_text(button_text, partial=True))
        strategy_types.append(StrategyType.UIAUTOMATOR)

        # 策略3: 坐标点击（如果提供了坐标）
        if x is not None and y is not None:
            strategies.append(strategy_manager.click_by_coordinate(x, y))
            strategy_types.append(StrategyType.COORDINATE)

        return strategy_manager, strategies, strategy_types

    @staticmethod
    def select_item_strategies(driver, item_text: str, xpath: str = None, x: int = None, y: int = None):
        """
        选择项目的策略组合
        优先级: XPath > 文字查找 > 坐标点击
        """
        strategy_manager = TicketStrategy(driver)

        strategies = []
        strategy_types = []

        # 策略1: XPath查找
        if xpath:
            strategies.append(strategy_manager.click_by_xpath(xpath))
            strategy_types.append(StrategyType.XPATH)

        # 策略2: 文字精确查找
        strategies.append(strategy_manager.click_by_text(item_text, partial=False))
        strategy_types.append(StrategyType.UIAUTOMATOR)

        # 策略3: 文字模糊查找
        strategies.append(strategy_manager.click_by_text(item_text, partial=True))
        strategy_types.append(StrategyType.UIAUTOMATOR)

        # 策略4: 坐标点击
        if x is not None and y is not None:
            strategies.append(strategy_manager.click_by_coordinate(x, y))
            strategy_types.append(StrategyType.COORDINATE)

        return strategy_manager, strategies, strategy_types
