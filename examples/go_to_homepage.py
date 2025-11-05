"""
返回首页脚本
"""
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options

# 配置
APPIUM_SERVER = "http://127.0.0.1:4723"
PACKAGE_NAME = "cn.damai"

def main():
    """主函数"""
    print("\n=== 返回首页 ===")

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = PACKAGE_NAME
    options.app_activity = "cn.damai.homepage.view.HomepageActivity"
    options.no_reset = True

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    driver.implicitly_wait(5)

    try:
        # 多次按返回键，确保回到首页
        print("按返回键...")
        for i in range(5):
            driver.press_keycode(4)  # KEYCODE_BACK
            time.sleep(0.5)

        print("\n[OK] 已返回首页")
        print("截图当前页面...")

        # 保存截图
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/homepage_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"截图已保存: {screenshot_path}")

        print("\n等待5秒后关闭...")
        time.sleep(5)

    except Exception as e:
        print(f"[ERROR] 错误: {e}")

    finally:
        driver.quit()
        print("[OK] 完成")

if __name__ == "__main__":
    main()
