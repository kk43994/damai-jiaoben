"""
学习脚本：点击第一个搜索结果
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

def analyze_search_results(driver):
    """分析搜索结果页面"""
    print("\n=== 分析搜索结果页面 ===")

    # 保存截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/before_click_result_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"截图: {screenshot_path}")

    # 查找所有文本元素
    try:
        text_views = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"\n页面文本元素: {len(text_views)} 个")
        print("\n前15个文本内容:")
        for i, el in enumerate(text_views[:15]):
            try:
                text = el.text
                if text and text.strip():
                    rect = el.rect
                    print(f"  {i+1}. '{text}' (y={rect['y']}, x={rect['x']})")
            except:
                pass
    except Exception as e:
        print(f"获取文本失败: {e}")

    # 查找所有可点击元素
    try:
        clickable = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        print(f"\n可点击元素: {len(clickable)} 个")
        print("\n前10个可点击元素的位置:")
        for i, el in enumerate(clickable[:10]):
            try:
                rect = el.rect
                print(f"  {i+1}. y={rect['y']}, x={rect['x']}, width={rect['width']}, height={rect['height']}")
            except:
                pass
    except Exception as e:
        print(f"获取可点击元素失败: {e}")

def click_first_result(driver):
    """点击第一个搜索结果"""
    print("\n=== 点击第一个搜索结果 ===")

    # 方法1: 查找包含关键词的文本并点击
    try:
        print("\n方法1: 查找包含关键词的文本...")
        # 查找包含"鹭卓"的元素
        results = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("鹭卓")'
        )
        if results:
            # 按y坐标排序，选择第一个（最上面的）
            first_result = min(results, key=lambda el: el.rect['y'])
            rect = first_result.rect
            print(f"找到第一个结果: '{first_result.text}' (y={rect['y']})")
            first_result.click()
            time.sleep(3)
            print("[OK] 已点击第一个搜索结果")
            return True
    except Exception as e:
        print(f"方法1失败: {e}")

    # 方法2: 查找搜索结果区域的可点击元素
    try:
        print("\n方法2: 查找搜索结果区域的可点击元素...")
        clickable = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        # 筛选在搜索框下方的元素 (y > 150)
        search_results = []
        for el in clickable:
            rect = el.rect
            if rect['y'] > 150 and rect['y'] < 800:
                if rect['height'] > 50 and rect['width'] > 200:
                    search_results.append((el, rect))

        if search_results:
            # 按y坐标排序
            search_results.sort(key=lambda x: x[1]['y'])
            first_result = search_results[0][0]
            rect = search_results[0][1]
            print(f"找到第一个可点击区域: y={rect['y']}, height={rect['height']}")
            first_result.click()
            time.sleep(3)
            print("[OK] 已点击第一个搜索结果")
            return True
    except Exception as e:
        print(f"方法2失败: {e}")

    print("[FAIL] 未能点击第一个搜索结果")
    return False

def analyze_next_page(driver):
    """分析点击后的页面"""
    print("\n=== 分析点击后的页面 ===")

    # 保存截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/after_click_result_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"截图: {screenshot_path}")

    # 查找页面关键词
    try:
        page_source = driver.page_source
        keywords = ["立即预订", "想看", "购票", "票档", "场次", "演出详情", "门票"]
        found = [kw for kw in keywords if kw in page_source]
        print(f"\n页面包含关键词: {', '.join(found) if found else '无'}")
    except Exception as e:
        print(f"分析页面失败: {e}")

    # 查找文本元素
    try:
        text_views = driver.find_elements(AppiumBy.CLASS_NAME, 'android.widget.TextView')
        print(f"\n页面文本元素: {len(text_views)} 个")
        print("\n前10个文本内容:")
        count = 0
        for el in text_views:
            try:
                text = el.text
                if text and text.strip() and len(text.strip()) > 1:
                    rect = el.rect
                    print(f"  {count+1}. '{text}' (y={rect['y']})")
                    count += 1
                    if count >= 10:
                        break
            except:
                pass
    except Exception as e:
        print(f"获取文本失败: {e}")

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        print("\n" + "="*60)
        print("当前任务：点击第一个搜索结果")
        print("="*60)

        # 分析当前页面
        analyze_search_results(driver)

        # 点击第一个结果
        if click_first_result(driver):
            # 分析下一页
            analyze_next_page(driver)
            print("\n" + "="*60)
            print("任务完成！")
            print("="*60)
        else:
            print("\n任务失败")

        print("\n[PAUSE] 程序将在60秒后关闭...")
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
