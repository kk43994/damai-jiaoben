#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
智能等待和性能优化模块
提供页面加载检测、并行弹窗处理、自动调优等功能
"""

import time
import threading
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass
from collections import deque


@dataclass
class StepTiming:
    """步骤耗时记录"""
    step_name: str
    start_time: float
    end_time: float
    duration: float
    success: bool


class SmartWait:
    """智能等待管理器"""

    def __init__(self):
        self.timings: List[StepTiming] = []
        self.timing_history: Dict[str, deque] = {}  # 每个步骤的历史耗时
        self.max_history = 10  # 保留最近10次记录

    def wait_for_page_load(self, driver, timeout=5, check_interval=0.2):
        """等待页面加载完成 - 智能检测

        替代固定sleep,通过检测页面稳定性判断加载完成

        Args:
            driver: Appium driver
            timeout: 最大等待时间
            check_interval: 检查间隔

        Returns:
            bool: 是否加载完成
        """
        start_time = time.time()
        previous_source = None
        stable_count = 0
        required_stable = 2  # 需要连续2次page_source相同才认为稳定

        while time.time() - start_time < timeout:
            try:
                current_source = driver.page_source

                if previous_source == current_source:
                    stable_count += 1
                    if stable_count >= required_stable:
                        # 页面稳定,加载完成
                        elapsed = time.time() - start_time
                        return True, elapsed
                else:
                    stable_count = 0

                previous_source = current_source
                time.sleep(check_interval)

            except Exception as e:
                # 获取page_source失败,继续等待
                time.sleep(check_interval)
                continue

        # 超时
        return False, timeout

    def wait_for_element(self, driver, finder_func, timeout=5, check_interval=0.2):
        """等待元素出现

        Args:
            driver: Appium driver
            finder_func: 查找元素的函数 (lambda: driver.find_element(...))
            timeout: 最大等待时间
            check_interval: 检查间隔

        Returns:
            element or None: 找到的元素或None
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                element = finder_func()
                if element:
                    return element
            except:
                pass

            time.sleep(check_interval)

        return None

    def smart_sleep(self, step_name, default_duration=1.0, min_duration=0.3, max_duration=3.0):
        """智能等待 - 基于历史数据自动调优

        根据该步骤的历史平均耗时,动态调整等待时间

        Args:
            step_name: 步骤名称
            default_duration: 默认等待时间
            min_duration: 最小等待时间
            max_duration: 最大等待时间

        Returns:
            float: 实际等待时间
        """
        if step_name in self.timing_history and len(self.timing_history[step_name]) > 0:
            # 计算历史平均耗时
            history = list(self.timing_history[step_name])
            avg_duration = sum(history) / len(history)

            # 使用平均值的1.2倍作为等待时间(留20%余量)
            wait_time = min(max(avg_duration * 1.2, min_duration), max_duration)
        else:
            wait_time = default_duration

        time.sleep(wait_time)
        return wait_time


class ParallelPopupHandler:
    """并行弹窗处理器 - 不阻塞主流程"""

    def __init__(self, driver, log_func=None):
        self.driver = driver
        self.log = log_func if log_func else print
        self.running = False
        self.check_thread = None
        self.popup_keywords = [
            '关闭', '取消', '知道了', '确定',
            '跳过', '稍后', '不了', '开启'
        ]

    def start(self, check_interval=2.0):
        """启动后台弹窗检查线程

        Args:
            check_interval: 检查间隔(秒)
        """
        if self.running:
            return

        self.running = True
        self.check_thread = threading.Thread(
            target=self._check_loop,
            args=(check_interval,),
            daemon=True
        )
        self.check_thread.start()
        self.log("后台弹窗检查已启动")

    def stop(self):
        """停止后台检查"""
        self.running = False
        if self.check_thread:
            self.check_thread.join(timeout=1)
        self.log("后台弹窗检查已停止")

    def _check_loop(self, interval):
        """后台检查循环"""
        while self.running:
            try:
                self._check_and_dismiss_popup()
            except Exception as e:
                # 静默失败,不影响主流程
                pass

            time.sleep(interval)

    def _check_and_dismiss_popup(self):
        """检查并关闭弹窗"""
        try:
            page_source = self.driver.page_source

            # ⚠️ 先检查是否在正常功能页面，避免误关闭
            functional_pages = [
                ('搜索框', ['搜你所想', '请输入', '搜索', '演唱会', '体育赛事', '音乐会', '话剧歌剧']),
                ('城市选择', ['请选择城市', '热门城市', '全部城市', '当前定位', '选择城市', '城市搜索', '切换城市', 'A-Z', 'ABCD']),
                ('筛选页', ['价格', '时间', '场次', '座位', '筛选', '排序']),
                ('详情页', ['立即购买', '选座购买', '加入购物车', '演出介绍', '购买须知', '选择场次']),
            ]

            for page_type, keywords in functional_pages:
                if any(keyword in page_source for keyword in keywords):
                    # 检测到功能页面，跳过弹窗检测
                    return False

            # 检测是否有弹窗
            has_popup = any(kw in page_source for kw in self.popup_keywords)

            if has_popup:
                # 尝试关闭弹窗
                self._try_dismiss()

        except:
            pass

    def _try_dismiss(self):
        """尝试关闭弹窗的多种方式"""
        try:
            from appium.webdriver.common.appiumby import AppiumBy

            # 方式1: 点击关闭按钮
            for text in ['关闭', '取消', '知道了']:
                try:
                    close_btn = self.driver.find_element(
                        AppiumBy.XPATH,
                        f"//*[contains(@text, '{text}')]"
                    )
                    close_btn.click()
                    self.log(f"[后台] 已关闭弹窗: {text}")
                    return True
                except:
                    continue

            # 方式2: 右上角固定坐标
            try:
                self.driver.execute_script("mobile: clickGesture", {
                    "x": 650, "y": 120
                })
                self.log("[后台] 使用坐标关闭弹窗")
                return True
            except:
                pass

        except:
            pass

        return False


