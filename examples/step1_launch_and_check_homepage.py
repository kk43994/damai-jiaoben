"""
第1步：启动大麦APP，处理广告和弹窗，确认在首页
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

def launch_app(driver):
    """启动大麦APP"""
    print("\n=== 步骤1: 启动大麦APP ===")
    driver.activate_app(PACKAGE_NAME)
    print("[OK] APP已启动")
    time.sleep(2)  # 等待启动

def wait_for_ad_finish(driver):
    """等待广告页面加载结束"""
    print("\n=== 步骤2: 等待广告页面加载结束 ===")

    # 等待3秒让广告页面完全显示
    time.sleep(3)

    # 检测是否有"跳过"按钮
    try:
        skip_btn = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("跳过")'
        )
        if skip_btn:
            print("  发现'跳过'按钮，点击跳过...")
            skip_btn.click()
            print("[OK] 已跳过广告")
            time.sleep(2)
            return True
    except:
        print("  未发现'跳过'按钮，可能广告已结束")

    # 如果没有跳过按钮，等待5秒让广告自动结束
    print("  等待广告自动播放结束...")
    time.sleep(5)
    print("[OK] 广告页面已结束")
    return True

def check_homepage(driver):
    """检查是否在首页"""
    print("\n=== 步骤3: 审查是否在首页 ===")

    # 保存当前页面截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/check_homepage_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"  当前页面截图: {screenshot_path}")

    # 查找首页特征元素
    homepage_indicators = [
        "首页",
        "演出",
        "体育",
        "搜索",
        "cn.damai:id/search_edit_view"
    ]

    found_indicators = []

    # 获取页面源码
    page_source = driver.page_source

    # 检查文字特征
    for indicator in homepage_indicators[:4]:
        if indicator in page_source:
            found_indicators.append(indicator)
            print(f"  找到首页特征: '{indicator}'")

    # 检查搜索框ID
    try:
        search_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
        if search_box:
            found_indicators.append("搜索框ID")
            print("  找到首页特征: '搜索框ID'")
    except:
        pass

    if len(found_indicators) >= 2:
        print(f"\n[OK] 确认在首页 (找到 {len(found_indicators)} 个特征)")
        return True
    else:
        print(f"\n[FAIL] 可能不在首页 (只找到 {len(found_indicators)} 个特征)")
        return False

def detect_and_close_popups(driver):
    """检测并关闭弹窗"""
    print("\n=== 步骤4: 检测是否有弹窗 ===")

    # 常见的弹窗关闭按钮文字
    popup_close_texts = [
        "下次再说",
        "暂不开启",
        "取消",
        "关闭",
        "我知道了",
        "稍后",
        "以后再说"
    ]

    closed_popups = []

    for close_text in popup_close_texts:
        try:
            btn = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{close_text}")'
            )
            if btn and btn.is_displayed():
                print(f"  发现弹窗，关闭按钮: '{close_text}'")
                btn.click()
                closed_popups.append(close_text)
                print(f"  [OK] 已关闭弹窗: '{close_text}'")
                time.sleep(1)  # 等待弹窗关闭动画
        except:
            pass

    # 检查是否有关闭按钮图标（通常在右上角）
    try:
        close_buttons = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().descriptionContains("关闭")'
        )
        for btn in close_buttons:
            if btn.is_displayed():
                rect = btn.rect
                # 检查是否在屏幕上方（y < 500）
                if rect['y'] < 500:
                    print(f"  发现关闭图标按钮 (y={rect['y']})")
                    btn.click()
                    closed_popups.append("关闭图标")
                    print("  [OK] 已点击关闭图标")
                    time.sleep(1)
    except:
        pass

    if closed_popups:
        print(f"\n[OK] 共关闭 {len(closed_popups)} 个弹窗")

        # 再次截图，确认弹窗已关闭
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/after_close_popup_{timestamp}.png"
        driver.save_screenshot(screenshot_path)
        print(f"  关闭弹窗后截图: {screenshot_path}")
    else:
        print("\n[OK] 未发现弹窗")

    return len(closed_popups)

def show_homepage_info(driver):
    """显示首页信息"""
    print("\n=== 首页信息 ===")

    # 查找可见的文本元素
    try:
        text_elements = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"文本元素总数: {len(text_elements)}")
        print("\n可见的文本内容（前20个）:")
        count = 0
        for el in text_elements:
            try:
                if el.is_displayed():
                    text = el.text
                    if text and text.strip():
                        rect = el.rect
                        print(f"  {count+1}. '{text}' (y={rect['y']})")
                        count += 1
                        if count >= 20:
                            break
            except:
                pass
    except Exception as e:
        print(f"获取页面信息失败: {e}")

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        # 步骤1: 启动APP
        launch_app(driver)

        # 步骤2: 等待广告结束
        wait_for_ad_finish(driver)

        # 步骤3: 检查是否在首页
        is_homepage = check_homepage(driver)

        if not is_homepage:
            print("\n[WARNING] 可能不在首页，请手动检查")

        # 步骤4: 检测并关闭弹窗
        popup_count = detect_and_close_popups(driver)

        # 显示首页信息
        show_homepage_info(driver)

        print("\n" + "="*60)
        print("第1步完成！")
        print("="*60)
        print("\n总结:")
        print(f"  - 在首页: {'是' if is_homepage else '否'}")
        print(f"  - 关闭弹窗数: {popup_count}")
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
