"""
第2步：在搜索框搜索"鹭卓"
"""
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# 配置
APPIUM_SERVER = "http://127.0.0.1:4723"
PACKAGE_NAME = "cn.damai"
SEARCH_KEYWORD = "鹭卓"

def init_driver():
    """初始化WebDriver"""
    print("\n=== 初始化连接 ===")
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = PACKAGE_NAME
    options.app_activity = "cn.damai.homepage.view.HomepageActivity"
    options.no_reset = True
    options.new_command_timeout = 600

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    driver.implicitly_wait(5)
    print("[OK] 连接成功")
    return driver

def click_search_box(driver):
    """点击搜索框"""
    print("\n=== 步骤2.1: 点击搜索框 ===")

    # 保存点击前的截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/before_click_search_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"  点击前截图: {screenshot_path}")

    # 方法1: 通过ID查找搜索框
    try:
        search_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
        print("  找到搜索框 (通过ID)")
        rect = search_box.rect
        print(f"  搜索框位置: x={rect['x']}, y={rect['y']}, width={rect['width']}, height={rect['height']}")

        search_box.click()
        print("[OK] 已点击搜索框")
        time.sleep(2)  # 等待搜索页面打开
        return True

    except Exception as e:
        print(f"  方法1失败: {e}")

    # 方法2: 通过文本"搜索"查找
    try:
        search_box = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("搜索")'
        )
        print("  找到搜索框 (通过文本)")
        search_box.click()
        print("[OK] 已点击搜索框")
        time.sleep(2)
        return True

    except Exception as e:
        print(f"  方法2失败: {e}")

    print("[FAIL] 未找到搜索框")
    return False

def input_search_keyword(driver, keyword):
    """输入搜索关键词"""
    print(f"\n=== 步骤2.2: 输入搜索关键词 '{keyword}' ===")

    # 保存输入前的截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/search_page_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"  搜索页面截图: {screenshot_path}")

    # 查找输入框
    try:
        # 方法1: 通过ID查找输入框
        input_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
        print("  找到输入框 (通过ID)")

    except:
        # 方法2: 查找当前焦点元素
        try:
            input_box = driver.find_element(
                AppiumBy.CLASS_NAME,
                "android.widget.EditText"
            )
            print("  找到输入框 (通过类名)")
        except Exception as e:
            print(f"[FAIL] 未找到输入框: {e}")
            return False

    # 清空输入框
    try:
        input_box.clear()
        print("  已清空输入框")
    except:
        pass

    # 输入关键词
    try:
        input_box.send_keys(keyword)
        print(f"[OK] 已输入关键词: '{keyword}'")
        time.sleep(1)

        # 保存输入后的截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/after_input_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"  输入后截图: {screenshot_path}")

        return True

    except Exception as e:
        print(f"[FAIL] 输入失败: {e}")
        return False

def execute_search(driver):
    """执行搜索（按回车或点击搜索按钮）"""
    print("\n=== 步骤2.3: 执行搜索 ===")

    # 方法1: 按回车键
    try:
        print("  尝试按回车键...")
        driver.press_keycode(66)  # KEYCODE_ENTER
        print("[OK] 已按回车键")
        time.sleep(3)  # 等待搜索结果加载
        return True

    except Exception as e:
        print(f"  按回车键失败: {e}")

    # 方法2: 点击搜索按钮
    try:
        print("  尝试点击搜索按钮...")
        search_button = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("搜索")'
        )
        search_button.click()
        print("[OK] 已点击搜索按钮")
        time.sleep(3)
        return True

    except Exception as e:
        print(f"  点击搜索按钮失败: {e}")

    print("[WARNING] 搜索可能未成功执行")
    return False

def show_search_results(driver):
    """显示搜索结果页面信息"""
    print("\n=== 搜索结果页面信息 ===")

    # 保存搜索结果截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/search_results_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"  搜索结果截图: {screenshot_path}")

    # 查找文本元素
    try:
        text_elements = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"\n文本元素总数: {len(text_elements)}")
        print("\n可见的搜索结果（前20个）:")
        count = 0
        for el in text_elements:
            try:
                if el.is_displayed():
                    text = el.text
                    if text and text.strip() and len(text) > 2:
                        rect = el.rect
                        print(f"  {count+1}. '{text}' (y={rect['y']})")
                        count += 1
                        if count >= 20:
                            break
            except:
                pass
    except Exception as e:
        print(f"获取搜索结果失败: {e}")

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        # 等待页面稳定
        time.sleep(1)

        # 步骤2.1: 点击搜索框
        if not click_search_box(driver):
            print("\n[ERROR] 点击搜索框失败，流程中断")
            return

        # 步骤2.2: 输入搜索关键词
        if not input_search_keyword(driver, SEARCH_KEYWORD):
            print("\n[ERROR] 输入关键词失败，流程中断")
            return

        # 步骤2.3: 执行搜索
        execute_search(driver)

        # 显示搜索结果
        show_search_results(driver)

        print("\n" + "="*60)
        print("第2步完成！")
        print("="*60)
        print(f"\n已搜索关键词: '{SEARCH_KEYWORD}'")
        print("\n等待用户指导下一步操作...")
        print("程序将在30秒后关闭")
        time.sleep(30)

    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\n=== 关闭连接 ===")
            driver.quit()
            print("[OK] 已断开连接")

if __name__ == "__main__":
    main()