class PerformanceMonitor:
    """性能监控器 - 记录每步耗时并自动调优"""

    def __init__(self, log_func=None):
        self.log = log_func if log_func else print
        self.timings: List[StepTiming] = []
        self.step_stats: Dict[str, Dict] = {}  # 步骤统计信息

    def start_step(self, step_name):
        """开始记录步骤

        Args:
            step_name: 步骤名称

        Returns:
            float: 开始时间
        """
        return time.time()

    def end_step(self, step_name, start_time, success=True):
        """结束记录步骤

        Args:
            step_name: 步骤名称
            start_time: 开始时间
            success: 是否成功
        """
        end_time = time.time()
        duration = end_time - start_time

        # 记录本次耗时
        timing = StepTiming(
            step_name=step_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=success
        )
        self.timings.append(timing)

        # 更新统计
        if step_name not in self.step_stats:
            self.step_stats[step_name] = {
                'count': 0,
                'total_duration': 0,
                'success_count': 0,
                'durations': deque(maxlen=10)  # 最近10次
            }

        stats = self.step_stats[step_name]
        stats['count'] += 1
        stats['total_duration'] += duration
        stats['durations'].append(duration)
        if success:
            stats['success_count'] += 1

        # 输出日志
        avg_duration = stats['total_duration'] / stats['count']
        success_rate = (stats['success_count'] / stats['count']) * 100

        self.log(
            f"[性能] {step_name}: {duration:.2f}秒 "
            f"(平均: {avg_duration:.2f}秒, 成功率: {success_rate:.0f}%)"
        )

    def get_recommended_wait(self, step_name, default=1.0):
        """获取推荐的等待时间

        基于历史数据计算最优等待时间

        Args:
            step_name: 步骤名称
            default: 默认值

        Returns:
            float: 推荐等待时间
        """
        if step_name not in self.step_stats:
            return default

        stats = self.step_stats[step_name]
        if len(stats['durations']) == 0:
            return default

        # 取最近10次的平均值
        recent_durations = list(stats['durations'])
        avg = sum(recent_durations) / len(recent_durations)

        # 返回平均值的1.2倍(留余量)
        return min(avg * 1.2, 3.0)  # 最大3秒

    def get_report(self):
        """生成性能报告

        Returns:
            dict: 性能统计报告
        """
        report = {
            'total_steps': len(self.timings),
            'total_duration': sum(t.duration for t in self.timings),
            'step_details': {}
        }

        for step_name, stats in self.step_stats.items():
            avg_duration = stats['total_duration'] / stats['count']
            success_rate = (stats['success_count'] / stats['count']) * 100

            report['step_details'][step_name] = {
                'count': stats['count'],
                'avg_duration': f"{avg_duration:.2f}s",
                'success_rate': f"{success_rate:.0f}%",
                'total_duration': f"{stats['total_duration']:.2f}s"
            }

        return report

    def print_report(self):
        """打印性能报告"""
        report = self.get_report()

        self.log("="*60)
        self.log("性能报告")
        self.log("="*60)
        self.log(f"总步骤数: {report['total_steps']}")
        self.log(f"总耗时: {report['total_duration']:.2f}秒")
        self.log("-"*60)

        for step_name, details in report['step_details'].items():
            self.log(f"\n{step_name}:")
            self.log(f"  执行次数: {details['count']}")
            self.log(f"  平均耗时: {details['avg_duration']}")
            self.log(f"  成功率: {details['success_rate']}")
            self.log(f"  总耗时: {details['total_duration']}")

        self.log("="*60)


# 使用示例
if __name__ == "__main__":
    # 示例: 性能监控
    monitor = PerformanceMonitor()

    # 模拟步骤执行
    start = monitor.start_step("城市选择")
    time.sleep(0.5)
    monitor.end_step("城市选择", start, success=True)

    start = monitor.start_step("搜索演出")
    time.sleep(0.8)
    monitor.end_step("搜索演出", start, success=True)

    # 打印报告
    monitor.print_report()
