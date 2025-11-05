"""
学习脚本：在首页顶部搜索框搜索关键词
"""
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# 配置
APPIUM_SERVER = "http://127.0.0.1:4723"
PACKAGE_NAME = "cn.damai"
SEARCH_KEYWORD = "鹭卓"  # 自定义搜索关键词

def init_driver():
    """初始化WebDriver"""
    print("\n=== 初始化WebDriver ===")
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.app_package = PACKAGE_NAME
    options.app_activity = "cn.damai.homepage.view.HomepageActivity"
    options.no_reset = True
    options.new_command_timeout = 600

    driver = webdriver.Remote(APPIUM_SERVER, options=options)
    driver.implicitly_wait(10)
    print("[OK] WebDriver初始化成功")
    return driver

def go_to_homepage(driver):
    """确保回到首页"""
    print("\n=== 确保在首页 ===")

    # 重启APP回到首页
    driver.terminate_app(PACKAGE_NAME)
    time.sleep(2)
    driver.activate_app(PACKAGE_NAME)
    time.sleep(3)

    # 关闭可能的弹窗
    try:
        for text in ["跳过", "下次再说", "暂不开启", "取消", "关闭"]:
            try:
                btn = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().text("{text}")'
                )
                btn.click()
                print(f"  关闭弹窗: {text}")
                time.sleep(1)
            except:
                pass
    except:
        pass

    print("[OK] 已回到首页")

def analyze_search_elements(driver):
    """分析首页的搜索元素"""
    print("\n=== 分析首页搜索元素 ===")

    # 查找所有EditText元素
    try:
        edit_texts = driver.find_elements(
            AppiumBy.CLASS_NAME,
            'android.widget.EditText'
        )
        print(f"\n找到 {len(edit_texts)} 个EditText元素:")
        for i, el in enumerate(edit_texts):
            try:
                rect = el.rect
                text = el.text if el.text else "(空)"
                resource_id = el.get_attribute('resource-id') if hasattr(el, 'get_attribute') else "?"
                print(f"  {i+1}. 位置: y={rect['y']}, x={rect['x']}")
                print(f"      文本: {text}")
                print(f"      ID: {resource_id}")
                print()
            except Exception as e:
                print(f"  {i+1}. 获取信息失败: {e}")
    except Exception as e:
        print(f"查找EditText失败: {e}")

    # 查找所有包含"搜索"的元素
    try:
        search_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("搜索")'
        )
        print(f"\n找到 {len(search_elements)} 个包含'搜索'的元素:")
        for i, el in enumerate(search_elements):
            try:
                rect = el.rect
                text = el.text
                class_name = el.get_attribute('className') if hasattr(el, 'get_attribute') else "?"
                print(f"  {i+1}. '{text}'")
                print(f"      位置: y={rect['y']}, x={rect['x']}")
                print(f"      类型: {class_name}")
                print()
            except Exception as e:
                print(f"  {i+1}. 获取信息失败: {e}")
    except Exception as e:
        print(f"查找包含'搜索'的元素失败: {e}")

    # 保存截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/homepage_search_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"\n截图已保存: {screenshot_path}")

def search_on_homepage(driver, keyword):
    """在首页顶部搜索框搜索关键词"""
    print(f"\n=== 在首页顶部搜索: {keyword} ===")

    # 方法1: 尝试使用ID查找顶部搜索框
    search_box = None
    try:
        print("  方法1: 尝试使用ID查找...")
        search_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
        print("  [OK] 找到搜索框 (通过ID)")
    except:
        pass

    # 方法2: 查找y坐标最小的EditText（顶部的）
    if not search_box:
        try:
            print("  方法2: 查找顶部的EditText...")
            edit_texts = driver.find_elements(
                AppiumBy.CLASS_NAME,
                'android.widget.EditText'
            )
            if edit_texts:
                # 按y坐标排序，选择最上面的
                sorted_edit_texts = sorted(edit_texts, key=lambda el: el.rect['y'])
                search_box = sorted_edit_texts[0]
                print(f"  [OK] 找到顶部EditText (y={search_box.rect['y']})")
        except Exception as e:
            print(f"  方法2失败: {e}")

    # 方法3: 查找包含"搜索"文字的元素附近的EditText
    if not search_box:
        try:
            print("  方法3: 查找'搜索'文字附近的EditText...")
            search_labels = driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("搜索")'
            )
            if search_labels:
                # 获取"搜索"文字的y坐标
                search_y = search_labels[0].rect['y']
                print(f"  '搜索'文字位置: y={search_y}")

                # 查找y坐标接近的EditText
                edit_texts = driver.find_elements(
                    AppiumBy.CLASS_NAME,
                    'android.widget.EditText'
                )
                for el in edit_texts:
                    el_y = el.rect['y']
                    if abs(el_y - search_y) < 100:  # y坐标差距小于100
                        search_box = el
                        print(f"  [OK] 找到接近'搜索'文字的EditText (y={el_y})")
                        break
        except Exception as e:
            print(f"  方法3失败: {e}")

    if not search_box:
        print("[FAIL] 未找到顶部搜索框")
        return False

    # 点击搜索框
    print("  点击搜索框...")
    rect = search_box.rect
    print(f"  搜索框位置: y={rect['y']}, x={rect['x']}, width={rect['width']}, height={rect['height']}")
    search_box.click()
    time.sleep(2)  # 等待页面跳转或输入框激活

    # 重新查找输入框（因为页面可能已跳转）
    print("  重新查找输入框...")
    try:
        # 尝试查找当前激活的输入框
        input_box = driver.find_element(
            AppiumBy.CLASS_NAME,
            'android.widget.EditText'
        )
        print("  [OK] 找到输入框")
    except:
        print("  使用原来的搜索框元素")
        input_box = search_box

    # 输入搜索关键词
    print(f"  输入关键词: {keyword}")
    input_box.send_keys(keyword)
    time.sleep(1)

    # 按回车键搜索
    print("  按回车键搜索...")
    driver.press_keycode(66)  # KEYCODE_ENTER
    time.sleep(3)  # 等待搜索结果

    # 保存搜索结果截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/search_result_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"  搜索结果截图: {screenshot_path}")

    print("[OK] 搜索完成")
    return True

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        # 回到首页
        go_to_homepage(driver)

        # 分析搜索元素
        analyze_search_elements(driver)

        # 在首页顶部搜索
        if search_on_homepage(driver, SEARCH_KEYWORD):
            print("\n=== 学习完成 ===")
            print(f"成功在首页顶部搜索: {SEARCH_KEYWORD}")
        else:
            print("\n=== 学习失败 ===")

        print("\n[PAUSE] 程序将在30秒后关闭...")
        time.sleep(30)

    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if driver:
            print("\n=== 关闭WebDriver ===")
            driver.quit()
            print("[OK] WebDriver已关闭")

if __name__ == "__main__":
    main()
