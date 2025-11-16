#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
大麦抢票智能AI版 - OCR识别 + 智能决策
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import time
from datetime import datetime
import json
from pathlib import Path
import io
import sys
import os
import cv2
import numpy as np
import gc  # 垃圾回收
import pyperclip  # 剪贴板操作

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "damai_appium"))

# 找到adb的完整路径
ADB_PATH = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools"
ADB_EXE = ADB_PATH / "adb.exe" if (ADB_PATH / "adb.exe").exists() else "adb"

# 同时也添加到PATH（双保险）
if ADB_PATH.exists():
    os.environ["PATH"] = str(ADB_PATH) + os.pathsep + os.environ.get("PATH", "")

from damai_appium.damai_app_v2 import DamaiBot, BotLogger
from damai_appium.fast_grabber import FastGrabber, GrabConfig
from environment_checker import EnvironmentChecker, EnvironmentFixer, CheckResult
from smart_wait import SmartWait, ParallelPopupHandler, PerformanceMonitor
from connection_auto_fixer import ConnectionAutoFixer

# 安全的print函数 - 避免Windows GBK编码错误
def safe_print(msg):
    """安全的print,避免emoji等Unicode字符导致的编码错误"""
    try:
        print(msg)
    except UnicodeEncodeError:
        # 如果编码错误,尝试替换特殊字符
        try:
            safe_msg = msg.replace('[OK]', 'OK').replace('[FAIL]', 'FAIL').replace('[WARN]', 'WARN')
            print(safe_msg)
        except:
            pass  # 完全忽略无法打印的消息

# 延迟导入OCR（首次使用时加载）
_ocr_instance = None

def get_ocr():
    """延迟加载OCR实例 - 增强版带详细日志和多种初始化策略"""
    global _ocr_instance
    if _ocr_instance is None:
        try:
            safe_print("[OCR] 开始初始化PaddleOCR...")
            from paddleocr import PaddleOCR

            # 兼容不同版本的PaddleOCR参数
            init_success = False
            last_error = None

            # 方法1: 使用新版参数 use_textline_orientation (不带show_log)
            try:
                safe_print("[OCR] 尝试方法1: use_textline_orientation=True, lang='ch'")
                _ocr_instance = PaddleOCR(use_textline_orientation=True, lang='ch')
                safe_print("[OCR] √ 方法1成功 (新版API)")
                init_success = True
            except Exception as e1:
                last_error = e1
                safe_print(f"[OCR] 方法1失败: {str(e1)[:100]}")

                # 方法2: 使用旧版参数 use_angle_cls (不带show_log)
                try:
                    safe_print("[OCR] 尝试方法2: use_angle_cls=True, lang='ch'")
                    _ocr_instance = PaddleOCR(use_angle_cls=True, lang='ch')
                    safe_print("[OCR] √ 方法2成功 (旧版API)")
                    init_success = True
                except Exception as e2:
                    last_error = e2
                    safe_print(f"[OCR] 方法2失败: {str(e2)[:100]}")

                    # 方法3: 最简参数
                    try:
                        safe_print("[OCR] 尝试方法3: lang='ch'")
                        _ocr_instance = PaddleOCR(lang='ch')
                        safe_print("[OCR] √ 方法3成功")
                        init_success = True
                    except Exception as e3:
                        last_error = e3
                        safe_print(f"[OCR] 方法3失败: {str(e3)[:100]}")

                        # 方法4: 无参数
                        try:
                            safe_print("[OCR] 尝试方法4: 无参数")
                            _ocr_instance = PaddleOCR()
                            safe_print("[OCR] √ 方法4成功")
                            init_success = True
                        except Exception as e4:
                            last_error = e4
                            safe_print(f"[OCR] 方法4失败: {str(e4)[:100]}")

            if init_success and _ocr_instance:
                safe_print(f"[OCR] OCR实例创建成功: {type(_ocr_instance).__name__}")
                # 测试OCR是否可用
                try:
                    safe_print("[OCR] 测试OCR实例...")
                    import numpy as np
                    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
                    _ocr_instance.predict(test_img)
                    safe_print("[OCR] √ OCR实例可用")
                except Exception as test_err:
                    safe_print(f"[OCR] ! OCR测试失败: {test_err}")
                    _ocr_instance = None
            else:
                safe_print(f"[OCR] X OCR初始化全部失败,最后错误: {last_error}")
                _ocr_instance = None

        except Exception as e:
            safe_print(f"[OCR] X OCR初始化完全失败: {e}")
            try:
                import traceback
                traceback.print_exc()
            except UnicodeEncodeError:
                pass  # 忽略traceback编码错误
            _ocr_instance = None
    else:
        safe_print("[OCR] 使用已缓存的OCR实例")

    return _ocr_instance


class PageState:
    """页面状态识别"""
    UNKNOWN = "未知"
    NOT_STARTED = "App未启动"
    LOADING = "加载中"
    HOME = "首页"
    CITY_SELECT = "城市选择页"  # 新增:城市选择页
    SEARCH = "搜索页"
    RESULT = "搜索结果"
    LIST = "演出列表"  # 新增:点击搜索结果后的演出列表页
    DETAIL = "演出详情"
    SESSION_TICKET = "场次票档页"  # 新增:场次和票档选择页
    SEAT = "选座页"
    ORDER = "订单页"
    PERMISSION_DIALOG = "权限弹窗"
    UPGRADE_DIALOG = "升级弹窗"
    POPUP = "通用弹窗"  # 新增：通用弹窗状态
    ERROR = "错误"  # 新增：通用错误状态（兼容旧代码）
    ERROR_PAGE = "错误页面"


class SmartAI:
    """智能决策系统"""

    def __init__(self):
        self.current_state = PageState.UNKNOWN
        self.ocr_cache = []  # 缓存OCR结果
        self.last_action_time = 0

        # ===== 集成 DamaiTicketBot 的稳定坐标配置 =====
        # 基于实际测试的11个验证坐标点
        self.stable_coords = {
            # 城市选择
            "city_selector": (216, 88),      # 城市选择入口
            "city_search_box": (148, 192),   # 城市搜索框 (需要先点击激活)
            "city_item": (99, 328),          # 城市选项

            # 搜索
            "search_entry": (326, 99),       # 搜索入口
            "search_result": (155, 195),     # 搜索结果

            # 演出选择
            "show_item": (337, 329),         # 演出项
            "buy_button": (464, 1227),       # 立即购票

            # 场次票档 (示例坐标,不同演出可能不同)
            "session_selector": (209, 435),  # 场次选择
            "price_selector": (169, 659),    # 票档选择
            "confirm_button": (558, 1233),   # 确定按钮

            # 排队重试
            "retry_button": (376, 907)       # 重试按钮
        }

        # 重试配置
        self.retry_config = {
            "max_click_retries": 3,          # 单次点击最大重试次数
            "click_wait": 2,                 # 点击后默认等待时间(秒)
        }

    def click_stable_coord(self, driver, coord_name: str, wait: float = None,
                          max_retries: int = None, log_func=None) -> bool:
        """使用稳定坐标点击 (来自 DamaiTicketBot)

        Args:
            driver: Appium driver
            coord_name: 坐标名称
            wait: 点击后等待时间(秒),None则使用默认值
            max_retries: 最大重试次数,None则使用默认值
            log_func: 日志函数

        Returns:
            bool: 是否点击成功
        """
        if coord_name not in self.stable_coords:
            if log_func:
                log_func(f"未找到稳定坐标配置: {coord_name}", "ERROR")
            return False

        x, y = self.stable_coords[coord_name]
        wait_time = wait if wait is not None else self.retry_config['click_wait']
        max_retries = max_retries if max_retries is not None else self.retry_config['max_click_retries']

        for attempt in range(max_retries):
            try:
                if attempt > 0 and log_func:
                    log_func(f"重试点击 {coord_name} (第 {attempt + 1}/{max_retries} 次)", "RETRY")
                else:
                    if log_func:
                        log_func(f"点击稳定坐标: {coord_name} ({x}, {y})", "INFO")

                driver.tap([(x, y)])
                time.sleep(wait_time)
                return True

            except Exception as e:
                if log_func:
                    log_func(f"点击失败: {e}", "WARNING")
                if attempt < max_retries - 1:
                    time.sleep(1)  # 重试前等待1秒
                    continue
                else:
                    if log_func:
                        log_func(f"点击 {coord_name} 最终失败", "ERROR")
                    return False

        return False

    def input_text_safe(self, driver, text: str, wait: float = 1, log_func=None) -> bool:
        """安全输入文本 (来自 DamaiTicketBot)

        Args:
            driver: Appium driver
            text: 要输入的文本
            wait: 输入后等待时间(秒)
            log_func: 日志函数

        Returns:
            bool: 是否输入成功
        """
        if log_func:
            log_func(f"输入文本: {text}", "INFO")

        try:
            # 查找活动的输入框
            active = driver.switch_to.active_element
            if active:
                active.clear()  # 先清空
                active.send_keys(text)
                time.sleep(wait)
                if log_func:
                    log_func(f"文本输入成功: {text}", "SUCCESS")
                return True
            else:
                if log_func:
                    log_func("未找到活动的输入框", "ERROR")
                return False

        except Exception as e:
            if log_func:
                log_func(f"输入失败: {e}", "ERROR")
            return False

    def analyze_screen(self, screenshot, use_ocr=True):
        """分析屏幕截图"""
        if not use_ocr:
            return []

        try:
            # 转换PIL Image到numpy数组
            img_array = np.array(screenshot)

            # OCR识别 (移除cls参数,使用新版API)
            ocr = get_ocr()
            if not ocr:
                safe_print("OCR实例为None,跳过识别")
                return []

            safe_print(f"[OCR] 开始识别图像 ({img_array.shape})...")
            result = ocr.predict(img_array)
            safe_print(f"[OCR] 识别完成,结果类型: {type(result)}")

            # 提取文字和位置 (适配新版API) - 增强错误处理
            texts = []
            if result:
                try:
                    # 新版PaddleOCR返回字典格式
                    if isinstance(result, dict) and 'rec_texts' in result:
                        rec_texts = result.get('rec_texts', [])
                        rec_scores = result.get('rec_scores', [])
                        dt_polys = result.get('dt_polys', [])

                        # 确保所有列表长度一致
                        min_len = min(len(rec_texts), len(rec_scores), len(dt_polys))

                        for i in range(min_len):
                            try:
                                text = rec_texts[i]
                                score = rec_scores[i]
                                box = dt_polys[i]

                                # 安全地计算中心点
                                if len(box) >= 3 and len(box[0]) >= 2 and len(box[2]) >= 2:
                                    center_x = int((box[0][0] + box[2][0]) / 2)
                                    center_y = int((box[0][1] + box[2][1]) / 2)
                                else:
                                    # 如果box格式不对,使用第一个点作为位置
                                    center_x = int(box[0][0]) if len(box) > 0 and len(box[0]) > 0 else 0
                                    center_y = int(box[0][1]) if len(box) > 0 and len(box[0]) > 1 else 0

                                texts.append({
                                    'text': text,
                                    'confidence': float(score),
                                    'position': (center_x, center_y),
                                    'box': box.tolist() if hasattr(box, 'tolist') else box
                                })
                            except Exception as item_err:
                                safe_print(f"  OCR单项解析错误(跳过): {item_err}")
                                continue

                    # 兼容旧版格式
                    elif isinstance(result, list) and len(result) > 0:
                        for line in result[0] if result[0] else []:
                            try:
                                if len(line) >= 2:
                                    box = line[0]
                                    text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                                    confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.9

                                    # 安全地计算中心点
                                    if len(box) >= 3:
                                        center_x = int((box[0][0] + box[2][0]) / 2)
                                        center_y = int((box[0][1] + box[2][1]) / 2)
                                    else:
                                        center_x = int(box[0][0]) if len(box) > 0 else 0
                                        center_y = int(box[0][1]) if len(box) > 0 else 0

                                    texts.append({
                                        'text': text,
                                        'confidence': float(confidence),
                                        'position': (center_x, center_y),
                                        'box': box
                                    })
                            except Exception as line_err:
                                safe_print(f"  OCR行解析错误(跳过): {line_err}")
                                continue
                except Exception as parse_err:
                    safe_print(f"  OCR结果解析错误: {parse_err}")

            safe_print(f"[OCR] 识别到 {len(texts)} 个文字区域")
            self.ocr_cache = texts
            return texts

        except Exception as e:
            safe_print(f"OCR识别错误: {e}")
            try:
                import traceback
                traceback.print_exc()
            except UnicodeEncodeError:
                pass
            return []

    def detect_page_state(self, texts):
        """检测当前页面状态 - 根据实际业务流程优化"""
        if not texts:
            return PageState.NOT_STARTED

        text_list = [t['text'] for t in texts]
        text_str = ''.join(text_list)

        # 检测输入框的存在
        has_edittext = any('EditText' in str(t) for t in texts)
        has_focused_input = any(t.get('focused', False) for t in texts if 'EditText' in str(t))

        # 按实际业务流程优先级检测 (从最具体到最模糊)

        # === 第1层: 弹窗类 (最高优先级) ===
        if any(keyword in text_str for keyword in ['立即开启', '下次再说', '位置权限']):
            return PageState.PERMISSION_DIALOG
        if any(keyword in text_str for keyword in ['升级提示', '立即下载', '新版本', '立即升级']):
            return PageState.UPGRADE_DIALOG
        # 排队弹窗
        if '当前排队的人数太多' in text_str or '排队中' in text_str:
            return PageState.SESSION_TICKET  # 仍在场次票档页,需要重试

        # === 第2层: 错误/异常页面 ===
        if any(keyword in text_str for keyword in ['网络异常', '加载失败', '服务器错误', '刷新重试']):
            return PageState.ERROR_PAGE

        # === 第3层: 加载中 ===
        if any(keyword in text_str for keyword in ['加载中', 'loading', '请稍候']):
            return PageState.LOADING

        # === 第4层: 订单页 ===
        if '提交订单' in text_str or '确认购买' in text_str or '订单确认' in text_str:
            return PageState.ORDER

        # === 第5层: 场次票档页 (点击购票后的页面) ===
        # 强特征: 同时有"场次"和"票档"
        if ('场次' in text_str and '票档' in text_str) or '选择场次' in text_str:
            return PageState.SESSION_TICKET
        # 或者有"确定"按钮 且 有价格和场次信息
        if '确定' in text_str and ('¥' in text_str or 'RMB' in text_str) and '场次' in text_str:
            return PageState.SESSION_TICKET

        # === 第6层: 详情页 (有"立即购票"等强特征) ===
        if any(keyword in text_str for keyword in ['立即购票', '立即购买', '立即预订', '立即抢购', '特惠选座', '选座购买']):
            return PageState.DETAIL
        if '演出详情' in text_str:
            return PageState.DETAIL

        # === 第7层: 城市选择页 (点击城市选择器后) ===
        # 强特征: 有"当前定位"或"热门城市"或"切换城市"
        if any(keyword in text_str for keyword in ['当前定位', '热门城市', '切换城市', '定位城市']):
            return PageState.CITY_SELECT
        # 或者: 有大量城市名称(检测是否有4个以上的城市相关文本)
        city_keywords = ['北京', '上海', '广州', '深圳', '成都', '杭州', '南京', '重庆', '武汉', '西安']
        city_count = len([t for t in texts if any(city in t['text'] for city in city_keywords)])
        if city_count >= 3:  # 至少3个城市名
            return PageState.CITY_SELECT

        # === 第8层: 搜索页 (搜索框激活) ===
        # 关键: 不能只看有EditText,要看是否在搜索状态
        # 强特征1: 输入框被聚焦
        if has_focused_input:
            # 进一步确认不是在城市选择页
            if not any(kw in text_str for kw in ['当前定位', '热门城市']):
                return PageState.SEARCH
        # 强特征2: 有"搜索演出"/"搜索场馆"明确文字
        if '搜索演出' in text_str or '搜索场馆' in text_str:
            return PageState.SEARCH
        # 强特征3: 有"历史搜索"或"搜索建议"
        if '历史搜索' in text_str or '搜索建议' in text_str or '大家都在搜' in text_str:
            return PageState.SEARCH
        # 强特征4: 有"取消"按钮且有输入框(搜索页特有)
        if '取消' in text_str and has_edittext and not any(kw in text_str for kw in ['热门城市', '当前定位']):
            return PageState.SEARCH

        # === 第9层: 演出列表页 (搜索后点击结果进入) ===
        # 特征: 有多个时间/场次信息,但没有"立即购票"按钮
        has_session_info = ('场次' in text_str or '剩余' in text_str)
        has_buy_button = any(btn in text_str for btn in ['立即购买', '立即预订', '立即抢购', '立即购票', '购票'])

        if has_session_info and not has_buy_button:
            # 且不是场次票档页(没有"票档"关键词)
            if '票档' not in text_str:
                return PageState.LIST

        # === 第10层: 首页 (底部导航栏 + 无其他强特征) ===
        has_bottom_nav = ('首页' in text_str and '发现' in text_str and '我的' in text_str)
        has_home_features = any(keyword in text_str for keyword in ['演出', '体育', '音乐会', '赛事', '推荐', '热门'])

        # 首页判断: 有底部导航栏 且 没有其他页面的强特征
        if has_bottom_nav:
            # 排除其他页面
            if not has_focused_input and not has_session_info:
                if not any(kw in text_str for kw in ['搜索演出', '搜索场馆', '历史搜索', '热门城市', '当前定位']):
                    return PageState.HOME

        # 备选首页: 有首页特征但没有其他强特征
        if has_home_features and not has_focused_input and not has_session_info:
            if not any(kw in text_str for kw in ['搜索演出', '热门城市', '场次', '票档', '立即购票']):
                return PageState.HOME

        # === 第11层: 搜索结果页 ===
        if '搜索结果' in text_str:
            return PageState.RESULT

        # === 第12层: 选座页 ===
        if '请先选座' in text_str or '选座购买' in text_str or '确认座位' in text_str:
            return PageState.SEAT

        # === 第13层: 默认未知 ===
        return PageState.UNKNOWN

    def suggest_action(self, page_state, texts, keyword=""):
        """根据页面状态建议操作"""
        actions = []

        if page_state == PageState.PERMISSION_DIALOG:
            # 查找"下次再说"或"立即开启"
            for t in texts:
                if '下次再说' in t['text'] or '暂不' in t['text']:
                    actions.append(('点击', t['text'], t['position'], '拒绝权限'))
                elif '立即开启' in t['text'] or '允许' in t['text']:
                    actions.append(('点击', t['text'], t['position'], '开启权限'))

        elif page_state == PageState.UPGRADE_DIALOG:
            # 查找关闭按钮
            for t in texts:
                if '取消' in t['text'] or '下次' in t['text']:
                    actions.append(('点击', t['text'], t['position'], '关闭升级提示'))

        elif page_state == PageState.HOME or page_state == PageState.SEARCH:
            # 查找搜索框
            for t in texts:
                if '搜索' in t['text']:
                    actions.append(('点击', t['text'], t['position'], '打开搜索'))

        elif page_state == PageState.RESULT:
            # 查找关键词匹配的结果
            if keyword:
                for t in texts:
                    if keyword[:5] in t['text']:  # 匹配前5个字
                        actions.append(('点击', t['text'], t['position'], f'选择演出: {t["text"]}'))

        elif page_state == PageState.DETAIL:
            # 查找"立即购买"
            for t in texts:
                if '立即购买' in t['text'] or '购票' in t['text']:
                    actions.append(('点击', t['text'], t['position'], '立即购买'))

        elif page_state == PageState.SEAT:
            # 建议选座位置（中央区域）
            actions.append(('点击', '座位区域', (360, 800), '选择座位'))

        return actions


class SmartAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("自动化抢购技术学习脚本 v2.1 (集成OCR与自动决策) - 仅供教学研究")
        # 窗口大小：Canvas 450x800(62.5%缩放) + 右侧控制区400 = 总宽870
        self.root.geometry("870x900")

        self.bot = None
        self.running = False
        self.monitor_thread = None
        self.grabbing = False  # 抢票运行状态
        self.grab_thread = None  # 抢票线程
        self.ai = SmartAI()
        self.use_ocr = tk.BooleanVar(value=True)
        self.auto_action = tk.BooleanVar(value=False)
        self.scale_1to1 = tk.BooleanVar(value=True)  # 1:1显示模式
        self.enable_popup_detection = tk.BooleanVar(value=False)  # 弹窗检测开关（默认关闭）
        self.device_width = 0
        self.device_height = 0
        self.current_screenshot = None  # 保存当前截图
        self.last_cleanup_time = time.time()  # 上次清理时间
        self.cleanup_interval = 20  # 清理间隔(秒)
        self.coordinates = {}  # 坐标配置

        # 智能优化模块
        self.smart_wait = SmartWait()
        self.performance_monitor = PerformanceMonitor(log_func=self.log)
        self.popup_handler = None  # 弹窗处理器(连接后初始化)

        # 设备管理器
        from damai_appium.device_manager import DeviceManager
        self.device_manager = DeviceManager("devices.json")

        # 显示缩放配置（适配1080p显示器）
        self.display_width = 450   # 显示宽度（62.5%缩放）
        self.display_height = 800  # 显示高度（62.5%缩放）
        self.target_width = 720    # 目标设备宽度
        self.target_height = 1280  # 目标设备高度

        # 截图保存
        self.screenshots_dir = Path(__file__).parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        self.last_screenshot_path = None  # 最新截图路径

        # 实时诊断悬浮窗
        self.diagnose_window = None
        self.diagnose_is_monitoring = False
        self.diagnose_thread = None

        # 快速抢票模块
        self.fast_grabber = None  # 连接后初始化

        # 抢票坐标配置
        self.grab_coords = {
            "session_x": tk.IntVar(value=360),
            "session_y": tk.IntVar(value=400),
            "price_x": tk.IntVar(value=360),
            "price_y": tk.IntVar(value=600),
            "buy_x": tk.IntVar(value=360),
            "buy_y": tk.IntVar(value=1100)
        }

        # 抢票参数
        self.click_interval = tk.DoubleVar(value=0.1)
        self.max_clicks = tk.IntVar(value=100)
        self.page_check_interval = tk.IntVar(value=5)

        # 坐标选择模式
        self.coord_picking_mode = None  # 当前正在选择的坐标类型

        self.create_widgets()
        self.load_config()

        # 刷新设备列表
        self.root.after(500, self.refresh_devices)

        # 启动时弹出法律免责声明（延迟300ms，确保主窗口已完全加载）
        self.root.after(300, self.show_disclaimer_window)

    def create_widgets(self):
        """创建界面"""

        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#1890ff", height=60)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(
            title_frame,
            text="针对自动化抢购集成OCR技术和自动决策技术的学习脚本（供教学用）",
            font=("微软雅黑", 13, "bold"),
            bg="#1890ff",
            fg="white"
        )
        title_label.pack(pady=8)

        # 版本号（小字）
        version_label = tk.Label(
            title_frame,
            text="v2.1.0 | 开源学习项目",
            font=("微软雅黑", 9),
            bg="#1890ff",
            fg="#e6f7ff"
        )
        version_label.pack(pady=(0, 8))

        # ⚠️ 法律免责声明横条（紧凑版）
        disclaimer_bar = tk.Frame(self.root, bg="#dc3545", height=22)
        disclaimer_bar.pack(fill=tk.X, padx=10, pady=(3, 5))
        disclaimer_bar.pack_propagate(False)  # 固定高度

        disclaimer_text = "⚠️ 法律声明：仅供技术学习 | 严禁商业倒卖/违法犯罪 | 使用者违法后果自负 | 点击查看详情"

        # 使用Button样式但无边框，可点击查看详情
        self.disclaimer_label = tk.Label(
            disclaimer_bar,
            text=disclaimer_text,
            font=("微软雅黑", 7),
            bg="#dc3545",
            fg="yellow",
            cursor="hand2"
        )
        self.disclaimer_label.pack(fill=tk.BOTH, expand=True)
        self.disclaimer_label.bind("<Button-1>", lambda e: self.show_disclaimer_window())

        # 主内容区
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 左侧：实时截图 + OCR识别结果 ===
        left_frame = ttk.LabelFrame(main_paned, text="实时截图 + OCR识别", padding="10")
        main_paned.add(left_frame, weight=3)

        # 添加滚动条容器
        canvas_container = ttk.Frame(left_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Canvas with scrollbars
        self.canvas = tk.Canvas(
            canvas_container,
            bg="black",
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 配置滚动条
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)

        # 绑定鼠标事件
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)  # 右键菜单

        # 创建右键菜单
        self.canvas_menu = tk.Menu(self.canvas, tearoff=0)
        self.canvas_menu.add_command(label="保存原始截图 (720x1280)", command=lambda: self.save_screenshot(original=True))
        self.canvas_menu.add_command(label="保存显示截图 (450x800)", command=lambda: self.save_screenshot(original=False))
        self.canvas_menu.add_separator()
        self.canvas_menu.add_command(label="复制最新截图路径", command=self.copy_latest_screenshot_path)

        screenshot_info = ttk.Frame(left_frame)
        screenshot_info.pack(fill=tk.X, pady=(5, 0))

        self.screenshot_time_label = ttk.Label(screenshot_info, text="等待连接...", font=("微软雅黑", 9))
        self.screenshot_time_label.pack(side=tk.LEFT)

        self.mouse_pos_label = ttk.Label(screenshot_info, text="坐标: -", font=("Consolas", 9))
        self.mouse_pos_label.pack(side=tk.LEFT, padx=(20, 0))

        self.fps_label = ttk.Label(screenshot_info, text="FPS: 0", font=("Consolas", 9))
        self.fps_label.pack(side=tk.RIGHT)

        # === 中间：控制和配置 (添加滚动条) ===
        middle_container = ttk.Frame(main_paned)
        main_paned.add(middle_container, weight=1)

        # 创建Canvas和Scrollbar实现滚动
        middle_canvas = tk.Canvas(middle_container, highlightthickness=0)
        middle_scrollbar = ttk.Scrollbar(middle_container, orient="vertical", command=middle_canvas.yview)
        middle_frame = ttk.Frame(middle_canvas)

        # 配置Canvas
        middle_canvas.configure(yscrollcommand=middle_scrollbar.set)
        middle_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        middle_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 将frame添加到Canvas
        canvas_frame = middle_canvas.create_window((0, 0), window=middle_frame, anchor="nw")

        # 绑定配置事件以更新scrollregion
        def on_middle_configure(event):
            middle_canvas.configure(scrollregion=middle_canvas.bbox("all"))
            # 同时调整Canvas窗口宽度以匹配Canvas宽度
            middle_canvas.itemconfig(canvas_frame, width=event.width)

        middle_frame.bind("<Configure>", on_middle_configure)
        middle_canvas.bind("<Configure>", lambda e: middle_canvas.itemconfig(canvas_frame, width=e.width))

        # 绑定鼠标滚轮事件
        def on_middle_mousewheel(event):
            middle_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        middle_canvas.bind_all("<MouseWheel>", on_middle_mousewheel)

        # 连接配置
        conn_frame = ttk.LabelFrame(middle_frame, text="设备连接", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        # 设备选择下拉框
        ttk.Label(conn_frame, text="选择设备:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.device_var = tk.StringVar(value="手动输入")
        self.device_combo = ttk.Combobox(conn_frame, textvariable=self.device_var, width=20, state="readonly")
        self.device_combo.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=(5, 0))
        self.device_combo.bind("<<ComboboxSelected>>", self.on_device_selected)

        # 刷新设备列表按钮
        ttk.Button(conn_frame, text="刷新", command=self.refresh_devices, width=6).grid(row=0, column=3, sticky=tk.W, padx=(5, 0))

        ttk.Label(conn_frame, text="ADB端口:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value="59700")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=12).grid(row=1, column=1, sticky=tk.W, padx=(5, 0))

        # 自动检测按钮
        self.auto_detect_btn = ttk.Button(conn_frame, text="自动检测", command=self.auto_detect_port, width=12)
        self.auto_detect_btn.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))

        # 添加设备按钮
        ttk.Button(conn_frame, text="+ 添加设备", command=self.add_device_dialog, width=12).grid(row=1, column=3, sticky=tk.W, padx=(5, 0))

        # 连接按钮区域
        conn_btn_frame = ttk.Frame(conn_frame)
        conn_btn_frame.grid(row=2, column=0, columnspan=4, pady=(8, 0), sticky=tk.W)

        self.connect_btn = ttk.Button(conn_btn_frame, text="连接设备", command=self.connect_device, width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.disconnect_btn = ttk.Button(conn_btn_frame, text="断开连接", command=self.disconnect_device, width=12, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reconnect_btn = ttk.Button(conn_btn_frame, text="重新连接", command=self.reconnect, width=12, state=tk.DISABLED)
        self.reconnect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.clear_zombie_btn = ttk.Button(conn_btn_frame, text="🧹 清除僵尸连接", command=self.clear_zombie_connections, width=15)
        self.clear_zombie_btn.pack(side=tk.LEFT)

        # 环境诊断按钮区域
        env_btn_frame = ttk.Frame(conn_frame)
        env_btn_frame.grid(row=3, column=0, columnspan=4, pady=(8, 0), sticky=tk.W)

        self.env_check_btn = ttk.Button(env_btn_frame, text="🔧 环境诊断", command=self.show_environment_check, width=12)
        self.env_check_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.env_fix_btn = ttk.Button(env_btn_frame, text="🔨 一键修复", command=self.auto_fix_environment, width=12)
        self.env_fix_btn.pack(side=tk.LEFT)

        # 连接状态
        self.status_label = tk.Label(conn_frame, text="● 未连接", fg="gray", font=("微软雅黑", 9, "bold"))
        self.status_label.grid(row=4, column=0, columnspan=4, pady=(8, 0))

        # AI配置
        ai_frame = ttk.LabelFrame(middle_frame, text="AI配置", padding="10")
        ai_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(ai_frame, text="启用OCR识别", variable=self.use_ocr).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(ai_frame, text="等比缩放显示(真实坐标)", variable=self.scale_1to1, command=self.on_scale_mode_change).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(ai_frame, text="自动执行操作（实验性）", variable=self.auto_action).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(ai_frame, text="启用弹窗检测（可能误关闭功能页面）", variable=self.enable_popup_detection).pack(anchor=tk.W, pady=2)

        ttk.Label(ai_frame, text="更新间隔:").pack(anchor=tk.W, pady=(5, 2))
        self.interval_var = tk.StringVar(value="0.5")
        interval_scale = ttk.Scale(ai_frame, from_=0.3, to=3.0, variable=self.interval_var, orient=tk.HORIZONTAL)
        interval_scale.pack(fill=tk.X, pady=2)
        self.interval_label = ttk.Label(ai_frame, text="0.5秒")
        self.interval_label.pack(anchor=tk.W)

        ttk.Label(ai_frame, text="内存清理间隔:").pack(anchor=tk.W, pady=(5, 2))
        self.cleanup_var = tk.StringVar(value="20")
        cleanup_scale = ttk.Scale(ai_frame, from_=10, to=60, variable=self.cleanup_var, orient=tk.HORIZONTAL)
        cleanup_scale.pack(fill=tk.X, pady=2)
        self.cleanup_label = ttk.Label(ai_frame, text="20秒")
        self.cleanup_label.pack(anchor=tk.W)

        # 显示设备分辨率
        self.resolution_label = ttk.Label(ai_frame, text="设备: 未连接", font=("Consolas", 8), foreground="gray")
        self.resolution_label.pack(anchor=tk.W, pady=(5, 0))

        # 抢票配置
        config_frame = ttk.LabelFrame(middle_frame, text="抢票配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # 城市 - 改为下拉框
        ttk.Label(config_frame, text="目标城市:").pack(anchor=tk.W, pady=2)
        self.city_var = tk.StringVar(value="北京")
        city_combo = ttk.Combobox(config_frame, textvariable=self.city_var, width=18)
        city_combo['values'] = ("北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "武汉", "西安", "重庆", "天津", "苏州", "长沙", "郑州", "济南")
        city_combo.pack(fill=tk.X, pady=2)

        # 演出名称
        ttk.Label(config_frame, text="演出名称:").pack(anchor=tk.W, pady=2)
        self.show_name_var = tk.StringVar(value="乌龙山伯爵")
        ttk.Entry(config_frame, textvariable=self.show_name_var, width=20).pack(fill=tk.X, pady=2)

        # 搜索关键词
        ttk.Label(config_frame, text="搜索关键词:").pack(anchor=tk.W, pady=2)
        self.keyword_var = tk.StringVar(value="乌龙山伯爵")
        ttk.Entry(config_frame, textvariable=self.keyword_var, width=20).pack(fill=tk.X, pady=2)

        # 坐标配置
        ttk.Label(config_frame, text="坐标配置:").pack(anchor=tk.W, pady=(8, 2))
        coord_btn_frame = ttk.Frame(config_frame)
        coord_btn_frame.pack(fill=tk.X, pady=2)

        ttk.Button(coord_btn_frame, text="导入坐标配置", command=self.import_coordinates, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(coord_btn_frame, text="编辑坐标", command=self.edit_coordinates, width=12).pack(side=tk.LEFT)

        self.coord_status_label = ttk.Label(config_frame, text="未加载坐标配置", foreground="gray", font=("微软雅黑", 8))
        self.coord_status_label.pack(anchor=tk.W, pady=2)

        # 购票数量 - 新增下拉框
        ttk.Label(config_frame, text="购票数量:").pack(anchor=tk.W, pady=2)
        self.ticket_count_var = tk.StringVar(value="1张")
        count_combo = ttk.Combobox(config_frame, textvariable=self.ticket_count_var, width=18, state="readonly")
        count_combo['values'] = ("1张", "2张", "3张", "4张", "5张", "6张")
        count_combo.pack(fill=tk.X, pady=2)

        # 抢票模式 - 新增下拉框
        ttk.Label(config_frame, text="抢票模式:").pack(anchor=tk.W, pady=2)
        self.grab_mode_var = tk.StringVar(value="极速模式")
        mode_combo = ttk.Combobox(config_frame, textvariable=self.grab_mode_var, width=18, state="readonly")
        mode_combo['values'] = ("极速模式", "稳定模式", "调试模式")
        mode_combo.pack(fill=tk.X, pady=2)

        # 控制按钮
        btn_frame = ttk.Frame(middle_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(btn_frame, text="开始监控", command=self.start_monitoring, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_monitoring, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # === 快速抢票坐标设置面板 ===
        coords_frame = ttk.LabelFrame(middle_frame, text="⚡ 快速抢票坐标设置", padding="10")
        coords_frame.pack(fill=tk.X, pady=(0, 10))

        # 场次坐标
        session_row = ttk.Frame(coords_frame)
        session_row.pack(fill=tk.X, pady=2)
        ttk.Label(session_row, text="场次:", width=6).pack(side=tk.LEFT)
        ttk.Entry(session_row, textvariable=self.grab_coords["session_x"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(session_row, textvariable=self.grab_coords["session_y"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(session_row, text="📍", command=lambda: self.pick_coord_from_screenshot("session"), width=3).pack(side=tk.LEFT, padx=2)

        # 票档坐标
        price_row = ttk.Frame(coords_frame)
        price_row.pack(fill=tk.X, pady=2)
        ttk.Label(price_row, text="票档:", width=6).pack(side=tk.LEFT)
        ttk.Entry(price_row, textvariable=self.grab_coords["price_x"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(price_row, textvariable=self.grab_coords["price_y"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(price_row, text="📍", command=lambda: self.pick_coord_from_screenshot("price"), width=3).pack(side=tk.LEFT, padx=2)

        # 购票按钮坐标
        buy_row = ttk.Frame(coords_frame)
        buy_row.pack(fill=tk.X, pady=2)
        ttk.Label(buy_row, text="购票:", width=6).pack(side=tk.LEFT)
        ttk.Entry(buy_row, textvariable=self.grab_coords["buy_x"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Entry(buy_row, textvariable=self.grab_coords["buy_y"], width=5).pack(side=tk.LEFT, padx=2)
        ttk.Button(buy_row, text="📍", command=lambda: self.pick_coord_from_screenshot("buy"), width=3).pack(side=tk.LEFT, padx=2)

        # 参数设置
        param_row = ttk.Frame(coords_frame)
        param_row.pack(fill=tk.X, pady=5)
        ttk.Label(param_row, text="间隔:", width=6).pack(side=tk.LEFT)
        ttk.Entry(param_row, textvariable=self.click_interval, width=5).pack(side=tk.LEFT, padx=2)
        ttk.Label(param_row, text="s").pack(side=tk.LEFT)
        ttk.Label(param_row, text="最大:", width=5).pack(side=tk.LEFT, padx=(5,0))
        ttk.Entry(param_row, textvariable=self.max_clicks, width=5).pack(side=tk.LEFT, padx=2)

        # 保存/加载按钮
        save_load_row = ttk.Frame(coords_frame)
        save_load_row.pack(fill=tk.X, pady=2)
        ttk.Button(save_load_row, text="保存坐标", command=self.save_grab_coords, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(save_load_row, text="加载坐标", command=self.load_grab_coords, width=10).pack(side=tk.LEFT, padx=2)

        # === 抢票控制按钮（修改为两阶段）===
        grab_btn_frame = ttk.Frame(middle_frame)
        grab_btn_frame.pack(fill=tk.X, pady=(0, 10))

        # 阶段一：场次导航按钮
        self.navigate_btn = ttk.Button(
            grab_btn_frame,
            text="①场次导航",
            command=self.navigate_to_session_page,
            width=12,
            state=tk.DISABLED
        )
        self.navigate_btn.pack(side=tk.LEFT, padx=(0, 2))

        # 阶段二：开始抢票按钮（新）
        self.grab_btn = ttk.Button(
            grab_btn_frame,
            text="②开始抢票",
            command=self.start_fast_grab,
            width=12,
            state=tk.DISABLED
        )
        self.grab_btn.pack(side=tk.LEFT, padx=(0, 2))

        # 停止按钮
        self.stop_grab_btn = ttk.Button(
            grab_btn_frame,
            text="⏹ 停止",
            command=self.stop_grab_ticket,
            width=12,
            state=tk.DISABLED
        )
        self.stop_grab_btn.pack(side=tk.LEFT)

        # 截图按钮
        screenshot_btn_frame = ttk.Frame(middle_frame)
        screenshot_btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.save_screenshot_btn = ttk.Button(
            screenshot_btn_frame,
            text="保存截图",
            command=lambda: self.save_screenshot(original=True),
            width=25
        )
        self.save_screenshot_btn.pack(fill=tk.X)

        # 实时诊断按钮
        diagnose_btn_frame = ttk.Frame(middle_frame)
        diagnose_btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.diagnose_btn = ttk.Button(
            diagnose_btn_frame,
            text="实时页面诊断",
            command=self.open_diagnose_window,
            width=25
        )
        self.diagnose_btn.pack(fill=tk.X)

        # AI决策建议
        suggest_frame = ttk.LabelFrame(middle_frame, text="AI决策建议", padding="10")
        suggest_frame.pack(fill=tk.BOTH, expand=True)

        self.suggest_text = scrolledtext.ScrolledText(suggest_frame, height=10, font=("微软雅黑", 9), wrap=tk.WORD)
        self.suggest_text.pack(fill=tk.BOTH, expand=True)

        # === 右侧：OCR识别结果 + 日志 ===
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)

        # 页面状态
        state_frame = ttk.LabelFrame(right_frame, text="页面状态", padding="10")
        state_frame.pack(fill=tk.X, pady=(0, 10))

        self.state_label = tk.Label(state_frame, text="未知", font=("微软雅黑", 14, "bold"), fg="#1890ff")
        self.state_label.pack()

        # OCR结果
        ocr_frame = ttk.LabelFrame(right_frame, text="OCR识别文字", padding="10")
        ocr_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.ocr_text = scrolledtext.ScrolledText(ocr_frame, height=15, font=("微软雅黑", 9), wrap=tk.WORD)
        self.ocr_text.pack(fill=tk.BOTH, expand=True)

        # 运行日志
        log_frame = ttk.LabelFrame(right_frame, text="运行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=("Consolas", 8), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        status_bar = tk.Frame(self.root, bg="#f0f0f0", height=30)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.bottom_status = tk.Label(status_bar, text="就绪 - 智能AI模式", bg="#f0f0f0", fg="#666", font=("微软雅黑", 9), anchor=tk.W)
        self.bottom_status.pack(fill=tk.X, padx=10, pady=5)

        # 绑定间隔更新
        interval_scale.config(command=lambda v: self.interval_label.config(text=f"{float(v):.1f}秒"))
        cleanup_scale.config(command=lambda v: self.cleanup_label.config(text=f"{int(float(v))}秒"))

    def log(self, message, level="INFO"):
        """添加日志 - 增强版"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]  # 精确到毫秒

        # 根据级别添加颜色标记和图标
        icons = {
            "INFO": "[INFO]",
            "OK": "[OK]",
            "SUCCESS": "[OK]",
            "WARN": "[WARN]",
            "WARNING": "[WARN]",
            "ERROR": "[ERROR]",
            "DEBUG": "[DEBUG]",
            "STEP": "[STEP]",
            "CLICK": "[CLICK]",
            "INPUT": "[INPUT]",
            "FIND": "[FIND]",
            "OCR": "[OCR]"
        }
        icon = icons.get(level, "•")

        # 格式化日志
        log_line = f"[{timestamp}] {icon:10s} {message}\n"

        # 添加到日志文本框
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)

        # 更新底部状态栏
        self.bottom_status.config(text=message[:100])

        # 同时输出到控制台（方便调试，使用try-except避免编码错误）
        try:
            print(log_line.strip())
        except UnicodeEncodeError:
            # Windows GBK环境下忽略编码错误
            pass

    def show_disclaimer_window(self):
        """显示法律免责声明悬浮窗"""
        # 创建置顶窗口
        disclaimer_win = tk.Toplevel(self.root)
        disclaimer_win.title("⚠️ 法律声明与使用须知")
        disclaimer_win.geometry("550x450")
        disclaimer_win.resizable(False, False)
        disclaimer_win.attributes('-topmost', True)  # 窗口置顶

        # 居中显示
        disclaimer_win.update_idletasks()
        x = (disclaimer_win.winfo_screenwidth() // 2) - (550 // 2)
        y = (disclaimer_win.winfo_screenheight() // 2) - (450 // 2)
        disclaimer_win.geometry(f"550x450+{x}+{y}")

        # 红色标题栏
        title_frame = tk.Frame(disclaimer_win, bg="#dc3545", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="⚠️  法律声明与使用须知  ⚠️",
            font=("微软雅黑", 16, "bold"),
            bg="#dc3545",
            fg="white"
        )
        title_label.pack(pady=15)

        # 主内容区（带滚动条）
        content_frame = tk.Frame(disclaimer_win, bg="white")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # 创建滚动文本框
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=("微软雅黑", 10),
            bg="#fffef5",
            relief=tk.FLAT,
            padx=15,
            pady=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        # 插入免责声明内容
        disclaimer_content = """🚨 重要提示

本项目为技术学习与研究项目，集成OCR识别和自动决策技术，仅供教学交流使用。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📜 使用声明

✅ 本项目完全开源免费，托管于GitHub平台
✅ 仅供个人学习、技术研究、教学演示使用

❌ 严禁用于任何违法犯罪活动
❌ 严禁商业倒卖门票、恶意抢票
❌ 严禁破坏平台公平秩序
❌ 严禁通过学习本项目进行任何违反法律法规的行为

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚖️ 法律责任

根据《中华人民共和国刑法》及相关司法解释：

• 开发者已明确声明本项目用途和使用限制
• 使用者的一切违法违规行为由使用者本人承担全部法律责任
• 与本项目开发者、贡献者无任何法律关系
• 使用本项目即视为同意本声明的所有条款

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 合法使用场景

✅ 学习Python自动化技术
✅ 研究Appium移动端自动化
✅ 研究OCR文字识别技术
✅ 教学演示自动化决策流程
✅ 技术竞赛、课程作业

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 特别说明

根据最高人民检察院关于"帮助信息网络犯罪活动罪"的司法解释，开发者已通过本声明履行告知义务，明确禁止将本项目用于违法用途。

任何违反本声明的使用行为，法律责任由使用者自行承担。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        text_widget.insert("1.0", disclaimer_content)
        text_widget.config(state=tk.DISABLED)  # 禁止编辑

        # 底部按钮区
        btn_frame = tk.Frame(disclaimer_win, bg="white")
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        # 同意并继续按钮
        agree_btn = tk.Button(
            btn_frame,
            text="✓ 我已阅读并同意遵守以上声明",
            font=("微软雅黑", 11, "bold"),
            bg="#28a745",
            fg="white",
            activebackground="#218838",
            activeforeground="white",
            relief=tk.FLAT,
            cursor="hand2",
            command=disclaimer_win.destroy,
            height=2
        )
        agree_btn.pack(fill=tk.X)

        # 聚焦到窗口
        disclaimer_win.focus_set()

    def load_config(self):
        """加载配置"""
        try:
            config_path = Path(__file__).parent / "last_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.port_var.set(config.get("adb_port", "59700"))
                self.keyword_var.set(config.get("keyword", "世界计划"))
                self.log("已加载配置", "INFO")

            # 提示默认显示模式
            self.log("默认启用等比缩放显示 - 720x1280缩放至450x800 (62.5%)", "INFO")
            self.log("鼠标坐标自动换算为真实设备坐标 (720x1280)，方便定位弹窗", "INFO")
        except Exception as e:
            self.log(f"加载配置失败: {e}", "WARN")

    def on_mouse_move(self, event):
        """鼠标移动事件 - 显示坐标（换算到真实设备坐标）"""
        if not self.current_screenshot or not self.scale_1to1.get():
            return

        try:
            if self.device_width > 0 and self.device_height > 0:
                # Canvas坐标（考虑滚动位置）
                canvas_x = self.canvas.canvasx(event.x)
                canvas_y = self.canvas.canvasy(event.y)

                # 换算到真实设备坐标（考虑缩放比例）
                scale_x = self.target_width / self.display_width    # 720/450 = 1.6
                scale_y = self.target_height / self.display_height  # 1280/800 = 1.6

                device_x = int(canvas_x * scale_x)
                device_y = int(canvas_y * scale_y)

                # 检查是否在有效范围内
                if 0 <= device_x < self.target_width and 0 <= device_y < self.target_height:
                    self.mouse_pos_label.config(text=f"坐标: ({device_x}, {device_y})")
                else:
                    self.mouse_pos_label.config(text="坐标: -")
        except:
            pass

    def on_canvas_click(self, event):
        """点击Canvas - 支持坐标选择和记录坐标"""
        # 优先处理：坐标选择模式
        if hasattr(self, 'coord_picking_mode') and self.coord_picking_mode:
            try:
                # 计算真实坐标（考虑缩放）
                canvas_x = self.canvas.canvasx(event.x)
                canvas_y = self.canvas.canvasy(event.y)

                if self.scale_1to1.get():
                    # 换算到真实设备坐标
                    real_x = int(canvas_x * self.target_width / self.display_width)
                    real_y = int(canvas_y * self.target_height / self.display_height)
                else:
                    real_x = int(canvas_x)
                    real_y = int(canvas_y)

                # 设置坐标
                coord_type = self.coord_picking_mode
                if coord_type == "session":
                    self.grab_coords["session_x"].set(real_x)
                    self.grab_coords["session_y"].set(real_y)
                    self.log(f"✓ 场次坐标已设置: ({real_x}, {real_y})", "SUCCESS")
                elif coord_type == "price":
                    self.grab_coords["price_x"].set(real_x)
                    self.grab_coords["price_y"].set(real_y)
                    self.log(f"✓ 票档坐标已设置: ({real_x}, {real_y})", "SUCCESS")
                elif coord_type == "buy":
                    self.grab_coords["buy_x"].set(real_x)
                    self.grab_coords["buy_y"].set(real_y)
                    self.log(f"✓ 购票按钮坐标已设置: ({real_x}, {real_y})", "SUCCESS")

                # 清除选择模式
                self.coord_picking_mode = None
                self.canvas.config(cursor="")
                return  # 坐标选择模式下直接返回
            except Exception as e:
                self.log(f"坐标选择错误: {e}", "ERROR")
                return

        # 原有功能：记录坐标
        if not self.current_screenshot or not self.scale_1to1.get():
            return

        try:
            if self.device_width > 0 and self.device_height > 0:
                # Canvas坐标（考虑滚动位置）
                canvas_x = self.canvas.canvasx(event.x)
                canvas_y = self.canvas.canvasy(event.y)

                # 换算到真实设备坐标
                scale_x = self.target_width / self.display_width   # 720/450 = 1.6
                scale_y = self.target_height / self.display_height # 1280/800 = 1.6

                device_x = int(canvas_x * scale_x)
                device_y = int(canvas_y * scale_y)

                if 0 <= device_x < self.target_width and 0 <= device_y < self.target_height:
                    self.log(f"点击坐标: ({device_x}, {device_y}) [真实设备坐标 720x1280]", "INFO")
                    self.log(f"显示坐标: ({int(canvas_x)}, {int(canvas_y)}) [缩放后 {self.display_width}x{self.display_height}]", "INFO")
        except Exception as e:
            self.log(f"点击处理错误: {e}", "ERROR")

    def on_scale_mode_change(self):
        """切换显示模式"""
        if self.scale_1to1.get():
            self.log("切换到等比缩放显示模式（真实坐标自动换算）", "INFO")
        else:
            self.log("切换到自适应显示模式", "INFO")

    def on_canvas_right_click(self, event):
        """Canvas右键菜单"""
        try:
            self.canvas_menu.post(event.x_root, event.y_root)
        except:
            pass

    def save_screenshot(self, original=True):
        """保存截图并复制路径到剪贴板"""
        if not self.current_screenshot:
            self.log("没有可用的截图", "WARN")
            return

        try:
            # 生成文件名（时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if original:
                filename = f"screenshot_original_{timestamp}.png"
                img_to_save = self.current_screenshot  # 原始720x1280
            else:
                filename = f"screenshot_display_{timestamp}.png"
                # 缩放到显示尺寸540x960
                img_to_save = self.current_screenshot.resize(
                    (self.display_width, self.display_height),
                    Image.Resampling.LANCZOS
                )

            # 保存路径
            save_path = self.screenshots_dir / filename
            img_to_save.save(save_path, "PNG")

            # 保存最新截图路径
            self.last_screenshot_path = str(save_path.absolute())

            # 复制路径到剪贴板
            pyperclip.copy(self.last_screenshot_path)

            # 日志提示
            size_str = f"{img_to_save.width}x{img_to_save.height}"
            self.log(f"[OK] 已保存截图 ({size_str}): {filename}", "OK")
            self.log(f"📋 路径已复制到剪贴板", "OK")

        except Exception as e:
            self.log(f"保存截图失败: {e}", "ERROR")

    def copy_latest_screenshot_path(self):
        """复制最新截图路径到剪贴板"""
        if not self.last_screenshot_path:
            self.log("没有可用的截图路径", "WARN")
            return

        try:
            pyperclip.copy(self.last_screenshot_path)
            self.log(f"📋 已复制路径: {Path(self.last_screenshot_path).name}", "OK")
        except Exception as e:
            self.log(f"复制路径失败: {e}", "ERROR")

    def cleanup_memory(self):
        """清理内存"""
        try:
            # 清空OCR缓存
            if hasattr(self.ai, 'ocr_cache'):
                self.ai.ocr_cache.clear()

            # 强制垃圾回收
            collected = gc.collect()

            self.log(f"内存清理完成 (回收 {collected} 个对象)", "INFO")
            self.last_cleanup_time = time.time()

        except Exception as e:
            self.log(f"内存清理错误: {e}", "WARN")

    def save_config(self):
        """保存配置"""
        try:
            # 完整配置（包含所有必需字段）
            config = {
                "server_url": "http://127.0.0.1:4723",
                "adb_port": self.port_var.get(),
                "keyword": self.keyword_var.get(),
                "users": [],
                "city": "北京",
                "date": "11.2",
                "price": "50",
                "price_index": 2,
                "if_commit_order": True
            }

            # 保存到config.jsonc
            config_path = Path(__file__).parent / "damai_appium" / "config.jsonc"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            # 保存到last_config.json（仅保存GUI相关字段）
            last_config_path = Path(__file__).parent / "last_config.json"
            last_config = {
                "adb_port": self.port_var.get(),
                "keyword": self.keyword_var.get(),
            }
            with open(last_config_path, 'w', encoding='utf-8') as f:
                json.dump(last_config, f, ensure_ascii=False, indent=2)

            self.log("配置已保存", "OK")
        except Exception as e:
            self.log(f"保存配置失败: {e}", "WARN")

    def update_screenshot_with_ocr(self):
        """更新截图并显示OCR结果"""
        if not self.bot or not self.bot.driver:
            return

        try:
            start_time = time.time()

            # 获取截图 (增加超时保护)
            try:
                screenshot_bytes = self.bot.driver.get_screenshot_as_png()
                screenshot = Image.open(io.BytesIO(screenshot_bytes))
            except Exception as ss_error:
                # 截图失败,可能是会话问题
                raise Exception(f"获取截图失败: {str(ss_error)}")

            # 保存原始截图和尺寸
            self.current_screenshot = screenshot
            img_width, img_height = screenshot.size

            # 更新设备分辨率（首次获取）
            if self.device_width == 0:
                self.device_width = img_width
                self.device_height = img_height
                self.resolution_label.config(
                    text=f"设备: {img_width}x{img_height} (显示: {self.display_width}x{self.display_height})",
                    foreground="green"
                )

            # OCR识别（如果启用）
            texts = []
            if self.use_ocr.get():
                texts = self.ai.analyze_screen(screenshot, use_ocr=True)

            # 在截图上绘制OCR识别框
            draw_image = screenshot.copy()
            if texts:
                draw = ImageDraw.Draw(draw_image)
                try:
                    font = ImageFont.truetype("msyh.ttc", 20)
                except:
                    font = None

                for t in texts:
                    box = t['box']
                    # 绘制边框
                    points = [(int(p[0]), int(p[1])) for p in box]
                    draw.polygon(points, outline='red', width=2)
                    # 绘制文字
                    if font:
                        draw.text((int(box[0][0]), int(box[0][1])-25), t['text'], fill='red', font=font)

            # 等比缩放到显示尺寸（450x800）- 强制缩放
            display_image = draw_image.resize(
                (self.display_width, self.display_height),
                Image.Resampling.LANCZOS
            )

            # 显示在Canvas上
            photo = ImageTk.PhotoImage(display_image)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.canvas.image = photo  # 保持引用防止被垃圾回收

            # 设置滚动区域
            self.canvas.config(scrollregion=(0, 0, display_image.width, display_image.height))

            # 更新OCR文字列表
            self.ocr_text.delete("1.0", tk.END)
            if texts:
                for i, t in enumerate(texts[:30], 1):  # 只显示前30个
                    conf_str = f"{t['confidence']:.2f}"
                    self.ocr_text.insert(tk.END, f"{i}. {t['text']} ({conf_str})\n")
            else:
                self.ocr_text.insert(tk.END, "未启用OCR或无识别结果\n")

            # 分析页面状态
            page_state = self.ai.detect_page_state(texts)
            self.ai.current_state = page_state
            self.state_label.config(text=page_state)

            # 获取AI建议
            actions = self.ai.suggest_action(page_state, texts, self.keyword_var.get())
            self.suggest_text.delete("1.0", tk.END)
            if actions:
                self.suggest_text.insert(tk.END, f"[{page_state}] AI建议:\n\n", "header")
                for i, action in enumerate(actions, 1):
                    action_type, target, pos, desc = action
                    self.suggest_text.insert(tk.END, f"{i}. {action_type} [{target}]\n")
                    self.suggest_text.insert(tk.END, f"   位置: {pos}\n")
                    self.suggest_text.insert(tk.END, f"   说明: {desc}\n\n")

                # 如果启用自动操作
                if self.auto_action.get() and actions:
                    # TODO: 自动执行第一个建议
                    pass
            else:
                self.suggest_text.insert(tk.END, f"[{page_state}] 暂无操作建议\n")

            self.suggest_text.tag_config("header", foreground="blue", font=("微软雅黑", 10, "bold"))

            # 计算FPS
            elapsed = time.time() - start_time
            fps = 1.0 / elapsed if elapsed > 0 else 0
            self.fps_label.config(text=f"FPS: {fps:.1f}")

            # 更新时间
            self.screenshot_time_label.config(text=f"更新: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

        except Exception as e:
            error_msg = str(e)

            # 忽略某些常见的非致命错误
            if "Invalid argument" in error_msg and "Errno 22" in error_msg:
                # 这通常是截图时的临时错误,不需要停止监控
                # 只记录警告,继续下一次更新
                return

            self.log(f"更新失败: {error_msg}", "ERROR")

            # 检测是否需要会话恢复
            need_recovery = (
                "instrumentation process is not running" in error_msg or
                "probably crashed" in error_msg or
                "WebDriver" in error_msg or
                "Session" in error_msg or
                "获取截图失败" in error_msg or
                "connection" in error_msg.lower()
            )

            if need_recovery:
                # 停止监控
                self.running = False

                # 使用统一的恢复机制
                if self._recover_session(error_msg):
                    # 恢复成功,可以继续监控
                    self.log("会话已恢复,可以重新开始监控", "OK")
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                else:
                    # 恢复失败,需要手动重连
                    self.log("自动恢复失败,请手动重新连接", "ERROR")
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)

    def monitor_loop(self):
        """监控循环 - 优化的错误处理"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.running:
            try:
                self.update_screenshot_with_ocr()

                # 成功更新,重置错误计数
                consecutive_errors = 0

                # 检查是否需要清理内存（从GUI读取用户设置的间隔）
                current_time = time.time()
                cleanup_interval = float(self.cleanup_var.get())
                if current_time - self.last_cleanup_time >= cleanup_interval:
                    self.cleanup_memory()

                interval = float(self.interval_var.get())
                time.sleep(interval)

            except Exception as e:
                error_msg = str(e)
                consecutive_errors += 1

                # 忽略临时性错误
                if "Invalid argument" in error_msg or "Errno 22" in error_msg:
                    # 临时错误,等待后重试
                    time.sleep(0.5)
                    continue

                self.log(f"监控错误 ({consecutive_errors}/{max_consecutive_errors}): {error_msg}", "WARN")

                # 连续错误过多,停止监控
                if consecutive_errors >= max_consecutive_errors:
                    self.log(f"连续错误{max_consecutive_errors}次,停止监控", "ERROR")
                    self.running = False
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    break

                time.sleep(1)

    def show_environment_check(self):
        """显示环境检测窗口"""
        # 创建弹出窗口
        env_window = tk.Toplevel(self.root)
        env_window.title("环境诊断")
        env_window.geometry("700x600")
        env_window.transient(self.root)

        # 标题
        title_label = tk.Label(
            env_window,
            text="🔧 环境诊断与检测",
            font=("微软雅黑", 14, "bold"),
            bg="#1890ff",
            fg="white",
            pady=15
        )
        title_label.pack(fill=tk.X)

        # 主框架
        main_frame = ttk.Frame(env_window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 检测结果文本框
        result_frame = ttk.LabelFrame(main_frame, text="检测结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=20
        )
        result_text.pack(fill=tk.BOTH, expand=True)

        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        check_btn = ttk.Button(
            btn_frame,
            text="开始检测",
            command=lambda: self.run_environment_check(result_text),
            width=15
        )
        check_btn.pack(side=tk.LEFT, padx=(0, 10))

        fix_btn = ttk.Button(
            btn_frame,
            text="🔨 尝试修复",
            command=lambda: self.fix_environment_issues(result_text),
            width=15
        )
        fix_btn.pack(side=tk.LEFT, padx=(0, 10))

        close_btn = ttk.Button(
            btn_frame,
            text="关闭",
            command=env_window.destroy,
            width=10
        )
        close_btn.pack(side=tk.RIGHT)

        # 自动开始检测
        env_window.after(500, lambda: self.run_environment_check(result_text))

    def run_environment_check(self, result_text):
        """执行环境检测"""
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "=" * 70 + "\n")
        result_text.insert(tk.END, "开始环境检测...\n")
        result_text.insert(tk.END, "=" * 70 + "\n\n")

        def do_check():
            try:
                checker = EnvironmentChecker()
                results = checker.check_all()

                # 状态映射
                status_symbols = {
                    'ok': '[OK]',
                    'warning': '[WARN]',
                    'error': '[ERROR]'
                }

                def update_ui():
                    for name, result in results.items():
                        symbol = status_symbols.get(result.status, '[?]')
                        result_text.insert(tk.END, f"\n{symbol} [{name.upper()}]\n")
                        result_text.insert(tk.END, f"  状态: {result.status.upper()}\n")
                        result_text.insert(tk.END, f"  信息: {result.message}\n")

                        if result.details:
                            result_text.insert(tk.END, f"  详情:\n")
                            for line in result.details.split('\n'):
                                result_text.insert(tk.END, f"    {line}\n")

                        if result.fix_available:
                            result_text.insert(tk.END, f"  修复建议: {result.fix_action}\n")

                        result_text.insert(tk.END, "\n")

                    # 总结
                    result_text.insert(tk.END, "=" * 70 + "\n")
                    result_text.insert(tk.END, "检测完成！\n")

                    error_count = sum(1 for r in results.values() if r.status == 'error')
                    warning_count = sum(1 for r in results.values() if r.status == 'warning')
                    ok_count = sum(1 for r in results.values() if r.status == 'ok')

                    result_text.insert(tk.END, f"正常: {ok_count}  警告: {warning_count}  错误: {error_count}\n")
                    result_text.insert(tk.END, "=" * 70 + "\n")

                    # 滚动到顶部
                    result_text.see(1.0)

                # 使用after在主线程中更新UI
                self.root.after(0, update_ui)

            except Exception as e:
                def show_error():
                    result_text.insert(tk.END, f"\n[ERROR] 检测过程出错: {str(e)}\n")
                self.root.after(0, show_error)

        threading.Thread(target=do_check, daemon=True).start()

    def fix_environment_issues(self, result_text):
        """尝试修复环境问题"""
        result_text.insert(tk.END, "\n" + "=" * 70 + "\n")
        result_text.insert(tk.END, "开始自动修复...\n")
        result_text.insert(tk.END, "=" * 70 + "\n\n")

        def do_fix():
            try:
                checker = EnvironmentChecker()
                fixer = EnvironmentFixer(checker.adb_path)

                # 1. 检查ADB设备连接
                result_text.insert(tk.END, "[1/3] 检查ADB设备连接...\n")
                device_result, devices = checker.check_adb_device()

                if not devices:
                    result_text.insert(tk.END, "  未检测到设备，尝试自动扫描端口...\n")
                    found_devices = fixer.scan_common_ports()

                    if found_devices:
                        result_text.insert(tk.END, f"  [OK] 成功连接到: {found_devices[0]}\n")
                        # 更新GUI端口显示
                        port = found_devices[0].split(':')[1]
                        self.port_var.set(port)
                    else:
                        result_text.insert(tk.END, "  ❌ 未找到可用设备\n")
                else:
                    result_text.insert(tk.END, f"  [OK] 设备已连接: {devices[0]}\n")

                # 2. 检查Appium服务
                result_text.insert(tk.END, "\n[2/3] 检查Appium服务...\n")
                appium_result = checker.check_appium_service()

                if appium_result.status == 'error':
                    result_text.insert(tk.END, "  Appium未运行，尝试启动...\n")
                    success, message = fixer.start_appium(background=True)

                    if success:
                        result_text.insert(tk.END, f"  [OK] {message}\n")
                    else:
                        result_text.insert(tk.END, f"  [INFO] {message}\n")
                        result_text.insert(tk.END, "  [INFO] 请手动执行: appium --address 127.0.0.1 --port 4723 --allow-cors\n")
                else:
                    result_text.insert(tk.END, "  [OK] Appium服务运行正常\n")

                # 3. 检查UiAutomator2
                result_text.insert(tk.END, "\n[3/3] 检查UiAutomator2 Server...\n")
                if devices:
                    ui2_result = checker.check_uiautomator2(devices[0])

                    if ui2_result.status != 'ok':
                        result_text.insert(tk.END, "  [WARN] UiAutomator2未完全安装\n")
                        result_text.insert(tk.END, "  [INFO] 将在首次连接时由Appium自动安装\n")
                    else:
                        result_text.insert(tk.END, "  [OK] UiAutomator2已安装\n")

                result_text.insert(tk.END, "\n" + "=" * 70 + "\n")
                result_text.insert(tk.END, "修复完成！\n")
                result_text.insert(tk.END, "建议重新运行环境检测确认状态\n")
                result_text.insert(tk.END, "=" * 70 + "\n")

            except Exception as e:
                result_text.insert(tk.END, f"\n❌ 修复过程出错: {str(e)}\n")

        threading.Thread(target=do_fix, daemon=True).start()

    def auto_fix_environment(self):
        """一键自动修复环境（主窗口调用） - 增强版集成WebDriver修复"""
        self.log("开始自动修复环境...", "INFO")
        self.log("="*60, "STEP")

        def do_auto_fix():
            try:
                checker = EnvironmentChecker()
                fixer = EnvironmentFixer(checker.adb_path)

                # 使用新的自动修复WebDriver功能
                self.log("[自动修复] 执行完整的环境诊断和修复...", "STEP")
                success, msg, results = fixer.auto_fix_webdriver()

                # 显示详细结果
                self.log("="*60, "STEP")
                self.log("[修复结果]", "STEP")

                if results.get('adb_devices'):
                    self.log(f"  ADB设备: {results['adb_devices']}", "INFO")

                if results.get('selected_port'):
                    port = results['selected_port']
                    self.port_var.set(port)
                    self.log(f"  已选择端口: {port}", "INFO")

                if results.get('config_sync'):
                    self.log(f"  配置同步: {results['config_sync']}", "INFO")

                if results.get('appium_service'):
                    self.log(f"  Appium服务: {results['appium_service']}", "INFO")

                if results.get('webdriver_test'):
                    test_msg = results['webdriver_test'][:200]
                    self.log(f"  WebDriver测试: {test_msg}", "INFO")

                self.log("="*60, "STEP")

                if success:
                    self.log(f"[成功] {msg}", "SUCCESS")
                    self.log("提示: 现在可以直接点击'连接设备'按钮", "OK")
                else:
                    self.log(f"[警告] {msg}", "WARN")
                    self.log("建议: 请查看上方日志,按提示手动修复", "WARN")

            except Exception as e:
                self.log(f"自动修复失败: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        threading.Thread(target=do_auto_fix, daemon=True).start()

    def auto_detect_port(self):
        """自动检测ADB端口"""
        self.log("正在自动检测ADB端口...", "INFO")
        self.auto_detect_btn.config(state=tk.DISABLED)

        def do_detect():
            try:
                import subprocess

                # 获取所有已连接的ADB设备
                result = subprocess.run(f'"{ADB_EXE}" devices', capture_output=True, text=True, shell=True, timeout=5)
                lines = result.stdout.strip().split('\n')[1:]  # 跳过第一行标题

                detected_devices = []
                for line in lines:
                    if line.strip() and '\t' in line:
                        device_id = line.split('\t')[0].strip()
                        status = line.split('\t')[1].strip()

                        # 只记录正常连接的设备
                        if status == "device" and "127.0.0.1:" in device_id:
                            port = device_id.split(':')[1]
                            detected_devices.append(port)

                if detected_devices:
                    # 使用第一个检测到的端口
                    port = detected_devices[0]
                    self.port_var.set(port)
                    self.log(f"[OK] 自动检测成功！找到端口: {port}", "OK")

                    if len(detected_devices) > 1:
                        self.log(f"提示: 还检测到其他端口: {', '.join(detected_devices[1:])}", "INFO")
                else:
                    self.log("❌ 未检测到任何ADB设备", "WARN")
                    self.log("请检查:", "WARN")
                    self.log("  1. 模拟器/云手机是否已启动", "WARN")
                    self.log("  2. ADB是否正确连接", "WARN")
                    self.log("  3. 尝试手动输入端口号", "WARN")

            except Exception as e:
                self.log(f"自动检测失败: {e}", "ERROR")
            finally:
                self.auto_detect_btn.config(state=tk.NORMAL)

        threading.Thread(target=do_detect, daemon=True).start()

    def connect_device(self):
        """连接设备（增强版 - 自动检测和修复连接）"""
        self.log("正在连接设备...", "INFO")
        self.status_label.config(text="● 连接中...", fg="orange")
        self.connect_btn.config(state=tk.DISABLED)

        def do_connect():
            import subprocess  # 在函数开头导入，避免 UnboundLocalError
            import time  # 确保导入所有需要的模块

            try:
                # 步骤0: 清理旧连接(如果存在)
                if self.bot and self.bot.driver:
                    try:
                        self.log("检测到旧连接,正在清理...", "INFO")
                        self.bot.driver.quit()
                        self.log("旧连接已清理", "OK")
                        time.sleep(1)  # 等待完全释放
                    except Exception as e:
                        self.log(f"清理旧连接警告: {e}", "WARN")
                self.bot = None

                # 步骤1: 使用ConnectionAutoFixer自动检测和修复连接
                port = self.port_var.get()
                self.log("="*60, "STEP")
                self.log("[自动连接修复] 开始检测和修复连接状态", "STEP")
                self.log("="*60, "STEP")

                # 创建日志适配器（将GUI的log方法适配为logger接口）
                class GUILogger:
                    def __init__(self, log_func):
                        self.log = log_func

                    def info(self, msg):
                        self.log(msg, 'INFO')

                    def warning(self, msg):
                        self.log(msg, 'WARN')

                    def error(self, msg):
                        self.log(msg, 'ERROR')

                    def success(self, msg):
                        self.log(msg, 'SUCCESS')

                # 创建连接修复器
                gui_logger = GUILogger(self.log)
                connection_fixer = ConnectionAutoFixer(
                    logger=gui_logger,
                    adb_port=port
                )

                # 执行自动修复（禁用自动扫描 - 只连接用户指定的端口）
                fix_success = connection_fixer.auto_fix_all(auto_scan=False)

                if not fix_success:
                    self.log("="*60, "ERROR")
                    self.log("✗ 连接自动修复失败", "ERROR")
                    self.log("", "ERROR")
                    self.log("可能的原因:", "ERROR")
                    self.log("  1. Appium服务未安装或未启动", "ERROR")
                    self.log("     解决：运行 start_appium.bat 或手动启动 Appium", "ERROR")
                    self.log("", "ERROR")
                    self.log("  2. 红手指云手机离线或端口号错误", "ERROR")
                    self.log(f"     当前端口: {port}", "ERROR")
                    self.log("     解决：打开红手指客户端，查看云手机状态和实际端口号", "ERROR")
                    self.log("", "ERROR")
                    self.log("  3. ADB连接被拒绝", "ERROR")
                    self.log("     解决：在云手机中开启USB调试/ADB调试权限", "ERROR")
                    self.log("", "ERROR")
                    self.log("  4. 网络连接问题", "ERROR")
                    self.log("     解决：检查网络连接，尝试重启红手指客户端", "ERROR")
                    self.log("="*60, "ERROR")
                    raise Exception("连接自动修复失败 - 请查看上述解决方案")

                # 如果端口被自动修改，更新GUI显示
                if connection_fixer.adb_port != port:
                    new_port = connection_fixer.adb_port
                    self.log(f"✓ 端口已自动更新: {port} → {new_port}", "SUCCESS")
                    self.port_var.set(new_port)
                    port = new_port

                # 步骤2: 保存配置(确保adb_port同步到config.jsonc)
                self.log("="*60, "STEP")
                self.log("[步骤2/3] 保存配置...", "STEP")
                self.log(f"  - 同步ADB端口: {port}", "INFO")
                self.save_config()
                self.log("[OK] 配置已保存(adb_port已同步到config.jsonc)", "SUCCESS")

                # 步骤3: 初始化Appium连接（增加超时和异常处理）
                # subprocess 已在函数开头导入

                # 再次验证ADB连接（确保设备就绪，添加重试机制）
                self.log("="*60, "STEP")
                self.log(f"[步骤3/3] 创建WebDriver会话...", "STEP")
                self.log(f"  - 目标设备: 127.0.0.1:{port}", "INFO")

                device_address = f"127.0.0.1:{port}"

                # 添加设备验证重试机制（最多3次，每次间隔1秒）
                device_found = False
                for verify_attempt in range(3):
                    if verify_attempt > 0:
                        self.log(f"  - 设备验证重试 {verify_attempt + 1}/3...", "DEBUG")
                        time.sleep(1)

                    try:
                        verify_result = subprocess.run(
                            f'"{ADB_EXE}" devices',
                            capture_output=True,
                            text=True,
                            shell=True,
                            timeout=5
                        )

                        if verify_result.returncode == 0 and verify_result.stdout:
                            for line in verify_result.stdout.splitlines():
                                if device_address in line and "device" in line and "offline" not in line:
                                    device_found = True
                                    break

                        if device_found:
                            break
                    except Exception as e:
                        self.log(f"  - 设备验证异常: {e}", "WARN")
                        continue

                if not device_found:
                    raise Exception(f"ADB设备验证失败: {device_address} 未找到或离线")

                self.log("  - ADB设备验证通过", "INFO")
                self.log("  - 正在创建WebDriver会话(DamaiBot将从config.jsonc读取配置)...", "INFO")

                start_time = time.time()

                # 添加超时和重试机制
                max_retries = 3
                retry_delay = 5

                for retry_count in range(max_retries):
                    if retry_count > 0:
                        self.log(f"  第 {retry_count + 1}/{max_retries} 次尝试...", "INFO")
                        time.sleep(retry_delay)

                    bot_creation_result = [None, None]  # [bot实例, 错误信息]

                    def create_bot():
                        try:
                            bot_creation_result[0] = DamaiBot()
                        except Exception as e:
                            bot_creation_result[1] = str(e)
                            import traceback
                            bot_creation_result.append(traceback.format_exc())

                    import threading
                    bot_thread = threading.Thread(target=create_bot, daemon=True)
                    bot_thread.start()

                    # 等待最多60秒
                    timeout_seconds = 60
                    self.log(f"  等待WebDriver会话创建（超时: {timeout_seconds}秒）...", "DEBUG")
                    bot_thread.join(timeout=timeout_seconds)

                    if bot_thread.is_alive():
                        self.log(f"  WebDriver会话创建超时（{timeout_seconds}秒）", "WARN")
                        if retry_count < max_retries - 1:
                            self.log(f"  将在{retry_delay}秒后重试...", "INFO")
                            continue
                        else:
                            self.log("  所有重试均超时，请检查Appium服务和设备状态", "ERROR")
                            raise Exception("WebDriver会话创建超时")

                    if bot_creation_result[1]:
                        error_msg = bot_creation_result[1]
                        self.log(f"  创建失败: {error_msg[:200]}", "WARN")
                        if len(bot_creation_result) > 2:
                            self.log(f"  详细错误: {bot_creation_result[2][:500]}", "DEBUG")

                        if retry_count < max_retries - 1:
                            self.log(f"  将在{retry_delay}秒后重试...", "INFO")
                            continue
                        else:
                            self.log("  所有重试均失败", "ERROR")
                            raise Exception(f"创建失败: {error_msg}")

                    if not bot_creation_result[0]:
                        self.log("  创建失败：未知错误", "WARN")
                        if retry_count < max_retries - 1:
                            self.log(f"  将在{retry_delay}秒后重试...", "INFO")
                            continue
                        else:
                            raise Exception("创建失败：未知错误")

                    # 成功创建
                    self.bot = bot_creation_result[0]
                    break

                connect_time = time.time() - start_time

                self.status_label.config(text="● 已连接", fg="green")
                self.log(f"[OK] Appium连接成功！(耗时: {connect_time:.2f}秒)", "SUCCESS")
                self.log(f"  - Session ID: {self.bot.driver.session_id[:16]}...", "DEBUG")

                # 重置设备分辨率（将在第一次截图时获取）
                self.device_width = 0
                self.device_height = 0

                # 预加载OCR
                self.log("="*50, "STEP")
                self.log("OCR引擎初始化中...", "INFO")
                try:
                    ocr = get_ocr()
                    if ocr:
                        self.log("√ OCR引擎就绪", "OK")
                        self.log(f"  OCR实例: {type(ocr).__name__}", "DEBUG")
                    else:
                        self.log("! OCR初始化返回None", "WARN")
                except Exception as e:
                    self.log(f"X OCR初始化失败: {e}", "ERROR")
                    # traceback输出也可能有编码问题,捕获错误
                    try:
                        import traceback
                        traceback.print_exc()
                    except UnicodeEncodeError:
                        pass  # 忽略traceback的编码错误
                self.log("="*50, "STEP")

                # 初始化弹窗处理器 - 根据用户配置决定是否启用
                if self.enable_popup_detection.get():
                    self.log("初始化并行弹窗处理器...", "INFO")
                    try:
                        self.popup_handler = ParallelPopupHandler(self.bot.driver, log_func=self.log)
                        self.popup_handler.start(check_interval=2.0)
                        self.log("√ 弹窗处理器已启动(后台运行)", "OK")
                    except Exception as e:
                        self.log(f"! 弹窗处理器启动失败: {e}", "WARN")
                else:
                    self.log("⚠️ 后台弹窗处理器已禁用（在AI配置中可启用）", "WARN")

                # 更新按钮状态
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.DISABLED)
                self.start_btn.config(state=tk.NORMAL)
                self.grab_btn.config(state=tk.NORMAL)  # 启用抢票按钮
                self.log("[OK] 抢票按钮已启用", "OK")

                # 自动启动截图监控
                self.log("="*60, "STEP")
                self.log("正在启动截图监控...", "INFO")
                self.running = True
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.log("[OK] 截图监控已自动启动", "SUCCESS")

            except subprocess.TimeoutExpired:
                self.log("ADB命令执行超时", "ERROR")
                self.status_label.config(text="● 连接失败", fg="red")
                self.connect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.NORMAL)
            except Exception as e:
                error_str = str(e)
                self.log(f"连接失败: {error_str}", "ERROR")

                # 检测UiAutomator2服务器崩溃并自动清理
                if "instrumentation process cannot be initialized" in error_str:
                    self.log("! 检测到UiAutomator2服务器崩溃", "WARN")
                    self.log("正在自动清理并准备重试...", "INFO")

                    try:
                        # DamaiBot已经清理了服务器，等待一下
                        time.sleep(1)
                        self.log("UiAutomator2服务器已清理完成", "OK")
                        self.log("提示: 请再次点击'连接设备'按钮重试", "INFO")
                        self.log("如果持续失败，请尝试:", "INFO")
                        self.log("  1. 在红手指中重启大麦App", "INFO")
                        self.log("  2. 检查设备是否响应正常", "INFO")
                    except Exception as cleanup_err:
                        self.log(f"清理过程出错: {cleanup_err}", "WARN")

                # 提供更友好的错误提示
                elif "Could not find a connected Android device" in error_str:
                    self.log("原因: Appium找不到Android设备", "ERROR")
                    self.log(f"解决方法: 请先确保 adb connect 127.0.0.1:{port} 成功", "ERROR")
                elif "ADB连接失败" not in error_str:
                    self.log("可能原因:", "ERROR")
                    self.log("  1. ADB连接未建立", "ERROR")
                    self.log("  2. Appium服务未启动", "ERROR")
                    self.log("  3. 设备/模拟器未运行", "ERROR")

                self.status_label.config(text="● 连接失败", fg="red")
                self.connect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.NORMAL)

        threading.Thread(target=do_connect, daemon=True).start()

    def disconnect_device(self):
        """断开连接"""
        self.log("正在断开连接...", "INFO")

        # 停止监控
        if self.running:
            self.running = False
            time.sleep(0.5)

        # 停止弹窗处理器
        if self.popup_handler:
            try:
                self.popup_handler.stop()
                self.log("弹窗处理器已停止", "OK")
            except Exception as e:
                self.log(f"停止弹窗处理器失败: {e}", "WARN")
            self.popup_handler = None

        # 关闭连接 - 强化清理逻辑
        if self.bot and self.bot.driver:
            try:
                self.log("正在关闭WebDriver会话...", "INFO")
                self.bot.driver.quit()
                self.log("WebDriver会话已关闭", "OK")
            except Exception as e:
                self.log(f"关闭WebDriver警告: {e}", "WARN")
        self.bot = None

        # 重置设备信息
        self.device_width = 0
        self.device_height = 0
        self.current_screenshot = None
        self.resolution_label.config(text="设备: 未连接", foreground="gray")
        self.mouse_pos_label.config(text="坐标: -")

        # 更新状态
        self.status_label.config(text="● 未连接", fg="gray")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.reconnect_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("已断开连接", "INFO")

    def refresh_devices(self):
        """刷新设备列表"""
        try:
            # 自动检测新设备
            new_devices = self.device_manager.auto_detect_devices()
            if new_devices:
                self.log(f"检测到 {len(new_devices)} 个新设备", "INFO")

            # 更新下拉框
            devices = self.device_manager.list_devices()
            device_list = ["手动输入"] + [f"{d.name} ({d.address})" for d in devices]
            self.device_combo['values'] = device_list

            self.log(f"已刷新设备列表 ({len(devices)}个设备)", "INFO")
        except Exception as e:
            self.log(f"刷新设备列表失败: {e}", "ERROR")

    def on_device_selected(self, event=None):
        """设备选择事件"""
        selected = self.device_var.get()
        if selected == "手动输入":
            return

        # 解析设备地址
        try:
            # 格式: "设备名 (127.0.0.1:58358)"
            address = selected.split("(")[1].split(")")[0]
            # 提取端口号
            port = address.split(":")[1]
            self.port_var.set(port)
            self.log(f"已选择设备: {selected}, 端口: {port}", "INFO")
        except Exception as e:
            self.log(f"解析设备地址失败: {e}", "ERROR")

    def add_device_dialog(self):
        """添加设备对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加红手指设备")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # 内容框架
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 设备名称
        ttk.Label(frame, text="设备名称:", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(0, 5))
        name_var = tk.StringVar(value="红手指1")
        name_entry = ttk.Entry(frame, textvariable=name_var, font=("微软雅黑", 10))
        name_entry.pack(fill=tk.X, pady=(0, 15))

        # ADB地址
        ttk.Label(frame, text="ADB地址 (格式: IP:端口):", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(0, 5))
        address_var = tk.StringVar(value="127.0.0.1:58358")
        address_entry = ttk.Entry(frame, textvariable=address_var, font=("微软雅黑", 10))
        address_entry.pack(fill=tk.X, pady=(0, 15))

        # 设备类型
        ttk.Label(frame, text="设备类型:", font=("微软雅黑", 10)).pack(anchor=tk.W, pady=(0, 5))
        type_var = tk.StringVar(value="hongshouzhi")
        type_combo = ttk.Combobox(frame, textvariable=type_var, values=["hongshouzhi", "emulator", "local", "cloud"], state="readonly")
        type_combo.pack(fill=tk.X, pady=(0, 20))

        # 按钮区域
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        def add_device():
            name = name_var.get().strip()
            address = address_var.get().strip()
            device_type = type_var.get()

            if not name:
                tk.messagebox.showerror("错误", "设备名称不能为空")
                return

            if not address or ":" not in address:
                tk.messagebox.showerror("错误", "ADB地址格式错误\n正确格式: IP:端口\n例如: 127.0.0.1:58358")
                return

            try:
                self.device_manager.add_device(name, address, device_type)
                self.log(f"已添加设备: {name} ({address})", "SUCCESS")
                self.refresh_devices()
                dialog.destroy()
                tk.messagebox.showinfo("成功", f"设备 '{name}' 已添加")
            except ValueError as e:
                tk.messagebox.showerror("错误", str(e))

        ttk.Button(btn_frame, text="添加", command=add_device, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT)

    def start_monitoring(self):
        """开始监控"""
        if not self.bot:
            self.log("请先连接设备", "WARN")
            return

        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log("开始监控...", "INFO")

        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("监控已停止", "INFO")

    def stop_grab_ticket(self):
        """停止抢票"""
        self.grabbing = False
        self.grab_btn.config(state=tk.NORMAL)
        self.stop_grab_btn.config(state=tk.DISABLED)
        self.log("="*60, "WARN")
        self.log("抢票已被用户停止", "WARN")
        self.log("="*60, "WARN")

    def start_grab_ticket(self):
        """开始抢票流程"""
        if not self.bot or not self.bot.driver:
            self.log("请先连接设备!", "ERROR")
            return

        self.log("="*60, "STEP")
        self.log("开始抢票流程", "STEP")
        self.log("="*60, "STEP")

        # 禁用抢票按钮,启用停止按钮
        self.grab_btn.config(state=tk.DISABLED)
        self.stop_grab_btn.config(state=tk.NORMAL)
        self.grabbing = True

        def do_grab():
            try:
                city = self.city_var.get()
                show_name = self.show_name_var.get()
                keyword = self.keyword_var.get()

                self.log(f"目标: {city} - {show_name}", "INFO")
                self.log(f"搜索关键词: {keyword}", "INFO")

                driver = self.bot.driver

                # 步骤0: 重启大麦App并等待进入首页
                self.log("="*60, "STEP")
                self.log("[步骤0] 重启大麦App,等待进入首页", "STEP")
                step0_start = self.performance_monitor.start_step("重启App")

                # 第一步: 强制关闭大麦App
                self.log("[1/3] 强制关闭大麦App...", "INFO")
                try:
                    driver.terminate_app("cn.damai")
                    self.log("  √ 大麦App已关闭", "SUCCESS")
                    time.sleep(1)  # 等待App完全关闭
                except Exception as e:
                    self.log(f"  ! 关闭App失败(可能未运行): {e}", "DEBUG")

                # 第二步: 启动大麦App
                self.log("[2/3] 启动大麦App...", "INFO")
                try:
                    driver.activate_app("cn.damai")
                    self.log("  √ 大麦App已启动", "SUCCESS")
                except Exception as e:
                    self.log(f"  ! 启动失败: {e}", "WARN")
                    # 尝试通过检查状态来启动
                    success, page_state, texts = self._ensure_app_running(driver)
                    if not success:
                        self.log("! App状态检测未通过,尝试启动App...", "WARN")

                # 第三步: 等待App完全加载
                self.log("[3/3] 等待大麦App完全加载...", "INFO")
                time.sleep(5)
                self.log("[OK] 大麦App重启完成,已进入首页", "SUCCESS")
                self.performance_monitor.end_step("启动App", step0_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤1: 处理首页弹窗
                self.log("="*60, "STEP")
                self.log("[步骤1] 检查并处理首页弹窗", "STEP")
                step1_start = self.performance_monitor.start_step("处理首页弹窗")

                # 简化弹窗检测: 检查是否有弹窗关键词
                popup_success = True
                try:
                    page_source = driver.page_source
                    popup_keywords = ['关闭', '取消', '知道了', '跳过', '稍后', '开启']
                    has_popup = any(keyword in page_source for keyword in popup_keywords)

                    # 根据配置决定是否检测弹窗
                    enable_popup = getattr(self, 'enable_popup_detection', False)
                    if enable_popup and has_popup:
                        self.log("检测到弹窗，尝试关闭", "INFO")
                        # 尝试多种关闭方式
                        # 方式1: 固定坐标(右上角)
                        try:
                            driver.execute_script("mobile: clickGesture", {"x": 650, "y": 120})
                            self.log("[OK] 使用坐标关闭弹窗成功: (650, 120)", "SUCCESS")
                            time.sleep(1)
                        except Exception as e:
                            self.log(f"坐标关闭失败,尝试其他方式: {e}", "DEBUG")
                            # 方式2: 调用通用弹窗处理
                            popup_result = self._dismiss_popups(driver)
                            if popup_result is False:
                                self.log("[INFO] 检测到功能页面，非弹窗，继续流程", "INFO")
                    else:
                        if not enable_popup:
                            self.log("[OK] 首页弹窗检测已禁用,直接进入流程", "SUCCESS")
                        else:
                            self.log("[OK] 首页无弹窗,直接进入流程", "SUCCESS")
                except Exception as e:
                    self.log(f"弹窗检测异常: {e}", "WARN")
                    popup_success = False

                self.performance_monitor.end_step("处理首页弹窗", step1_start, success=popup_success)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤2: 检查/切换城市
                self.log("="*60, "STEP")
                self.log("[步骤2] 检查并切换城市", "STEP")
                step2_start = self.performance_monitor.start_step("城市切换")

                # 切换城市（_check_and_switch_city会负责点击城市选择器）
                city_success = self._check_and_switch_city(driver, city)

                # 验证: 城市切换后检查弹窗
                self._check_and_handle_popup(driver)
                time.sleep(0.5)
                self.performance_monitor.end_step("城市切换", step2_start, success=city_success)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤3: 点击搜索框
                self.log("="*60, "STEP")
                self.log("[步骤3] 点击搜索框", "STEP")
                step3_start = self.performance_monitor.start_step("进入搜索")
                self._goto_search_page(driver)

                # 检查弹窗
                self._check_and_handle_popup(driver)
                self.performance_monitor.end_step("进入搜索", step3_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤4: 输入关键词并搜索
                self.log("="*60, "STEP")
                self.log("[步骤4] 输入关键词并搜索", "STEP")
                step4_start = self.performance_monitor.start_step("搜索演出")
                self._input_and_search(driver, keyword)

                # ✨ 优化: 等待搜索结果加载 (2秒 → 1秒)
                time.sleep(1)
                self.log("[OK] 搜索完成,等待结果加载", "OK")
                self.performance_monitor.end_step("搜索演出", step4_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤5: 点击第一个搜索结果(进入演出列表页)
                self.log("="*60, "STEP")
                self.log("[步骤5] 点击第一个搜索结果", "STEP")
                step5_start = self.performance_monitor.start_step("进入列表页")
                self._click_first_search_result(driver)

                # ✨ 优化: 等待页面加载 (2秒 → 1秒)
                time.sleep(1)
                self._check_and_handle_popup(driver)
                self.performance_monitor.end_step("进入列表页", step5_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤6: 在演出列表页点击演出项
                self.log("="*60, "STEP")
                self.log("[步骤6] 点击演出项", "STEP")
                step6_start = self.performance_monitor.start_step("进入详情页")
                self._click_first_show_in_list(driver, show_name)

                # ✨ 优化: 等待详情页加载 (2秒 → 1秒)
                time.sleep(1)
                self._check_and_handle_popup(driver)
                self.log("[OK] 已进入演出详情页", "OK")
                self.performance_monitor.end_step("进入详情页", step6_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤6.5: 点击进入票档和场次选择页面 (手动验证坐标)
                self.log("="*60, "STEP")
                self.log("[步骤6.5] 点击票档和场次选择入口", "STEP")
                step6_5_start = self.performance_monitor.start_step("进入票档选择")
                self._click_ticket_entry(driver)
                time.sleep(1)
                self._check_and_handle_popup(driver)
                self.log("[OK] 已进入票档和场次选择页面", "OK")
                self.performance_monitor.end_step("进入票档选择", step6_5_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤7: 点击立即购票
                self.log("="*60, "STEP")
                self.log("[步骤7] 点击立即购票", "STEP")
                step7_start = self.performance_monitor.start_step("点击购票")
                self._click_buy_button(driver)

                # ✨ 优化: 等待进入场次/票档页面 (3秒 → 1.5秒)
                self.log("提示: 如果出现滑块验证,请手动完成", "WARNING")
                time.sleep(3)  # 等待滑块验证 + 页面加载

                # 检查弹窗（滑块验证后可能出现弹窗）
                self._check_and_handle_popup(driver)
                self.performance_monitor.end_step("点击购票", step7_start, success=True)

                # 检查是否被停止
                if not self.grabbing:
                    self.log("="*60, "WARN")
                    self.log("抢票已被用户停止", "WARN")
                    self.log("="*60, "WARN")
                    return

                # 步骤8: 选择场次和票档
                self.log("="*60, "STEP")
                self.log("[步骤8] 选择场次和票档 (快速模式)", "STEP")
                step8_start = self.performance_monitor.start_step("选择场次票档")
                session_success = self._select_session_and_price(driver)

                if session_success:
                    self.log("[OK] 场次/票档选择成功", "OK")
                    self.performance_monitor.end_step("选择场次票档", step8_start, success=True)

                    # 检查是否被停止
                    if not self.grabbing:
                        self.log("="*60, "WARN")
                        self.log("抢票已被用户停止", "WARN")
                        self.log("="*60, "WARN")
                        return

                    # 步骤9: 排队重试
                    self.log("="*60, "STEP")
                    self.log("[步骤9] 检查排队并疯狂重试 (优化版)", "STEP")
                    step9_start = self.performance_monitor.start_step("排队重试")

                    # ✨ 优化: 等待页面加载 (2秒 → 1秒)
                    time.sleep(1)

                    # 调用优化后的排队重试方法
                    retry_success = self._handle_queue_retry(driver, max_retries=200)

                    if retry_success:
                        self.log("[OK] 排队处理成功(或无需排队)", "OK")
                        self.performance_monitor.end_step("排队重试", step9_start, success=True)
                    else:
                        self.log("[WARN] 排队重试未成功,可能需要继续等待或手动操作", "WARNING")
                        self.performance_monitor.end_step("排队重试", step9_start, success=False)

                else:
                    self.log("[WARN] 场次/票档选择失败,可能需要手动操作", "WARNING")
                    self.performance_monitor.end_step("选择场次票档", step8_start, success=False)

                # 步骤10: 保存截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_file = f"grab_ticket_{timestamp}.png"
                driver.get_screenshot_as_file(screenshot_file)
                self.log(f"截图已保存: {screenshot_file}", "OK")

                self.log("="*60, "STEP")
                self.log("[OK] 抢票流程完成! 请查看截图和设备屏幕", "OK")
                self.log("="*60, "STEP")

                # 打印性能报告
                self.performance_monitor.print_report()

            except Exception as e:
                self.log(f"抢票出错: {e}", "ERROR")
                try:
                    import traceback
                    traceback.print_exc()
                except UnicodeEncodeError:
                    pass

                # 失败后禁用按钮5秒,防止死循环
                self.log("! 抢票失败,5秒后恢复按钮", "WARN")
                self.root.after(5000, lambda: self.grab_btn.config(state=tk.NORMAL))
                return  # 不恢复按钮

            finally:
                # 恢复按钮状态
                self.grabbing = False
                self.grab_btn.config(state=tk.NORMAL)
                self.stop_grab_btn.config(state=tk.DISABLED)

        threading.Thread(target=do_grab, daemon=True).start()

    # ========== 快速抢票功能（新增）==========

    def pick_coord_from_screenshot(self, coord_type: str):
        """从当前截图点击获取坐标"""
        if not self.current_screenshot:
            self.log("请先连接设备查看截图", "WARNING")
            return

        # 设置坐标选择模式
        self.coord_picking_mode = coord_type

        coord_names = {
            "session": "场次",
            "price": "票档",
            "buy": "购票按钮"
        }

        self.log(f"📍 请在截图上点击选择【{coord_names.get(coord_type, coord_type)}】位置...", "INFO")

        # 临时修改鼠标光标样式（如果Canvas支持）
        self.canvas.config(cursor="crosshair")


    def save_grab_coords(self):
        """保存抢票坐标配置"""
        config = {
            "session_x": self.grab_coords["session_x"].get(),
            "session_y": self.grab_coords["session_y"].get(),
            "price_x": self.grab_coords["price_x"].get(),
            "price_y": self.grab_coords["price_y"].get(),
            "buy_x": self.grab_coords["buy_x"].get(),
            "buy_y": self.grab_coords["buy_y"].get(),
            "click_interval": self.click_interval.get(),
            "max_clicks": self.max_clicks.get(),
            "page_check_interval": self.page_check_interval.get()
        }

        try:
            with open("grab_coords.json", 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log("✓ 坐标配置已保存到 grab_coords.json", "SUCCESS")
        except Exception as e:
            self.log(f"✗ 保存失败: {e}", "ERROR")

    def load_grab_coords(self):
        """加载抢票坐标配置"""
        try:
            with open("grab_coords.json", 'r', encoding='utf-8') as f:
                config = json.load(f)

            self.grab_coords["session_x"].set(config.get("session_x", 360))
            self.grab_coords["session_y"].set(config.get("session_y", 400))
            self.grab_coords["price_x"].set(config.get("price_x", 360))
            self.grab_coords["price_y"].set(config.get("price_y", 600))
            self.grab_coords["buy_x"].set(config.get("buy_x", 360))
            self.grab_coords["buy_y"].set(config.get("buy_y", 1100))
            self.click_interval.set(config.get("click_interval", 0.1))
            self.max_clicks.set(config.get("max_clicks", 100))
            self.page_check_interval.set(config.get("page_check_interval", 5))

            self.log("✓ 坐标配置已加载", "SUCCESS")
        except FileNotFoundError:
            self.log("未找到配置文件 grab_coords.json", "WARNING")
        except Exception as e:
            self.log(f"✗ 加载失败: {e}", "ERROR")

    def navigate_to_session_page(self):
        """阶段一：导航到场次选择页面（不执行抢票）"""
        if not self.bot or not self.bot.driver:
            self.log("请先连接设备!", "ERROR")
            return

        if self.grabbing:
            self.log("正在执行任务，请等待完成", "WARNING")
            return

        self.grabbing = True
        self.navigate_btn.config(state=tk.DISABLED)
        self.grab_btn.config(state=tk.DISABLED)

        def navigate_task():
            try:
                self.log("=" * 60, "STEP")
                self.log("阶段一：场次导航", "STEP")
                self.log("=" * 60, "STEP")

                # 这里复用原有的抢票流程，但只到场次选择页面
                # 根据实际情况调整...

                self.log("✓ 导航完成！请在截图上设置抢票坐标", "SUCCESS")
                self.log("  1. 点击 📍 按钮", "INFO")
                self.log("  2. 在截图上点击目标位置", "INFO")
                self.log("  3. 设置完成后点击'②开始抢票'", "INFO")

                # 启用"开始抢票"按钮
                self.grab_btn.config(state=tk.NORMAL)

            except Exception as e:
                self.log(f"✗ 导航失败: {e}", "ERROR")
            finally:
                self.grabbing = False
                self.navigate_btn.config(state=tk.NORMAL)

        threading.Thread(target=navigate_task, daemon=True).start()

    def start_fast_grab(self):
        """阶段二：开始快速抢票"""
        if not self.bot or not self.bot.driver:
            self.log("请先连接设备!", "ERROR")
            return

        if self.grabbing:
            self.log("正在执行任务，请等待完成", "WARNING")
            return

        self.grabbing = True
        self.grab_btn.config(state=tk.DISABLED)
        self.stop_grab_btn.config(state=tk.NORMAL)
        self.navigate_btn.config(state=tk.DISABLED)

        def grab_task():
            try:
                # 初始化FastGrabber
                if not self.fast_grabber:
                    self.fast_grabber = FastGrabber(self.bot.driver, logger=BotLogger)

                # 创建配置
                config = GrabConfig(
                    session_x=self.grab_coords["session_x"].get(),
                    session_y=self.grab_coords["session_y"].get(),
                    price_x=self.grab_coords["price_x"].get(),
                    price_y=self.grab_coords["price_y"].get(),
                    buy_x=self.grab_coords["buy_x"].get(),
                    buy_y=self.grab_coords["buy_y"].get(),
                    click_interval=self.click_interval.get(),
                    max_clicks=self.max_clicks.get(),
                    page_check_interval=self.page_check_interval.get()
                )

                self.log("=" * 60, "STEP")
                self.log("阶段二：快速抢票", "STEP")
                self.log("=" * 60, "STEP")

                # 执行快速抢票
                success, message = self.fast_grabber.start_grab(
                    config,
                    on_progress=lambda msg: self.log(msg, "INFO")
                )

                if success:
                    self.log("=" * 60, "SUCCESS")
                    self.log("🎉 抢票成功！页面已变化", "SUCCESS")
                    self.log(message, "SUCCESS")
                    self.log("=" * 60, "SUCCESS")
                else:
                    self.log("=" * 60, "WARNING")
                    self.log("⚠ 抢票未完成", "WARNING")
                    self.log(message, "WARNING")
                    self.log("=" * 60, "WARNING")

                # 打印统计
                self.fast_grabber.print_statistics()

            except Exception as e:
                self.log(f"✗ 抢票出错: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
            finally:
                self.grabbing = False
                self.grab_btn.config(state=tk.NORMAL)
                self.stop_grab_btn.config(state=tk.DISABLED)
                self.navigate_btn.config(state=tk.NORMAL)

        threading.Thread(target=grab_task, daemon=True).start()

    # ========== 会话管理和错误恢复 ==========

    def _with_error_handling(self, func, func_name="操作", max_retries=3, timeout=30, allow_fail=False):
        """
        通用错误处理包装器 - 为所有操作提供统一的错误处理、重试和超时控制

        Args:
            func: 要执行的函数
            func_name: 操作名称(用于日志)
            max_retries: 最大重试次数
            timeout: 超时时间(秒)
            allow_fail: 是否允许失败(True=失败时返回None, False=失败时抛异常)

        Returns:
            函数执行结果,或None(如果allow_fail=True且失败)
        """
        start_time = time.time()
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                # 检查超时
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    raise TimeoutError(f"{func_name}超时({timeout}秒)")

                # 执行函数
                result = func()

                # 成功
                if retry_count > 0:
                    self.log(f"  [OK] {func_name}成功 (重试{retry_count}次后)", "OK")

                return result

            except Exception as e:
                last_error = e
                error_msg = str(e)
                retry_count += 1

                # 记录错误
                self.log(f"  {func_name}失败 (尝试 {retry_count}/{max_retries}): {error_msg[:150]}", "WARN")

                # 判断是否需要会话恢复
                need_session_recovery = (
                    "instrumentation process is not running" in error_msg or
                    "probably crashed" in error_msg or
                    "Session" in error_msg
                )

                if need_session_recovery:
                    self.log(f"  检测到会话错误,尝试恢复...", "WARN")
                    if self._recover_session(error_msg):
                        self.log(f"  会话恢复成功,继续重试{func_name}", "OK")
                        time.sleep(1)
                        continue
                    else:
                        if not allow_fail:
                            raise Exception(f"{func_name}失败: 会话恢复失败")
                        else:
                            self.log(f"  会话恢复失败,跳过{func_name}", "ERROR")
                            return None

                # 普通错误重试
                if retry_count < max_retries:
                    wait_time = min(retry_count * 2, 5)  # 指数退避,最多5秒
                    self.log(f"  等待{wait_time}秒后重试...", "INFO")
                    time.sleep(wait_time)
                else:
                    # 达到最大重试次数
                    if allow_fail:
                        self.log(f"  {func_name}失败,已达最大重试次数,跳过", "ERROR")
                        return None
                    else:
                        raise Exception(f"{func_name}失败(重试{max_retries}次): {error_msg}")

        # 不应该到这里,但保险起见
        if not allow_fail:
            raise last_error if last_error else Exception(f"{func_name}失败")
        return None

    def _recover_session(self, error_msg=""):
        """会话恢复机制 - 检测错误并尝试自动恢复（增强版 - 支持ADB重连）"""
        self.log("="*60, "WARN")
        self.log("检测到会话错误,尝试自动恢复...", "WARN")

        # 检测错误类型
        is_instrumentation_crash = "instrumentation process is not running" in error_msg or "probably crashed" in error_msg
        is_session_error = "WebDriver" in error_msg or "Session" in error_msg
        is_connection_error = "connection" in error_msg.lower() or "timeout" in error_msg.lower()
        is_device_not_found = "Could not find a connected Android device" in error_msg

        if is_device_not_found:
            self.log("错误类型: ADB设备未找到或断开连接", "WARN")
        elif is_instrumentation_crash:
            self.log("错误类型: UiAutomator2进程崩溃", "WARN")
        elif is_session_error:
            self.log("错误类型: WebDriver会话错误", "WARN")
        elif is_connection_error:
            self.log("错误类型: 连接超时或断开", "WARN")
        else:
            self.log(f"错误类型: 未知 - {error_msg[:100]}", "WARN")

        try:
            # 步骤0: 如果是设备未找到错误，先尝试重新连接ADB
            if is_device_not_found:
                self.log("步骤0/4: 检测到ADB设备断开，尝试重新连接...", "INFO")
                import subprocess
                port = self.port_var.get()
                device_address = f"127.0.0.1:{port}"

                try:
                    # 尝试重新连接ADB
                    connect_result = subprocess.run(
                        f'"{ADB_EXE}" connect {device_address}',
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=10
                    )

                    if "connected" in connect_result.stdout.lower() or "already connected" in connect_result.stdout.lower():
                        self.log(f"  [OK] ADB重新连接成功: {device_address}", "OK")
                        time.sleep(2)  # 等待设备稳定
                    else:
                        self.log(f"  [WARN] ADB连接失败: {connect_result.stdout.strip()}", "WARN")
                        self.log("  尝试继续恢复流程...", "INFO")

                except Exception as adb_err:
                    self.log(f"  [WARN] ADB重连异常: {adb_err}", "WARN")
                    self.log("  尝试继续恢复流程...", "INFO")

            # 步骤1: 清理损坏的会话
            if self.bot and self.bot.driver:
                self.log("步骤1/4: 清理损坏的会话...", "INFO")
                try:
                    self.bot.driver.quit()
                    self.log("  旧会话已关闭", "OK")
                except:
                    self.log("  旧会话已失效,跳过关闭", "INFO")

                self.bot = None
                time.sleep(2)  # 等待资源释放

            # 步骤2: 重新创建会话
            self.log("步骤2/4: 重新创建Appium会话...", "INFO")
            from damai_appium.damai_app_v2 import DamaiBot

            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    self.bot = DamaiBot()
                    self.log(f"  [OK] 会话创建成功 (尝试 {retry_count + 1}/{max_retries})", "OK")
                    break
                except Exception as retry_err:
                    retry_count += 1
                    self.log(f"  尝试 {retry_count}/{max_retries} 失败: {retry_err}", "WARN")
                    if retry_count < max_retries:
                        self.log(f"  等待3秒后重试...", "INFO")
                        time.sleep(3)
                    else:
                        raise Exception(f"重试{max_retries}次后仍然失败: {retry_err}")

            # 步骤3: 验证会话
            self.log("步骤3/4: 验证会话状态...", "INFO")
            if self.bot and self.bot.driver:
                # 尝试获取一次截图来验证会话是否正常
                try:
                    _ = self.bot.driver.get_screenshot_as_png()
                    self.log("  [OK] 会话验证成功", "OK")
                except Exception as verify_err:
                    self.log(f"  [FAIL] 会话验证失败: {verify_err}", "ERROR")
                    raise Exception(f"会话创建成功但验证失败: {verify_err}")

            # 更新GUI状态
            self.status_label.config(text="● 已连接", fg="green")
            self.reconnect_btn.config(state=tk.DISABLED)

            # 步骤4: 重启截图监控
            self.log("步骤4/4: 重启截图监控...", "INFO")
            try:
                # 先停止旧的监控
                if self.running:
                    self.running = False
                    time.sleep(0.5)

                # 启动新的监控
                self.running = True
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.log("  [OK] 截图监控已重启", "OK")
            except Exception as monitor_err:
                self.log(f"  [WARN] 截图监控重启失败: {monitor_err}", "WARN")
                # 监控失败不影响会话恢复

            self.log("="*60, "OK")
            self.log("[OK] 会话恢复成功!", "OK")
            self.log("="*60, "OK")

            return True

        except Exception as recover_err:
            self.log("="*60, "ERROR")
            self.log(f"[FAIL] 会话恢复失败: {recover_err}", "ERROR")
            self.log("="*60, "ERROR")

            # 更新GUI状态为断开
            self.status_label.config(text="● 连接断开", fg="red")
            self.reconnect_btn.config(state=tk.NORMAL)

            import traceback
            traceback.print_exc()

            return False

    def _safe_driver_operation(self, operation_func, operation_name="操作", max_retries=2):
        """安全的driver操作包装器 - 自动处理会话崩溃和重试"""
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # 执行操作
                result = operation_func()
                return result

            except Exception as e:
                error_msg = str(e)
                self.log(f"{operation_name}失败 (尝试 {retry_count + 1}/{max_retries + 1}): {error_msg[:100]}", "WARN")

                # 检查是否需要恢复会话
                need_recovery = (
                    "instrumentation process is not running" in error_msg or
                    "probably crashed" in error_msg or
                    "Session" in error_msg or
                    "WebDriver" in error_msg
                )

                if need_recovery and retry_count < max_retries:
                    # 尝试恢复会话
                    self.log(f"尝试恢复会话并重试{operation_name}...", "INFO")
                    if self._recover_session(error_msg):
                        retry_count += 1
                        time.sleep(1)  # 恢复后等待1秒再重试
                        continue
                    else:
                        raise Exception(f"会话恢复失败,无法继续{operation_name}")
                else:
                    # 不需要恢复或已达到最大重试次数
                    raise

        raise Exception(f"{operation_name}失败,已重试{max_retries}次")

    # ========== 智能诊断和恢复系统 ==========

    def _diagnose_and_recover(self, driver, expected_state, current_state, texts):
        """
        智能诊断当前状态并采取恢复措施

        Args:
            driver: WebDriver实例
            expected_state: 期望到达的状态
            current_state: 当前实际状态
            texts: OCR/page_source识别的文字

        Returns:
            (recovered: bool, new_state: str, message: str)
        """
        self.log("="*50, "INFO")
        self.log("【智能诊断】开始分析并尝试恢复...", "INFO")
        self.log(f"  期望状态: {expected_state}", "INFO")
        self.log(f"  当前状态: {current_state}", "INFO")
        self.log(f"  识别元素: {len(texts)}个", "INFO")

        # 保存诊断截图
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"diagnose_{current_state}_{timestamp}.png"
            driver.get_screenshot_as_file(screenshot_path)
            self.log(f"√ 诊断截图已保存: {screenshot_path}", "DEBUG")
        except:
            pass

        # 策略1: 处理各种弹窗
        if self._check_and_handle_dialogs(driver, texts):
            self.log("√ 检测并处理了弹窗", "OK")
            time.sleep(1)
            new_state, new_texts = self._get_current_page_state(driver)
            return True, new_state, "已处理弹窗"

        # 策略2: 如果在错误页面,尝试返回
        if current_state == PageState.ERROR_PAGE:
            self.log("  检测到错误页面,尝试返回...", "INFO")
            if self._try_go_back(driver):
                time.sleep(2)
                new_state, new_texts = self._get_current_page_state(driver)
                return True, new_state, "从错误页返回"

        # 策略3: 如果不在大麦App,重新启动
        try:
            current_package = driver.current_package
            if current_package != "cn.damai":
                self.log(f"  不在大麦App(当前:{current_package}),重新启动...", "INFO")
                driver.activate_app("cn.damai")
                time.sleep(3)
                new_state, new_texts = self._get_current_page_state(driver)
                return True, new_state, "重新启动App"
        except:
            pass

        # 策略4: 根据期望状态智能导航
        recovery_action = self._get_recovery_action(expected_state, current_state)
        if recovery_action:
            self.log(f"  执行恢复操作: {recovery_action['description']}", "INFO")
            if self._execute_recovery_action(driver, recovery_action):
                time.sleep(2)
                new_state, new_texts = self._get_current_page_state(driver)
                return True, new_state, recovery_action['description']

        # 策略5: 通用返回到首页策略
        if current_state not in [PageState.HOME, expected_state]:
            self.log("  尝试返回首页...", "INFO")
            if self._navigate_to_home(driver):
                time.sleep(2)
                new_state, new_texts = self._get_current_page_state(driver)
                return True, new_state, "导航回首页"

        self.log("X 无法自动恢复", "WARN")
        return False, current_state, "无恢复方案"

    def _check_and_handle_dialogs(self, driver, texts):
        """检查并处理各种对话框"""
        text_list = [t['text'] for t in texts]
        text_str = ''.join(text_list)

        # 检测弹窗关键词
        dialog_keywords = {
            '权限': ['下次再说', '暂不', '取消'],
            '升级': ['暂不升级', '取消', '下次'],
            '广告': ['关闭', '跳过'],
            '通知': ['暂不', '取消'],
            '定位': ['下次再说', '取消']
        }

        for dialog_type, close_keywords in dialog_keywords.items():
            if any(keyword in text_str for keyword in [dialog_type, '提示', '请求']):
                self.log(f"  检测到{dialog_type}弹窗", "INFO")
                # 尝试点击关闭按钮
                for text in texts:
                    if any(keyword in text['text'] for keyword in close_keywords):
                        try:
                            if text['position'] != (0, 0):
                                x, y = text['position']
                                driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                                self.log(f"  点击关闭: {text['text']}", "OK")
                                return True
                        except:
                            pass

                # 不再使用固定坐标680,100关闭弹窗
                # 改为返回首页重新开始流程

        return False

    def _try_go_back(self, driver):
        """尝试返回上一页"""
        try:
            driver.back()
            return True
        except:
            return False

    def _navigate_to_home(self, driver):
        """导航回首页"""
        try:
            self.log("返回首页: 按返回键...", "INFO")
            # 方法1: 多次返回
            for _ in range(3):
                driver.back()
                time.sleep(0.5)

            # 方法2: 点击首页按钮（底部导航栏）
            page_source = driver.page_source
            if '首页' in page_source or 'tab_home' in page_source:
                self.log("点击底部首页按钮", "INFO")
                # 点击底部导航栏的首页按钮
                driver.execute_script("mobile: clickGesture", {"x": 72, "y": 1240})
                time.sleep(1)

            self.log("[OK] 已返回首页", "OK")
            return True
        except:
            return False

    def _check_and_handle_popup(self, driver, enable_detection=None):
        """检测并处理弹窗，返回是否需要恢复流程"""
        # 根据参数或对象属性决定是否启用弹窗检测
        if enable_detection is None:
            enable_detection = getattr(self, 'enable_popup_detection', False)

        if not enable_detection:
            return False

        try:
            page_source = driver.page_source

            # 检测常见弹窗关键词
            popup_keywords = ['关闭', '取消', '知道了', '确定', '跳过', '稍后', '不了']
            has_popup = any(keyword in page_source for keyword in popup_keywords)

            if has_popup:
                self.log("[WARN] 检测到弹窗", "WARNING")
                # 尝试关闭弹窗
                popup_result = self._dismiss_popups(driver)
                if popup_result is True:
                    # 成功关闭弹窗
                    self.log("[OK] 弹窗已关闭", "OK")
                    time.sleep(0.5)
                    return True  # 需要重新验证页面状态
                elif popup_result is False:
                    # 在功能页面，跳过了弹窗检测
                    self.log("[INFO] 在功能页面，无需处理弹窗", "INFO")
                    return False  # 继续正常流程
                else:
                    # popup_result is None 或其他情况：未找到弹窗
                    self.log("[INFO] 未检测到需要关闭的弹窗", "INFO")
                    return False  # 继续正常流程

            return False  # 无弹窗，继续正常流程
        except Exception as e:
            self.log(f"弹窗检测失败: {e}", "ERROR")
            return False

    def _validate_and_recover(self, driver, expected_page, validation_func, max_attempts=3):
        """验证页面状态并在失败时自动恢复

        Args:
            driver: WebDriver实例
            expected_page: 期望的页面类型（如"homepage", "search", "detail"）
            validation_func: 验证函数，返回True表示在正确页面
            max_attempts: 最大恢复尝试次数

        Returns:
            bool: 是否成功到达目标页面
        """
        for attempt in range(max_attempts):
            # 首先检查是否有弹窗
            if self._check_and_handle_popup(driver):
                self.log(f"[尝试 {attempt+1}/{max_attempts}] 处理弹窗后重新验证", "INFO")
                time.sleep(1)

            # 验证页面状态
            if validation_func():
                self.log(f"[OK] 已在目标页面: {expected_page}", "OK")
                return True

            # 页面状态不对，尝试恢复
            self.log(f"[WARN] 未在目标页面: {expected_page} (尝试 {attempt+1}/{max_attempts})", "WARNING")

            # 恢复策略
            if expected_page == "homepage":
                self._navigate_to_home(driver)
                time.sleep(1)
            elif expected_page == "search":
                self._navigate_to_home(driver)
                time.sleep(1)
                driver.execute_script("mobile: clickGesture", {"x": 326, "y": 99})  # 搜索框
                time.sleep(1)
            elif expected_page == "detail":
                # 如果不在详情页，返回首页重新搜索
                self._navigate_to_home(driver)
                time.sleep(1)
                return False  # 需要重新开始整个流程
            else:
                self.log(f"! 未知页面类型: {expected_page}", "ERROR")
                return False

        self.log(f"[FAIL] 无法到达目标页面: {expected_page}", "ERROR")
        return False

    def _get_recovery_action(self, expected_state, current_state):
        """获取恢复操作方案"""
        recovery_map = {
            # 期望到搜索页
            (PageState.SEARCH, PageState.HOME): {
                'description': '从首页进入搜索',
                'action': 'click_search_icon',
                'coords': (360, 100)
            },
            (PageState.SEARCH, PageState.DETAIL): {
                'description': '从详情页返回搜索',
                'action': 'go_back',
                'times': 1
            },

            # 期望到详情页
            (PageState.DETAIL, PageState.RESULT): {
                'description': '从结果页进入详情',
                'action': 'click_first_result',
                'coords': (360, 400)
            },
            (PageState.DETAIL, PageState.HOME): {
                'description': '从首页搜索进入详情',
                'action': 'search_then_click',
            },

            # 期望到结果页
            (PageState.RESULT, PageState.SEARCH): {
                'description': '在搜索页执行搜索',
                'action': 'execute_search'
            },
            (PageState.RESULT, PageState.HOME): {
                'description': '从首页进入搜索',
                'action': 'click_search_icon',
                'coords': (360, 100)
            }
        }

        return recovery_map.get((expected_state, current_state))

    def _execute_recovery_action(self, driver, action):
        """执行恢复操作"""
        try:
            action_type = action.get('action')

            if action_type == 'go_back':
                times = action.get('times', 1)
                for _ in range(times):
                    driver.back()
                    time.sleep(0.5)
                return True

            elif action_type == 'click_search_icon':
                coords = action.get('coords')
                driver.execute_script("mobile: clickGesture", {"x": coords[0], "y": coords[1]})
                return True

            elif action_type == 'click_first_result':
                coords = action.get('coords')
                driver.execute_script("mobile: clickGesture", {"x": coords[0], "y": coords[1]})
                return True

            elif action_type == 'execute_search':
                # 执行搜索操作
                driver.execute_script("mobile: clickGesture", {"x": 360, "y": 1200})
                return True

            return False
        except:
            return False

    # ========== 页面检测和验证方法 ==========

    def _get_current_page_state(self, driver):
        """获取当前页面状态 - 通过截图+OCR识别或page_source"""
        try:
            # 方法1: 优先使用OCR
            if self.use_ocr.get():
                try:
                    screenshot = driver.get_screenshot_as_png()
                    pil_img = Image.open(io.BytesIO(screenshot))
                    texts = self.ai.analyze_screen(pil_img, use_ocr=True)
                    if texts:  # OCR成功
                        page_state = self.ai.detect_page_state(texts)
                        return page_state, texts
                except Exception as ocr_err:
                    self.log(f"OCR检测失败,切换到page_source: {ocr_err}", "DEBUG")

            # 方法2: 使用page_source作为后备
            page_source = driver.page_source
            texts = self._extract_texts_from_page_source(page_source)
            page_state = self.ai.detect_page_state(texts)
            return page_state, texts

        except Exception as e:
            self.log(f"获取页面状态失败: {e}", "ERROR")
            return PageState.UNKNOWN, []

    def _extract_texts_from_page_source(self, page_source):
        """从page_source提取文字(后备方案)"""
        try:
            from xml.etree import ElementTree as ET
            texts = []

            # 解析XML
            root = ET.fromstring(page_source)

            # 提取所有text和content-desc属性
            for elem in root.iter():
                text_content = elem.get('text', '').strip()
                content_desc = elem.get('content-desc', '').strip()

                if text_content:
                    texts.append({
                        'text': text_content,
                        'confidence': 1.0,
                        'position': (0, 0),
                        'box': []
                    })
                if content_desc and content_desc != text_content:
                    texts.append({
                        'text': content_desc,
                        'confidence': 1.0,
                        'position': (0, 0),
                        'box': []
                    })

            return texts
        except Exception as e:
            safe_print(f"page_source解析失败: {e}")
            return []

    def _verify_page_state(self, driver, expected_states, operation_name="操作", timeout=10, auto_recover=True):
        """
        验证页面状态是否符合预期 - 增强版支持自动恢复

        Args:
            driver: WebDriver实例
            expected_states: 期望的页面状态(单个或列表)
            operation_name: 操作名称(用于日志)
            timeout: 超时时间(秒)
            auto_recover: 是否启用自动恢复

        Returns:
            (success: bool, actual_state: str, texts: list)
        """
        if isinstance(expected_states, str):
            expected_states = [expected_states]

        self.log(f"【页面验证】检查是否在: {', '.join(expected_states)}", "INFO")

        start_time = time.time()
        recovery_attempted = False

        while time.time() - start_time < timeout:
            page_state, texts = self._get_current_page_state(driver)

            if page_state in expected_states:
                self.log(f"√ 页面状态正确: {page_state}", "OK")
                return True, page_state, texts

            # 如果是加载中,继续等待
            if page_state == PageState.LOADING:
                self.log(f"  页面加载中,等待...", "INFO")
                time.sleep(0.5)
                continue

            # 如果是错误页面或状态不对,尝试智能恢复(仅尝试一次)
            if auto_recover and not recovery_attempted:
                elapsed = time.time() - start_time
                if elapsed > timeout / 2:  # 超过一半时间才恢复,避免过早干预
                    self.log(f"! 状态不符(当前:{page_state}),尝试智能恢复...", "WARN")
                    recovered, new_state, message = self._diagnose_and_recover(
                        driver, expected_states[0], page_state, texts
                    )
                    recovery_attempted = True

                    if recovered and new_state in expected_states:
                        self.log(f"√ 恢复成功: {message}", "OK")
                        return True, new_state, texts
                    else:
                        self.log(f"! 恢复未达到期望状态: {message}", "WARN")

            # 继续等待
            self.log(f"  当前: {page_state}, 期望: {', '.join(expected_states)}, 等待...", "DEBUG")
            time.sleep(0.5)

        # 超时 - 最后再尝试一次恢复
        page_state, texts = self._get_current_page_state(driver)

        if auto_recover and not recovery_attempted:
            self.log(f"! 验证超时,最后尝试恢复...", "WARN")
            recovered, new_state, message = self._diagnose_and_recover(
                driver, expected_states[0], page_state, texts
            )
            if recovered and new_state in expected_states:
                self.log(f"√ 最后恢复成功: {message}", "OK")
                return True, new_state, texts

        self.log(f"X {operation_name}超时! 当前: {page_state}, 期望: {', '.join(expected_states)}", "ERROR")
        return False, page_state, texts

    def _ensure_app_running(self, driver):
        """确保大麦App正常运行 - 增强版支持自动恢复"""
        self.log("【App检测】检查大麦App是否正常运行...", "INFO")

        try:
            # 方法1: 检查当前Activity
            current_activity = driver.current_activity
            self.log(f"  当前Activity: {current_activity}", "DEBUG")

            # 大麦App的包名
            expected_package = "cn.damai"

            # 方法2: 检查当前包名
            current_package = driver.current_package
            self.log(f"  当前包名: {current_package}", "DEBUG")

            if current_package != expected_package:
                self.log(f"! 当前不在大麦App! 当前包名: {current_package}", "WARN")
                # 尝试启动大麦App
                self.log("  尝试启动大麦App...", "INFO")
                try:
                    driver.activate_app(expected_package)
                    time.sleep(3)

                    # 再次检查
                    current_package = driver.current_package
                    if current_package != expected_package:
                        self.log(f"! 启动后仍不在大麦App: {current_package}", "WARN")
                except Exception as activate_err:
                    self.log(f"! 启动App失败: {activate_err}", "WARN")

            # 方法3: 检测页面内容(使用page_source作为后备,不依赖OCR)
            page_state, texts = self._get_current_page_state(driver)

            # 只要能获取到文字内容,就认为App在运行
            if texts and len(texts) > 0:
                self.log(f"√ 检测到页面内容({len(texts)}个元素),当前页面: {page_state}", "OK")
                return True, page_state, texts
            elif page_state != PageState.NOT_STARTED and page_state != PageState.UNKNOWN:
                # 即使没有文字,但状态正确也算成功
                self.log(f"√ 页面状态正常: {page_state}", "OK")
                return True, page_state, texts
            else:
                # 尝试等待一下
                self.log("  未检测到页面内容,等待2秒后重试...", "INFO")
                time.sleep(2)
                page_state, texts = self._get_current_page_state(driver)
                if texts and len(texts) > 0:
                    self.log(f"√ 重试成功,当前页面: {page_state}", "OK")
                    return True, page_state, texts
                else:
                    self.log("! App可能处于加载状态,继续执行...", "WARN")
                    # 不抛异常,允许继续
                    return True, PageState.LOADING, texts

        except Exception as e:
            self.log(f"! App检测异常: {e}, 尝试继续...", "WARN")
            # 不再直接失败,而是返回warning状态
            return True, PageState.UNKNOWN, []

    # ========== 抢票辅助方法 ==========

    def _dismiss_popups(self, driver, max_retries=3):
        """处理各种弹窗 - 健壮版,支持多种弹窗类型+完整错误处理"""

        # 先检查是否在正常功能页面，避免误关闭
        try:
            page_source = driver.page_source
            # 检测正常功能页面的特征关键词 - 扩展关键词列表
            functional_pages = [
                ('搜索框', ['搜你所想', '请输入', '搜索', '演唱会', '体育赛事', '音乐会', '话剧歌剧']),
                ('城市选择', ['请选择城市', '热门城市', '全部城市', '当前定位', '选择城市', '城市搜索', '切换城市', 'A-Z', 'ABCD']),
                ('筛选页', ['价格', '时间', '场次', '座位', '筛选', '排序']),
                ('详情页', ['立即购买', '选座购买', '加入购物车', '演出介绍', '购买须知', '选择场次']),
            ]

            for page_type, keywords in functional_pages:
                if any(keyword in page_source for keyword in keywords):
                    self.log(f"[INFO] ⚠️ 检测到正常功能页面({page_type}),跳过弹窗检测 ⚠️", "INFO")
                    self.log(f"[INFO] 匹配关键词: {[kw for kw in keywords if kw in page_source]}", "DEBUG")
                    return False  # 明确返回False表示跳过
        except Exception as e:
            self.log(f"[WARN] 功能页面检测失败: {e}", "DEBUG")
            pass  # 如果检测失败，继续执行弹窗处理

        self.log("="*50, "INFO")
        self.log("【弹窗处理】开始检查...", "INFO")

        # 定义多种弹窗匹配模式
        popup_patterns = [
            ('new UiSelector().textContains("关闭")', "关闭"),
            ('new UiSelector().textContains("稍后")', "稍后"),
            ('new UiSelector().textContains("知道了")', "知道了"),
            ('new UiSelector().textContains("下次再说")', "下次再说"),
            ('new UiSelector().textContains("取消")', "取消"),
            ('new UiSelector().textContains("暂不")', "暂不"),
            ('new UiSelector().textContains("以后再说")', "以后再说"),
            ('new UiSelector().descriptionContains("关闭")', "关闭图标"),
            ('new UiSelector().descriptionContains("close")', "close图标"),
            ('new UiSelector().className("android.widget.ImageButton")', "图片按钮"),
        ]

        from appium.webdriver.common.appiumby import AppiumBy

        popup_closed = False
        retry_count = 0

        while retry_count < max_retries and not popup_closed:
            try:
                # 方法1: 文本/描述匹配
                self.log(f"  尝试 {retry_count + 1}/{max_retries}: 文本匹配查找弹窗...", "INFO")

                for pattern, name in popup_patterns:
                    try:
                        els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, pattern)
                        if els and len(els) > 0:
                            self.log(f"    找到弹窗元素: {name} (共{len(els)}个)", "INFO")

                            # 尝试点击第一个可见的元素
                            for i, el in enumerate(els[:3]):  # 最多尝试前3个
                                try:
                                    # 检查元素是否可点击和可见
                                    is_displayed = el.is_displayed() if hasattr(el, 'is_displayed') else True
                                    is_enabled = el.is_enabled() if hasattr(el, 'is_enabled') else True

                                    if is_displayed and is_enabled:
                                        el.click()
                                        self.log(f"    [OK] 成功点击: {name} (第{i+1}个元素)", "OK")
                                        time.sleep(0.8)
                                        popup_closed = True
                                        break
                                    else:
                                        self.log(f"    跳过不可见/不可用元素: {name} (第{i+1}个)", "DEBUG")
                                except Exception as click_err:
                                    self.log(f"    点击{name}第{i+1}个元素失败: {click_err}", "DEBUG")
                                    continue

                            if popup_closed:
                                break

                    except Exception as find_err:
                        self.log(f"    查找{name}时出错: {find_err}", "DEBUG")
                        continue

                # 方法2: 如果文本匹配失败,尝试坐标点击
                if not popup_closed:
                    self.log(f"  文本匹配未找到弹窗,尝试坐标点击...", "INFO")

                    close_coords = [
                        (650, 120),   # 右上角位置1
                        (340, 160),   # 弹窗右上角
                        (700, 80),    # 更靠右上
                        (360, 140),   # 中间偏右
                    ]

                    for x, y in close_coords:
                        try:
                            driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                            self.log(f"    尝试点击坐标: ({x}, {y})", "DEBUG")
                            time.sleep(0.5)

                            # 验证点击是否有效(检查弹窗是否还在)
                            verification_failed = False
                            for pattern, name in popup_patterns[:3]:  # 只检查前3个常见模式
                                try:
                                    els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, pattern)
                                    if els:
                                        verification_failed = True
                                        break
                                except:
                                    pass

                            if not verification_failed:
                                self.log(f"    [OK] 坐标点击可能成功: ({x}, {y})", "OK")
                                popup_closed = True
                                break
                            else:
                                self.log(f"    坐标点击无效,弹窗仍存在", "DEBUG")

                        except Exception as coord_err:
                            self.log(f"    坐标({x}, {y})点击失败: {coord_err}", "DEBUG")
                            continue

            except Exception as outer_err:
                self.log(f"  第{retry_count + 1}次尝试出现异常: {outer_err}", "ERROR")
                import traceback
                self.log(f"  异常堆栈: {traceback.format_exc()}", "DEBUG")

            # 如果这次尝试失败,增加重试计数
            if not popup_closed:
                retry_count += 1
                if retry_count < max_retries:
                    self.log(f"  未找到弹窗,等待1秒后重试...", "INFO")
                    time.sleep(1)

        # 最终结果
        if popup_closed:
            self.log("[OK] 【弹窗处理】成功关闭弹窗", "OK")
        else:
            self.log("【弹窗处理】未发现需要关闭的弹窗(或所有尝试均失败)", "INFO")

        self.log("="*50, "INFO")
        return popup_closed

    def _check_and_switch_city(self, driver, target_city="北京", max_retries=3, timeout=30):
        """检查并切换城市 - 优化版,集成手动教学的4步流程+坐标点击"""
        self.log("="*60, "STEP")
        self.log(f"【城市切换】目标城市: {target_city}", "STEP")
        self.log("="*60, "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 手动教学验证的坐标 (基于实际测试 2025-11-16 最新)
        CITY_SELECTOR_COORD = (188, 88)      # 城市选择入口 (首页固定坐标) - 已验证
        CITY_SEARCH_BOX_COORD = (182, 208)   # 搜索框激活 [WARN] 关键步骤! - 已验证
        CITY_ITEM_COORD = (118, 326)         # 城市选项 (第一个搜索结果) - 已验证

        try:
            # 等待首页加载
            time.sleep(2)

            # 多种方式查找城市控件
            city_patterns = [
                (AppiumBy.ID, "cn.damai:id/city_name_tv"),
                (AppiumBy.ID, "cn.damai:id/city_text"),
                (AppiumBy.ID, "cn.damai:id/tv_city"),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceIdMatches(".*city.*")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").textMatches(".*市|.*京|.*海|.*州.*")'),
            ]

            current_city = None
            city_el = None

            for by, selector in city_patterns:
                try:
                    els = driver.find_elements(by, selector)
                    if els:
                        city_el = els[0]
                        current_city = city_el.text
                        if current_city:  # 确保不是空字符串
                            self.log(f"当前城市: {current_city}", "INFO")
                            break
                except Exception as e:
                    self.log(f"城市查找尝试失败: {e}", "DEBUG")
                    continue

            # 判断是否需要切换
            if current_city and target_city in current_city:
                self.log(f"[OK] 城市已是 {target_city},无需切换", "OK")
                return True

            # 需要切换城市 - 使用4步流程
            self.log(f"当前城市: {current_city or '未知'}, 需要切换到 {target_city}", "WARN")
            self.log("="*50, "INFO")
            self.log("【4步城市切换流程】基于手动教学验证", "INFO")
            self.log("="*50, "INFO")

            # === 步骤1: 点击城市选择入口 (216, 88) ===
            self.log(f"[步骤1/4] 点击城市选择入口 {CITY_SELECTOR_COORD}", "STEP")
            success = False

            # 优先使用元素点击
            if city_el:
                try:
                    city_el.click()
                    self.log("[OK] 使用元素方式点击城市选择器", "OK")
                    success = True
                except Exception as e:
                    self.log(f"元素点击失败: {e}", "WARN")

            # 元素点击失败则使用坐标
            if not success:
                try:
                    driver.tap([CITY_SELECTOR_COORD])
                    self.log(f"[OK] 使用坐标 {CITY_SELECTOR_COORD} 点击城市选择器", "OK")
                    success = True
                except Exception as e:
                    self.log(f"坐标点击失败: {e}", "ERROR")
                    return False

            time.sleep(1)  # 等待城市选择页面弹出

            # === 步骤2: 点击搜索框激活 (148, 192) [WARN] 关键步骤! ===
            self.log(f"[步骤2/4] 点击搜索框激活 {CITY_SEARCH_BOX_COORD} (关键!)", "STEP")

            # 优先尝试坐标点击(实测更可靠)
            try:
                driver.tap([CITY_SEARCH_BOX_COORD])
                self.log(f"[OK] 使用坐标 {CITY_SEARCH_BOX_COORD} 激活搜索框", "OK")
                time.sleep(0.5)
            except Exception as e:
                self.log(f"搜索框激活失败,尝试元素查找: {e}", "WARN")

                # 备用方案:查找搜索框元素
                search_patterns = [
                    (AppiumBy.CLASS_NAME, "android.widget.EditText"),
                    (AppiumBy.ID, "cn.damai:id/search_input"),
                    (AppiumBy.ID, "cn.damai:id/et_search"),
                ]

                search_el = None
                for by, selector in search_patterns:
                    try:
                        els = driver.find_elements(by, selector)
                        if els:
                            search_el = els[0]
                            search_el.click()  # 激活搜索框
                            self.log(f"[OK] 使用元素方式激活搜索框", "OK")
                            time.sleep(0.5)
                            break
                    except:
                        continue

            # === 步骤3: 输入城市名称 - 使用ADBKeyboard broadcast方式 (已验证) ===
            self.log(f"[步骤3/4] 输入城市名称: {target_city}", "STEP")

            input_success = False
            time.sleep(0.5)  # 等待搜索框完全激活

            # 方法1: 使用ADBKeyboard broadcast (最可靠) - 手动教学验证
            try:
                import subprocess
                udid = driver.capabilities.get('udid', '')

                # 切换到ADBKeyboard
                subprocess.run([
                    'adb', '-s', udid, 'shell', 'ime', 'set', 'com.android.adbkeyboard/.AdbIME'
                ], check=True, capture_output=True)

                time.sleep(0.3)

                # 使用broadcast发送文本
                subprocess.run([
                    'adb', '-s', udid, 'shell',
                    'am', 'broadcast',
                    '-a', 'ADB_INPUT_TEXT',
                    '--es', 'msg', target_city
                ], check=True, capture_output=True)

                self.log(f"[OK] 已使用ADBKeyboard输入: {target_city}", "OK")
                input_success = True
            except Exception as e:
                self.log(f"ADBKeyboard输入失败,尝试备用方案: {e}", "WARN")

                # 方法2: 备用方案 - send_keys
                try:
                    els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                    if els:
                        input_el = els[0]
                        input_el.clear()
                        time.sleep(0.2)
                        input_el.send_keys(target_city)
                        self.log(f"[OK] 备用方案成功输入: {target_city}", "OK")
                        input_success = True
                except Exception as e2:
                    self.log(f"[WARN] 备用方案也失败: {str(e2)[:80]}", "WARN")

            if not input_success:
                self.log("X 输入城市名失败", "ERROR")
                driver.press_keycode(4)  # 返回键
                return False

            time.sleep(1)  # 等待搜索结果

            # === 步骤4: 点击城市选项 (99, 328) ===
            self.log(f"[步骤4/4] 点击城市选项 {CITY_ITEM_COORD}", "STEP")

            # 优先使用文本匹配
            clicked = False
            try:
                textviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                for tv in textviews[:20]:  # 只检查前20个
                    try:
                        text = tv.text or ""
                        if target_city in text:
                            tv.click()
                            self.log(f"[OK] 选择城市: {text} (文本匹配)", "OK")
                            time.sleep(1)
                            clicked = True
                            break
                    except:
                        continue
            except Exception as e:
                self.log(f"文本匹配失败: {e}", "WARN")

            # 文本匹配失败则使用坐标
            if not clicked:
                try:
                    driver.tap([CITY_ITEM_COORD])
                    self.log(f"[OK] 使用坐标 {CITY_ITEM_COORD} 点击城市选项", "OK")
                    time.sleep(1)
                    clicked = True
                except Exception as e:
                    self.log(f"坐标点击失败: {e}", "ERROR")

            if not clicked:
                self.log("未能选择目标城市,尝试关闭对话框", "WARN")
                driver.press_keycode(4)  # 返回键
                return False

            self.log("="*50, "OK")
            self.log(f"[OK] 城市切换完成: {target_city}", "OK")
            self.log("="*50, "OK")
            return True

        except Exception as e:
            self.log(f"城市切换出错: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False

    def _goto_search_page(self, driver):
        """进入搜索页 - 优化版,集成手动教学验证的坐标"""
        self.log("=== 点击搜索框 ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 手动教学验证的坐标 (2025-11-16 最新验证)
        SEARCH_ENTRY_COORD = (315, 97)  # 搜索入口坐标 - 已验证

        # 演出详情页坐标 (2025-11-16 手动验证)
        DETAIL_PAGE_TICKET_ENTRY_COORD = (464, 1277)  # 票档和场次选择入口 - 已验证

        # 多种方式点击搜索框(增加重试)
        search_patterns = [
            (AppiumBy.ID, "cn.damai:id/homepage_header_search_layout", "首页搜索布局"),
            (AppiumBy.ID, "cn.damai:id/home_search_btn", "首页搜索按钮"),
            (AppiumBy.ID, "cn.damai:id/search_layout", "搜索布局"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("搜索").clickable(true)', "搜索文本"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("搜索").clickable(true)', "搜索描述"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText")', "输入框"),
        ]

        # 尝试3次
        for attempt in range(3):
            if attempt > 0:
                self.log(f"第{attempt + 1}次尝试点击搜索框...", "INFO")
                time.sleep(0.5)

            for by, selector, desc in search_patterns:
                try:
                    els = driver.find_elements(by, selector)
                    if els:
                        # 确保元素可见和可点击
                        if els[0].is_displayed() and els[0].is_enabled():
                            els[0].click()
                            self.log(f"[OK] 点击搜索框成功 (方式: {desc})", "OK")
                            time.sleep(1.5)  # 增加等待时间,确保键盘弹出
                            return True
                        else:
                            self.log(f"元素不可见或不可点击: {desc}", "DEBUG")
                except Exception as e:
                    self.log(f"尝试 {desc} 失败: {str(e)[:50]}", "DEBUG")
                    continue

            # 坐标兜底 - 优先使用手动教学验证的坐标
            if attempt == 1:  # 第2次尝试用坐标
                self.log("尝试使用坐标点击搜索框...", "WARN")
                # 使用新验证的坐标
                try:
                    driver.tap([SEARCH_ENTRY_COORD])
                    self.log(f"[OK] 使用坐标 {SEARCH_ENTRY_COORD} 点击搜索框", "OK")
                    time.sleep(1.5)
                    return True
                except Exception as e:
                    self.log(f"坐标点击失败: {str(e)[:30]}", "DEBUG")

        self.log("X 所有方式都无法点击搜索框", "ERROR")
        return False

    def _input_and_search(self, driver, keyword):
        """输入关键词并搜索 - 增强健壮性版本"""
        self.log(f"=== 输入并搜索: '{keyword}' ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 等待输入框出现(点击搜索框后需要时间)
        time.sleep(0.8)

        # 查找输入框(多种方式,增加重试)
        input_patterns = [
            (AppiumBy.CLASS_NAME, "android.widget.EditText", "通用输入框"),
            (AppiumBy.ID, "cn.damai:id/search_input_text", "搜索输入框1"),
            (AppiumBy.ID, "cn.damai:id/et_search_keyword", "搜索输入框2"),
            (AppiumBy.ID, "cn.damai:id/search_edit_view", "搜索输入框3"),
            (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").focused(true)', "已聚焦输入框"),
        ]

        input_el = None
        input_method = None

        # 尝试3次查找输入框
        for attempt in range(3):
            if attempt > 0:
                self.log(f"第{attempt + 1}次尝试查找输入框...", "INFO")
                time.sleep(0.5)

            for by, selector, desc in input_patterns:
                try:
                    els = driver.find_elements(by, selector)
                    if els and els[0].is_displayed():
                        input_el = els[0]
                        input_method = desc
                        self.log(f"[OK] 找到输入框 (方式: {desc})", "OK")
                        break
                except Exception as e:
                    self.log(f"尝试 {desc} 失败: {str(e)[:30]}", "DEBUG")
                    continue

            if input_el:
                break

        # 输入关键词 - 使用ADBKeyboard broadcast (手动教学验证)
        input_success = False

        # 方法1: 使用ADBKeyboard broadcast (最可靠) - 2025-11-16验证
        try:
            import subprocess
            udid = driver.capabilities.get('udid', '')

            # 切换到ADBKeyboard
            subprocess.run([
                'adb', '-s', udid, 'shell', 'ime', 'set', 'com.android.adbkeyboard/.AdbIME'
            ], check=True, capture_output=True, timeout=5)

            time.sleep(0.3)

            # 使用broadcast发送文本
            subprocess.run([
                'adb', '-s', udid, 'shell',
                'am', 'broadcast',
                '-a', 'ADB_INPUT_TEXT',
                '--es', 'msg', keyword
            ], check=True, capture_output=True, timeout=5)

            self.log(f"[OK] 已使用ADBKeyboard输入: {keyword}", "OK")
            input_success = True
        except Exception as e:
            self.log(f"ADBKeyboard输入失败,尝试备用方案: {e}", "WARN")

            # 方法2: 备用方案 - send_keys
            if input_el:
                try:
                    # 确保输入框获得焦点
                    if not input_el.is_focused():
                        input_el.click()
                        time.sleep(0.5)

                    input_el.clear()
                    time.sleep(0.2)
                    input_el.send_keys(keyword)
                    self.log(f"[OK] 备用方案send_keys输入成功: {keyword}", "OK")
                    input_success = True
                except Exception as e2:
                    self.log(f"send_keys也失败: {str(e2)[:80]}", "ERROR")
        else:
            # 坐标兜底 - 使用固定坐标 (326, 99)
            self.log("未找到输入框,尝试坐标点击", "WARN")
            try:
                driver.tap([(326, 99)])
                time.sleep(0.5)

                # 重新查找输入框
                els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                if els:
                    els[0].send_keys(keyword)
                    # 验证输入是否成功
                    time.sleep(0.3)
                    actual_text = els[0].text or els[0].get_attribute('text') or ""
                    if keyword in actual_text or actual_text in keyword:
                        self.log(f"[OK] 使用坐标 (326, 99) 点击后输入成功,已验证: '{actual_text}'", "OK")
                        input_success = True
                    else:
                        self.log(f"[WARN] 坐标输入验证失败,期望:'{keyword}',实际:'{actual_text}'", "WARNING")
            except Exception as e:
                self.log(f"坐标点击失败: {str(e)[:50]}", "ERROR")

        if not input_success:
            self.log("X 所有输入方式都失败", "ERROR")
            return False

        time.sleep(0.8)

        # 执行搜索(回车键)
        try:
            driver.press_keycode(66)  # KEYCODE_ENTER
            self.log("[OK] 执行搜索 (回车)", "OK")
            time.sleep(2.5)  # 增加等待时间,确保搜索结果加载
        except Exception as e:
            self.log(f"搜索执行失败: {e}", "ERROR")
            # 尝试点击搜索按钮作为备用
            try:
                search_btns = driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().text("搜索").clickable(true)'
                )
                if search_btns:
                    search_btns[0].click()
                    self.log("[OK] 点击搜索按钮", "OK")
                    time.sleep(2.5)
                else:
                    return False
            except:
                return False

        # 关闭键盘
        try:
            driver.hide_keyboard()
            time.sleep(0.3)
            self.log("关闭键盘", "DEBUG")
        except:
            pass

        return True

    def _click_first_search_result(self, driver):
        """点击第一个搜索结果,进入演出列表页

        在搜索结果页(RESULT)点击第一个结果,进入该演出的列表页(LIST)
        """
        self.log("=== 点击第一个搜索结果 ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 等待搜索结果加载
        self.log("等待搜索结果加载...", "INFO")
        time.sleep(2)

        # 尝试多种方式点击第一个搜索结果
        clicked = False

        # 方法1: 查找第一个可点击的TextView(通常是演出标题)
        try:
            self.log("方法1: 查找第一个演出标题...", "DEBUG")
            textviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")

            for tv in textviews[:30]:  # 检查前30个TextView
                try:
                    if not tv.is_displayed():
                        continue

                    text = tv.text or ""
                    if not text or len(text) < 2:
                        continue

                    # 获取位置,排除顶部标题栏
                    location = tv.location
                    if location['y'] < 200:  # 顶部200像素内的跳过
                        continue

                    # 找到第一个有效的演出标题
                    self.log(f"找到第一个搜索结果: '{text[:20]}...'", "INFO")
                    tv.click()
                    self.log("[OK] 点击成功", "OK")
                    clicked = True
                    time.sleep(2)
                    break

                except Exception as e:
                    continue

        except Exception as e:
            self.log(f"方法1失败: {str(e)[:50]}", "DEBUG")

        # 方法2: 使用坐标点击 - 优先使用手动教学验证的坐标
        if not clicked:
            try:
                self.log("方法2: 使用手动教学验证的坐标点击第一个搜索结果...", "DEBUG")
                # 手动教学验证的坐标
                SEARCH_RESULT_COORD = (155, 195)  # 搜索结果坐标

                # 优先使用手动教学坐标
                driver.tap([SEARCH_RESULT_COORD])
                self.log(f"[OK] 使用手动教学坐标 {SEARCH_RESULT_COORD} 点击成功", "OK")
                clicked = True
                time.sleep(2)
            except Exception as e:
                self.log(f"手动教学坐标失败,尝试备用坐标: {str(e)[:50]}", "DEBUG")
                # 备用坐标
                try:
                    driver.tap([(540, 350)])  # 备用坐标
                    self.log("[OK] 备用坐标点击成功", "OK")
                    clicked = True
                    time.sleep(2)
                except Exception as e2:
                    self.log(f"方法2失败: {str(e2)[:50]}", "DEBUG")

        if not clicked:
            raise Exception("无法点击第一个搜索结果")

        return True

    def _click_first_show_in_list(self, driver, keyword):
        """在演出列表页点击第一个相关演出

        在演出列表页(LIST)点击第一个与关键词相关的演出,进入详情页(DETAIL)

        Args:
            keyword: 演出关键词(用于验证)
        """
        self.log(f"=== 在列表页点击第一个相关演出: '{keyword}' ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 等待列表页加载
        self.log("等待演出列表加载...", "INFO")
        time.sleep(2)

        clicked = False

        # 方法1: 查找包含关键词的TextView
        try:
            self.log("方法1: 查找包含关键词的演出...", "DEBUG")
            textviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")

            for tv in textviews[:50]:
                try:
                    if not tv.is_displayed():
                        continue

                    text = tv.text or ""

                    # 检查是否包含关键词
                    if keyword[:3] in text:  # 使用关键词前3个字匹配
                        location = tv.location
                        if location['y'] < 200:  # 排除顶部标题
                            continue

                        self.log(f"找到相关演出: '{text[:20]}...'", "INFO")
                        tv.click()
                        self.log("[OK] 点击成功", "OK")
                        clicked = True
                        time.sleep(2)
                        break

                except Exception as e:
                    continue

        except Exception as e:
            self.log(f"方法1失败: {str(e)[:50]}", "DEBUG")

        # 方法2: 点击第一个演出项(不管是否包含关键词)
        if not clicked:
            try:
                self.log("方法2: 点击第一个演出项...", "DEBUG")
                textviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")

                for tv in textviews[:30]:
                    try:
                        if not tv.is_displayed():
                            continue

                        text = tv.text or ""
                        if not text or len(text) < 2:
                            continue

                        location = tv.location
                        if location['y'] < 200:
                            continue

                        # 找到第一个有效项
                        self.log(f"找到演出: '{text[:20]}...'", "INFO")
                        tv.click()
                        self.log("[OK] 点击成功", "OK")
                        clicked = True
                        time.sleep(2)
                        break

                    except Exception as e:
                        continue

            except Exception as e:
                self.log(f"方法2失败: {str(e)[:50]}", "DEBUG")

        # 方法3: 使用坐标点击 - 优先使用手动教学验证的坐标
        if not clicked:
            try:
                self.log("方法3: 使用手动教学验证的坐标点击...", "DEBUG")
                # 手动教学验证的坐标
                SHOW_ITEM_COORD = (337, 329)  # 演出项坐标

                # 优先使用手动教学坐标
                driver.tap([SHOW_ITEM_COORD])
                self.log(f"[OK] 使用手动教学坐标 {SHOW_ITEM_COORD} 点击成功", "OK")
                clicked = True
                time.sleep(2)
            except Exception as e:
                self.log(f"手动教学坐标失败,尝试备用坐标: {str(e)[:50]}", "DEBUG")
                # 备用坐标
                try:
                    driver.tap([(540, 400)])  # 备用坐标
                    self.log("[OK] 备用坐标点击成功", "OK")
                    clicked = True
                    time.sleep(2)
                except Exception as e2:
                    self.log(f"方法3失败: {str(e2)[:50]}", "DEBUG")

        if not clicked:
            raise Exception("无法在列表页点击演出")

        return True

    def _click_target_show(self, driver, keyword):
        """点击目标演出 - 增强健壮性版本

        增强功能:
        1. 多种元素类型查找(TextView + 列表项)
        2. 滚动搜索机制
        3. 多次重试机制
        4. 可见性验证
        5. 多种点击方式(元素点击 + 坐标点击)
        6. 详细日志记录
        """
        self.log(f"=== 点击搜索结果: '{keyword}' ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 等待搜索结果加载完成
        self.log("等待搜索结果加载...", "INFO")
        time.sleep(2)  # 从1.5秒增加到2秒

        # 尝试3次查找和点击
        for attempt in range(3):
            if attempt > 0:
                self.log(f"第{attempt + 1}次尝试查找搜索结果...", "INFO")
                # 向下滚动查找更多结果
                try:
                    driver.execute_script("mobile: scrollGesture", {
                        "left": 100, "top": 400, "width": 500, "height": 800,
                        "direction": "down",
                        "percent": 0.5
                    })
                    self.log("向下滚动查找更多结果", "DEBUG")
                    time.sleep(1)
                except Exception as e:
                    self.log(f"滚动失败: {str(e)[:30]}", "DEBUG")

            # 方法1: 查找TextView元素
            self.log("方法1: 查找TextView元素...", "DEBUG")
            candidates = []

            try:
                textviews = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                self.log(f"找到 {len(textviews)} 个TextView元素", "DEBUG")

                # 策略A: 完全匹配关键词
                for tv in textviews[:80]:  # 从50个增加到80个
                    try:
                        if not tv.is_displayed():
                            continue
                        text = tv.text or ""
                        if keyword in text:
                            # 验证元素位置合理(排除标题栏等)
                            location = tv.location
                            if location['y'] > 200:  # 标题栏一般在200px以内
                                candidates.append((tv, text, 100, "完全匹配"))
                                self.log(f"找到完全匹配: {text[:30]}", "DEBUG")
                    except Exception as e:
                        continue

                # 策略B: 关键词前5个字匹配 (之前是3个字)
                if not candidates and len(keyword) >= 5:
                    short_keyword = keyword[:5]
                    self.log(f"尝试前5字匹配: '{short_keyword}'", "DEBUG")
                    for tv in textviews[:80]:
                        try:
                            if not tv.is_displayed():
                                continue
                            text = tv.text or ""
                            if text and short_keyword in text:
                                location = tv.location
                                if location['y'] > 200:
                                    candidates.append((tv, text, 90, "前5字匹配"))
                                    self.log(f"找到前5字匹配: {text[:30]}", "DEBUG")
                        except:
                            continue

                # 策略C: 关键词前3个字匹配
                if not candidates and len(keyword) >= 3:
                    short_keyword = keyword[:3]
                    self.log(f"尝试前3字匹配: '{short_keyword}'", "DEBUG")
                    for tv in textviews[:80]:
                        try:
                            if not tv.is_displayed():
                                continue
                            text = tv.text or ""
                            if text and short_keyword in text:
                                location = tv.location
                                if location['y'] > 200:
                                    candidates.append((tv, text, 80, "前3字匹配"))
                                    self.log(f"找到前3字匹配: {text[:30]}", "DEBUG")
                        except:
                            continue

                # 策略D: 任意连续3个字符匹配
                if not candidates and len(keyword) >= 3:
                    self.log("尝试部分匹配...", "DEBUG")
                    for tv in textviews[:80]:
                        try:
                            if not tv.is_displayed():
                                continue
                            text = tv.text or ""
                            if text and len(text) >= 3:
                                for i in range(len(keyword) - 2):
                                    substr = keyword[i:i+3]
                                    if substr in text:
                                        location = tv.location
                                        if location['y'] > 200:
                                            candidates.append((tv, text, 60, "部分匹配"))
                                            self.log(f"找到部分匹配: {text[:30]}", "DEBUG")
                                            break
                        except:
                            continue

            except Exception as e:
                self.log(f"TextView查找失败: {str(e)[:50]}", "WARN")

            # 方法2: 尝试通过UiAutomator查找
            if not candidates:
                self.log("方法2: 尝试UiAutomator查找...", "DEBUG")
                try:
                    # 完全匹配
                    selector = f'new UiSelector().textContains("{keyword}").clickable(true)'
                    els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
                    if els:
                        for el in els[:3]:
                            try:
                                if el.is_displayed():
                                    text = el.text or keyword
                                    candidates.append((el, text, 95, "UiAutomator完全匹配"))
                                    self.log(f"UiAutomator找到: {text[:30]}", "DEBUG")
                            except:
                                continue

                    # 前3字匹配
                    if not candidates and len(keyword) >= 3:
                        short_keyword = keyword[:3]
                        selector = f'new UiSelector().textContains("{short_keyword}").clickable(true)'
                        els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
                        if els:
                            for el in els[:3]:
                                try:
                                    if el.is_displayed():
                                        text = el.text or short_keyword
                                        candidates.append((el, text, 75, "UiAutomator前3字匹配"))
                                        self.log(f"UiAutomator前3字: {text[:30]}", "DEBUG")
                                except:
                                    continue

                except Exception as e:
                    self.log(f"UiAutomator查找失败: {str(e)[:50]}", "DEBUG")

            # 如果找到候选项,按优先级排序并点击
            if candidates:
                # 按优先级排序
                candidates.sort(key=lambda x: x[2], reverse=True)
                self.log(f"找到 {len(candidates)} 个候选项", "INFO")

                # 尝试点击前3个候选项(防止第一个点击失败)
                for idx, (element, text, priority, match_type) in enumerate(candidates[:3]):
                    try:
                        self.log(f"尝试点击候选项{idx+1}: {text[:40]} (优先级:{priority}, 类型:{match_type})", "INFO")

                        # 方式1: 直接点击元素
                        try:
                            element.click()
                            self.log(f"[OK] 元素点击成功", "OK")
                            time.sleep(2.5)  # 增加等待时间确保页面跳转
                            return True
                        except Exception as e1:
                            self.log(f"元素点击失败: {str(e1)[:30]}", "DEBUG")

                            # 方式2: 获取元素坐标后点击
                            try:
                                location = element.location
                                size = element.size
                                x = location['x'] + size['width'] // 2
                                y = location['y'] + size['height'] // 2

                                driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                                self.log(f"[OK] 坐标点击成功 ({x}, {y})", "OK")
                                time.sleep(2.5)
                                return True
                            except Exception as e2:
                                self.log(f"坐标点击失败: {str(e2)[:30]}", "DEBUG")
                                continue

                    except Exception as e:
                        self.log(f"候选项{idx+1}点击失败: {str(e)[:50]}", "WARN")
                        continue

                # 如果前3个都失败,继续下一轮尝试
                if attempt < 2:
                    continue

        # 所有尝试都失败后,使用坐标兜底
        self.log("所有匹配尝试失败,使用坐标兜底点击第一个搜索结果", "WARN")

        # 使用固定的搜索结果坐标 (337, 329)
        try:
            x, y = 337, 329
            self.log(f"使用坐标点击搜索结果: ({x}, {y})", "INFO")
            driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
            time.sleep(2.5)

            # 验证是否跳转成功(检测是否不在搜索结果页)
            try:
                time.sleep(0.5)
                # 简单验证:搜索结果页特征消失
                search_indicator = driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().className("android.widget.EditText")'
                )
                if not search_indicator or not search_indicator[0].is_displayed():
                    self.log(f"[OK] 坐标点击成功,已跳转", "OK")
                    return True
            except:
                pass

            self.log(f"坐标点击完成,等待验证...", "INFO")
            return True

        except Exception as e:
            self.log(f"坐标点击失败: {str(e)[:50]}", "ERROR")

        self.log("所有点击尝试均失败", "ERROR")
        return False

    def _wait_for_detail_page(self, driver, timeout=5):
        """等待详情页加载 - 增强版"""
        self.log("=== 步骤5: 等待详情页加载 ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 多种详情页标识
        detail_markers = [
            ('new UiSelector().textContains("立即购买")', "立即购买"),
            ('new UiSelector().textContains("立即抢购")', "立即抢购"),
            ('new UiSelector().textContains("特惠选座")', "特惠选座"),
            ('new UiSelector().textContains("选座购买")', "选座购买"),
            ('new UiSelector().textContains("选择场次")', "选择场次"),
            ('new UiSelector().textContains("想看")', "想看"),
            ('new UiSelector().textContains("购票")', "购票"),
        ]

        end_time = time.time() + timeout
        while time.time() < end_time:
            for marker, name in detail_markers:
                try:
                    els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, marker)
                    if els:
                        self.log(f"[OK] 找到详情页元素: {name}", "OK")
                        return True
                except:
                    continue
            time.sleep(0.5)

        self.log("详情页未加载,可能在演出列表页", "WARN")
        return False

    def _dismiss_detail_popups(self, driver):
        """关闭详情页弹窗 - 增强版 (服务说明、购票须知等)"""
        self.log("检查详情页弹窗...", "INFO")

        from appium.webdriver.common.appiumby import AppiumBy

        # 检查常见弹窗类型
        popup_types = [
            'new UiSelector().textContains("服务说明")',
            'new UiSelector().textContains("购票须知")',
            'new UiSelector().textContains("温馨提示")',
            'new UiSelector().textContains("重要提示")',
        ]

        has_popup = False
        for popup_type in popup_types:
            try:
                popup_check = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, popup_type)
                if popup_check:
                    popup_name = popup_type.split('"')[1]
                    self.log(f"检测到弹窗: {popup_name}", "INFO")
                    has_popup = True
                    break
            except:
                continue

        if not has_popup:
            self.log("没有发现详情页弹窗", "INFO")
            return False

        # 方法1: 查找关闭按钮
        close_patterns = [
            'new UiSelector().resourceId("cn.damai:id/btn_close")',
            'new UiSelector().resourceId("cn.damai:id/iv_close")',
            'new UiSelector().descriptionContains("关闭")',
            'new UiSelector().descriptionContains("close")',
            'new UiSelector().className("android.widget.ImageView").clickable(true)',
        ]

        for pattern in close_patterns:
            try:
                els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, pattern)
                # 查找右上角的关闭按钮 (x > 300, y < 200)
                for el in els:
                    try:
                        bounds = el.get_attribute("bounds")
                        if bounds and "[" in bounds:
                            coords = bounds.replace("][", ",").replace("[", "").replace("]", "").split(",")
                            x1, y1 = int(coords[0]), int(coords[1])
                            if x1 > 300 and y1 < 200:
                                el.click()
                                self.log(f"[OK] 点击关闭按钮 (坐标约: {x1}, {y1})", "OK")
                                time.sleep(1)
                                return True
                    except:
                        continue
            except:
                continue

        # 方法2: 坐标点击
        self.log("尝试坐标点击关闭弹窗", "INFO")
        close_coords = [
            (340, 160),  # 右上角位置1
            (338, 158),
            (345, 163),
            (680, 160),  # 更靠右
            (650, 140),
        ]

        for x, y in close_coords:
            try:
                driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                self.log(f"点击坐标 ({x}, {y})", "DEBUG")
                time.sleep(0.8)

                # 检查弹窗是否还在
                still_has_popup = False
                for popup_type in popup_types:
                    try:
                        popup_check = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, popup_type)
                        if popup_check:
                            still_has_popup = True
                            break
                    except:
                        continue

                if not still_has_popup:
                    self.log(f"[OK] 成功关闭弹窗 (坐标: {x}, {y})", "OK")
                    return True
            except:
                continue

        self.log("未能关闭弹窗,将继续尝试", "WARN")
        return False

    def _click_ticket_entry(self, driver):
        """点击票档和场次选择入口 - 使用手动验证的固定坐标"""
        self.log("=== 点击票档和场次选择入口 ===", "STEP")

        # 演出详情页票档入口坐标 (2025-11-16 手动验证)
        DETAIL_PAGE_TICKET_ENTRY_COORD = (464, 1277)

        try:
            # 先关闭可能的弹窗
            self._dismiss_detail_popups(driver)
            time.sleep(0.5)

            # 使用坐标点击
            self.log(f"点击坐标 {DETAIL_PAGE_TICKET_ENTRY_COORD} (票档和场次选择入口)", "INFO")
            driver.tap([DETAIL_PAGE_TICKET_ENTRY_COORD])
            self.log("[OK] 已点击票档和场次选择入口", "OK")
            return True

        except Exception as e:
            self.log(f"点击票档入口失败: {e}", "ERROR")
            # 尝试重试一次
            try:
                time.sleep(1)
                driver.tap([DETAIL_PAGE_TICKET_ENTRY_COORD])
                self.log("[OK] 重试成功", "OK")
                return True
            except Exception as e2:
                self.log(f"重试失败: {e2}", "ERROR")
                return False

    def _click_buy_button(self, driver):
        """点击购买按钮 - 增强版 (支持多种按钮文本和坐标兜底)"""
        self.log("=== 步骤6: 点击购买按钮 ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        # 先关闭可能的弹窗
        self._dismiss_detail_popups(driver)
        time.sleep(0.5)

        # 扩展的购买按钮匹配模式
        buy_patterns = [
            ('new UiSelector().textContains("特惠选座")', "特惠选座"),
            ('new UiSelector().textContains("立即购买")', "立即购买"),
            ('new UiSelector().textContains("立即抢购")', "立即抢购"),
            ('new UiSelector().textContains("立即预订")', "立即预订"),
            ('new UiSelector().textContains("马上抢")', "马上抢"),
            ('new UiSelector().textContains("选座购买")', "选座购买"),
            ('new UiSelector().textContains("选择场次")', "选择场次"),
            ('new UiSelector().textContains("购票")', "购票"),
            ('new UiSelector().textContains("抢票")', "抢票"),
        ]

        for pattern, name in buy_patterns:
            try:
                els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, pattern)
                if els:
                    # 尝试点击每个匹配的元素
                    for i, el in enumerate(els[:3]):  # 最多尝试3个
                        try:
                            # 检查元素是否可点击
                            clickable = el.get_attribute("clickable")
                            bounds = el.get_attribute("bounds")

                            if clickable == "true" or not clickable:  # 可点击或未知
                                el.click()
                                self.log(f"[OK] 点击按钮: {name} (第{i+1}个)", "OK")
                                time.sleep(2)
                                return True
                        except Exception as e:
                            self.log(f"点击{name}第{i+1}个失败: {e}", "DEBUG")
                            continue
            except:
                continue

        # 文本匹配失败,使用坐标兜底 - 优先使用手动教学验证的坐标
        self.log("文本匹配失败,尝试手动教学验证的坐标点击购票按钮", "WARN")

        # 手动教学验证的坐标 + 备用坐标
        BUY_BUTTON_COORD = (464, 1227)  # 立即购票按钮 (手动教学验证)
        button_coords = [
            BUY_BUTTON_COORD,  # 手动教学验证的坐标 (优先)
            (513, 1208),  # 特惠选座按钮 (右下角)
            (600, 1200),  # 购买按钮可能位置1
            (360, 1200),  # 购买按钮可能位置2
            (360, 1250),  # 底部中间
            (500, 1250),  # 底部偏右
        ]

        for x, y in button_coords:
            try:
                driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
                self.log(f"点击坐标: ({x}, {y})", "INFO")
                time.sleep(2)

                # 简单检查:是否进入了下一步
                # 可以通过检查页面是否有变化来判断
                try:
                    # 如果能找到订单相关元素,说明点击成功
                    order_markers = [
                        'new UiSelector().textContains("提交订单")',
                        'new UiSelector().textContains("确认")',
                        'new UiSelector().textContains("座位")',
                        'new UiSelector().textContains("场次")',
                    ]

                    for marker in order_markers:
                        els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, marker)
                        if els:
                            self.log(f"[OK] 坐标点击成功,已进入下一步", "OK")
                            return True
                except:
                    pass

            except Exception as e:
                self.log(f"坐标 ({x}, {y}) 点击失败: {e}", "DEBUG")
                continue

        # 最后尝试:如果所有都失败,至少点击一次最常用的位置
        self.log("使用最后兜底坐标: (513, 1208)", "WARN")
        driver.execute_script("mobile: clickGesture", {"x": 513, "y": 1208})
        time.sleep(2)
        return True

    def _select_session_and_price(self, driver, max_retries=3):
        """选择场次和票档 - 优化版 (快速点击API + 减少等待)

        参数:
            driver: Appium driver
            max_retries: 最大重试次数

        返回:
            bool: 是否选择成功

        注意:
            - 场次/票档坐标因演出而异,这里提供的是参考坐标
            - 使用前建议手动测试坐标是否准确
        """
        self.log("=== 选择场次和票档 (优化版) ===", "STEP")

        # 手动教学验证的坐标 (参考坐标,因演出而异)
        SESSION_SELECTOR_COORD = (209, 435)   # 场次选择坐标
        PRICE_SELECTOR_COORD = (169, 659)     # 票档选择坐标
        CONFIRM_BUTTON_COORD = (558, 1233)    # 确认按钮坐标

        self.log("[WARN] 场次/票档坐标因演出而异,请确保坐标正确!", "WARNING")

        # 快速点击函数 (使用mobile:clickGesture提速)
        def fast_click(coord, name):
            for retry in range(max_retries):
                try:
                    if retry > 0:
                        time.sleep(0.3)  # ✨ 优化: 1秒 → 0.3秒

                    # ✨ 优化: 使用mobile:clickGesture代替tap
                    driver.execute_script("mobile: clickGesture", {
                        "x": coord[0],
                        "y": coord[1]
                    })
                    self.log(f"[OK] {name} 点击成功 {coord}", "OK")
                    return True

                except Exception as e:
                    if retry == max_retries - 1:
                        self.log(f"{name}点击失败: {str(e)[:50]}", "ERROR")
                        return False
            return False

        # 步骤1: 选择场次 (快速点击)
        self.log(f"[1/3] 选择场次 {SESSION_SELECTOR_COORD}", "STEP")
        if not fast_click(SESSION_SELECTOR_COORD, "场次"):
            return False
        time.sleep(0.5)  # ✨ 优化: 1秒 → 0.5秒

        # 步骤2: 选择票档 (快速点击)
        self.log(f"[2/3] 选择票档 {PRICE_SELECTOR_COORD}", "STEP")
        if not fast_click(PRICE_SELECTOR_COORD, "票档"):
            return False
        time.sleep(0.5)  # ✨ 优化: 1秒 → 0.5秒

        # 步骤3: 点击确认按钮 (快速点击)
        self.log(f"[3/3] 点击确认 {CONFIRM_BUTTON_COORD}", "STEP")
        if not fast_click(CONFIRM_BUTTON_COORD, "确认按钮"):
            return False
        time.sleep(1.5)  # ✨ 优化: 2秒 → 1.5秒

        self.log("[OK] 场次和票档选择完成! (总耗时: ~2.5秒)", "SUCCESS")
        return True

    def _handle_queue_retry(self, driver, max_retries=200):
        """处理排队重试 - 优化版 (快速点击 + 智能检测)

        参数:
            driver: Appium driver
            max_retries: 最大重试次数

        返回:
            bool: 是否成功突破排队或无需排队
        """
        self.log("=== 检查是否需要排队重试 (优化版) ===", "STEP")

        # 手动教学验证的重试按钮坐标
        RETRY_BUTTON_COORD = (376, 907)

        # 排队关键词
        queue_keywords = [
            "当前排队的人数太多",
            "排队的人数太多",
            "正在排队",
            "please wait"
        ]

        # 1. 快速检测是否有排队消息
        def check_queue():
            try:
                page_source = driver.page_source
                for keyword in queue_keywords:
                    if keyword in page_source:
                        return True, keyword
                return False, None
            except:
                return None, None

        self.log("检测页面是否显示排队消息...", "INFO")
        time.sleep(0.5)  # ✨ 优化: 1秒 → 0.5秒

        queue_detected, detected_keyword = check_queue()

        if queue_detected is False:
            self.log("[OK] 未检测到排队消息,无需重试", "OK")
            return True

        if queue_detected is None:
            self.log("[WARN] 检测失败,尝试点击几次", "WARN")
            queue_detected = True  # 保守处理

        # 2. 疯狂点击模式 (优化版)
        if queue_detected:
            self.log("="*50, "WARNING")
            self.log(f"开始疯狂点击 (最多{max_retries}次, 坐标{RETRY_BUTTON_COORD})...", "WARNING")
            self.log(f"检测到: {detected_keyword}", "INFO")
            self.log("="*50, "WARNING")

            retry_count = 0
            check_interval = 5  # ✨ 优化: 10次 → 5次检查一次

            while retry_count < max_retries:
                # 检查是否被用户停止
                if not self.grabbing:
                    self.log("抢票已被用户停止", "WARN")
                    return False

                retry_count += 1

                # ✨ 优化: 更频繁检查状态 (5次而不是10次)
                if retry_count % check_interval == 0:
                    self.log(f"已重试 {retry_count}/{max_retries} 次", "INFO")

                    still_queuing, _ = check_queue()
                    if still_queuing is False:
                        self.log(f"[OK] 成功突破排队! (共{retry_count}次)", "SUCCESS")
                        return True

                try:
                    # ✨ 优化: 使用mobile:clickGesture快速点击
                    driver.execute_script("mobile: clickGesture", {
                        "x": RETRY_BUTTON_COORD[0],
                        "y": RETRY_BUTTON_COORD[1]
                    })
                    time.sleep(0.05)  # ✨ 优化: 0.1秒 → 0.05秒 (更快!)

                except Exception as e:
                    # 静默失败,继续重试
                    pass
                    time.sleep(0.3)

            if success:
                self.log("[OK] 成功突破排队!", "SUCCESS")
            else:
                self.log(f"完成 {retry_count} 次重试,可能需要继续等待", "INFO")

            return success

        return True

    def _recover_page_state(self, driver, target_state, max_attempts=3):
        """页面状态恢复机制 - 当页面状态异常时自动恢复

        参数:
            driver: Appium driver
            target_state: 目标页面状态 (PageState枚举)
            max_attempts: 最大尝试次数

        返回:
            (success, current_state): 是否成功恢复, 当前页面状态
        """
        self.log(f"=== 页面状态恢复 (目标: {target_state}) ===", "STEP")

        from appium.webdriver.common.appiumby import AppiumBy

        for attempt in range(max_attempts):
            if attempt > 0:
                self.log(f"第{attempt + 1}次恢复尝试...", "INFO")
                time.sleep(1)

            # 检测当前页面状态
            try:
                success, current_state, texts = self._verify_page_state(
                    driver, target_state, f"恢复尝试{attempt+1}", timeout=3
                )
                if success:
                    self.log(f"[OK] 页面状态已正确: {current_state}", "OK")
                    return True, current_state

                self.log(f"当前状态: {current_state}, 目标: {target_state}", "INFO")

            except Exception as e:
                self.log(f"状态检测失败: {str(e)[:50]}", "WARN")
                current_state = PageState.UNKNOWN

            # 根据当前状态和目标状态,执行恢复操作
            try:
                # 情况1: 目标是HOME,但不在HOME
                if target_state == PageState.HOME and current_state != PageState.HOME:
                    self.log("尝试返回首页...", "INFO")

                    # 方法A: 按返回键多次
                    for _ in range(3):
                        try:
                            driver.press_keycode(4)  # KEYCODE_BACK
                            time.sleep(0.5)
                        except:
                            pass

                    # 方法B: 点击首页标签
                    try:
                        home_tabs = [
                            'new UiSelector().textContains("首页").clickable(true)',
                            'new UiSelector().descriptionContains("首页").clickable(true)',
                            'new UiSelector().resourceId("cn.damai:id/tab_home")',
                        ]
                        for selector in home_tabs:
                            els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
                            if els and els[0].is_displayed():
                                els[0].click()
                                self.log("点击首页标签", "INFO")
                                time.sleep(1)
                                break
                    except Exception as e:
                        self.log(f"点击首页失败: {str(e)[:30]}", "DEBUG")

                    continue

                # 情况2: 目标是SEARCH,但不在SEARCH
                elif target_state == PageState.SEARCH and current_state != PageState.SEARCH:
                    self.log("尝试进入搜索页...", "INFO")

                    # 先回到首页
                    driver.press_keycode(4)  # KEYCODE_BACK
                    time.sleep(0.5)

                    # 点击搜索框
                    try:
                        self._goto_search_page(driver)
                    except Exception as e:
                        self.log(f"进入搜索页失败: {str(e)[:50]}", "WARN")

                    continue

                # 情况3: 目标是RESULT,但不在RESULT
                elif target_state == PageState.RESULT and current_state != PageState.RESULT:
                    self.log("搜索结果页丢失,无法自动恢复,需要重新搜索", "WARN")
                    return False, current_state

                # 情况4: 在弹窗/错误页
                elif current_state in [PageState.POPUP, PageState.ERROR]:
                    # 根据配置决定是否处理弹窗
                    enable_popup = getattr(self, 'enable_popup_detection', False)

                    if not enable_popup:
                        self.log("[INFO] ⚠️ 弹窗检测已禁用，跳过弹窗/错误处理", "INFO")
                        time.sleep(1)
                        continue

                    self.log("检测到弹窗/错误,尝试关闭...", "INFO")

                    # 关闭弹窗 - 检查返回值
                    popup_result = self._dismiss_popups(driver)

                    if popup_result is False:
                        # 检测到是功能页面，不是弹窗，不应该关闭
                        self.log("[INFO] ⚠️ 检测到功能页面(非弹窗)，跳过关闭操作", "INFO")
                        # 等待一下，可能页面状态会改变
                        time.sleep(1)
                        continue

                    # 确实是弹窗才执行后续操作
                    time.sleep(1)

                    # 如果还是不对,按返回键
                    driver.press_keycode(4)
                    time.sleep(0.5)

                    continue

                # 情况5: 未知状态
                elif current_state == PageState.UNKNOWN:
                    self.log("页面状态未知,尝试返回首页...", "WARN")

                    # 多次返回
                    for _ in range(5):
                        driver.press_keycode(4)
                        time.sleep(0.3)

                    # 点击首页标签
                    try:
                        home_tab = driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().textContains("首页").clickable(true)'
                        )
                        if home_tab:
                            home_tab[0].click()
                            time.sleep(1)
                    except:
                        pass

                    continue

                # 其他情况
                else:
                    self.log(f"无法处理的状态组合: 当前={current_state}, 目标={target_state}", "WARN")
                    return False, current_state

            except Exception as e:
                self.log(f"恢复操作失败: {str(e)[:50]}", "ERROR")
                continue

        # 所有尝试失败
        self.log(f"页面状态恢复失败 (尝试{max_attempts}次)", "ERROR")
        try:
            _, final_state, _ = self._verify_page_state(driver, target_state, "最终", timeout=2)
            return False, final_state
        except:
            return False, PageState.UNKNOWN

    # ========== 辅助方法结束 ==========

    def reconnect(self):
        """重新连接设备"""
        self.log("正在重新连接设备...", "INFO")
        self.status_label.config(text="● 重连中...", fg="orange")
        self.reconnect_btn.config(state=tk.DISABLED)

        def do_reconnect():
            try:
                import subprocess

                # 停止监控
                if self.running:
                    self.running = False
                    time.sleep(0.5)

                # 关闭旧连接
                if self.bot and self.bot.driver:
                    try:
                        self.bot.driver.quit()
                    except:
                        pass
                self.bot = None

                # 等待清理
                time.sleep(1)

                # 步骤1: 检查ADB连接
                port = self.port_var.get()
                self.log(f"[步骤1/2] 检查ADB连接 (端口: {port})...", "INFO")

                result = subprocess.run(f'"{ADB_EXE}" devices', capture_output=True, text=True, shell=True, timeout=5)
                device_address = f"127.0.0.1:{port}"
                is_connected = device_address in result.stdout and "offline" not in result.stdout

                if is_connected:
                    self.log(f"ADB设备已连接: {device_address}", "OK")
                else:
                    self.log(f"正在连接到 {device_address}...", "INFO")
                    connect_result = subprocess.run(
                        f'"{ADB_EXE}" connect {device_address}',
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=10
                    )

                    if "connected" in connect_result.stdout.lower() or "already connected" in connect_result.stdout.lower():
                        self.log(f"ADB连接成功", "OK")
                    else:
                        raise Exception(f"ADB连接失败: {connect_result.stdout.strip()}")

                # 验证连接（等待设备完全就绪）
                time.sleep(2)
                verify_result = subprocess.run(f'"{ADB_EXE}" devices', capture_output=True, text=True, shell=True, timeout=5)

                # 检查目标设备的状态（避免被其他offline设备影响）
                device_found = False
                device_offline = False
                for line in verify_result.stdout.splitlines():
                    if device_address in line:
                        device_found = True
                        if "offline" in line:
                            device_offline = True
                        elif "device" in line:
                            device_offline = False
                        break

                if not device_found:
                    raise Exception(f"ADB设备 {device_address} 未找到")
                if device_offline:
                    raise Exception(f"ADB设备 {device_address} 已离线")

                # 步骤2: 重新初始化Appium
                self.log("[步骤2/2] 初始化Appium连接...", "INFO")
                self.bot = DamaiBot()
                self.status_label.config(text="● 已连接", fg="green")
                self.log("重新连接成功！", "OK")

                # 重置设备分辨率
                self.device_width = 0
                self.device_height = 0

                # 更新按钮状态
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.DISABLED)
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.grab_btn.config(state=tk.NORMAL)  # 启用抢票按钮
                self.log("[OK] 抢票按钮已启用", "OK")

                # 自动启动截图监控
                self.log("="*60, "STEP")
                self.log("正在启动截图监控...", "INFO")
                self.running = True
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)
                self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.log("[OK] 截图监控已自动启动", "SUCCESS")

            except subprocess.TimeoutExpired:
                self.log("ADB命令执行超时", "ERROR")
                self.status_label.config(text="● 连接失败", fg="red")
                self.connect_btn.config(state=tk.NORMAL)
                self.disconnect_btn.config(state=tk.DISABLED)
                self.reconnect_btn.config(state=tk.NORMAL)
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)
            except Exception as e:
                error_str = str(e)
                self.log(f"重新连接失败: {error_str}", "ERROR")

                if "Could not find a connected Android device" in error_str:
                    self.log("原因: Appium找不到Android设备", "ERROR")
                    self.log(f"解决方法: 请先确保 adb connect 127.0.0.1:{port} 成功", "ERROR")

                self.status_label.config(text="● 连接失败", fg="red")
                self.connect_btn.config(state=tk.NORMAL)
                self.disconnect_btn.config(state=tk.DISABLED)
                self.reconnect_btn.config(state=tk.NORMAL)
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)

        threading.Thread(target=do_reconnect, daemon=True).start()

    def clear_zombie_connections(self):
        """清除ADB僵尸连接"""
        self.log("="*60, "STEP")
        self.log("开始清除ADB僵尸连接...", "STEP")
        self.log("="*60, "STEP")

        self.clear_zombie_btn.config(state=tk.DISABLED)

        def do_clear():
            try:
                # 创建日志适配器
                class GUILogger:
                    def __init__(self, log_func):
                        self.log = log_func

                    def info(self, msg):
                        self.log(msg, 'INFO')

                    def warning(self, msg):
                        self.log(msg, 'WARN')

                    def error(self, msg):
                        self.log(msg, 'ERROR')

                    def success(self, msg):
                        self.log(msg, 'SUCCESS')

                # 创建连接修复器
                gui_logger = GUILogger(self.log)
                from connection_auto_fixer import ConnectionAutoFixer
                fixer = ConnectionAutoFixer(logger=gui_logger)

                # 执行清除
                success = fixer.clear_zombie_connections(max_retries=3)

                if success:
                    self.log("="*60, "OK")
                    self.log("✓ ADB僵尸连接已清除！", "OK")
                    self.log("="*60, "OK")
                    self.log("提示: 现在可以重新连接设备了", "INFO")
                else:
                    self.log("="*60, "ERROR")
                    self.log("✗ 清除僵尸连接失败", "ERROR")
                    self.log("="*60, "ERROR")
                    self.log("建议:", "ERROR")
                    self.log("  1. 重启红手指客户端", "ERROR")
                    self.log("  2. 重启电脑（如果问题持续）", "ERROR")

            except Exception as e:
                self.log(f"清除僵尸连接时出错: {e}", "ERROR")
            finally:
                self.clear_zombie_btn.config(state=tk.NORMAL)

        threading.Thread(target=do_clear, daemon=True).start()

    # ==================== 实时诊断悬浮窗 ====================

    def open_diagnose_window(self):
        """打开实时诊断悬浮窗"""
        if self.diagnose_window is not None and self.diagnose_window.winfo_exists():
            # 窗口已存在,激活它
            self.diagnose_window.deiconify()
            self.diagnose_window.lift()
            return

        # 创建新窗口
        self.diagnose_window = tk.Toplevel(self.root)
        self.diagnose_window.title("实时页面诊断")
        self.diagnose_window.geometry("450x700")
        self.diagnose_window.attributes("-topmost", True)

        # 创建界面
        main_frame = ttk.Frame(self.diagnose_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="【实时页面状态监控】",
                                font=('Microsoft YaHei', 12, 'bold'))
        title_label.pack(pady=5)

        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.diag_start_btn = ttk.Button(control_frame, text="开始监控",
                                         command=self.start_diagnose_monitoring)
        self.diag_start_btn.pack(side=tk.LEFT, padx=5)

        self.diag_stop_btn = ttk.Button(control_frame, text="停止监控",
                                        command=self.stop_diagnose_monitoring,
                                        state=tk.DISABLED)
        self.diag_stop_btn.pack(side=tk.LEFT, padx=5)

        self.diag_refresh_btn = ttk.Button(control_frame, text="立即刷新",
                                           command=self.diagnose_manual_refresh)
        self.diag_refresh_btn.pack(side=tk.LEFT, padx=5)

        # 配置区
        config_frame = ttk.LabelFrame(main_frame, text="监控配置", padding=5)
        config_frame.pack(fill=tk.X, pady=5)

        ttk.Label(config_frame, text="刷新间隔(秒):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.diag_interval_var = tk.StringVar(value="2")
        ttk.Entry(config_frame, textvariable=self.diag_interval_var, width=10).grid(row=0, column=1, padx=5)

        # 当前状态显示
        status_frame = ttk.LabelFrame(main_frame, text="当前状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 页面状态 - 大字体
        ttk.Label(status_frame, text="页面状态:").pack(anchor=tk.W)
        self.diag_state_label = ttk.Label(status_frame, text="未连接",
                                          font=('Microsoft YaHei', 18, 'bold'),
                                          foreground='red')
        self.diag_state_label.pack(anchor=tk.W, pady=5)

        # Activity
        ttk.Label(status_frame, text="当前Activity:").pack(anchor=tk.W, pady=(10,0))
        self.diag_activity_label = ttk.Label(status_frame, text="-",
                                             font=('Consolas', 9))
        self.diag_activity_label.pack(anchor=tk.W)

        # Package
        ttk.Label(status_frame, text="当前Package:").pack(anchor=tk.W, pady=(5,0))
        self.diag_package_label = ttk.Label(status_frame, text="-",
                                            font=('Consolas', 9))
        self.diag_package_label.pack(anchor=tk.W)

        # 元素数量
        ttk.Label(status_frame, text="页面元素数:").pack(anchor=tk.W, pady=(5,0))
        self.diag_element_label = ttk.Label(status_frame, text="0",
                                            font=('Microsoft YaHei', 10))
        self.diag_element_label.pack(anchor=tk.W)

        # 更新时间
        self.diag_time_label = ttk.Label(status_frame, text="最后更新: -",
                                         font=('Consolas', 8),
                                         foreground='gray')
        self.diag_time_label.pack(anchor=tk.W, pady=(10,0))

        # 状态历史
        history_frame = ttk.LabelFrame(main_frame, text="状态变化历史", padding=5)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.diag_history_text = scrolledtext.ScrolledText(history_frame, height=12,
                                                           font=('Consolas', 8))
        self.diag_history_text.pack(fill=tk.BOTH, expand=True)

        # 窗口关闭事件
        self.diagnose_window.protocol("WM_DELETE_WINDOW", self.on_diagnose_window_closing)

        self.log("实时诊断窗口已打开", "INFO")

    def on_diagnose_window_closing(self):
        """诊断窗口关闭事件"""
        self.stop_diagnose_monitoring()
        if self.diagnose_window:
            self.diagnose_window.withdraw()

    def start_diagnose_monitoring(self):
        """开始诊断监控"""
        if self.diagnose_is_monitoring:
            return

        if not self.bot or not self.bot.driver:
            self.diag_add_history("X 未连接设备,请先连接!")
            return

        self.diagnose_is_monitoring = True
        self.diag_start_btn.config(state=tk.DISABLED)
        self.diag_stop_btn.config(state=tk.NORMAL)

        # 启动监控线程
        self.diagnose_thread = threading.Thread(target=self._diagnose_monitor_loop, daemon=True)
        self.diagnose_thread.start()

        self.diag_add_history("开始实时监控...")
        self.log("实时诊断: 开始监控", "INFO")

    def stop_diagnose_monitoring(self):
        """停止诊断监控"""
        self.diagnose_is_monitoring = False
        if hasattr(self, 'diag_start_btn'):
            self.diag_start_btn.config(state=tk.NORMAL)
        if hasattr(self, 'diag_stop_btn'):
            self.diag_stop_btn.config(state=tk.DISABLED)

        self.diag_add_history("停止监控")
        self.log("实时诊断: 停止监控", "INFO")

    def diagnose_manual_refresh(self):
        """手动刷新一次"""
        if not self.bot or not self.bot.driver:
            self.diag_add_history("X 未连接设备!")
            return

        threading.Thread(target=self._diagnose_refresh_once, daemon=True).start()

    def _diagnose_monitor_loop(self):
        """诊断监控循环(增强健壮度)"""
        try:
            interval = float(self.diag_interval_var.get())
            last_state = None
            error_count = 0
            max_errors = 5  # 连续错误超过5次则停止

            while self.diagnose_is_monitoring:
                try:
                    page_state, activity, package, element_count = self._diagnose_get_state()

                    # 检测会话崩溃
                    if page_state == "会话崩溃":
                        self.diag_add_history("! 检测到会话崩溃，停止监控")
                        self.diagnose_is_monitoring = False
                        if hasattr(self, 'diag_start_btn'):
                            self.root.after(0, lambda: self.diag_start_btn.config(state=tk.NORMAL))
                        if hasattr(self, 'diag_stop_btn'):
                            self.root.after(0, lambda: self.diag_stop_btn.config(state=tk.DISABLED))
                        break

                    # 更新显示
                    self._diagnose_update_display(page_state, activity, package, element_count)

                    # 检测状态变化
                    if last_state != page_state:
                        self.diag_add_history(f"状态变化: {page_state}")
                        last_state = page_state

                    # 重置错误计数
                    error_count = 0
                    time.sleep(interval)

                except Exception as e:
                    error_count += 1
                    error_msg = str(e)[:50]
                    self.diag_add_history(f"X 监控错误({error_count}/{max_errors}): {error_msg}")

                    # 连续错误过多，停止监控
                    if error_count >= max_errors:
                        self.diag_add_history(f"! 连续错误{max_errors}次，停止监控")
                        self.diagnose_is_monitoring = False
                        if hasattr(self, 'diag_start_btn'):
                            self.root.after(0, lambda: self.diag_start_btn.config(state=tk.NORMAL))
                        if hasattr(self, 'diag_stop_btn'):
                            self.root.after(0, lambda: self.diag_stop_btn.config(state=tk.DISABLED))
                        break

                    time.sleep(interval)

        except Exception as e:
            self.diag_add_history(f"X 监控线程异常: {str(e)[:100]}")
            self.diagnose_is_monitoring = False
            if hasattr(self, 'diag_start_btn'):
                self.root.after(0, lambda: self.diag_start_btn.config(state=tk.NORMAL))
            if hasattr(self, 'diag_stop_btn'):
                self.root.after(0, lambda: self.diag_stop_btn.config(state=tk.DISABLED))

    def _diagnose_refresh_once(self):
        """手动刷新一次"""
        try:
            page_state, activity, package, element_count = self._diagnose_get_state()
            self._diagnose_update_display(page_state, activity, package, element_count)
            self.diag_add_history(f"手动刷新: {page_state}")

        except Exception as e:
            self.diag_add_history(f"X 刷新失败: {str(e)[:100]}")

    def _diagnose_get_state(self):
        """获取设备状态(增强健壮度)"""
        if not self.bot or not self.bot.driver:
            return "未连接", "-", "-", 0

        driver = self.bot.driver

        try:
            # 设置超时 (红手指云设备需要更长时间)
            driver.implicitly_wait(2)  # 从0.5秒增加到2秒

            # 获取Activity和Package (快速操作)
            activity = "未知"
            package = "未知"
            try:
                activity = driver.current_activity or "未知"
                package = driver.current_package or "未知"
            except Exception as e:
                error_msg = f"[诊断] 获取Activity/Package失败: {e}"
                safe_print(error_msg)
                self.diag_add_history(f"获取Activity/Package失败")

            # 获取page_source (可能慢，添加重试)
            page_source = None
            for retry in range(3):  # 从2次增加到3次
                try:
                    msg = f"[诊断] 尝试获取page_source (第{retry+1}/3次)..."
                    safe_print(msg)
                    if retry == 0:  # 只在第一次尝试时添加到历史记录
                        self.diag_add_history(f"获取page_source...")

                    start_time = time.time()
                    page_source = driver.page_source
                    elapsed = time.time() - start_time

                    if page_source:
                        msg = f"[诊断] 获取成功! 耗时{elapsed:.2f}秒, XML长度{len(page_source)}字符"
                        safe_print(msg)
                        self.diag_add_history(f"OK 获取成功({elapsed:.1f}秒)")
                        break
                    else:
                        safe_print(f"[诊断] page_source为空")
                        self.diag_add_history(f"X page_source为空")
                except Exception as e:
                    error_msg = str(e)[:150]
                    if retry < 2:
                        msg = f"[诊断] 第{retry+1}次失败: {error_msg}, 等待后重试..."
                        safe_print(msg)
                        self.diag_add_history(f"第{retry+1}次失败,重试...")
                        time.sleep(1)  # 从0.3秒增加到1秒
                    else:
                        msg = f"[诊断] 第{retry+1}次失败: {error_msg}, 放弃"
                        safe_print(msg)
                        self.diag_add_history(f"X 第{retry+1}次失败: {error_msg[:50]}")

            if not page_source:
                safe_print(f"[诊断] 最终返回: 获取失败")
                self.diag_add_history(f"! 最终状态: 获取失败")
                return "获取失败", activity, package, 0

            # 解析XML
            try:
                root = ET.fromstring(page_source)
            except ET.ParseError as e:
                safe_print(f"[诊断] XML解析失败: {e}")
                return "XML解析错误", activity, package, 0

            # 提取文字
            all_texts = []
            try:
                for elem in root.iter():
                    text = elem.get('text', '').strip()
                    if text:
                        all_texts.append(text)
            except Exception as e:
                safe_print(f"[诊断] 提取文字失败: {e}")
                all_texts = []

            # 检测页面状态
            page_state = self._diagnose_detect_page_state(all_texts)

            return page_state, activity, package, len(all_texts)

        except Exception as e:
            # 记录详细错误信息
            error_msg = str(e)

            # 检测会话是否崩溃
            if "instrumentation process" in error_msg or "Session" in error_msg:
                safe_print(f"[诊断] 检测到会话崩溃: {error_msg}")
                return "会话崩溃", "-", "-", 0

            safe_print(f"[诊断] 获取状态失败: {error_msg}")
            return "获取失败", error_msg[:30], "-", 0

        finally:
            # 恢复默认超时
            try:
                driver.implicitly_wait(0)
            except:
                pass

    def _diagnose_detect_page_state(self, texts):
        """检测页面状态"""
        text_str = ''.join(texts)

        # 按优先级检测
        if any(k in text_str for k in ['立即开启', '下次再说', '位置权限']):
            return "权限弹窗"
        elif any(k in text_str for k in ['升级提示', '立即下载', '新版本']):
            return "升级弹窗"
        elif any(k in text_str for k in ['网络异常', '加载失败', '服务器错误']):
            return "错误页面"
        elif any(k in text_str for k in ['提交订单', '确认购买', '订单确认']):
            return "订单页"
        elif any(k in text_str for k in ['请先选座', '选座购买', '确认座位']):
            return "选座页"
        elif any(k in text_str for k in ['立即购买', '立即预订', '选择场次', '演出详情']):
            return "详情页"
        elif '搜索结果' in text_str or len([t for t in texts if '•' in t or '音乐' in t]) > 0:
            return "搜索结果页"
        elif any(k in text_str for k in ['搜索演出', '搜索场馆']):
            return "搜索页"
        elif any(k in text_str for k in ['首页', '发现', '我的']):
            return "首页"
        elif any(k in text_str for k in ['加载中', 'loading']):
            return "加载中"
        else:
            return "未知页面"

    def _diagnose_update_display(self, page_state, activity, package, element_count):
        """更新诊断窗口显示"""
        if not hasattr(self, 'diag_state_label'):
            return

        def update():
            # 更新状态文字
            self.diag_state_label.config(text=page_state)

            # 根据状态设置颜色
            color_map = {
                "首页": "green",
                "搜索页": "blue",
                "搜索结果页": "blue",
                "详情页": "purple",
                "选座页": "orange",
                "订单页": "orange",
                "权限弹窗": "red",
                "升级弹窗": "red",
                "错误页面": "red",
                "加载中": "gray",
                "未知页面": "brown",
                "未连接": "red"
            }
            color = color_map.get(page_state, "black")
            self.diag_state_label.config(foreground=color)

            # 更新其他信息
            self.diag_activity_label.config(text=activity)
            self.diag_package_label.config(text=package)
            self.diag_element_label.config(text=str(element_count))

            # 更新时间
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.diag_time_label.config(text=f"最后更新: {timestamp}")

        self.root.after(0, update)

    def diag_add_history(self, message):
        """添加诊断历史记录"""
        if not hasattr(self, 'diag_history_text'):
            return

        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"

        def _add():
            self.diag_history_text.insert(tk.END, log_msg)
            self.diag_history_text.see(tk.END)

            # 限制历史记录行数
            lines = int(self.diag_history_text.index('end-1c').split('.')[0])
            if lines > 100:
                self.diag_history_text.delete('1.0', '2.0')

        self.root.after(0, _add)


    def import_coordinates(self):
        """导入坐标配置文件"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="选择坐标配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filepath:
            try:
                import json
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.coordinates = json.load(f)
                self.coord_status_label.config(text=f"已加载: {Path(filepath).name}", foreground="green")
                self.log(f"坐标配置已加载: {filepath}", "OK")
                self.log(f"包含 {len(self.coordinates)} 个坐标点", "INFO")
            except Exception as e:
                self.log(f"加载坐标配置失败: {e}", "ERROR")
                self.coord_status_label.config(text="加载失败", foreground="red")

    def edit_coordinates(self):
        """打开坐标编辑器"""
        import subprocess
        coord_file = Path(__file__).parent / "coordinates.json"
        if not coord_file.exists():
            # 创建示例坐标文件
            sample_coords = {
                "city_selector": [216, 88],
                "search_entry": [326, 99],
                "search_result": [155, 195],
                "show_item": [337, 329],
                "buy_button": [464, 1227],
                "session_1": [209, 435],
                "session_2": [209, 535],
                "session_3": [209, 635],
                "price_1": [169, 659],
                "price_2": [169, 759],
                "price_3": [169, 859],
                "confirm_button": [558, 1233],
                "retry_button": [376, 907]
            }
            import json
            with open(coord_file, 'w', encoding='utf-8') as f:
                json.dump(sample_coords, f, indent=2, ensure_ascii=False)
            self.log(f"已创建示例坐标文件: {coord_file}", "INFO")

        try:
            subprocess.Popen(['notepad', str(coord_file)])
            self.log("已打开坐标编辑器", "INFO")
        except Exception as e:
            self.log(f"打开编辑器失败: {e}", "ERROR")


def main():
    root = tk.Tk()
    app = SmartAIGUI(root)

    def on_closing():
        app.running = False
        if app.bot and app.bot.driver:
            try:
                app.bot.driver.quit()
            except:
                pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
