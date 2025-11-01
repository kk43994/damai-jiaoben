# -*- coding: UTF-8 -*-
"""
__Author__ = "BlueCestbon"
__Version__ = "2.0.0"
__Description__ = "大麦app抢票自动化 - 优化版"
__Created__ = 2025/09/13 19:27
"""

import time
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


class DamaiBot:
    def __init__(self):
        self.config = Config.load_config()
        self.driver = None
        self.wait = None
        self._setup_driver()

    def _setup_driver(self):
        """初始化驱动配置 - 包含反检测设置"""
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
        self.driver = webdriver.Remote(self.config.server_url, options=device_app_info)

        # 更激进的性能优化设置
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
            print("开始抢票流程...")
            start_time = time.time()

            # 0. 等待 APP 完全启动
            print("等待APP启动...")
            max_wait_time = 10  # 最多等待10秒
            for i in range(max_wait_time):
                time.sleep(1)
                current_activity = self.driver.current_activity
                print(f"当前Activity: {current_activity}")

                # 如果已经离开启动页，进入主页
                if "SplashActivity" not in current_activity and "Splash" not in current_activity:
                    print(f"APP启动完成，进入{current_activity}")
                    break

                if i == max_wait_time - 1:
                    print("APP启动超时")
                    return False

            # 再等待1秒确保页面完全加载
            time.sleep(2)

            # 关闭可能出现的广告弹窗
            print("检查并关闭广告弹窗...")
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
                                    print(f"点击了文字关闭按钮")
                                    break
                            except:
                                continue
                except:
                    pass

                # 方式2: 查找右上角的小ImageView（X按钮通常是小图标）
                if not ad_closed:
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
                                    print(f"点击了右上角X按钮 ({rect['x']}, {rect['y']})")
                                    break
                            except:
                                continue
                    except:
                        pass

                # 方式3: 直接点击右上角固定位置
                if not ad_closed:
                    try:
                        screen_size = self.driver.get_window_size()
                        x = screen_size['width'] - 50  # 右上角
                        y = 50
                        self.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                        ad_closed = True
                        print(f"点击了右上角固定位置 ({x}, {y})")
                    except:
                        pass

                if ad_closed:
                    time.sleep(1)  # 等待广告关闭动画
                else:
                    print("未检测到广告，继续...")

            except Exception as e:
                print(f"关闭广告失败: {e}")

            # 重新获取当前页面
            current_activity = self.driver.current_activity
            print(f"当前页面: {current_activity}")

            # 判断是否需要搜索
            need_search = False
            need_click_result = False
            need_select_city = False

            # 检查是否在影城选择页面
            if "Cinema" in current_activity:
                print("在影城选择页面，跳过搜索流程")
                # 不需要搜索，直接到影城选择环节
            elif ".homepage.MainActivity" in current_activity or "HomePageActivity" in current_activity:
                need_select_city = True  # 在首页需要选择城市
                need_search = True
                need_click_result = True
                print("在首页，需要完整搜索流程")
            elif "SearchActivity" in current_activity:
                # 在搜索页面，检查是否有搜索结果
                try:
                    results = self.driver.find_elements(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiSelector().textContains("{self.config.keyword[:10]}")'
                    )
                    if results:
                        need_click_result = True
                        print("在搜索页面，发现搜索结果，需要点击")
                    else:
                        need_search = True
                        need_click_result = True
                        print("在搜索页面，但无结果，需要重新搜索")
                except:
                    need_click_result = True
                    print("在搜索页面，尝试点击结果")

            # 执行搜索流程
            if need_search:
                print(f"在首页，开始搜索关键词: {self.config.keyword}")

                # 0.1 尝试多种方式找到并点击搜索框
                print("查找搜索框...")
                search_clicked = False

                # 方式1: 通过ID查找
                try:
                    search_box = self.driver.find_element(By.ID, "cn.damai:id/search_edit_view")
                    search_box.click()
                    search_clicked = True
                    print("通过ID找到搜索框")
                except:
                    pass

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
                            print("通过文本找到搜索框")
                    except Exception as e:
                        print(f"方式2失败: {e}")

                # 方式3: 查找 EditText
                if not search_clicked:
                    try:
                        edit_texts = self.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
                        if edit_texts:
                            edit_texts[0].click()
                            search_clicked = True
                            print("通过EditText找到搜索框")
                    except Exception as e:
                        print(f"方式3失败: {e}")

                if not search_clicked:
                    print("搜索框点击失败")
                    return False

                time.sleep(1)  # 等待搜索框打开

                # 0.1.5 处理位置权限弹窗（关键步骤！）
                print("检查位置权限弹窗...")
                time.sleep(1.5)  # 等待弹窗显示

                try:
                    permission_handled = False

                    # 方式1: 查找"立即开启"按钮（优先点击这个）
                    try:
                        print("  查找'立即开启'按钮...")
                        buttons = self.driver.find_elements(
                            AppiumBy.ANDROID_UIAUTOMATOR,
                            'new UiSelector().text("立即开启")'
                        )
                        if buttons:
                            buttons[0].click()
                            permission_handled = True
                            print("  ✅ 点击了'立即开启'按钮")
                            time.sleep(1)
                    except Exception as e:
                        print(f"  方式1失败: {e}")

                    # 方式2: 查找"下次再说"按钮
                    if not permission_handled:
                        try:
                            print("  查找'下次再说'按钮...")
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().text("下次再说")'
                            )
                            if buttons:
                                buttons[0].click()
                                permission_handled = True
                                print("  ✅ 点击了'下次再说'按钮")
                                time.sleep(1)
                        except Exception as e:
                            print(f"  方式2失败: {e}")

                    # 方式3: 通用匹配 - 查找包含"开启"、"允许"等文本的按钮
                    if not permission_handled:
                        try:
                            print("  尝试通用权限按钮匹配...")
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textMatches(".*开启.*|.*允许.*|.*同意.*").clickable(true)'
                            )
                            if buttons:
                                for btn in buttons:
                                    try:
                                        text = btn.text if hasattr(btn, 'text') else ''
                                        print(f"  找到按钮: {text}")
                                        btn.click()
                                        permission_handled = True
                                        print(f"  ✅ 点击了: {text}")
                                        time.sleep(1)
                                        break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"  方式3失败: {e}")

                    # 方式4: 如果都没找到，尝试"下次"、"取消"、"暂不"等
                    if not permission_handled:
                        try:
                            print("  查找拒绝按钮...")
                            buttons = self.driver.find_elements(
                                AppiumBy.ANDROID_UIAUTOMATOR,
                                'new UiSelector().textMatches(".*下次.*|.*取消.*|.*暂不.*").clickable(true)'
                            )
                            if buttons:
                                buttons[0].click()
                                permission_handled = True
                                print(f"  ✅ 点击了拒绝按钮")
                                time.sleep(1)
                        except:
                            pass

                    if permission_handled:
                        print("  权限弹窗已处理")
                    else:
                        print("  未发现权限弹窗，继续...")

                except Exception as e:
                    print(f"  权限弹窗处理异常: {e}")

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

                    time.sleep(3)  # 等待进入详情页
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

            time.sleep(2)  # 等待进入选票页面

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
