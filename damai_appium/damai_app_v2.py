# -*- coding: UTF-8 -*-
"""
__Author__ = "BlueCestbon"
__Version__ = "2.0.0"
__Description__ = "大麦app抢票自动化 - 优化版"
__Created__ = 2025/09/13 19:27
"""

import time
import logging
from datetime import datetime
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from .config import Config
except ImportError:
    from config import Config


class BotLogger:
    """大麦Bot日志系统 - 提供详细的运行日志和错误反馈"""

    # 文本图标（兼容所有终端）
    ICONS = {
        'INFO': '[INFO]',
        'SUCCESS': '[OK]',
        'WARNING': '[WARN]',
        'ERROR': '[ERROR]',
        'DEBUG': '[DEBUG]',
        'STEP': '[STEP]',
        'WAIT': '[WAIT]'
    }

    @staticmethod
    def _safe_print(message):
        """安全打印，处理编码问题"""
        try:
            print(message)
        except UnicodeEncodeError:
            # 如果遇到编码问题，使用ASCII编码并替换无法编码的字符
            print(message.encode('ascii', 'replace').decode('ascii'))

    @staticmethod
    def _format_message(level, message, step=None):
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        icon = BotLogger.ICONS.get(level, '')

        if step:
            prefix = f"[{timestamp}] {icon} [步骤{step}]"
        else:
            prefix = f"[{timestamp}] {icon}"

        return f"{prefix} {message}"

    @staticmethod
    def info(message, step=None):
        """信息日志"""
        BotLogger._safe_print(BotLogger._format_message('INFO', message, step))

    @staticmethod
    def success(message, step=None):
        """成功日志"""
        BotLogger._safe_print(BotLogger._format_message('SUCCESS', message, step))

    @staticmethod
    def warning(message, step=None):
        """警告日志"""
        BotLogger._safe_print(BotLogger._format_message('WARNING', message, step))

    @staticmethod
    def error(message, error_obj=None, step=None):
        """错误日志"""
        error_msg = BotLogger._format_message('ERROR', message, step)
        if error_obj:
            error_msg += f"\n    详细错误: {type(error_obj).__name__}: {str(error_obj)}"
        BotLogger._safe_print(error_msg)

    @staticmethod
    def debug(message):
        """调试日志"""
        BotLogger._safe_print(BotLogger._format_message('DEBUG', message))

    @staticmethod
    def step(step_num, description):
        """步骤日志"""
        separator = "=" * 60
        BotLogger._safe_print(f"\n{separator}")
        BotLogger._safe_print(BotLogger._format_message('STEP', f"步骤 {step_num}: {description}"))
        BotLogger._safe_print(separator)

    @staticmethod
    def wait(message):
        """等待日志"""
        BotLogger._safe_print(BotLogger._format_message('WAIT', message))


