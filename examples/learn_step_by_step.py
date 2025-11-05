"""
分步学习脚本：学习首页搜索关键词的完整流程
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

def show_page_info(driver, step_name):
    """显示当前页面信息"""
    print(f"\n=== 页面分析: {step_name} ===")

    # 保存截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/step_{step_name}_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"截图: {screenshot_path}")

    # 查找EditText
    try:
        edit_texts = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText')
        print(f"EditText数量: {len(edit_texts)}")
        for i, el in enumerate(edit_texts):
            rect = el.rect
            text = el.text if el.text else "(空)"
            print(f"  {i+1}. EditText y={rect['y']}, text='{text}'")
    except:
        print("EditText: 无")

    # 查找Button
    try:
        buttons = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.Button')
        print(f"Button数量: {len(buttons)}")
        for i, el in enumerate(buttons[:5]):  # 只显示前5个
            rect = el.rect
            text = el.text if el.text else "(空)"
            print(f"  {i+1}. Button y={rect['y']}, text='{text}'")
    except:
        print("Button: 无")

def step1_click_search_button(driver):
    """第1步：点击首页顶部的搜索按钮"""
    print("\n=== 第1步：点击首页顶部搜索按钮 ===")

    # 显示当前页面信息
    show_page_info(driver, "homepage")

    # 查找"搜索"按钮或文本
    search_btn = None

    # 方法1: 查找包含"搜索"的元素
    try:
        print("\n查找'搜索'元素...")
        search_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("搜索")'
        )
        if search_elements:
            # 选择y坐标最小的（最顶部的）
            search_btn = min(search_elements, key=lambda el: el.rect['y'])
            rect = search_btn.rect
            print(f"找到顶部'搜索'按钮: y={rect['y']}, x={rect['x']}")
    except Exception as e:
        print(f"查找失败: {e}")

    # 方法2: 如果没找到，尝试查找ID
    if not search_btn:
        try:
            print("\n尝试通过ID查找...")
            search_btn = driver.find_element(
                AppiumBy.ID,
                "cn.damai:id/search_edit_view"
            )
            print("找到搜索框 (通过ID)")
        except:
            pass

    if not search_btn:
        print("[FAIL] 未找到搜索按钮")
        return False

    # 点击搜索按钮
    print("\n点击搜索按钮...")
    search_btn.click()
    time.sleep(2)  # 等待跳转到搜索页面
    print("[OK] 已点击搜索按钮，等待搜索页面加载")

    return True

def step2_input_keyword(driver, keyword):
    """第2步：在搜索页面输入关键词"""
    print(f"\n=== 第2步：输入搜索关键词 '{keyword}' ===")

    # 显示当前页面信息
    show_page_info(driver, "search_page")

    # 查找输入框
    input_box = None

    # 方法1: 查找EditText
    try:
        print("\n查找EditText输入框...")
        edit_texts = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.EditText')
        if edit_texts:
            # 选择第一个EditText
            input_box = edit_texts[0]
            rect = input_box.rect
            print(f"找到输入框: y={rect['y']}, x={rect['x']}")
    except Exception as e:
        print(f"查找EditText失败: {e}")

    # 方法2: 通过ID查找
    if not input_box:
        try:
            print("\n尝试通过ID查找...")
            input_box = driver.find_element(
                AppiumBy.ID,
                "cn.damai:id/search_edit_view"
            )
            print("找到输入框 (通过ID)")
        except:
            pass

    if not input_box:
        print("[FAIL] 未找到输入框")
        return False

    # 清空输入框
    try:
        input_box.clear()
        time.sleep(0.5)
    except:
        pass

    # 输入关键词
    print(f"\n输入关键词: {keyword}")
    input_box.send_keys(keyword)
    time.sleep(1)
    print("[OK] 已输入关键词")

    return True

def step3_press_search(driver):
    """第3步：按回车键或点击搜索按钮"""
    print("\n=== 第3步：执行搜索 ===")

    # 方法1: 按回车键
    try:
        print("按回车键搜索...")
        driver.press_keycode(66)  # KEYCODE_ENTER
        time.sleep(3)  # 等待搜索结果
        print("[OK] 已执行搜索")
        return True
    except Exception as e:
        print(f"按回车失败: {e}")

    # 方法2: 查找并点击搜索按钮
    try:
        print("\n查找搜索按钮...")
        search_btn = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("搜索")'
        )
        search_btn.click()
        time.sleep(3)
        print("[OK] 已点击搜索按钮")
        return True
    except:
        pass

    print("[FAIL] 执行搜索失败")
    return False

def step4_analyze_result(driver):
    """第4步：分析搜索结果"""
    print("\n=== 第4步：分析搜索结果 ===")

    # 显示页面信息
    show_page_info(driver, "search_result")

    # 查找页面文本
    try:
        text_views = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"\n页面文本元素: {len(text_views)} 个")
        print("\n前20个文本内容:")
        count = 0
        for el in text_views:
            try:
                text = el.text
                if text and text.strip() and len(text.strip()) > 1:
                    rect = el.rect
                    print(f"  {count+1}. '{text}' (y={rect['y']})")
                    count += 1
                    if count >= 20:
                        break
            except:
                pass
    except Exception as e:
        print(f"获取文本失败: {e}")

    print("\n[OK] 搜索结果分析完成")
    return True

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        print("\n" + "="*60)
        print("开始学习：首页搜索关键词完整流程")
        print("="*60)

        # 第1步：点击搜索按钮
        if not step1_click_search_button(driver):
            print("\n流程终止：第1步失败")
            return

        # 第2步：输入关键词
        if not step2_input_keyword(driver, SEARCH_KEYWORD):
            print("\n流程终止：第2步失败")
            return

        # 第3步：执行搜索
        if not step3_press_search(driver):
            print("\n流程终止：第3步失败")
            return

        # 第4步：分析结果
        step4_analyze_result(driver)

        print("\n" + "="*60)
        print("学习完成！")
        print("="*60)
        print(f"\n学到的知识:")
        print(f"1. 首页顶部有'搜索'按钮，点击后跳转到搜索页面")
        print(f"2. 搜索页面有EditText输入框，可以输入关键词")
        print(f"3. 按回车键(keycode 66)可以执行搜索")
        print(f"4. 搜索关键词是自定义的，可以在GUI中配置")

        print("\n[PAUSE] 程序将在60秒后关闭，请查看截图...")
        time.sleep(60)

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
