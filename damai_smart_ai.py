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
from environment_checker import EnvironmentChecker, EnvironmentFixer, CheckResult

# 延迟导入OCR（首次使用时加载）
_ocr_instance = None

def get_ocr():
    """延迟加载OCR实例"""
    global _ocr_instance
    if _ocr_instance is None:
        from paddleocr import PaddleOCR
        _ocr_instance = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    return _ocr_instance


class PageState:
    """页面状态识别"""
    UNKNOWN = "未知"
    HOME = "首页"
    SEARCH = "搜索页"
    RESULT = "搜索结果"
    DETAIL = "演出详情"
    SEAT = "选座页"
    ORDER = "订单页"
    PERMISSION_DIALOG = "权限弹窗"
    UPGRADE_DIALOG = "升级弹窗"


class SmartAI:
    """智能决策系统"""

    def __init__(self):
        self.current_state = PageState.UNKNOWN
        self.ocr_cache = []  # 缓存OCR结果
        self.last_action_time = 0

    def analyze_screen(self, screenshot, use_ocr=True):
        """分析屏幕截图"""
        if not use_ocr:
            return []

        try:
            # 转换PIL Image到numpy数组
            img_array = np.array(screenshot)

            # OCR识别
            ocr = get_ocr()
            result = ocr.ocr(img_array, cls=True)

            # 提取文字和位置
            texts = []
            if result and result[0]:
                for line in result[0]:
                    box = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text = line[1][0]  # 文字
                    confidence = line[1][1]  # 置信度

                    # 计算中心点
                    center_x = int((box[0][0] + box[2][0]) / 2)
                    center_y = int((box[0][1] + box[2][1]) / 2)

                    texts.append({
                        'text': text,
                        'confidence': confidence,
                        'position': (center_x, center_y),
                        'box': box
                    })

            self.ocr_cache = texts
            return texts

        except Exception as e:
            print(f"OCR识别错误: {e}")
            return []

    def detect_page_state(self, texts):
        """检测当前页面状态"""
        text_list = [t['text'] for t in texts]
        text_str = ''.join(text_list)

        # 按优先级检测
        if any(keyword in text_str for keyword in ['立即开启', '立即升级', '下次再说', '位置权限']):
            return PageState.PERMISSION_DIALOG
        elif any(keyword in text_str for keyword in ['升级提示', '立即下载', '新版本']):
            return PageState.UPGRADE_DIALOG
        elif '请先选座' in text_str or '选座购买' in text_str:
            return PageState.SEAT
        elif '提交订单' in text_str or '确认购买' in text_str:
            return PageState.ORDER
        elif '立即购买' in text_str or '购票' in text_str:
            return PageState.DETAIL
        elif '搜索' in text_str and len([t for t in texts if '搜索' in t['text']]) > 0:
            if any('结果' in t['text'] for t in texts):
                return PageState.RESULT
            else:
                return PageState.SEARCH
        elif '首页' in text_str or '发现' in text_str:
            return PageState.HOME
        else:
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
        self.root.title("大麦抢票智能AI v2.0 - OCR识别")
        # 窗口大小：Canvas 450x800(62.5%缩放) + 右侧控制区400 = 总宽870
        self.root.geometry("870x900")

        self.bot = None
        self.running = False
        self.monitor_thread = None
        self.ai = SmartAI()
        self.use_ocr = tk.BooleanVar(value=True)
        self.auto_action = tk.BooleanVar(value=False)
        self.scale_1to1 = tk.BooleanVar(value=True)  # 1:1显示模式
        self.device_width = 0
        self.device_height = 0
        self.current_screenshot = None  # 保存当前截图
        self.last_cleanup_time = time.time()  # 上次清理时间
        self.cleanup_interval = 20  # 清理间隔(秒)

        # 显示缩放配置（适配1080p显示器）
        self.display_width = 450   # 显示宽度（62.5%缩放）
        self.display_height = 800  # 显示高度（62.5%缩放）
        self.target_width = 720    # 目标设备宽度
        self.target_height = 1280  # 目标设备高度

        # 截图保存
        self.screenshots_dir = Path(__file__).parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        self.last_screenshot_path = None  # 最新截图路径

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        """创建界面"""

        # 顶部标题
        title_frame = tk.Frame(self.root, bg="#1890ff", height=50)
        title_frame.pack(fill=tk.X)
        title_label = tk.Label(
            title_frame,
            text="大麦抢票智能AI - OCR文字识别 + 自动决策",
            font=("微软雅黑", 14, "bold"),
            bg="#1890ff",
            fg="white"
        )
        title_label.pack(pady=12)

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

        # === 中间：控制和配置 ===
        middle_frame = ttk.Frame(main_paned)
        main_paned.add(middle_frame, weight=1)

        # 连接配置
        conn_frame = ttk.LabelFrame(middle_frame, text="设备连接", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(conn_frame, text="ADB端口:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.port_var = tk.StringVar(value="59700")
        ttk.Entry(conn_frame, textvariable=self.port_var, width=12).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        # 自动检测按钮
        self.auto_detect_btn = ttk.Button(conn_frame, text="🔍 自动检测", command=self.auto_detect_port, width=12)
        self.auto_detect_btn.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))

        # 连接按钮区域
        conn_btn_frame = ttk.Frame(conn_frame)
        conn_btn_frame.grid(row=1, column=0, columnspan=3, pady=(8, 0), sticky=tk.W)

        self.connect_btn = ttk.Button(conn_btn_frame, text="连接设备", command=self.connect_device, width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.disconnect_btn = ttk.Button(conn_btn_frame, text="断开连接", command=self.disconnect_device, width=12, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.reconnect_btn = ttk.Button(conn_btn_frame, text="重新连接", command=self.reconnect, width=12, state=tk.DISABLED)
        self.reconnect_btn.pack(side=tk.LEFT)

        # 环境诊断按钮区域
        env_btn_frame = ttk.Frame(conn_frame)
        env_btn_frame.grid(row=2, column=0, columnspan=3, pady=(8, 0), sticky=tk.W)

        self.env_check_btn = ttk.Button(env_btn_frame, text="🔧 环境诊断", command=self.show_environment_check, width=12)
        self.env_check_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.env_fix_btn = ttk.Button(env_btn_frame, text="🔨 一键修复", command=self.auto_fix_environment, width=12)
        self.env_fix_btn.pack(side=tk.LEFT)

        # 连接状态
        self.status_label = tk.Label(conn_frame, text="● 未连接", fg="gray", font=("微软雅黑", 9, "bold"))
        self.status_label.grid(row=3, column=0, columnspan=3, pady=(8, 0))

        # AI配置
        ai_frame = ttk.LabelFrame(middle_frame, text="AI配置", padding="10")
        ai_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(ai_frame, text="启用OCR识别", variable=self.use_ocr).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(ai_frame, text="等比缩放显示(真实坐标)", variable=self.scale_1to1, command=self.on_scale_mode_change).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(ai_frame, text="自动执行操作（实验性）", variable=self.auto_action).pack(anchor=tk.W, pady=2)

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

        ttk.Label(config_frame, text="关键词:").pack(anchor=tk.W, pady=2)
        self.keyword_var = tk.StringVar(value="世界计划")
        ttk.Entry(config_frame, textvariable=self.keyword_var, width=20).pack(fill=tk.X, pady=2)

        # 控制按钮
        btn_frame = ttk.Frame(middle_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(btn_frame, text="开始监控", command=self.start_monitoring, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_monitoring, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)

        # 截图按钮
        screenshot_btn_frame = ttk.Frame(middle_frame)
        screenshot_btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.save_screenshot_btn = ttk.Button(
            screenshot_btn_frame,
            text="📷 保存截图",
            command=lambda: self.save_screenshot(original=True),
            width=25
        )
        self.save_screenshot_btn.pack(fill=tk.X)

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
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.see(tk.END)
        self.bottom_status.config(text=message[:80])

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
        """点击Canvas - 记录坐标（换算到真实设备坐标）"""
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
            self.log(f"✅ 已保存截图 ({size_str}): {filename}", "OK")
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

            # 获取截图
            screenshot_bytes = self.bot.driver.get_screenshot_as_png()
            screenshot = Image.open(io.BytesIO(screenshot_bytes))

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
            self.log(f"更新失败: {e}", "ERROR")
            # 如果是连接相关错误，启用重新连接按钮
            if "WebDriver" in str(e) or "Session" in str(e) or "connection" in str(e).lower():
                self.status_label.config(text="● 连接断开", fg="red")
                self.reconnect_btn.config(state=tk.NORMAL)
                self.running = False
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)

    def monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.update_screenshot_with_ocr()

                # 检查是否需要清理内存（从GUI读取用户设置的间隔）
                current_time = time.time()
                cleanup_interval = float(self.cleanup_var.get())
                if current_time - self.last_cleanup_time >= cleanup_interval:
                    self.cleanup_memory()

                interval = float(self.interval_var.get())
                time.sleep(interval)
            except Exception as e:
                self.log(f"监控错误: {e}", "ERROR")
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
            text="🔍 开始检测",
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
                    'ok': '✅',
                    'warning': '⚠️',
                    'error': '❌'
                }

                for name, result in results.items():
                    symbol = status_symbols.get(result.status, '❓')
                    result_text.insert(tk.END, f"\n{symbol} [{name.upper()}]\n")
                    result_text.insert(tk.END, f"  状态: {result.status.upper()}\n")
                    result_text.insert(tk.END, f"  信息: {result.message}\n")

                    if result.details:
                        result_text.insert(tk.END, f"  详情:\n")
                        for line in result.details.split('\n'):
                            result_text.insert(tk.END, f"    {line}\n")

                    if result.fix_available:
                        result_text.insert(tk.END, f"  💡 修复建议: {result.fix_action}\n")

                    result_text.insert(tk.END, "\n")

                # 总结
                result_text.insert(tk.END, "=" * 70 + "\n")
                result_text.insert(tk.END, "检测完成！\n")

                error_count = sum(1 for r in results.values() if r.status == 'error')
                warning_count = sum(1 for r in results.values() if r.status == 'warning')
                ok_count = sum(1 for r in results.values() if r.status == 'ok')

                result_text.insert(tk.END, f"✅ 正常: {ok_count}  ⚠️ 警告: {warning_count}  ❌ 错误: {error_count}\n")
                result_text.insert(tk.END, "=" * 70 + "\n")

                # 滚动到顶部
                result_text.see(1.0)

            except Exception as e:
                result_text.insert(tk.END, f"\n❌ 检测过程出错: {str(e)}\n")

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
                        result_text.insert(tk.END, f"  ✅ 成功连接到: {found_devices[0]}\n")
                        # 更新GUI端口显示
                        port = found_devices[0].split(':')[1]
                        self.port_var.set(port)
                    else:
                        result_text.insert(tk.END, "  ❌ 未找到可用设备\n")
                else:
                    result_text.insert(tk.END, f"  ✅ 设备已连接: {devices[0]}\n")

                # 2. 检查Appium服务
                result_text.insert(tk.END, "\n[2/3] 检查Appium服务...\n")
                appium_result = checker.check_appium_service()

                if appium_result.status == 'error':
                    result_text.insert(tk.END, "  Appium未运行，尝试启动...\n")
                    success, message = fixer.start_appium(background=True)

                    if success:
                        result_text.insert(tk.END, f"  ✅ {message}\n")
                    else:
                        result_text.insert(tk.END, f"  ℹ️ {message}\n")
                        result_text.insert(tk.END, "  💡 请手动执行: appium --address 127.0.0.1 --port 4723 --allow-cors\n")
                else:
                    result_text.insert(tk.END, "  ✅ Appium服务运行正常\n")

                # 3. 检查UiAutomator2
                result_text.insert(tk.END, "\n[3/3] 检查UiAutomator2 Server...\n")
                if devices:
                    ui2_result = checker.check_uiautomator2(devices[0])

                    if ui2_result.status != 'ok':
                        result_text.insert(tk.END, "  ⚠️ UiAutomator2未完全安装\n")
                        result_text.insert(tk.END, "  💡 将在首次连接时由Appium自动安装\n")
                    else:
                        result_text.insert(tk.END, "  ✅ UiAutomator2已安装\n")

                result_text.insert(tk.END, "\n" + "=" * 70 + "\n")
                result_text.insert(tk.END, "修复完成！\n")
                result_text.insert(tk.END, "建议重新运行环境检测确认状态\n")
                result_text.insert(tk.END, "=" * 70 + "\n")

            except Exception as e:
                result_text.insert(tk.END, f"\n❌ 修复过程出错: {str(e)}\n")

        threading.Thread(target=do_fix, daemon=True).start()

    def auto_fix_environment(self):
        """一键自动修复环境（主窗口调用）"""
        self.log("开始自动修复环境...", "INFO")

        def do_auto_fix():
            try:
                checker = EnvironmentChecker()
                fixer = EnvironmentFixer(checker.adb_path)

                # 检查并修复ADB连接
                _, devices = checker.check_adb_device()
                if not devices:
                    self.log("扫描ADB设备端口...", "INFO")
                    found = fixer.scan_common_ports()
                    if found:
                        port = found[0].split(':')[1]
                        self.port_var.set(port)
                        self.log(f"✅ 自动连接到端口: {port}", "OK")
                    else:
                        self.log("❌ 未找到可用设备", "WARN")

                # 检查并启动Appium
                appium_result = checker.check_appium_service()
                if appium_result.status == 'error':
                    self.log("尝试启动Appium服务...", "INFO")
                    success, message = fixer.start_appium()
                    if success:
                        self.log(f"✅ {message}", "OK")
                    else:
                        self.log(f"ℹ️ {message}", "WARN")

                self.log("自动修复完成！可点击'连接设备'继续", "OK")

            except Exception as e:
                self.log(f"自动修复失败: {e}", "ERROR")

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
                    self.log(f"✅ 自动检测成功！找到端口: {port}", "OK")

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
        """连接设备"""
        self.log("正在连接设备...", "INFO")
        self.status_label.config(text="● 连接中...", fg="orange")
        self.connect_btn.config(state=tk.DISABLED)

        def do_connect():
            try:
                import subprocess

                # 步骤1: 检查ADB连接
                port = self.port_var.get()
                self.log(f"[步骤1/3] 检查ADB连接 (端口: {port})...", "INFO")

                # 检查设备是否已连接
                result = subprocess.run(f'"{ADB_EXE}" devices', capture_output=True, text=True, shell=True, timeout=5)
                devices_output = result.stdout

                device_address = f"127.0.0.1:{port}"
                is_connected = device_address in devices_output and "offline" not in devices_output

                if is_connected:
                    self.log(f"ADB设备已连接: {device_address}", "OK")
                else:
                    # 尝试连接
                    self.log(f"ADB设备未连接，正在连接到 {device_address}...", "INFO")
                    connect_result = subprocess.run(
                        f'"{ADB_EXE}" connect {device_address}',
                        capture_output=True,
                        text=True,
                        shell=True,
                        timeout=10,
                        encoding='utf-8',
                        errors='ignore'
                    )

                    # 合并stdout和stderr的输出
                    output = (connect_result.stdout + connect_result.stderr).lower()

                    if "connected" in output or "已连接" in output:
                        self.log(f"ADB连接成功: {device_address}", "OK")
                    else:
                        # 即使输出为空，也再次验证设备是否真的连接了
                        verify = subprocess.run(f'"{ADB_EXE}" devices', capture_output=True, text=True, shell=True, timeout=5)
                        if device_address in verify.stdout:
                            self.log(f"ADB连接成功: {device_address} (验证通过)", "OK")
                        else:
                            error_msg = f"ADB连接失败: stdout={connect_result.stdout.strip()}, stderr={connect_result.stderr.strip()}"
                            self.log(error_msg, "ERROR")
                            self.log("请检查:", "ERROR")
                            self.log("  1. 模拟器/设备是否已启动", "ERROR")
                            self.log(f"  2. ADB端口 {port} 是否正确", "ERROR")
                            self.log("  3. 尝试手动运行: adb connect 127.0.0.1:{port}", "ERROR")
                            raise Exception(error_msg)

                # 再次验证连接（等待设备完全就绪）
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

                # 步骤2: 保存配置
                self.log("[步骤2/3] 保存配置...", "INFO")
                self.save_config()

                # 步骤3: 初始化Appium连接
                self.log("[步骤3/3] 初始化Appium连接...", "INFO")
                self.bot = DamaiBot()
                self.status_label.config(text="● 已连接", fg="green")
                self.log("Appium连接成功！", "OK")

                # 重置设备分辨率（将在第一次截图时获取）
                self.device_width = 0
                self.device_height = 0

                # 预加载OCR
                self.log("OCR引擎初始化中...", "INFO")
                get_ocr()
                self.log("OCR引擎就绪", "OK")

                # 更新按钮状态
                self.connect_btn.config(state=tk.DISABLED)
                self.disconnect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.DISABLED)
                self.start_btn.config(state=tk.NORMAL)

            except subprocess.TimeoutExpired:
                self.log("ADB命令执行超时", "ERROR")
                self.status_label.config(text="● 连接失败", fg="red")
                self.connect_btn.config(state=tk.NORMAL)
                self.reconnect_btn.config(state=tk.NORMAL)
            except Exception as e:
                error_str = str(e)
                self.log(f"连接失败: {error_str}", "ERROR")

                # 提供更友好的错误提示
                if "Could not find a connected Android device" in error_str:
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

        # 关闭连接
        if self.bot and self.bot.driver:
            try:
                self.bot.driver.quit()
            except:
                pass
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
