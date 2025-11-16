# -*- coding: UTF-8 -*-
"""
声音提示系统 - 提升用户体验
支持：成功/失败/警告/提示音
"""

import os
import sys
import threading
from enum import Enum
from pathlib import Path


class SoundType(Enum):
    """声音类型"""
    SUCCESS = "success"  # 成功音效
    ERROR = "error"  # 错误音效
    WARNING = "warning"  # 警告音效
    INFO = "info"  # 提示音效
    COUNTDOWN = "countdown"  # 倒计时音效
    TICKET_GRABBED = "ticket_grabbed"  # 抢到票音效


class SoundNotifier:
    """声音通知器"""

    def __init__(self, enabled: bool = True, volume: float = 1.0):
        self.enabled = enabled
        self.volume = volume
        self.platform = sys.platform

        # 检测是否可以播放声音
        self.can_play_sound = self._check_sound_support()

    def _check_sound_support(self) -> bool:
        """检查声音支持"""
        try:
            if self.platform == 'win32':
                import winsound
                return True
            elif self.platform == 'darwin':  # macOS
                return os.system('which afplay > /dev/null 2>&1') == 0
            else:  # Linux
                return (os.system('which aplay > /dev/null 2>&1') == 0 or
                       os.system('which paplay > /dev/null 2>&1') == 0)
        except:
            return False

    def play(self, sound_type: SoundType, async_play: bool = True):
        """
        播放声音

        Args:
            sound_type: 声音类型
            async_play: 是否异步播放（不阻塞主线程）
        """
        if not self.enabled or not self.can_play_sound:
            return

        if async_play:
            thread = threading.Thread(target=self._play_sync, args=(sound_type,))
            thread.daemon = True
            thread.start()
        else:
            self._play_sync(sound_type)

    def _play_sync(self, sound_type: SoundType):
        """同步播放声音"""
        try:
            if self.platform == 'win32':
                self._play_windows(sound_type)
            elif self.platform == 'darwin':
                self._play_macos(sound_type)
            else:
                self._play_linux(sound_type)
        except Exception as e:
            print(f"[声音] 播放失败: {e}")

    def _play_windows(self, sound_type: SoundType):
        """Windows平台播放"""
        import winsound

        # 使用Windows系统音效
        sound_map = {
            SoundType.SUCCESS: winsound.MB_OK,
            SoundType.ERROR: winsound.MB_ICONHAND,
            SoundType.WARNING: winsound.MB_ICONEXCLAMATION,
            SoundType.INFO: winsound.MB_ICONASTERISK,
            SoundType.COUNTDOWN: winsound.MB_OK,
            SoundType.TICKET_GRABBED: winsound.MB_OK,
        }

        sound_flag = sound_map.get(sound_type, winsound.MB_OK)

        # 播放系统提示音
        winsound.MessageBeep(sound_flag)

        # 对于重要事件，播放额外的蜂鸣声
        if sound_type in [SoundType.SUCCESS, SoundType.TICKET_GRABBED]:
            # 成功音：三声短促的蜂鸣
            for i in range(3):
                winsound.Beep(1000 + i * 200, 100)

        elif sound_type == SoundType.ERROR:
            # 错误音：低频长蜂鸣
            winsound.Beep(400, 500)

        elif sound_type == SoundType.WARNING:
            # 警告音：两声蜂鸣
            winsound.Beep(800, 150)
            winsound.Beep(800, 150)

    def _play_macos(self, sound_type: SoundType):
        """macOS平台播放"""
        # 使用系统音效
        sound_map = {
            SoundType.SUCCESS: "Glass",
            SoundType.ERROR: "Basso",
            SoundType.WARNING: "Sosumi",
            SoundType.INFO: "Purr",
            SoundType.COUNTDOWN: "Tink",
            SoundType.TICKET_GRABBED: "Glass",
        }

        sound_name = sound_map.get(sound_type, "Purr")
        os.system(f'afplay /System/Library/Sounds/{sound_name}.aiff &')

    def _play_linux(self, sound_type: SoundType):
        """Linux平台播放"""
        # 使用beep命令（如果可用）
        if os.system('which beep > /dev/null 2>&1') == 0:
            freq_map = {
                SoundType.SUCCESS: 1000,
                SoundType.ERROR: 400,
                SoundType.WARNING: 800,
                SoundType.INFO: 600,
                SoundType.COUNTDOWN: 1200,
                SoundType.TICKET_GRABBED: 1000,
            }

            freq = freq_map.get(sound_type, 600)
            os.system(f'beep -f {freq} -l 200 &')

    def play_success(self):
        """播放成功音效"""
        self.play(SoundType.SUCCESS)

    def play_error(self):
        """播放错误音效"""
        self.play(SoundType.ERROR)

    def play_warning(self):
        """播放警告音效"""
        self.play(SoundType.WARNING)

    def play_info(self):
        """播放提示音效"""
        self.play(SoundType.INFO)

    def play_countdown(self):
        """播放倒计时音效"""
        self.play(SoundType.COUNTDOWN)

    def play_ticket_grabbed(self):
        """播放抢到票音效"""
        self.play(SoundType.TICKET_GRABBED)

    def play_custom_sequence(self, sequence: list[tuple[int, int]]):
        """
        播放自定义音序列（仅Windows）

        Args:
            sequence: [(频率, 持续时间), ...] 列表
        """
        if not self.enabled or self.platform != 'win32':
            return

        def _play():
            import winsound
            for freq, duration in sequence:
                try:
                    winsound.Beep(int(freq), int(duration))
                except:
                    pass

        thread = threading.Thread(target=_play)
        thread.daemon = True
        thread.start()

    def enable(self):
        """启用声音"""
        self.enabled = True

    def disable(self):
        """禁用声音"""
        self.enabled = False

    def toggle(self) -> bool:
        """切换声音开关"""
        self.enabled = not self.enabled
        return self.enabled


# 预定义音效序列

class SoundSequences:
    """预定义音效序列"""

    # 抢票成功：欢快的上升音阶
    TICKET_SUCCESS = [
        (523, 100),  # C5
        (587, 100),  # D5
        (659, 100),  # E5
        (698, 100),  # F5
        (784, 300),  # G5
    ]

    # 抢票失败：下降音阶
    TICKET_FAIL = [
        (659, 150),  # E5
        (587, 150),  # D5
        (523, 150),  # C5
        (440, 400),  # A4
    ]

    # 倒计时最后5秒：滴答声
    COUNTDOWN_5SEC = [
        (1000, 100),
        (1000, 100),
        (1000, 100),
        (1000, 100),
        (1200, 200),  # 最后一声更高
    ]

    # 警告：急促蜂鸣
    URGENT_WARNING = [
        (800, 100),
        (800, 100),
        (800, 100),
    ]

    # 操作完成：简单提示音
    OPERATION_DONE = [
        (1000, 100),
        (1200, 100),
    ]


# 单例模式
_sound_notifier_instance = None


def get_sound_notifier(enabled: bool = True) -> SoundNotifier:
    """获取声音通知器单例"""
    global _sound_notifier_instance
    if _sound_notifier_instance is None:
        _sound_notifier_instance = SoundNotifier(enabled=enabled)
    return _sound_notifier_instance
