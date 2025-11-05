"""
分步学习脚本 - 一次只做一个操作，方便调试
"""
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# 配置
APPIUM_SERVER = "http://127.0.0.1:4723"
PACKAGE_NAME = "cn.damai"

def init_driver():
    """初始化WebDriver"""
    print("\n[初始化] 连接到APP...")
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

def show_current_page_info(driver):
    """显示当前页面信息"""
    print("\n=== 当前页面信息 ===")

    # 查找所有文本元素
    try:
        text_elements = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"文本元素数量: {len(text_elements)}")
        print("\n前15个可见文本:")
        count = 0
        for el in text_elements:
            try:
                text = el.text
                if text and text.strip() and el.is_displayed():
                    rect = el.rect
                    print(f"  {count+1}. '{text}' (y={rect['y']}, x={rect['x']})")
                    count += 1
                    if count >= 15:
                        break
            except:
                pass
    except Exception as e:
        print(f"获取文本元素失败: {e}")

    # 保存截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/current_page_{timestamp}.png"
    try:
        driver.save_screenshot(screenshot_path)
        print(f"\n截图已保存: {screenshot_path}")
    except Exception as e:
        print(f"截图失败: {e}")

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        # 等待一下，让页面稳定
        time.sleep(2)

        # 显示当前页面信息
        show_current_page_info(driver)

        print("\n=== 等待用户指导下一步操作 ===")
        print("程序将在60秒后自动关闭...")
        time.sleep(60)

    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\n[关闭] 断开连接...")
            driver.quit()
            print("[OK] 已断开")

if __name__ == "__main__":
    main()
