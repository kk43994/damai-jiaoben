#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
快速测试脚本 - 保持Appium会话，快速执行测试
避免每次都重新连接（节省2分钟初始化时间）
"""
import time
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options

# 全局driver，保持会话
global_driver = None

APPIUM_URL = "http://127.0.0.1:4723"
UDID = "127.0.0.1:53910"
PKG = "cn.damai"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def get_driver():
    """获取或创建driver（只初始化一次）"""
    global global_driver

    if global_driver is not None:
        try:
            # 测试连接是否还活跃
            global_driver.current_activity
            log("[复用] 使用现有Appium会话")
            return global_driver
        except:
            log("[重连] 会话已失效，重新创建")
            global_driver = None

    log("[初始化] 创建新Appium会话（约2分钟）...")
    opts = UiAutomator2Options()
    opts.set_capability("platformName", "Android")
    opts.set_capability("automationName", "UiAutomator2")
    opts.set_capability("udid", UDID)
    opts.set_capability("appPackage", PKG)
    opts.set_capability("noReset", True)
    opts.set_capability("newCommandTimeout", 300)
    opts.set_capability("adbExecTimeout", 120000)
    opts.set_capability("uiautomator2ServerLaunchTimeout", 60000)
    opts.set_capability("uiautomator2ServerInstallTimeout", 120000)
    opts.set_capability("ignoreHiddenApiPolicyError", True)
    opts.set_capability("disableWindowAnimation", True)
    opts.set_capability("skipLogcatCapture", True)

    global_driver = webdriver.Remote(APPIUM_URL, options=opts)
    global_driver.update_settings({"waitForIdleTimeout": 0})
    log("[OK] Appium会话已创建")

    return global_driver

def reset_to_homepage(driver):
    """重置到首页（快速，只需3秒）"""
    log("[重置] 返回首页...")
    try:
        # 多次按返回键回到首页
        for _ in range(5):
            driver.press_keycode(4)  # BACK
            time.sleep(0.3)

        # 激活App
        driver.activate_app(PKG)
        time.sleep(2)
        log("[OK] 已返回首页")
        return True
    except Exception as e:
        log(f"[ERROR] 重置失败: {e}")
        return False

def quick_search(driver, city, keyword):
    """快速搜索测试"""
    log("="*60)
    log(f"测试: 城市={city}, 关键词={keyword}")
    log("="*60)

    # 等待首页加载
    time.sleep(2)

    # 1. 城市选择（简化版）
    try:
        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/home_city")
        if els:
            current = els[0].text or ""
            log(f"  当前城市: {current}")
            if city not in current:
                log(f"  切换到: {city}")
                els[0].click()
                time.sleep(0.5)

                # 搜索城市并点击结果（不要按回车！）
                input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                if input_els:
                    input_els[0].send_keys(city)
                    time.sleep(0.8)  # 等待搜索结果出现

                    # 从搜索结果中找到并点击城市
                    city_results = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                    for result in city_results:
                        try:
                            text = result.text or ""
                            if city in text:
                                result.click()
                                time.sleep(0.5)
                                log(f"  [OK] 已切换到{city}")
                                break
                        except:
                            continue
    except Exception as e:
        log(f"  [SKIP] 城市选择: {e}")

    # 2. 点击搜索框
    try:
        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/homepage_header_search_layout")
        if els:
            els[0].click()
            time.sleep(1)
            log("  [OK] 进入搜索页")
    except:
        log("  [ERROR] 搜索框点击失败")
        return False

    # 3. 输入关键词
    try:
        input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        if input_els:
            input_els[0].clear()
            time.sleep(0.2)
            input_els[0].send_keys(keyword)
            time.sleep(0.5)
            log(f"  [OK] 输入: {keyword}")
    except Exception as e:
        log(f"  [ERROR] 输入失败: {e}")
        return False

    # 4. 搜索
    try:
        driver.press_keycode(66)  # ENTER
        time.sleep(2)
        log("  [OK] 搜索完成")

        # 截图
        img = driver.get_screenshot_as_png()
        filename = f"search_{city}_{keyword[:10]}.png"
        with open(filename, "wb") as f:
            f.write(img)
        log(f"  [OK] 截图: {filename}")

        return True
    except Exception as e:
        log(f"  [ERROR] 搜索失败: {e}")
        return False

def find_and_click_show(driver):
    """在搜索结果中查找并点击演出"""
    log("\n  步骤: 查找演出列表")
    try:
        time.sleep(1.5)  # 等待列表加载

        # 尝试多种方式查找演出列表项
        item_ids = [
            f"{PKG}:id/item_project_title",
            f"{PKG}:id/project_title",
            f"{PKG}:id/title",
        ]

        found_items = []
        for item_id in item_ids:
            try:
                els = driver.find_elements(AppiumBy.ID, item_id)
                if els:
                    log(f"  通过 {item_id} 找到 {len(els)} 个")
                    found_items.extend(els)
                    break
            except:
                pass

        # 通过文本查找
        if not found_items:
            log("  尝试通过文本查找...")
            try:
                els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("鹭卓")')
                if els:
                    found_items.extend(els)
                    log(f"  通过关键词找到 {len(els)} 个")
            except:
                pass

        if found_items:
            log(f"  [INFO] 找到 {len(found_items)} 个候选项")

            # 点击第一个包含"鹭卓"的
            for item in found_items:
                try:
                    text = item.text or ""
                    if "鹭卓" in text or len(text) > 5:
                        log(f"  点击: {text[:30]}...")
                        item.click()
                        time.sleep(2)
                        log("  [OK] 已点击演出")
                        return True
                except:
                    continue

            # 如果没找到，点击第一个
            try:
                found_items[0].click()
                time.sleep(2)
                log("  [OK] 已点击第一个")
                return True
            except:
                pass

        log("  [WARN] 未找到演出项")
        return False

    except Exception as e:
        log(f"  [ERROR] {e}")
        return False

def verify_detail_page(driver):
    """验证是否进入详情页"""
    log("\n  步骤: 验证详情页")
    try:
        time.sleep(1.5)

        # 查找详情页锚点
        anchors = ["立即购买", "立即抢购", "选择场次", "想看"]

        for anchor in anchors:
            try:
                els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{anchor}")')
                if els:
                    log(f"  [OK] 找到锚点: {anchor}")

                    # 保存截图
                    img = driver.get_screenshot_as_png()
                    with open("detail_page_success.png", "wb") as f:
                        f.write(img)
                    log("  [OK] 截图: detail_page_success.png")

                    return True
            except:
                pass

        log("  [WARN] 未找到详情页锚点")

        # 保存调试截图
        img = driver.get_screenshot_as_png()
        with open("detail_page_unknown.png", "wb") as f:
            f.write(img)
        log("  已保存调试截图: detail_page_unknown.png")

        return False

    except Exception as e:
        log(f"  [ERROR] {e}")
        return False

def main():
    """主函数 - 快速完整流程测试"""
    log("="*60)
    log("快速完整流程测试 - 保持会话")
    log("="*60)

    test_city = "北京"
    test_keyword = "鹭卓 Ready To The Top 巡回演唱会"

    try:
        # 获取driver（第一次慢，后续快）
        driver = get_driver()

        log("\n" + "="*60)
        log(f"测试: 城市={test_city}, 关键词={test_keyword}")
        log("="*60)

        # 重置到首页
        if not reset_to_homepage(driver):
            log("[ERROR] 重置失败")
            return

        # 等待首页
        time.sleep(2)

        # 1. 城市选择
        try:
            els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/home_city")
            if els:
                current = els[0].text or ""
                log(f"  当前城市: {current}")

                if test_city not in current:
                    log(f"  切换到: {test_city}")
                    els[0].click()
                    time.sleep(0.5)

                    # 输入搜索
                    input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                    if input_els:
                        input_els[0].send_keys(test_city)
                        time.sleep(0.8)

                        # 从结果中点击
                        city_results = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                        for result in city_results:
                            try:
                                text = result.text or ""
                                if test_city in text:
                                    result.click()
                                    time.sleep(0.5)
                                    log(f"  [OK] 已切换到{test_city}")
                                    break
                            except:
                                continue
                else:
                    log(f"  [OK] 已是{test_city}")
        except Exception as e:
            log(f"  [SKIP] 城市选择: {e}")

        # 2. 点击搜索框
        try:
            els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/homepage_header_search_layout")
            if els:
                els[0].click()
                time.sleep(1)
                log("  [OK] 进入搜索页")
            else:
                log("  [ERROR] 未找到搜索框")
                return
        except Exception as e:
            log(f"  [ERROR] 搜索框点击失败: {e}")
            return

        # 3. 输入关键词
        try:
            input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if input_els:
                input_els[0].clear()
                time.sleep(0.2)
                input_els[0].send_keys(test_keyword)
                time.sleep(0.5)
                log(f"  [OK] 输入: {test_keyword}")
            else:
                log("  [ERROR] 未找到输入框")
                return
        except Exception as e:
            log(f"  [ERROR] 输入失败: {e}")
            return

        # 4. 搜索
        try:
            driver.press_keycode(66)  # ENTER
            time.sleep(1.5)
            log("  [OK] 按下回车")

            # 关闭键盘
            try:
                driver.hide_keyboard()
                time.sleep(0.5)
                log("  [OK] 已关闭键盘")
            except:
                pass

            # 点击搜索建议（带放大镜的项）来真正执行搜索
            log("  尝试点击搜索建议...")
            try:
                # 查找包含关键词的搜索建议项
                suggest_els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("鹭卓")')
                if suggest_els:
                    suggest_els[0].click()
                    time.sleep(0.5)
                    log("  [OK] 已点击搜索建议")
            except:
                log("  [SKIP] 未找到搜索建议，继续...")

            # 等待演出列表页加载（重要！）
            log("  等待演出列表加载...")
            time.sleep(3)

            # 保存搜索结果截图
            img = driver.get_screenshot_as_png()
            with open("search_results_list.png", "wb") as f:
                f.write(img)
            log("  [OK] 截图: search_results_list.png")
        except Exception as e:
            log(f"  [ERROR] 搜索失败: {e}")
            return

        # 5. 查找并点击演出
        if not find_and_click_show(driver):
            log("[ERROR] 查找演出失败")
            return

        # 6. 验证详情页
        if verify_detail_page(driver):
            log("\n" + "="*60)
            log("[SUCCESS] 完整流程测试通过！")
            log("="*60)
        else:
            log("\n" + "="*60)
            log("[PARTIAL] 部分成功")
            log("="*60)

        # 不quit，保持会话
        log("\n会话保持中，可继续测试...")

    except KeyboardInterrupt:
        log("\n[中断] 用户停止")
    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
