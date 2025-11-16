# -*- coding: UTF-8 -*-
"""
抢票倒计时系统 - 精确定时抢票
支持：倒计时显示、自动启动、提前准备
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional
from enum import Enum


class CountdownState(Enum):
    """倒计时状态"""
    IDLE = "idle"  # 空闲
    WAITING = "waiting"  # 等待中
    PREPARING = "preparing"  # 准备中（倒计时最后阶段）
    READY = "ready"  # 准备就绪
    RUNNING = "running"  # 正在抢票
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消


class CountdownTimer:
    """倒计时计时器"""

    def __init__(self,
                 target_time: datetime,
                 prepare_seconds: int = 30,
                 on_countdown_update: Optional[Callable[[int], None]] = None,
                 on_prepare: Optional[Callable[[], None]] = None,
                 on_start: Optional[Callable[[], None]] = None,
                 on_complete: Optional[Callable[[], None]] = None):
        """
        初始化倒计时器

        Args:
            target_time: 目标时间（开票时间）
            prepare_seconds: 提前准备的秒数（用于提前加载页面等）
            on_countdown_update: 倒计时更新回调 (剩余秒数)
            on_prepare: 准备阶段回调
            on_start: 开始抢票回调
            on_complete: 完成回调
        """
        self.target_time = target_time
        self.prepare_seconds = prepare_seconds
        self.on_countdown_update = on_countdown_update
        self.on_prepare = on_prepare
        self.on_start = on_start
        self.on_complete = on_complete

        self.state = CountdownState.IDLE
        self.countdown_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()

        self.prepare_time = target_time - timedelta(seconds=prepare_seconds)

    def start(self):
        """启动倒计时"""
        if self.state != CountdownState.IDLE:
            print(f"[倒计时] 当前状态为 {self.state.value}，无法启动")
            return False

        # 检查目标时间
        now = datetime.now()
        if now >= self.target_time:
            print(f"[倒计时] 目标时间已过，立即执行")
            self._trigger_start()
            return True

        self.state = CountdownState.WAITING
        self.stop_flag.clear()

        # 启动倒计时线程
        self.countdown_thread = threading.Thread(target=self._countdown_loop, daemon=True)
        self.countdown_thread.start()

        print(f"[倒计时] 已启动，目标时间: {self.target_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    def stop(self):
        """停止倒计时"""
        self.stop_flag.set()
        self.state = CountdownState.CANCELLED
        print(f"[倒计时] 已取消")

    def _countdown_loop(self):
        """倒计时循环"""
        prepare_triggered = False

        while not self.stop_flag.is_set():
            now = datetime.now()

            # 计算剩余时间
            remaining = (self.target_time - now).total_seconds()

            if remaining <= 0:
                # 时间到，开始抢票
                self._trigger_start()
                break

            # 检查是否进入准备阶段
            if not prepare_triggered and now >= self.prepare_time:
                self._trigger_prepare()
                prepare_triggered = True

            # 更新倒计时显示
            if self.on_countdown_update:
                self.on_countdown_update(int(remaining))

            # 根据剩余时间调整更新频率
            if remaining > 60:
                # 大于1分钟，每秒更新
                time.sleep(1)
            elif remaining > 10:
                # 10秒-1分钟，每0.5秒更新
                time.sleep(0.5)
            else:
                # 最后10秒，每0.1秒更新
                time.sleep(0.1)

        # 倒计时结束
        if not self.stop_flag.is_set():
            self.state = CountdownState.COMPLETED
            if self.on_complete:
                self.on_complete()

    def _trigger_prepare(self):
        """触发准备阶段"""
        self.state = CountdownState.PREPARING
        print(f"[倒计时] 进入准备阶段（提前 {self.prepare_seconds} 秒）")

        if self.on_prepare:
            try:
                self.on_prepare()
            except Exception as e:
                print(f"[倒计时] 准备阶段回调错误: {e}")

    def _trigger_start(self):
        """触发开始抢票"""
        self.state = CountdownState.RUNNING
        print(f"[倒计时] 时间到！开始抢票")

        if self.on_start:
            try:
                self.on_start()
            except Exception as e:
                print(f"[倒计时] 开始回调错误: {e}")

    def get_remaining_time(self) -> timedelta:
        """获取剩余时间"""
        now = datetime.now()
        remaining = self.target_time - now

        if remaining.total_seconds() < 0:
            return timedelta(0)
        return remaining

    def get_remaining_seconds(self) -> int:
        """获取剩余秒数"""
        return int(self.get_remaining_time().total_seconds())

    def format_remaining_time(self) -> str:
        """格式化剩余时间"""
        remaining = self.get_remaining_time()

        if remaining.total_seconds() <= 0:
            return "00:00:00"

        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 24:
            days = hours // 24
            hours = hours % 24
            return f"{days}天 {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def is_active(self) -> bool:
        """是否正在运行"""
        return self.state in [CountdownState.WAITING, CountdownState.PREPARING]


class CountdownManager:
    """倒计时管理器（支持多个倒计时任务）"""

    def __init__(self):
        self.timers: dict[str, CountdownTimer] = {}

    def add_timer(self, name: str, timer: CountdownTimer):
        """添加倒计时器"""
        self.timers[name] = timer

    def remove_timer(self, name: str):
        """移除倒计时器"""
        if name in self.timers:
            self.timers[name].stop()
            del self.timers[name]

    def get_timer(self, name: str) -> Optional[CountdownTimer]:
        """获取倒计时器"""
        return self.timers.get(name)

    def list_timers(self) -> list[str]:
        """列出所有倒计时器名称"""
        return list(self.timers.keys())

    def stop_all(self):
        """停止所有倒计时"""
        for timer in self.timers.values():
            timer.stop()


def parse_datetime(time_str: str) -> Optional[datetime]:
    """
    解析时间字符串

    支持格式:
    - "2025-12-31 20:00:00"
    - "2025-12-31 20:00"
    - "12-31 20:00"（使用当前年份）
    - "20:00"（使用今天日期）
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m-%d %H:%M",
        "%H:%M",
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(time_str, fmt)

            # 补全年份和日期
            now = datetime.now()
            if fmt == "%m-%d %H:%M":
                parsed = parsed.replace(year=now.year)
            elif fmt == "%H:%M":
                parsed = parsed.replace(year=now.year, month=now.month, day=now.day)

            # 如果时间已过，假设是明天或明年
            if parsed < now:
                if fmt == "%H:%M":
                    parsed += timedelta(days=1)
                elif fmt == "%m-%d %H:%M" and parsed.month < now.month:
                    parsed = parsed.replace(year=now.year + 1)

            return parsed

        except ValueError:
            continue

    return None


def format_time_delta(seconds: int) -> str:
    """
    格式化时间差

    Args:
        seconds: 秒数

    Returns:
        格式化的时间字符串
    """
    if seconds < 0:
        return "已过期"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 24:
        days = hours // 24
        hours = hours % 24
        return f"{days}天{hours}小时{minutes}分{secs}秒"
    elif hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    elif minutes > 0:
        return f"{minutes}分{secs}秒"
    else:
        return f"{secs}秒"
