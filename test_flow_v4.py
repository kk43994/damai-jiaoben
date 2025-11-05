#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
基础流程测试 v4 - 扩展到搜索结果和详情页
流程：首页 -> 搜索 -> 输入关键词 -> 查看结果 -> 点击目标 -> 进入详情页
"""

import time
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options

APPIUM_URL = "http://127.0.0.1:4723"
UDID = "127.0.0.1:53910"
PKG  = "cn.damai"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def build_driver():
    """创建驱动"""
    opts = UiAutomator2Options()
    opts.set_capability("platformName", "Android")
    opts.set_capability("automationName", "UiAutomator2")
    opts.set_capability("udid", UDID)
    opts.set_capability("appPackage", PKG)
    opts.set_capability("noReset", True)
    opts.set_capability("newCommandTimeout", 300)
    opts.set_capability("adbExecTimeout", 120000)
    opts.set_capability("uiautomator2ServerLaunchTimeout", 60000)  # 增加到60秒
    opts.set_capability("uiautomator2ServerInstallTimeout", 120000)  # 增加到120秒
    opts.set_capability("ignoreHiddenApiPolicyError", True)
    opts.set_capability("disableWindowAnimation", True)
    opts.set_capability("skipLogcatCapture", True)

    log("="*60)
    log("连接Appium...")
    driver = webdriver.Remote(APPIUM_URL, options=opts)
    log("[OK] 连接成功")

    driver.update_settings({"waitForIdleTimeout": 0})
    driver.activate_app(PKG)
    driver.implicitly_wait(0)
    time.sleep(3)  # 等待首页加载

    return driver

def dismiss_common_overlays(driver):
    """处理常见弹窗（基于GPT建议）- 不包括搜索页的"取消"按钮"""
    overlay_patterns = [
        ('new UiSelector().textContains("关闭")', "关闭按钮"),
        ('new UiSelector().textContains("稍后")', "稍后按钮"),
        ('new UiSelector().textContains("知道了")', "知道了按钮"),
        ('new UiSelector().descriptionContains("关闭")', "关闭描述"),
    ]

    for selector, desc in overlay_patterns:
        try:
            els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
            if els:
                els[0].click()
                log(f"  [OK] 关闭弹窗: {desc}")
                time.sleep(0.5)
                return True
        except:
            continue
    return False

def _ensure_in_search_page(driver):
    """确认当前是搜索页：'取消'/EditText/标题含'搜索' 任一命中"""
    time.sleep(0.35)  # 过渡动画缓冲
    end = time.time() + 3.0
    while time.time() < end:
        if driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("取消")'):
            return True
        if driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText"):
            return True
        if driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("搜索")'):
            return True
        time.sleep(0.2)
    return False

def _get_search_input_element(driver, pkg="cn.damai"):
    """更鲁棒地拿输入控件（SearchView/自定义/Compose 都尽量覆盖）"""
    candidates = [
        (AppiumBy.ID, f"{pkg}:id/search_input_text"),
        (AppiumBy.ID, f"{pkg}:id/search_src_text"),  # 常见 SearchView 文本框ID
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("搜索")'),
        (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("搜索")'),
        (AppiumBy.CLASS_NAME, "android.widget.EditText"),
    ]
    for by, val in candidates:
        try:
            els = driver.find_elements(by, val)
            if els:
                return els[0]
        except:
            pass
    return None

def _focus_then_check_keyboard(driver, el=None, fallback_xy=(360, 150)):
    """点中输入框并尽量唤起键盘；必要时用坐标兜底再点一次"""
    try:
        if el:
            el.click()
        else:
            driver.execute_script("mobile: clickGesture", {"x": fallback_xy[0], "y": fallback_xy[1]})
        time.sleep(0.25)
    except:
        pass
    try:
        if not driver.is_keyboard_shown():  # 某些环境不支持也没关系
            if el:
                el.click()
            else:
                driver.execute_script("mobile: clickGesture", {"x": fallback_xy[0], "y": fallback_xy[1]})
            time.sleep(0.25)
    except:
        pass

def _device_level_input(driver, text: str) -> bool:
    """设备级输入兜底（最稳）：mobile:shell input text"""
    safe = text.replace(" ", "%s")
    try:
        driver.execute_script("mobile: shell", {
            "command": "input",
            "args": ["text", safe],
            "includeStderr": True,
            "timeout": 5000
        })
        return True
    except Exception as e:
        log(f"[WARN] device-level input failed: {e}")
        return False

def select_city(driver, target_city="广州"):
    """
    自动检测并切换城市。
    1. 找顶部城市 TextView
    2. 若当前城市 != target_city，点击并选择
    """
    log("="*60)
    log("步骤0: 检查/切换城市")
    log("="*60)

    try:
        # 等待首页完全加载（城市控件加载较慢）
        log("  等待首页加载...")
        time.sleep(2)

        # 找城市控件（带重试机制）
        els = None
        for attempt in range(3):
            els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/home_city")
            if els:
                break
            # 尝试旧版ID
            els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/tv_city")
            if els:
                break
            if attempt < 2:
                log(f"  第{attempt+1}次未找到，等待1秒后重试...")
                time.sleep(1)

        if not els:
            log("[WARN] 未找到城市控件（重试3次后失败）")
            return False

        city_el = els[0]
        current_city = city_el.text.strip() if city_el.text else ""
        try:
            log(f"  当前城市: {current_city}")
        except:
            log(f"  当前城市: (含特殊字符)")

        if target_city in current_city:
            log(f"  [OK] 当前城市已是 {target_city}")
            return True

        log(f"  [INFO] 需切换到城市: {target_city}")
        city_el.click()
        time.sleep(0.8)

        # 尝试点击城市名称（大多数为 TextView）
        els2 = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{target_city}")')
        if els2:
            els2[0].click()
            log(f"  [OK] 已切换城市到 {target_city}")
            time.sleep(1.0)
            return True
        else:
            # 输入搜索城市（部分新版大麦城市过多需搜索）
            try:
                input_box = driver.find_element(AppiumBy.CLASS_NAME, "android.widget.EditText")
                input_box.click()
                input_box.clear()
                input_box.send_keys(target_city)
                time.sleep(0.8)  # 等待搜索结果出现

                # 直接从搜索结果中找到并点击城市（不要按回车！）
                first = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                if first:
                    for item in first:
                        try:
                            text = item.text or ""
                            if target_city in text:
                                item.click()
                                log(f"  [OK] 已通过搜索切换城市到 {target_city}")
                                time.sleep(1.0)
                                return True
                        except:
                            continue
            except Exception as e:
                try:
                    log(f"  [WARN] 搜索城市失败: {e}")
                except:
                    log(f"  [WARN] 搜索城市失败（编码错误）")

        log("  [WARN] 未能切换城市，保持默认城市")
        return False

    except Exception as e:
        try:
            log(f"[ERROR] 城市选择失败: {e}")
        except:
            log(f"[ERROR] 城市选择失败（编码错误）")
        return False

def test_click_search_area(driver):
    """步骤1: 点击搜索框"""
    log("="*60)
    log("步骤1: 点击搜索框")

    # 先处理可能的首页弹窗（只处理特定的，不包括"取消"）
    dismiss_common_overlays(driver)
    time.sleep(0.3)

    # 记录当前activity
    try:
        activity = driver.current_activity
        log(f"  当前Activity: {activity}")
    except:
        pass

    # 方法1: homepage_header_search_layout
    try:
        log("  尝试：homepage_header_search_layout...")
        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/homepage_header_search_layout")
        if els:
            t0 = time.time()
            els[0].click()
            log("  [OK] 点击搜索框布局")
            if _ensure_in_search_page(driver):
                elapsed = time.time() - t0
                log(f"  [OK] 进入搜索页成功 (耗时 {elapsed:.2f}s)")
                dismiss_common_overlays(driver)
                return True
            else:
                log("  [WARN] 点击后未检测到搜索页锚点，继续尝试其它方式")
        else:
            log("  [SKIP] 未找到homepage_header_search_layout")
    except Exception as e:
        log(f"  [SKIP] 方法1失败: {e}")

    # 方法2: pioneer_homepage_header_search_btn
    try:
        log("  尝试：pioneer_homepage_header_search_btn...")
        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/pioneer_homepage_header_search_btn")
        if els:
            t0 = time.time()
            els[0].click()
            log("  [OK] 点击搜索按钮")
            if _ensure_in_search_page(driver):
                elapsed = time.time() - t0
                log(f"  [OK] 进入搜索页成功 (耗时 {elapsed:.2f}s)")
                dismiss_common_overlays(driver)
                return True
            else:
                log("  [WARN] 点击后未检测到搜索页锚点，继续尝试其它方式")
        else:
            log("  [SKIP] 未找到pioneer_homepage_header_search_btn")
    except Exception as e:
        log(f"  [SKIP] 方法2失败: {e}")

    # 方法3: 坐标点击
    try:
        log("  尝试：坐标点击...")
        x, y = 408, 88
        t0 = time.time()
        driver.execute_script("mobile: clickGesture", {"x": x, "y": y})
        log(f"  [OK] 坐标点击 ({x}, {y})")
        if _ensure_in_search_page(driver):
            elapsed = time.time() - t0
            log(f"  [OK] 进入搜索页成功 (耗时 {elapsed:.2f}s)")
            dismiss_common_overlays(driver)
            return True
        else:
            log("  [ERROR] 坐标点击后仍未进入搜索页")
    except Exception as e:
        log(f"  [ERROR] 坐标点击失败: {e}")

    log("  [ERROR] 所有方法失败")
    return False

def test_input_and_search(driver, keyword="演唱会"):
    """步骤2: 输入关键词并搜索（稳定版）"""
    log("="*60)
    log(f"步骤2: 输入关键词并搜索: {keyword}")

    # 1) 确认已在搜索页（若Step1已修改，这段可作为双重保险）
    if not _ensure_in_search_page(driver):
        log("[WARN] 未确认在搜索页，尝试再次点击顶部搜索入口后重试")
        for by, val in [
            (AppiumBy.ID, f"{PKG}:id/pioneer_homepage_header_search_btn"),
            (AppiumBy.ID, f"{PKG}:id/homepage_header_search_layout"),
        ]:
            try:
                els = driver.find_elements(by, val)
                if els:
                    els[0].click()
                    time.sleep(0.4)
                    if _ensure_in_search_page(driver):
                        break
            except:
                pass
        if not _ensure_in_search_page(driver):
            log("[ERROR] 仍未进入搜索页，退出")
            # 保存调试信息
            try:
                activity = driver.current_activity
                log(f"  当前Activity: {activity}")
                source = driver.page_source
                with open("debug_not_in_search_page.xml", "w", encoding="utf-8") as f:
                    f.write(source[:2000])  # 只保存前2000字符
            except:
                pass
            return False

    dismiss_common_overlays(driver)

    # 记录键盘状态
    try:
        keyboard_shown = driver.is_keyboard_shown()
        log(f"  键盘状态: {keyboard_shown}")
    except:
        log("  键盘状态: N/A")

    # 2) 拿输入框并聚焦（必要时坐标兜底）
    el = _get_search_input_element(driver, pkg=PKG)
    if not el:
        log("[WARN] 未直接找到输入框，坐标聚焦兜底")
        _focus_then_check_keyboard(driver, el=None)
    else:
        log(f"  [OK] 找到输入框")
        _focus_then_check_keyboard(driver, el=el)

    # 3) 三段式输入（任一步成功即通过）
    input_success = False
    input_method = ""

    # 3.1 send_keys
    try:
        if el:
            el.clear()
            time.sleep(0.2)
            el.send_keys(keyword)
            time.sleep(0.4)
            text = el.text or el.get_attribute("text")
            if keyword in (text or ""):
                log(f"  [OK] send_keys 成功: {text}")
                input_success = True
                input_method = "send_keys"
    except Exception as e:
        log(f"  [WARN] send_keys 失败: {e}")

    # 3.2 set_value
    if not input_success:
        try:
            if el:
                el.clear()
                time.sleep(0.2)
                el.set_value(keyword)
                time.sleep(0.4)
                text = el.text or el.get_attribute("text")
                if keyword in (text or ""):
                    log(f"  [OK] set_value 成功: {text}")
                    input_success = True
                    input_method = "set_value"
        except Exception as e:
            log(f"  [WARN] set_value 失败: {e}")

    # 3.3 设备级输入兜底
    if not input_success:
        if _device_level_input(driver, keyword):
            log("[OK] 设备级输入成功（mobile:shell input text）")
            input_success = True
            input_method = "device_level"

    # 4) 按回车搜索
    if input_success:
        log(f"  输入成功，使用方法: {input_method}")
        log("  按回车键搜索...")
        try:
            driver.press_keycode(66)  # KEYCODE_ENTER
            time.sleep(2)  # 等待搜索结果
        except Exception as e:
            log(f"  [WARN] 按回车失败: {e}")

        # 验证搜索结果
        try:
            source = driver.page_source
            if keyword in source or "搜索结果" in source:
                log("  [OK] 搜索成功，出现结果")
                return True
            else:
                log("  [WARN] 未验证到搜索结果")
                return False
        except:
            return False
    else:
        # 最终失败：回车尝试触发搜索
        try:
            driver.press_keycode(66)
        except:
            pass
        log("[ERROR] 三段式输入均未成功，需检查 page_source 与控件类型")
        # 保存调试信息
        try:
            source = driver.page_source
            with open("debug_input_failed.xml", "w", encoding="utf-8") as f:
                f.write(source[:2000])
        except:
            pass
        return False

def find_and_click_target(driver, target_keyword=None, max_scrolls=5):
    """步骤3: 在搜索结果中找到目标并点击（基于GPT建议）"""
    log("="*60)
    log(f"步骤3: 查找目标演出{f': {target_keyword}' if target_keyword else ''}")

    try:
        dismiss_common_overlays(driver)  # 先处理弹窗

        for scroll_count in range(max_scrolls):
            log(f"  第 {scroll_count + 1}/{max_scrolls} 轮查找...")

            # 获取当前页面所有可能的演出项
            # 尝试多种定位方式找到演出列表项
            item_selectors = [
                (AppiumBy.ID, f"{PKG}:id/item_project_title"),  # 演出标题
                (AppiumBy.ID, f"{PKG}:id/project_title"),
                (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView")'),
            ]

            found_items = []
            for by, val in item_selectors:
                try:
                    els = driver.find_elements(by, val)
                    if els:
                        found_items.extend(els)
                        break
                except:
                    continue

            if not found_items:
                log("  [WARN] 未找到任何演出项")
                # 尝试滚动
                if scroll_count < max_scrolls - 1:
                    log("  向下滚动...")
                    driver.execute_script("mobile: scrollGesture", {
                        "left": 100, "top": 800, "width": 500, "height": 800,
                        "direction": "down", "percent": 0.75
                    })
                    time.sleep(1)
                    continue
                else:
                    return False

            log(f"  找到 {len(found_items)} 个候选项")

            # 如果指定了关键词，按关键词过滤
            if target_keyword:
                for item in found_items:
                    try:
                        text = item.text or item.get_attribute("text") or ""
                        if target_keyword in text:
                            # 处理编码问题
                            try:
                                display_text = text[:30]
                                log(f"  [OK] 找到目标: {display_text}...")
                            except UnicodeEncodeError:
                                log(f"  [OK] 找到目标（含特殊字符）")
                            item.click()
                            time.sleep(2)
                            return True
                    except Exception as e:
                        continue

                # 没找到，继续滚动
                if scroll_count < max_scrolls - 1:
                    log(f"  未找到包含'{target_keyword}'的项，继续滚动...")
                    driver.execute_script("mobile: scrollGesture", {
                        "left": 100, "top": 800, "width": 500, "height": 800,
                        "direction": "down", "percent": 0.75
                    })
                    time.sleep(1)
                else:
                    log(f"  [WARN] 滚动{max_scrolls}次仍未找到目标")
                    return False
            else:
                # 没有指定关键词，点击第一个
                try:
                    first_item = found_items[0]
                    text = first_item.text or first_item.get_attribute("text") or "未知"
                    # 处理编码问题
                    try:
                        display_text = text[:30] if len(text) > 30 else text
                        log(f"  [OK] 点击第一个演出: {display_text}...")
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        log(f"  [OK] 点击第一个演出（含特殊字符）...")
                    first_item.click()
                    time.sleep(2)
                    return True
                except Exception as e:
                    # 处理异常消息的编码问题
                    try:
                        log(f"  [ERROR] 点击失败: {e}")
                    except:
                        log(f"  [ERROR] 点击失败（编码错误）")
                    return False

        return False

    except Exception as e:
        log(f"  [ERROR] 查找失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_detail_page(driver):
    """步骤4: 验证是否进入详情页（基于GPT建议的锚点）"""
    log("="*60)
    log("步骤4: 验证详情页")

    try:
        time.sleep(1.5)  # 等待页面加载
        dismiss_common_overlays(driver)  # 处理弹窗

        # 检查详情页锚点元素
        anchor_patterns = [
            ('new UiSelector().textContains("立即购买")', "立即购买"),
            ('new UiSelector().textContains("立即抢购")', "立即抢购"),
            ('new UiSelector().textContains("选择场次")', "选择场次"),
            ('new UiSelector().textContains("想看")', "想看按钮"),
            (f"{PKG}:id/project_detail_title", "详情页标题"),
        ]

        for selector_or_id, desc in anchor_patterns:
            try:
                if selector_or_id.startswith("new UiSelector"):
                    els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector_or_id)
                else:
                    els = driver.find_elements(AppiumBy.ID, selector_or_id)

                if els:
                    log(f"  [OK] 找到锚点: {desc}")

                    # 获取演出标题
                    try:
                        title_els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/project_detail_title")
                        if not title_els:
                            title_els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                                                            'new UiSelector().className("android.widget.TextView")')
                        if title_els:
                            title = title_els[0].text or title_els[0].get_attribute("text")
                            log(f"  [INFO] 演出标题: {title}")
                    except:
                        pass

                    return True
            except:
                continue

        log("  [WARN] 未找到详情页锚点")

        # 保存页面源码用于调试
        source = driver.page_source
        with open("debug_detail_page.xml", "w", encoding="utf-8") as f:
            f.write(source)
        log("  已保存页面XML到 debug_detail_page.xml")

        return False

    except Exception as e:
        log(f"  [ERROR] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_screenshot(driver, filename="test_final_v4.png"):
    """截图保存"""
    log("="*60)
    log(f"步骤5: 保存截图: {filename}")
    try:
        img = driver.get_screenshot_as_png()
        with open(filename, "wb") as f:
            f.write(img)
        log(f"[OK] 截图已保存: {filename}")
        return True
    except Exception as e:
        log(f"[ERROR] 截图失败: {e}")
        return False

def main():
    """主流程"""
    log("="*60)
    log("基础流程测试 v4 - 扩展到详情页")
    log("="*60)

    drv = None
    passed = 0
    total = 6  # 增加了城市选择步骤

    try:
        # 连接
        drv = build_driver()
        passed += 1

        # 步骤0: 城市选择（在搜索之前）
        if select_city(drv, target_city="北京"):
            passed += 1
        else:
            log("[WARN] 城市选择失败，继续测试")
            passed += 0.5  # 部分成功

        # 步骤1: 点击搜索框
        if test_click_search_area(drv):
            passed += 1
        else:
            log("[ERROR] 步骤1失败，终止测试")
            return

        # 步骤2: 输入并搜索
        search_keyword = "鹭卓 Ready To The Top 巡回演唱会"
        if test_input_and_search(drv, search_keyword):
            passed += 1
        else:
            log("[ERROR] 步骤2失败，终止测试")
            return

        # 步骤3: 查找并点击目标演出
        # 可以指定关键词，如: find_and_click_target(drv, "鹿晗")
        # 或不指定，点击第一个: find_and_click_target(drv)
        if find_and_click_target(drv):
            passed += 1
        else:
            log("[ERROR] 步骤3失败，终止测试")
            test_screenshot(drv, "test_search_results_failed.png")
            return

        # 步骤4: 验证详情页
        if verify_detail_page(drv):
            passed += 1
        else:
            log("[WARN] 步骤4验证失败，但可能已进入详情页")
            passed += 0.5  # 部分成功

        # 步骤5: 截图
        test_screenshot(drv)

    except KeyboardInterrupt:
        log("\n[INTERRUPT] 用户中断")
    except Exception as e:
        log(f"\n[ERROR] 测试异常: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if drv:
            try:
                log("\n关闭连接...")
                drv.quit()
                log("[OK] 已关闭")
            except:
                pass

        log("="*60)
        log(f"测试完成: {passed}/{total} ({passed/total*100:.1f}%)")
        if passed == total:
            log("[SUCCESS] 全部通过！详情页流程OK")
        elif passed >= 4:
            log("[PARTIAL] 大部分通过，基本流程打通")
        else:
            log("[FAILED] 测试失败")

if __name__ == "__main__":
    main()
