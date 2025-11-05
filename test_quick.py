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

def main():
    """主函数 - 稳定性测试（5次）"""
    log("="*60)
    log("稳定性测试 - 连续5次测试")
    log("="*60)

    success_count = 0
    total_tests = 5
    test_city = "北京"
    test_keyword = "鹭卓 Ready To The Top 巡回演唱会"

    try:
        # 获取driver（第一次慢，后续快）
        driver = get_driver()

        for i in range(total_tests):
            log(f"\n{'='*60}")
            log(f"[测试 {i+1}/{total_tests}] 城市={test_city}, 关键词={test_keyword}")
            log("="*60)

            # 重置到首页（快！）
            if not reset_to_homepage(driver):
                log(f"  [失败] 第{i+1}次：重置失败")
                continue

            # 执行搜索
            if quick_search(driver, test_city, test_keyword):
                success_count += 1
                log(f"  [成功] 第{i+1}次测试通过")
            else:
                log(f"  [失败] 第{i+1}次测试失败")

            time.sleep(1)

        # 统计结果
        success_rate = (success_count / total_tests) * 100
        log("\n" + "="*60)
        log("测试完成 - 稳定性统计")
        log("="*60)
        log(f"总测试次数: {total_tests}")
        log(f"成功次数: {success_count}")
        log(f"失败次数: {total_tests - success_count}")
        log(f"成功率: {success_rate:.1f}%")

        if success_rate == 100:
            log("\n[优秀] 100% 稳定性！")
        elif success_rate >= 80:
            log("\n[良好] 稳定性较高")
        elif success_rate >= 60:
            log("\n[一般] 稳定性中等，需优化")
        else:
            log("\n[较差] 稳定性较低，需排查")

        log("="*60)

        # 不quit，保持会话
        # driver.quit()  # 注释掉，保持会话

    except KeyboardInterrupt:
        log("\n[中断] 用户停止")
    except Exception as e:
        log(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
