# -*- coding: UTF-8 -*-
"""
快速抢票模块 - 高速点击 + 页面变化检测
用于抢票的核心逻辑：不断点击购票按钮直到页面变化
"""

import time
import hashlib
from typing import Optional, Callable, Tuple
from dataclasses import dataclass


@dataclass
class GrabConfig:
    """抢票配置"""
    session_x: int  # 场次坐标X
    session_y: int  # 场次坐标Y
    price_x: int    # 票档坐标X
    price_y: int    # 票档坐标Y
    buy_x: int      # 购票按钮坐标X
    buy_y: int      # 购票按钮坐标Y
    click_interval: float = 0.1  # 点击间隔（秒）
    max_clicks: int = 100  # 最大点击次数
    page_check_interval: int = 5  # 每N次点击检查一次页面


class FastGrabber:
    """快速抢票器"""

    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger
        self.is_grabbing = False
        self.grab_stats = {
            "total_clicks": 0,
            "session_selected": False,
            "price_selected": False,
            "buy_button_clicked": 0,
            "page_changed": False
        }

    def log(self, msg: str, level: str = "INFO"):
        """统一日志输出"""
        if self.logger:
            if hasattr(self.logger, level.lower()):
                getattr(self.logger, level.lower())(msg)
        else:
            print(f"[{level}] {msg}")

    def get_page_hash(self) -> str:
        """获取当前页面的哈希值（用于检测页面变化）"""
        try:
            # 方式1: 使用page_source
            page_source = self.driver.page_source
            return hashlib.md5(page_source.encode()).hexdigest()
        except Exception as e:
            self.log(f"获取页面哈希失败: {e}", "WARNING")
            # 方式2: 使用截图
            try:
                screenshot = self.driver.get_screenshot_as_png()
                return hashlib.md5(screenshot).hexdigest()
            except:
                return ""

    def is_page_changed(self, original_hash: str, threshold: float = 0.9) -> bool:
        """
        检测页面是否变化

        Args:
            original_hash: 原始页面哈希
            threshold: 相似度阈值（暂未使用，简单比较hash）

        Returns:
            bool: 页面是否变化
        """
        current_hash = self.get_page_hash()
        return current_hash != original_hash

    def click_coordinate(self, x: int, y: int, description: str = ""):
        """点击坐标"""
        try:
            self.driver.tap([(x, y)])
            self.log(f"点击 {description or f'({x}, {y})'}", "INFO")
            self.grab_stats["total_clicks"] += 1
            return True
        except Exception as e:
            self.log(f"点击失败: {e}", "ERROR")
            return False

    def select_session(self, x: int, y: int) -> bool:
        """选择场次"""
        self.log("=" * 60, "INFO")
        self.log("步骤1: 选择场次", "INFO")
        self.log("=" * 60, "INFO")

        success = self.click_coordinate(x, y, f"场次 ({x}, {y})")
        if success:
            time.sleep(0.5)  # 等待页面响应
            self.grab_stats["session_selected"] = True
            self.log("✓ 场次选择完成", "SUCCESS")
        else:
            self.log("✗ 场次选择失败", "ERROR")

        return success

    def select_price(self, x: int, y: int) -> bool:
        """选择票档"""
        self.log("=" * 60, "INFO")
        self.log("步骤2: 选择票档", "INFO")
        self.log("=" * 60, "INFO")

        success = self.click_coordinate(x, y, f"票档 ({x}, {y})")
        if success:
            time.sleep(0.5)  # 等待页面响应
            self.grab_stats["price_selected"] = True
            self.log("✓ 票档选择完成", "SUCCESS")
        else:
            self.log("✗ 票档选择失败", "ERROR")

        return success

    def fast_click_buy_button(self,
                             x: int,
                             y: int,
                             max_clicks: int = 100,
                             click_interval: float = 0.1,
                             check_interval: int = 5) -> Tuple[bool, str]:
        """
        快速点击购票按钮，直到页面变化

        Args:
            x: 购票按钮X坐标
            y: 购票按钮Y坐标
            max_clicks: 最大点击次数
            click_interval: 每次点击间隔（秒）
            check_interval: 每N次点击检查一次页面

        Returns:
            (success, message): 是否成功和消息
        """
        self.log("=" * 60, "INFO")
        self.log("步骤3: 快速点击购票按钮", "INFO")
        self.log("=" * 60, "INFO")

        # 获取初始页面状态
        original_hash = self.get_page_hash()
        if not original_hash:
            return False, "无法获取页面状态"

        self.log(f"开始快速点击 (最多{max_clicks}次, 间隔{click_interval}秒)", "INFO")
        self.log(f"每{check_interval}次点击检查页面变化", "INFO")

        click_count = 0
        start_time = time.time()

        while click_count < max_clicks and self.is_grabbing:
            # 点击购票按钮
            self.click_coordinate(x, y, f"购票按钮 [第{click_count + 1}次]")
            click_count += 1
            self.grab_stats["buy_button_clicked"] = click_count

            # 每N次检查页面变化
            if click_count % check_interval == 0:
                self.log(f"检查页面变化... ({click_count}/{max_clicks})", "INFO")

                if self.is_page_changed(original_hash):
                    elapsed = time.time() - start_time
                    self.grab_stats["page_changed"] = True
                    self.log("=" * 60, "SUCCESS")
                    self.log(f"✓ 页面已变化！成功进入下一页面", "SUCCESS")
                    self.log(f"  总点击次数: {click_count}", "SUCCESS")
                    self.log(f"  总耗时: {elapsed:.2f}秒", "SUCCESS")
                    self.log(f"  平均速度: {click_count / elapsed:.1f}次/秒", "SUCCESS")
                    self.log("=" * 60, "SUCCESS")
                    return True, f"成功！点击{click_count}次，耗时{elapsed:.2f}秒"

            # 等待间隔
            time.sleep(click_interval)

        # 达到最大点击次数仍未成功
        elapsed = time.time() - start_time
        msg = f"达到最大点击次数({max_clicks})，页面未变化"
        self.log(f"✗ {msg}", "WARNING")
        self.log(f"  总耗时: {elapsed:.2f}秒", "WARNING")
        return False, msg

    def start_grab(self, config: GrabConfig, on_progress: Optional[Callable[[str], None]] = None) -> Tuple[bool, str]:
        """
        开始抢票（完整流程）

        Args:
            config: 抢票配置
            on_progress: 进度回调函数

        Returns:
            (success, message): 是否成功和消息
        """
        self.is_grabbing = True
        self.grab_stats = {
            "total_clicks": 0,
            "session_selected": False,
            "price_selected": False,
            "buy_button_clicked": 0,
            "page_changed": False
        }

        def progress(msg: str):
            if on_progress:
                on_progress(msg)

        try:
            # 步骤1: 选择场次
            progress("正在选择场次...")
            if not self.select_session(config.session_x, config.session_y):
                return False, "场次选择失败"

            # 步骤2: 选择票档
            progress("正在选择票档...")
            if not self.select_price(config.price_x, config.price_y):
                return False, "票档选择失败"

            # 步骤3: 快速点击购票按钮
            progress("正在快速点击购票按钮...")
            success, message = self.fast_click_buy_button(
                config.buy_x,
                config.buy_y,
                config.max_clicks,
                config.click_interval,
                config.page_check_interval
            )

            if success:
                progress("抢票成功！")
            else:
                progress(f"抢票失败: {message}")

            return success, message

        except Exception as e:
            self.log(f"抢票过程出错: {e}", "ERROR")
            return False, f"抢票过程出错: {str(e)}"

        finally:
            self.is_grabbing = False

    def stop_grab(self):
        """停止抢票"""
        self.log("收到停止信号", "WARNING")
        self.is_grabbing = False

    def get_statistics(self) -> dict:
        """获取抢票统计"""
        return {
            **self.grab_stats,
            "status": "运行中" if self.is_grabbing else "已停止"
        }

    def print_statistics(self):
        """打印统计信息"""
        stats = self.get_statistics()

        self.log("=" * 60, "INFO")
        self.log("抢票统计信息", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"状态: {stats['status']}", "INFO")
        self.log(f"总点击次数: {stats['total_clicks']}", "INFO")
        self.log(f"场次已选择: {'是' if stats['session_selected'] else '否'}", "INFO")
        self.log(f"票档已选择: {'是' if stats['price_selected'] else '否'}", "INFO")
        self.log(f"购票按钮点击: {stats['buy_button_clicked']}次", "INFO")
        self.log(f"页面已变化: {'是' if stats['page_changed'] else '否'}", "INFO")
        self.log("=" * 60, "INFO")


def test_fast_grabber():
    """测试快速抢票器"""
    # 这是一个示例，实际使用需要真实的driver
    class MockDriver:
        def tap(self, coords):
            print(f"点击: {coords}")

        def get_screenshot_as_png(self):
            return b"mock screenshot"

        @property
        def page_source(self):
            return "<html>mock page</html>"

    driver = MockDriver()
    grabber = FastGrabber(driver)

    config = GrabConfig(
        session_x=360,
        session_y=400,
        price_x=360,
        price_y=600,
        buy_x=360,
        buy_y=1100,
        click_interval=0.1,
        max_clicks=50,
        page_check_interval=5
    )

    success, message = grabber.start_grab(config)
    print(f"结果: {success}, {message}")
    grabber.print_statistics()


if __name__ == "__main__":
    test_fast_grabber()