class DamaiBot:
    def __init__(self):
        BotLogger.step(0, "初始化大麦抢票Bot")
        BotLogger.info("加载配置文件...")
        self.config = Config.load_config()
        BotLogger.success(f"配置加载成功: 关键词='{self.config.keyword}', 城市='{self.config.city}'")

        self.driver = None
        self.wait = None
        self._setup_driver()

    def _setup_driver(self):
        """初始化驱动配置 - 包含反检测设置"""
        BotLogger.info("初始化Appium WebDriver...")
        BotLogger.info(f"服务器地址: {self.config.server_url}")

        capabilities = {
            "platformName": "Android",  # 操作系统
            # 不指定 platformVersion 和 deviceName，让 Appium 自动检测
            "appPackage": "cn.damai",  # app 包名
            "appActivity": ".launcher.splash.SplashMainActivity",  # app 启动 Activity
            "unicodeKeyboard": False,  # 禁用 Unicode 输入（避免需要 Appium Settings）
            "resetKeyboard": False,  # 不重置键盘
            "noReset": True,  # 不重置 app
            "newCommandTimeout": 6000,  # 超时时间
            "automationName": "UiAutomator2",  # 使用 uiautomator2

            # === 反检测配置 ===
            "skipServerInstallation": False,  # 需要安装 UiAutomator2 服务器
            "skipDeviceInitialization": False,  # 需要初始化设备
            "ignoreHiddenApiPolicyError": True,  # 忽略隐藏 API 策略错误
            "disableWindowAnimation": True,  # 禁用窗口动画

            # 隐藏自动化特征
            "skipLogcatCapture": True,  # 不捕获logcat日志
            "disableSuppressAccessibilityService": True,  # 不禁用辅助功能服务

            # 性能优化配置
            "mjpegServerFramerate": 1,  # 降低截图帧率
            "shouldTerminateApp": False,
            "adbExecTimeout": 60000,  # 增加ADB执行超时到60秒
            "androidInstallTimeout": 120000,  # 延长安装超时时间到120秒

            # 使用更隐蔽的设置
            "settings[disableIdLocatorAutocompletion]": True,  # 禁用ID定位器自动完成
        }

        device_app_info = AppiumOptions()
        device_app_info.load_capabilities(capabilities)

        try:
            BotLogger.info("正在连接到设备...")
            self.driver = webdriver.Remote(self.config.server_url, options=device_app_info)
            BotLogger.success("成功连接到设备!")
        except Exception as e:
            BotLogger.error("连接设备失败", e)
            raise

        # 更激进的性能优化设置
        BotLogger.info("配置性能优化参数...")
        self.driver.update_settings({
            "waitForIdleTimeout": 0,  # 空闲时间，0 表示不等待，让 UIAutomator2 不等页面“空闲”再返回
            "actionAcknowledgmentTimeout": 0,  # 禁止等待动作确认
            "keyInjectionDelay": 0,  # 禁止输入延迟
            "waitForSelectorTimeout": 300,  # 从500减少到300ms
            "ignoreUnimportantViews": False,  # 保持false避免元素丢失
            "allowInvisibleElements": True,
            "enableNotificationListener": False,  # 禁用通知监听
        })

        # 极短的显式等待，抢票场景下速度优先
        self.wait = WebDriverWait(self.driver, 2)  # 从5秒减少到2秒
        BotLogger.success("WebDriver初始化完成!")

    def press_back(self):
        """按返回键"""
        try:
            self.driver.press_keycode(4)  # KEYCODE_BACK
            BotLogger.info("已按返回键退回上一步")
            time.sleep(0.5)
            return True
        except Exception as e:
            BotLogger.warning("按返回键失败", e)
            return False

    def verify_page_content(self, expected_keywords, timeout=2):
        """验证页面内容是否包含预期关键词"""
        try:
            for keyword in expected_keywords:
                elements = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{keyword}")'
                )
                if elements:
                    BotLogger.success(f"页面验证通过: 发现'{keyword}'")
                    return True
            BotLogger.warning(f"页面验证失败: 未发现预期内容 {expected_keywords}")
            return False
        except Exception as e:
            BotLogger.warning("页面验证出错", e)
            return False

    def select_session_and_ticket_class(self):
        """
        在同一页面上选择场次和票档

        重要：场次和票档必须在同一个WebDriver会话中完成！
        点击场次后不跳转页面，而是在底部弹出票档选择。

        Returns:
            bool: 选择成功返回True，失败返回False
        """
        try:
            BotLogger.step(100, "开始场次和票档选择")

            # ========== 第一步：选择有票的场次 ==========
            BotLogger.info("步骤1: 识别并点击有票的场次")
            time.sleep(2)  # 等待页面加载

            # 查找"无票"标记
            BotLogger.info("查找所有'无票'标记...")
            no_ticket_positions = []
            try:
                no_ticket_elements = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().text("无票")'
                )
                BotLogger.info(f"找到 {len(no_ticket_elements)} 个'无票'标记")

                for i, el in enumerate(no_ticket_elements):
                    try:
                        rect = el.rect
                        no_ticket_positions.append(rect['y'])
                        BotLogger.debug(f"  无票标记{i+1}: y={rect['y']}")
                    except:
                        pass
            except Exception as e:
                BotLogger.debug(f"查找'无票'标记失败: {e}")

            # 查找所有场次方框
            BotLogger.info("查找所有场次方框...")
            session_boxes = []
            try:
                all_clickable = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().clickable(true)'
                )
                BotLogger.debug(f"找到 {len(all_clickable)} 个可点击元素")

                for i, el in enumerate(all_clickable):
                    try:
                        rect = el.rect
                        # 场次方框特征：较大的可点击区域，在屏幕中上部
                        if 200 < rect['y'] < 900 and rect['height'] > 80 and rect['width'] > 400:
                            session_boxes.append({
                                'element': el,
                                'y': rect['y'],
                                'height': rect['height'],
                                'y_end': rect['y'] + rect['height'],
                                'index': i
                            })
                            BotLogger.debug(f"  场次方框{len(session_boxes)}: y={rect['y']}-{rect['y']+rect['height']}")
                    except:
                        pass

                BotLogger.info(f"找到 {len(session_boxes)} 个场次方框")

            except Exception as e:
                BotLogger.warning(f"查找场次方框失败: {e}")
                return False

            # 判断哪些场次有票
            BotLogger.info("判断哪些场次有票...")
            available_sessions = []

            for i, box in enumerate(session_boxes):
                has_ticket = True
                box_y_start = box['y']
                box_y_end = box['y_end']

                # 检查"无票"标记是否在这个方框内
                for no_ticket_y in no_ticket_positions:
                    if box_y_start <= no_ticket_y <= box_y_end:
                        has_ticket = False
                        BotLogger.debug(f"  场次{i+1} (y={box_y_start}-{box_y_end}) 无票")
                        break

                if has_ticket:
                    available_sessions.append(box)
                    BotLogger.success(f"  ✓ 场次{i+1} (y={box_y_start}-{box_y_end}) 有票！")

            # 点击第一个有票的场次
            if not available_sessions:
                BotLogger.error("没有找到有票的场次！")
                return False

            BotLogger.info(f"点击第一个有票的场次（共{len(available_sessions)}个有票场次）")

            selected_session = available_sessions[0]
            BotLogger.debug(f"选择场次: y={selected_session['y']}-{selected_session['y_end']}")

            try:
                selected_session['element'].click()
                BotLogger.success("成功点击有票的场次！")
            except Exception as e:
                BotLogger.error("点击场次失败", e)
                return False

            # 等待票档弹出（关键！不要退出，继续在同一页面操作）
            BotLogger.wait("等待票档弹出...")
            time.sleep(2)

            # ========== 第二步：在同一页面上选择有票的票档 ==========
            BotLogger.info("步骤2: 识别并点击有票的票档")

            # 查找"票档"文字位置，用于区分场次方框和票档方框
            BotLogger.info("查找'票档'文字位置...")
            ticket_class_label_y = 0
            try:
                ticket_class_labels = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().text("票档")'
                )
                if ticket_class_labels:
                    rect = ticket_class_labels[0].rect
                    ticket_class_label_y = rect['y']
                    BotLogger.debug(f"找到'票档'文字: y={ticket_class_label_y}")
                else:
                    # 备用：查找包含"票档"的元素
                    ticket_class_labels = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("票档")'
                    )
                    if ticket_class_labels:
                        rect = ticket_class_labels[0].rect
                        ticket_class_label_y = rect['y']
                        BotLogger.debug(f"找到包含'票档'的文字: y={ticket_class_label_y}")
            except Exception as e:
                BotLogger.debug(f"查找'票档'文字失败: {e}")

            # 查找所有"缺货登记"标记
            BotLogger.info("查找所有'缺货登记'标记...")
            out_of_stock_positions = []
            try:
                out_of_stock_elements = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("缺货登记")'
                )
                BotLogger.info(f"找到 {len(out_of_stock_elements)} 个'缺货登记'标记")

                for i, el in enumerate(out_of_stock_elements):
                    try:
                        rect = el.rect
                        out_of_stock_positions.append(rect['y'])
                        BotLogger.debug(f"  缺货登记{i+1}: y={rect['y']}")
                    except:
                        pass
            except Exception as e:
                BotLogger.debug(f"查找'缺货登记'标记失败: {e}")

            # 重新查找所有可点击元素（因为票档刚弹出）
            BotLogger.info("查找所有票档方框...")
            ticket_boxes = []
            try:
                all_clickable = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().clickable(true)'
                )
                BotLogger.debug(f"找到 {len(all_clickable)} 个可点击元素")

                for i, el in enumerate(all_clickable):
                    try:
                        rect = el.rect
                        # 票档方框特征：较大的可点击区域，且在"票档"文字下方
                        if 200 < rect['y'] < 1100 and rect['height'] > 50 and rect['width'] > 300:
                            # 如果找到了"票档"文字，只选择在其下方的方框
                            if ticket_class_label_y > 0:
                                if rect['y'] > ticket_class_label_y:
                                    ticket_boxes.append({
                                        'element': el,
                                        'y': rect['y'],
                                        'height': rect['height'],
                                        'y_end': rect['y'] + rect['height'],
                                        'index': i
                                    })
                                    BotLogger.debug(f"  票档方框{len(ticket_boxes)}: y={rect['y']}-{rect['y']+rect['height']} (在'票档'文字下方)")
                                else:
                                    BotLogger.debug(f"  跳过场次方框: y={rect['y']} (在'票档'文字上方)")
                            else:
                                # 如果没找到"票档"文字，只选择y坐标较大的方框（在下方的）
                                if rect['y'] > 700:  # 票档通常在页面下半部分
                                    ticket_boxes.append({
                                        'element': el,
                                        'y': rect['y'],
                                        'height': rect['height'],
                                        'y_end': rect['y'] + rect['height'],
                                        'index': i
                                    })
                                    BotLogger.debug(f"  票档方框{len(ticket_boxes)}: y={rect['y']}-{rect['y']+rect['height']}")
                    except:
                        pass

                BotLogger.info(f"找到 {len(ticket_boxes)} 个票档方框")

            except Exception as e:
                BotLogger.warning(f"查找票档方框失败: {e}")
                return False

            # 判断哪些票档有票
            BotLogger.info("判断哪些票档有票...")
            available_tickets = []

            for i, box in enumerate(ticket_boxes):
                has_ticket = True
                box_y_start = box['y']
                box_y_end = box['y_end']

                # 检查"缺货登记"标记是否在这个方框内
                for out_of_stock_y in out_of_stock_positions:
                    if box_y_start <= out_of_stock_y <= box_y_end:
                        has_ticket = False
                        BotLogger.debug(f"  票档{i+1} (y={box_y_start}-{box_y_end}) 缺货")
                        break

                if has_ticket:
                    available_tickets.append(box)
                    BotLogger.success(f"  ✓ 票档{i+1} (y={box_y_start}-{box_y_end}) 有票！")

            # 点击第一个有票的票档
            if not available_tickets:
                BotLogger.error("没有找到有票的票档！")
                BotLogger.warning("当前场次的所有票档都已缺货，需要返回重新选择场次")
                return False

            BotLogger.info(f"点击第一个有票的票档（共{len(available_tickets)}个有票票档）")

            selected_ticket = available_tickets[0]
            BotLogger.debug(f"选择票档: y={selected_ticket['y']}-{selected_ticket['y_end']}")

            try:
                selected_ticket['element'].click()
                BotLogger.success("成功点击有票的票档！")
            except Exception as e:
                BotLogger.error("点击票档失败", e)
                return False

            time.sleep(2)

            # 验证是否进入下一步
            BotLogger.info("验证是否进入下一步...")
            try:
                keywords = ["实名", "购票人", "确认订单", "提交订单", "立即购买"]
                found_keyword = False

                for keyword in keywords:
                    elements = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{keyword}")'
                    )
                    if elements:
                        BotLogger.success(f"成功进入下一步！发现'{keyword}'")
                        found_keyword = True
                        break

                if not found_keyword:
                    BotLogger.info("已点击票档，等待页面响应...")

            except Exception as e:
                BotLogger.debug(f"验证时出错: {e}")

            BotLogger.success("场次和票档选择完成！")
            return True

        except Exception as e:
            BotLogger.error("场次和票档选择过程出错", e)
            return False

    def ultra_fast_click(self, by, value, timeout=1.5):
        """超快速点击 - 适合抢票场景"""
        try:
            # 直接查找并点击，不等待可点击状态
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            # 使用坐标点击更快
            rect = el.rect
            x = rect['x'] + rect['width'] // 2
            y = rect['y'] + rect['height'] // 2
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 50  # 极短点击时间
            })
            return True
        except TimeoutException:
            return False

    def batch_click(self, elements_info, delay=0.1):
        """批量点击操作"""
        for by, value in elements_info:
            if self.ultra_fast_click(by, value):
                if delay > 0:
                    time.sleep(delay)
            else:
                print(f"点击失败: {value}")

    def ultra_batch_click(self, elements_info, timeout=2):
        """超快批量点击 - 带等待机制"""
        coordinates = []
        # 批量收集坐标，带超时等待
        for by, value in elements_info:
            try:
                # 等待元素出现
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                coordinates.append((x, y, value))
            except TimeoutException:
                print(f"超时未找到用户: {value}")
            except Exception as e:
                print(f"查找用户失败 {value}: {e}")
        print(f"成功找到 {len(coordinates)} 个用户")
        # 快速连续点击
        for i, (x, y, value) in enumerate(coordinates):
            self.driver.execute_script("mobile: clickGesture", {
                "x": x,
                "y": y,
                "duration": 30
            })
            if i < len(coordinates) - 1:
                time.sleep(0.01)
            print(f"点击用户: {value}")

    def smart_wait_and_click(self, by, value, backup_selectors=None, timeout=1.5):
        """智能等待和点击 - 支持备用选择器"""
        selectors = [(by, value)]
        if backup_selectors:
            selectors.extend(backup_selectors)

        for selector_by, selector_value in selectors:
            try:
                el = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((selector_by, selector_value))
                )
                rect = el.rect
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                self.driver.execute_script("mobile: clickGesture", {"x": x, "y": y, "duration": 50})
                return True
            except TimeoutException:
                continue
        return False

    def run_ticket_grabbing(self):
        """执行抢票主流程"""
        try:
            BotLogger.step(1, "开始抢票流程")
            start_time = time.time()

            # 0. 强制重启大麦APP
            BotLogger.step(2, "重启大麦APP确保初始状态")
            try:
                BotLogger.info("关闭大麦APP...")
                self.driver.terminate_app("cn.damai")
                time.sleep(2)
                BotLogger.success("大麦APP已关闭")

                BotLogger.info("启动大麦APP...")
                self.driver.activate_app("cn.damai")
                time.sleep(2)
                BotLogger.success("大麦APP已重新启动")
            except Exception as e:
                BotLogger.warning("重启APP时出现异常，继续执行", e)

            # 1. 等待 APP 完全启动
            BotLogger.step(3, "等待大麦APP完全启动")
            max_wait_time = 10  # 最多等待10秒
            for i in range(max_wait_time):
                time.sleep(1)
                current_activity = self.driver.current_activity
                BotLogger.info(f"检测当前Activity: {current_activity} ({i+1}/{max_wait_time}秒)")

                # 如果已经离开启动页，进入主页
                if "SplashActivity" not in current_activity and "Splash" not in current_activity:
                    BotLogger.success(f"APP启动完成! 当前页面: {current_activity}")
                    break

                if i == max_wait_time - 1:
                    BotLogger.error("APP启动超时 (超过10秒)")
                    return False

            # 再等待1秒确保页面完全加载
            BotLogger.wait("等待页面完全加载...")
            time.sleep(2)

            # 关闭可能出现的广告弹窗
            BotLogger.step(4, "检测并关闭广告弹窗")
            try:
                # 尝试多种方式关闭广告
                ad_closed = False

                # 方式1: 查找包含"X"、"关闭"、"跳过"的按钮
                try:
                    close_buttons = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textMatches(".*[Xx×].*|.*关闭.*|.*跳过.*")'
                    )
                    if close_buttons:
                        for btn in close_buttons:
                            try:
                                rect = btn.rect
                                # 右上角的关闭按钮
                                if rect['x'] > 500 and rect['y'] < 200:
                                    btn.click()
                                    ad_closed = True
                                    BotLogger.success(f"方式1成功: 点击了文字关闭按钮 位置({rect['x']}, {rect['y']})")
                                    break
                            except:
                                continue
                except:
                    pass

                # 方式2: 查找右上角的小ImageView（X按钮通常是小图标）
                if not ad_closed:
                    BotLogger.info("尝试方式2: 查找右上角X按钮...")
                    try:
                        images = self.driver.find_elements(By.CLASS_NAME, "android.widget.ImageView")
                        for img in images:
                            try:
                                rect = img.rect
                                # 右上角小图标（X按钮）
                                if (rect['x'] > 600 and rect['y'] < 150 and
                                    rect['width'] < 80 and rect['height'] < 80):
                                    img.click()
                                    ad_closed = True
                                    BotLogger.success(f"方式2成功: 点击了右上角X按钮 位置({rect['x']}, {rect['y']})")
                                    break
                            except:
                                continue
                    except:
                        pass

                # 方式3: 直接点击右上角固定位置
                if not ad_closed:
                    BotLogger.info("尝试方式3: 点击右上角固定位置...")
                    try:
                        screen_size = self.driver.get_window_size()
                        x = screen_size['width'] - 50  # 右上角
                        y = 50
                        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                        ad_closed = True
                        BotLogger.success(f"方式3成功: 点击了右上角固定位置 ({x}, {y})")
                    except:
                        pass

                if ad_closed:
                    BotLogger.wait("等待广告关闭动画...")
                    time.sleep(1)  # 等待广告关闭动画
                else:
                    BotLogger.info("未检测到广告弹窗，继续...")

            except Exception as e:
                BotLogger.warning(f"关闭广告过程出现异常", e)

            # 重新获取当前页面
            current_activity = self.driver.current_activity
            BotLogger.info(f"检查当前页面: {current_activity}")

            # 判断是否需要搜索
            need_search = False
            need_click_result = False
            need_select_city = False

            # 检查是否在影城选择页面
            if "Cinema" in current_activity:
                BotLogger.info("检测到影城选择页面，跳过搜索流程")
                # 不需要搜索，直接到影城选择环节
            elif ".homepage.MainActivity" in current_activity or "HomePageActivity" in current_activity:
                need_select_city = True  # 在首页需要选择城市
                need_search = True
                need_click_result = True
                BotLogger.info("检测到首页，需要执行完整搜索流程")
            elif "SearchActivity" in current_activity:
                # 在搜索页面，检查是否有搜索结果
                BotLogger.info("检测到搜索页面，检查是否有搜索结果...")
                try:
                    results = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{self.config.keyword[:10]}")'
                    )
                    if results:
                        need_click_result = True
                        BotLogger.success(f"发现 {len(results)} 个匹配的搜索结果")
                    else:
                        need_search = True
                        need_click_result = True
                        BotLogger.warning("未发现搜索结果，需要重新搜索")
                except Exception as e:
                    need_click_result = True
                    BotLogger.warning("检查搜索结果时出错，尝试点击结果", e)

            # 执行搜索流程
            if need_search:
                BotLogger.step(5, f"搜索演出: {self.config.keyword}")

                # 检查是否已经在SearchActivity
                search_clicked = False
                if "SearchActivity" in current_activity:
                    BotLogger.info("已在搜索页面，尝试直接定位输入框...")
                    # 在SearchActivity页面，搜索框可能已经激活，直接查找EditText
                    try:
                        edit_texts = self.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                        if edit_texts:
                            # 直接使用第一个EditText，可能已经是焦点
                            BotLogger.success(f"找到 {len(edit_texts)} 个输入框，使用第一个")
                            search_clicked = True
                        else:
                            BotLogger.warning("未找到EditText，尝试其他方式")
                    except Exception as e:
                        BotLogger.debug(f"查找EditText失败: {e}")

                # 如果不在SearchActivity或未找到，使用传统方式
                if not search_clicked:
                    BotLogger.info("尝试定位并点击搜索框...")

                    # 方式1: 通过ID查找
                    try:
                        search_box = self.driver.find_element(By.ID, "cn.damai:id/search_edit_view")
                        search_box.click()
                        search_clicked = True
                        BotLogger.success("方式1成功: 通过ID找到搜索框")
                    except Exception as e:
                        BotLogger.debug(f"方式1失败: {e}")

                    # 方式2: 通过 UIAutomator 查找包含"搜索"的元素
                    if not search_clicked:
                        try:
                            search_elements = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textContains("搜索").clickable(true)'
                            )
                            if search_elements:
                                search_elements[0].click()
                                search_clicked = True
                                BotLogger.success("方式2成功: 通过文本找到搜索框")
                        except Exception as e:
                            BotLogger.debug(f"方式2失败: {e}")

                    # 方式3: 查找 EditText 并点击
                    if not search_clicked:
                        try:
                            edit_texts = self.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                            if edit_texts:
                                edit_texts[0].click()
                                search_clicked = True
                                BotLogger.success("方式3成功: 通过EditText找到搜索框")
                        except Exception as e:
                            BotLogger.debug(f"方式3失败: {e}")

                if not search_clicked:
                    BotLogger.error("所有方式都无法点击搜索框")
                    return False

                BotLogger.wait("等待搜索框就绪...")
                time.sleep(1)  # 等待搜索框打开

                # 0.1.5 处理位置权限弹窗（关键步骤！）
                BotLogger.step(6, "处理位置权限弹窗")
                BotLogger.wait("等待可能的权限弹窗显示...")
                time.sleep(1.5)  # 等待弹窗显示

                try:
                    permission_handled = False

                    # 方式1: 查找"立即开启"按钮（优先点击这个）
                    BotLogger.info("方式1: 查找'立即开启'按钮...")
                    try:
                        buttons = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().text("立即开启")'
                        )
                        if buttons:
                            buttons[0].click()
                            permission_handled = True
                            BotLogger.success("方式1成功: 点击了'立即开启'按钮")
                            time.sleep(1)
                    except Exception as e:
                        BotLogger.debug(f"方式1失败: {e}")

                    # 方式2: 查找"下次再说"按钮
                    if not permission_handled:
                        BotLogger.info("方式2: 查找'下次再说'按钮...")
                        try:
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().text("下次再说")'
                            )
                            if buttons:
                                buttons[0].click()
                                permission_handled = True
                                BotLogger.success("方式2成功: 点击了'下次再说'按钮")
                                time.sleep(1)
                        except Exception as e:
                            BotLogger.debug(f"方式2失败: {e}")

                    # 方式3: 通用匹配 - 查找包含"开启"、"允许"等文本的按钮
                    if not permission_handled:
                        BotLogger.info("方式3: 尝试通用权限按钮匹配...")
                        try:
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textMatches(".*开启.*|.*允许.*|.*同意.*").clickable(true)'
                            )
                            if buttons:
                                for btn in buttons:
                                    try:
                                        text = btn.text if hasattr(btn, 'text') else ''
                                        BotLogger.info(f"  找到按钮: {text}")
                                        btn.click()
                                        permission_handled = True
                                        BotLogger.success(f"方式3成功: 点击了 {text}")
                                        time.sleep(1)
                                        break
                                    except:
                                        continue
                        except Exception as e:
                            BotLogger.debug(f"方式3失败: {e}")

                    # 方式4: 如果都没找到，尝试"下次"、"取消"、"暂不"等
                    if not permission_handled:
                        BotLogger.info("方式4: 查找拒绝按钮...")
                        try:
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textMatches(".*下次.*|.*取消.*|.*暂不.*").clickable(true)'
                            )
                            if buttons:
                                buttons[0].click()
                                permission_handled = True
                                BotLogger.success("方式4成功: 点击了拒绝按钮")
                                time.sleep(1)
                        except:
                            pass

                    if permission_handled:
                        BotLogger.success("权限弹窗已成功处理")
                    else:
                        BotLogger.info("未发现权限弹窗，继续执行...")

                except Exception as e:
                    BotLogger.warning("权限弹窗处理过程出现异常", e)

                BotLogger.wait("确保弹窗完全关闭...")
                time.sleep(1)  # 确保弹窗完全关闭

                # 0.2 输入搜索关键词 - 重新查找输入框
                print(f"输入关键词: {self.config.keyword}")
                try:
                    # 重新查找当前聚焦的输入框
                    for _ in range(3):  # 尝试3次
                        try:
                            # 先清空
                            self.driver.press_keycode(123)  # KEYCODE_DEL
                            time.sleep(0.2)

                            # 输入关键词
                            search_inputs = self.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                            if search_inputs:
                                search_inputs[0].send_keys(self.config.keyword)
                                print("输入成功")
                                break
                            time.sleep(0.5)
                        except Exception as e:
                            print(f"输入尝试失败: {e}")
                            if _ == 2:  # 最后一次尝试
                                raise

                    time.sleep(1)
                except Exception as e:
                    print(f"输入关键词失败: {e}")
                    # 尝试备用方案：使用 ADB 输入
                    try:
                        print("尝试使用ADB输入...")
                        self.driver.execute_script('mobile: shell', {
                            'command': 'input',
                            'args': ['text', self.config.keyword]
                        })
                        time.sleep(0.5)
                    except Exception as e2:
                        print(f"ADB输入也失败: {e2}")
                        return False

                # 0.3 执行搜索
                print("执行搜索...")
                self.driver.press_keycode(66)  # KEYCODE_ENTER
                time.sleep(3)  # 等待搜索结果加载

            # 0.4 点击第一个搜索结果（如果需要）
            if need_click_result:
                print("选择搜索结果...")
                print(f"搜索关键词: {self.config.keyword}")
                time.sleep(2)  # 等待搜索结果完全加载
                try:
                    # 尝试多种方式找到搜索结果
                    result_clicked = False

                    # 方式1: 查找包含关键词前几个字的TextView
                    try:
                        # 使用关键词的前5个字进行搜索
                        search_text = self.config.keyword[:5] if len(self.config.keyword) > 5 else self.config.keyword
                        print(f"方式1: 查找包含'{search_text}'的TextView...")
                        results = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().className("android.widget.TextView").textContains("{search_text}")'
                        )
                        print(f"找到{len(results)}个TextView结果")
                        if results:
                            # 找到在屏幕中上部分的结果
                            for i, result in enumerate(results[:10]):
                                try:
                                    rect = result.rect
                                    text = result.text if hasattr(result, 'text') else ''
                                    print(f"  结果{i}: y={rect['y']}, text='{text[:20]}...'")
                                    if 50 < rect['y'] < 1000:  # 扩大范围
                                        result.click()
                                        result_clicked = True
                                        print(f"[成功] 点击了TextView搜索结果，y={rect['y']}")
                                        break
                                except Exception as e:
                                    print(f"  结果{i}点击失败: {e}")
                                    continue
                    except Exception as e:
                        print(f"方式1失败: {e}")

                    # 方式2: 如果TextView不可点击，尝试点击其父容器
                    if not result_clicked:
                        try:
                            # 找到包含关键词的任何元素
                            results = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                f'new UiSelector().textContains("{self.config.keyword[:10]}")'
                            )
                            if results:
                                # 尝试点击元素所在的位置
                                rect = results[0].rect
                                x = rect['x'] + rect['width'] // 2
                                y = rect['y'] + rect['height'] // 2
                                self.driver.execute_script('mobile: clickGesture', {
                                    'x': x,
                                    'y': y
                                })
                                result_clicked = True
                                print(f"点击了搜索结果位置 ({x}, {y})")
                        except Exception as e:
                            print(f"方式2失败: {e}")

                    # 方式3: 查找可点击的列表项
                    if not result_clicked:
                        try:
                            clickables = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().clickable(true)'
                            )
                            # 找到y坐标在屏幕上部的元素
                            for el in clickables[:15]:
                                try:
                                    rect = el.rect
                                    if 150 < rect['y'] < 600:  # 搜索结果通常在上部
                                        el.click()
                                        result_clicked = True
                                        print(f"点击了可点击元素，y={rect['y']}")
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"方式3失败: {e}")

                    if not result_clicked:
                        print("搜索结果点击失败")
                        return False

                    BotLogger.wait("等待进入演出详情页...")
                    time.sleep(3)  # 等待进入详情页

                    # 验证是否进入了正确的详情页
                    BotLogger.info("验证是否进入演出详情页...")
                    detail_page_ok = False
                    for retry in range(2):  # 最多重试2次
                        # 检查是否有购票相关按钮（说明进入了详情页）
                        try:
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textMatches(".*购票.*|.*预约.*|.*购买.*")'
                            )
                            if buttons and len(buttons) > 0:
                                detail_page_ok = True
                                BotLogger.success(f"已进入详情页! 发现{len(buttons)}个购票按钮")
                                break
                            else:
                                BotLogger.warning(f"未发现购票按钮，可能点击错误 (尝试{retry+1}/2)")
                                if retry < 1:  # 还有重试机会
                                    BotLogger.info("按返回键退回...")
                                    self.press_back()
                                    time.sleep(1)
                                    # 重新点击搜索结果
                                    BotLogger.info("重新点击搜索结果...")
                                    if result_clicked:
                                        time.sleep(2)
                        except Exception as e:
                            BotLogger.debug(f"验证详情页时出错: {e}")

                    if not detail_page_ok:
                        BotLogger.error("无法进入正确的演出详情页")
                        return False

                except Exception as e:
                    print(f"点击搜索结果失败: {e}")
                    return False

            # 2. 点击购票按钮 - 多种可能的按钮文本
            print("点击购票按钮...")
            book_clicked = False

            # 方式1: 优先查找明确的购票相关按钮（不包含距离、场馆等干扰词）
            print("  尝试方式1：查找购票按钮...")
            try:
                buttons = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textMatches(".*购票.*|.*特惠.*|.*预约.*|.*购买.*|.*立即.*")'
                )
                print(f"  找到{len(buttons)}个匹配按钮")
                if buttons:
                    # 过滤掉包含干扰词的按钮
                    valid_buttons = []
                    for btn in buttons:
                        try:
                            text = btn.text if btn.text else ""
                            # 排除包含km、场馆、距离的按钮
                            if not any(word in text for word in ["km", "场馆", "距离", "公里"]):
                                valid_buttons.append(btn)
                        except:
                            continue

                    print(f"  过滤后剩余{len(valid_buttons)}个有效按钮")

                    # 优先点击底部的按钮
                    for i, btn in enumerate(reversed(valid_buttons)):
                        try:
                            rect = btn.rect
                            text = btn.text if btn.text else "[无文本]"
                            print(f"    按钮[{i}]: '{text}', y={rect['y']}")
                            if rect['y'] > 800:  # 底部区域
                                btn.click()
                                book_clicked = True
                                print(f"  [OK] 点击了底部购票按钮: {text}, y={rect['y']}")
                                break
                        except Exception as e:
                            print(f"    按钮[{i}]点击失败")
                            continue

                    # 如果没有底部按钮，点击第一个有效按钮
                    if not book_clicked and valid_buttons:
                        valid_buttons[0].click()
                        book_clicked = True
                        print(f"  [OK] 点击了购票按钮: {valid_buttons[0].text}")
                else:
                    print("  未找到匹配按钮")
            except Exception as e:
                print(f"  方式1失败: {e}")

            # 方式2: 通过ID查找
            if not book_clicked:
                try:
                    btn = self.driver.find_element(By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl")
                    btn.click()
                    book_clicked = True
                    print("通过ID点击了购票按钮")
                except Exception as e:
                    print(f"方式2失败: {e}")

            # 方式3: 点击屏幕底部中央
            if not book_clicked:
                try:
                    screen_size = self.driver.get_window_size()
                    x = screen_size['width'] // 2
                    y = screen_size['height'] - 100  # 底部往上100像素
                    self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                    book_clicked = True
                    print(f"点击了底部中央位置 ({x}, {y})")
                except Exception as e:
                    print(f"方式3失败: {e}")

            if not book_clicked:
                print("购票按钮点击失败")
                return False

            BotLogger.wait("等待进入场次选择页面...")
            time.sleep(2)  # 等待进入选票页面

            # 关闭可能出现的"服务说明"弹窗
            BotLogger.step(7, "检测并关闭服务说明弹窗")
            try:
                service_popup_closed = False

                # 方式1: 查找"服务说明"文字右边的×按钮
                BotLogger.info("查找服务说明弹窗...")
                try:
                    service_text = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("服务说明")'
                    )
                    if service_text:
                        BotLogger.info("发现服务说明弹窗，查找关闭按钮...")
                        # 查找所有ImageView（×通常是ImageView）
                        images = self.driver.find_elements(By.CLASS_NAME, "android.widget.ImageView")
                        service_rect = service_text[0].rect

                        # 查找在"服务说明"右侧的小图标
                        for img in images:
                            try:
                                rect = img.rect
                                # × 应该在服务说明文字的右侧，y坐标接近
                                if (rect['x'] > service_rect['x'] and
                                    abs(rect['y'] - service_rect['y']) < 50 and
                                    rect['width'] < 80 and rect['height'] < 80):
                                    img.click()
                                    service_popup_closed = True
                                    BotLogger.success(f"方式1成功: 点击了服务说明右侧的×按钮")
                                    time.sleep(0.5)
                                    break
                            except:
                                continue
                except Exception as e:
                    BotLogger.debug(f"方式1失败: {e}")

                # 方式2: 查找包含"×"、"关闭"的元素
                if not service_popup_closed:
                    BotLogger.info("方式2: 查找关闭/×按钮...")
                    try:
                        close_buttons = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().textMatches(".*[×Xx关闭].*")'
                        )
                        if close_buttons:
                            close_buttons[0].click()
                            service_popup_closed = True
                            BotLogger.success("方式2成功: 点击了关闭按钮")
                            time.sleep(0.5)
                    except:
                        pass

                # 方式3: 点击弹窗右上角区域
                if not service_popup_closed:
                    BotLogger.info("方式3: 尝试点击右上角...")
                    try:
                        screen_size = self.driver.get_window_size()
                        # 弹窗通常不是全屏，尝试点击右上角
                        x = screen_size['width'] - 60
                        y = 200  # 估计的弹窗顶部位置
                        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                        service_popup_closed = True
                        BotLogger.success(f"方式3成功: 点击了右上角位置")
                        time.sleep(0.5)
                    except:
                        pass

                if service_popup_closed:
                    BotLogger.success("服务说明弹窗已关闭")
                else:
                    BotLogger.info("未发现服务说明弹窗，继续...")
            except Exception as e:
                BotLogger.warning("处理服务说明弹窗时出错", e)

            # 验证是否进入了选票页面
            BotLogger.info("验证是否进入选票/场次选择页面...")
            try:
                # 检查是否有日期、价格、场次等选择元素
                page_indicators = self.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textMatches(".*日期.*|.*场次.*|.*票档.*|.*选择.*|.*座位.*")'
                )
                if page_indicators and len(page_indicators) > 0:
                    BotLogger.success(f"已进入选票页面! 发现{len(page_indicators)}个选择元素")
                else:
                    BotLogger.warning("未发现选票页面的典型元素，可能点击了错误按钮")
                    BotLogger.info("尝试按返回键并重新点击购票按钮...")
                    self.press_back()
                    time.sleep(1)
                    # 这里可以添加重试逻辑，但为了避免无限循环，先记录警告
                    BotLogger.warning("请检查是否需要手动干预")
            except Exception as e:
                BotLogger.debug(f"验证选票页面时出错: {e}")

            # 2.5 智能选择场次和票档（演唱会票流程）
            BotLogger.step(8, "智能选择场次和票档")
            try:
                # 检查是否是演唱会票流程（需要选择场次和票档）
                current_activity = self.driver.current_activity
                is_concert_ticket = "Cinema" not in current_activity and "cinema" not in current_activity

                if is_concert_ticket:
                    # 检查是否有"场次"或"票档"关键词
                    session_indicators = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textMatches(".*场次.*|.*票档.*")'
                    )

                    if session_indicators:
                        BotLogger.info("检测到演唱会票流程，开始场次和票档选择...")
                        if not self.select_session_and_ticket_class():
                            BotLogger.error("场次和票档选择失败")
                            # 可以选择返回False或继续执行
                            # return False
                            BotLogger.warning("跳过场次和票档选择，继续后续流程...")
                        else:
                            BotLogger.success("场次和票档选择成功！")
                    else:
                        BotLogger.info("未检测到场次/票档选择页面，可能是其他类型的票")
                else:
                    BotLogger.info("检测到电影票流程，跳过场次和票档选择...")

            except Exception as e:
                BotLogger.warning("场次和票档选择过程出错", e)
                BotLogger.info("继续执行后续流程...")

            # 3. 选择影城门店（如果是电影票）
            print("检查是否需要选择影城...")
            try:
                # 检查当前是否在影城选择页面
                current_activity = self.driver.current_activity
                if "Cinema" in current_activity or "影城" in current_activity:
                    print("进入影城选择页面，选择门店...")
                    # 查找包含"中影大成国家影城"的元素
                    cinema_name = "中影大成国家影城"
                    cinema_found = False

                    try:
                        cinemas = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            f'new UiSelector().textContains("{cinema_name}")'
                        )
                        if cinemas:
                            cinemas[0].click()
                            cinema_found = True
                            print(f"选择了影城: {cinema_name}")
                        else:
                            # 如果找不到完整名称，尝试搜索关键词
                            print(f"未找到{cinema_name}，尝试搜索...")
                            search_elements = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textContains("搜索").clickable(true)'
                            )
                            if search_elements:
                                search_elements[0].click()
                                time.sleep(1)
                                # 输入影城名称
                                edit_texts = self.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                                if edit_texts:
                                    edit_texts[0].send_keys(cinema_name)
                                    time.sleep(1)
                                    # 点击搜索结果
                                    results = self.driver.find_elements(
                                        AppiumBy.ANDROID_UIAUTOMATOR,
                                        f'new UiSelector().textContains("{cinema_name}")'
                                    )
                                    if results:
                                        results[0].click()
                                        cinema_found = True
                                        print(f"搜索并选择了影城: {cinema_name}")
                    except Exception as e:
                        print(f"影城选择出错: {e}")

                    if cinema_found:
                        time.sleep(2)  # 等待进入场次选择
                    else:
                        print("未找到指定影城，继续...")
                else:
                    print("不在影城选择页面，跳过")
            except Exception as e:
                print(f"影城选择失败: {e}")

            # 3.5. 选座（如果是电影票）- V3 增强版
            print("检查是否需要选座...")
            try:
                # 更智能的选座页面检测：检查是否有"请先选座"按钮
                need_select_seat = False
                try:
                    seat_buttons = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("选座")'
                    )
                    if seat_buttons:
                        need_select_seat = True
                        print("检测到选座按钮，进入选座流程...")
                except:
                    pass

                if need_select_seat:
                    print("=== 开始选座 ===")
                    screen_size = self.driver.get_window_size()
                    center_x = screen_size['width'] // 2

                    # 座位图通常在屏幕上半部分（从截图看大约在200-500的y坐标范围）
                    seat_area_top = 200
                    seat_area_bottom = 500
                    seat_area_center_y = (seat_area_top + seat_area_bottom) // 2

                    # 步骤1：尝试缩小视图以看到更多座位
                    print("步骤1: 调整视图...")
                    try:
                        self.driver.execute_script('mobile: pinchCloseGesture', {
                            'left': center_x - 150,
                            'top': seat_area_center_y - 150,
                            'width': 300,
                            'height': 300,
                            'percent': 0.6,
                            'speed': 800
                        })
                        time.sleep(1)
                    except Exception as e:
                        print(f"  缩放失败(可忽略): {e}")

                    # 步骤2：在座位区域多点尝试选座
                    print("步骤2: 智能选座...")
                    seat_selected = False

                    # 在座位图区域尝试多个位置
                    try_positions = [
                        (center_x, seat_area_center_y),  # 中心
                        (center_x - 60, seat_area_center_y),  # 中心偏左
                        (center_x + 60, seat_area_center_y),  # 中心偏右
                        (center_x, seat_area_center_y - 50),  # 中心偏上
                        (center_x, seat_area_center_y + 50),  # 中心偏下
                        (center_x - 40, seat_area_center_y - 40),  # 左上
                        (center_x + 40, seat_area_center_y - 40),  # 右上
                    ]

                    for i, (x, y) in enumerate(try_positions):
                        if seat_selected:
                            break

                        print(f"  尝试位置{i+1}: ({x}, {y})")
                        try:
                            # 点击座位
                            self.driver.execute_script('mobile: clickGesture', {
                                'x': x,
                                'y': y,
                                'duration': 80
                            })
                            time.sleep(0.8)

                            # 检查底部按钮文本是否变化
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().className("android.widget.Button")'
                            )

                            for btn in reversed(buttons):  # 从底部开始
                                try:
                                    rect = btn.rect
                                    if rect['y'] > screen_size['height'] - 300:  # 底部区域
                                        btn_text = btn.text if hasattr(btn, 'text') else ''
                                        print(f"    底部按钮文本: '{btn_text}'")
                                        # 如果按钮文本不再是"请先选座"，说明选座成功
                                        if btn_text and "请先选座" not in btn_text:
                                            seat_selected = True
                                            print(f"  ✅ 选座成功！位置({x},{y})")
                                            break
                                except:
                                    continue
                        except Exception as e:
                            print(f"    位置{i+1}失败: {e}")
                            continue

                    if not seat_selected:
                        print("  ⚠️ 未能自动选座，尝试备用方案...")
                        # 备用方案：直接点击座位图中心偏上的位置
                        try:
                            self.driver.execute_script('mobile: clickGesture', {
                                'x': center_x,
                                'y': 300,  # 固定在300的y坐标
                                'duration': 100
                            })
                            time.sleep(1)
                            print("  执行了备用点击")
                        except:
                            pass

                    # 步骤3：点击底部确认按钮（不管是否成功选座都尝试）
                    print("步骤3: 点击确认按钮...")
                    time.sleep(1)
                    try:
                        buttons = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().className("android.widget.Button")'
                        )
                        clicked = False
                        for btn in reversed(buttons):
                            try:
                                rect = btn.rect
                                if rect['y'] > screen_size['height'] - 300:
                                    btn_text = btn.text if hasattr(btn, 'text') else ''
                                    print(f"  找到底部按钮: '{btn_text}'")
                                    btn.click()
                                    clicked = True
                                    print(f"  ✅ 点击了按钮: {btn_text}")
                                    break
                            except:
                                continue

                        if not clicked:
                            # 如果没找到按钮，直接点击底部中央
                            print("  使用坐标点击底部...")
                            self.driver.execute_script('mobile: clickGesture', {
                                'x': center_x,
                                'y': screen_size['height'] - 100
                            })
                    except Exception as e:
                        print(f"  点击确认按钮失败: {e}")

                    time.sleep(2)
                    print("=== 选座流程完成 ===")
                else:
                    print("未检测到选座页面，跳过")
            except Exception as e:
                print(f"选座处理失败: {e}")

            # 4. 检查是否是电影票（电影票跳过票价选择）
            current_activity = self.driver.current_activity
            is_movie_ticket = "movie" in current_activity.lower() or "cinema" in current_activity.lower() or "seat" in current_activity.lower()

            if is_movie_ticket:
                print("检测到电影票流程，跳过票价选择...")

                # 先勾选协议（在弹窗中）
                print("勾选用户协议...")
                time.sleep(1)  # 等待弹窗完全显示
                try:
                    agreement_checked = False

                    # 方式1: 查找包含"我已阅读并同意"的文本，点击其左边的复选框
                    try:
                        agreements = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().textContains("我已阅读并同意")'
                        )
                        if agreements:
                            for agreement in agreements:
                                try:
                                    rect = agreement.rect
                                    # 点击文本左边60px的位置（复选框圆圈）
                                    x = rect['x'] - 60
                                    y = rect['y'] + rect['height'] // 2
                                    if x > 20:  # 确保坐标在屏幕内
                                        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                                        agreement_checked = True
                                        print(f"点击了协议文本左边的复选框 ({x}, {y})")
                                        break
                                except Exception as e:
                                    print(f"单个协议元素处理失败: {e}")
                                    continue
                    except Exception as e:
                        print(f"方式1失败: {e}")

                    # 方式2: 通过坐标点击弹窗中的复选框（弹窗居中，复选框在左侧）
                    if not agreement_checked:
                        try:
                            screen_size = self.driver.get_window_size()
                            # 弹窗通常在屏幕中央，复选框在弹窗中"我已阅读"文字左边
                            # 估算位置：屏幕中央偏左
                            x = screen_size['width'] // 2 - 80
                            y = screen_size['height'] // 2 + 100  # 弹窗中下部
                            self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                            agreement_checked = True
                            print(f"点击了弹窗协议复选框位置 ({x}, {y})")
                        except Exception as e:
                            print(f"方式2失败: {e}")

                    # 方式3: 查找RadioButton或ImageView（未选中的圆圈）
                    if not agreement_checked:
                        try:
                            # 查找屏幕中央区域的小图标
                            images = self.driver.find_elements(By.CLASS_NAME, "android.widget.ImageView")
                            for img in images:
                                try:
                                    rect = img.rect
                                    screen_size = self.driver.get_window_size()
                                    # 弹窗中央区域的小图标
                                    if (400 < rect['y'] < 700 and
                                        rect['width'] < 60 and rect['height'] < 60 and
                                        rect['x'] < screen_size['width'] // 2):
                                        img.click()
                                        agreement_checked = True
                                        print(f"点击了弹窗中的ImageView复选框")
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"方式3失败: {e}")

                    if agreement_checked:
                        time.sleep(0.5)  # 等待复选框状态更新
                    else:
                        print("未找到协议复选框，尝试继续...")

                except Exception as e:
                    print(f"勾选协议失败: {e}")

                # 第二步：点击"继续购票"
                print("点击继续购票...")
                try:
                    continue_clicked = False

                    # 查找"继续购票"按钮
                    continue_buttons = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textMatches(".*继续购票.*|.*继续.*|.*下一步.*")'
                    )
                    if continue_buttons:
                        for btn in continue_buttons:
                            try:
                                btn.click()
                                continue_clicked = True
                                print(f"点击了继续购票按钮: {btn.text}")
                                break
                            except:
                                continue

                    if not continue_clicked:
                        print("未找到继续购票按钮，尝试继续...")

                    time.sleep(2)  # 等待进入支付页面
                except Exception as e:
                    print(f"点击继续购票失败: {e}")

                # 第三步：点击"立即付款"
                print("点击立即付款...")
                try:
                    payment_clicked = False

                    # 查找"立即付款"按钮（通常在右下角）
                    payment_buttons = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textMatches(".*立即付款.*|.*去支付.*|.*确认支付.*|.*付款.*")'
                    )
                    if payment_buttons:
                        for btn in reversed(payment_buttons):
                            try:
                                rect = btn.rect
                                # 右下角按钮
                                if rect['y'] > 900 and rect['x'] > 300:
                                    btn.click()
                                    payment_clicked = True
                                    print(f"点击了立即付款按钮: {btn.text}, 位置({rect['x']}, {rect['y']})")
                                    break
                            except:
                                continue

                    # 备用方案：点击右下角
                    if not payment_clicked:
                        screen_size = self.driver.get_window_size()
                        x = screen_size['width'] - 100  # 右下角
                        y = screen_size['height'] - 80
                        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                        payment_clicked = True
                        print(f"点击了右下角位置 ({x}, {y})")

                    time.sleep(1)
                except Exception as e:
                    print(f"点击立即付款失败: {e}")

                end_time = time.time()
                print(f"抢票流程完成，耗时: {end_time - start_time:.2f}秒")
                return True

            # 以下是演唱会票流程
            # 4. 票价选择 - 优化查找逻辑
            print("选择票价...")
            try:
                # 直接尝试点击，不等待容器，实际每次都失败，只能等待
                price_container = self.driver.find_element(By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')
                # price_container = self.wait.until(  # 等待找到容器
                #     EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')))
                # 在容器内找 index=1 且 clickable="true" 的 FrameLayout【因为799元的票价是排在第二的，但是page里text是空的被隐藏了】
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})
            except Exception as e:
                print(f"票价选择失败，启动备用方案: {e}")
                # 备用方案
                # 先找到大容器
                price_container = self.wait.until(
                    EC.presence_of_element_located((By.ID, 'cn.damai:id/project_detail_perform_price_flowlayout')))
                # 在容器内找 index=1 且 clickable="true" 的 FrameLayout【因为799元的票价是排在第二的，但是page里text是空的被隐藏了】
                target_price = price_container.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().className("android.widget.FrameLayout").index({self.config.price_index}).clickable(true)'
                )
                self.driver.execute_script('mobile: clickGesture', {'elementId': target_price.id})

                # if not self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR,
                #                              'new UiSelector().textMatches(".*799.*|.*\\d+元.*")'):
                #     return False

            # 4. 数量选择
            print("选择数量...")
            if self.driver.find_elements(by=By.ID, value='layout_num'):
                clicks_needed = len(self.config.users) - 1
                if clicks_needed > 0:
                    try:
                        plus_button = self.driver.find_element(By.ID, 'img_jia')
                        for i in range(clicks_needed):
                            rect = plus_button.rect
                            x = rect['x'] + rect['width'] // 2
                            y = rect['y'] + rect['height'] // 2
                            self.driver.execute_script("mobile: clickGesture", {
                                "x": x,
                                "y": y,
                                "duration": 50
                            })
                            time.sleep(0.02)
                    except Exception as e:
                        print(f"快速点击加号失败: {e}")

            # if self.driver.find_elements(by=By.ID, value='layout_num') and self.config.users is not None:
            #     for i in range(len(self.config.users) - 1):
            #         self.driver.find_element(by=By.ID, value='img_jia').click()

            # 5. 确定购买
            print("确定购买...")
            if not self.ultra_fast_click(By.ID, "btn_buy_view"):
                # 备用按钮文本
                self.ultra_fast_click(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*确定.*|.*购买.*")')

            # 6. 批量选择用户
            print("选择用户...")
            user_clicks = [(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{user}")') for user in
                           self.config.users]
            # self.batch_click(user_clicks, delay=0.05)  # 极短延迟
            self.ultra_batch_click(user_clicks)

            # 7. 提交订单
            print("提交订单...")
            submit_selectors = [
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("立即提交")'),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches(".*提交.*|.*确认.*")'),
                (By.XPATH, '//*[contains(@text,"提交")]')
            ]
            self.smart_wait_and_click(*submit_selectors[0], submit_selectors[1:])

            end_time = time.time()
            print(f"抢票流程完成，耗时: {end_time - start_time:.2f}秒")
            return True

        except Exception as e:
            print(f"抢票过程发生错误: {e}")
            return False
        finally:
            time.sleep(1)  # 给最后的操作一点时间
            self.driver.quit()

    def run_with_retry(self, max_retries=3):
        """带重试机制的抢票"""
        for attempt in range(max_retries):
            print(f"第 {attempt + 1} 次尝试...")
            if self.run_ticket_grabbing():
                print("抢票成功！")
                return True
            else:
                print(f"第 {attempt + 1} 次尝试失败")
                if attempt < max_retries - 1:
                    print("2秒后重试...")
                    time.sleep(2)
                    # 重新初始化驱动
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self._setup_driver()

        print("所有尝试均失败")
        return False


# 使用示例
if __name__ == "__main__":
    bot = DamaiBot()
    bot.run_with_retry(max_retries=3)
