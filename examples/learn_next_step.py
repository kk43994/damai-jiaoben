"""
学习脚本：运行完整流程到票档选择，然后观察下一步
"""
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

# 配置
APPIUM_SERVER = "http://127.0.0.1:4723"
PACKAGE_NAME = "cn.damai"
SEARCH_KEYWORD = "大麦乐迷省心包"  # 使用唯一标识

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

def restart_app(driver):
    """重启APP"""
    print("\n=== 第1步：重启大麦APP ===")
    driver.terminate_app(PACKAGE_NAME)
    time.sleep(2)
    driver.activate_app(PACKAGE_NAME)
    time.sleep(2)  # 等待APP启动

    # 处理广告页面 - 点击"跳过"按钮
    print("  处理广告页面...")
    time.sleep(1)  # 等待广告页面显示
    try:
        skip_btn = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("跳过")'
        )
        skip_btn.click()
        print("  已点击'跳过'按钮")
        time.sleep(2)  # 等待进入首页
    except:
        print("  未找到'跳过'按钮，可能已进入首页")
        time.sleep(2)

    # 处理可能的其他弹窗
    try:
        for text in ["下次再说", "暂不开启", "取消", "关闭"]:
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

    print("[OK] APP已重启并进入首页")

def search_show(driver, keyword):
    """搜索演出"""
    print(f"\n=== 第2步：搜索演出 '{keyword}' ===")

    # 点击搜索框
    try:
        search_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
    except:
        # 如果找不到，尝试其他方式
        print("  未找到搜索框ID，尝试查找文本...")
        try:
            search_box = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("搜索")'
            )
        except:
            print("  仍未找到搜索框，列出当前页面元素...")
            page_source = driver.page_source
            if "搜索" in page_source:
                print("  页面包含'搜索'文字")
            else:
                print("  页面不包含'搜索'文字")
            raise

    search_box.click()
    time.sleep(2)  # 等待页面跳转到搜索页面

    # 点击后页面会跳转，需要重新查找输入框
    try:
        input_box = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/search_edit_view"
        )
    except:
        # 尝试查找包含"搜索"的输入框
        try:
            input_box = driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().className("android.widget.EditText")'
            )
        except:
            print("  未找到输入框")
            raise

    # 输入搜索关键词（前5个字）
    search_text = keyword[:5]
    input_box.send_keys(search_text)
    print(f"  输入关键词: {search_text}")
    time.sleep(1)

    # 按回车键搜索
    driver.press_keycode(66)  # KEYCODE_ENTER
    time.sleep(2)
    print("[OK] 搜索完成")

def click_search_result(driver):
    """点击搜索结果"""
    print("\n=== 第3步：点击搜索结果 ===")

    # 获取页面源码，查找可点击的元素
    clickable = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().clickable(true)'
    )

    # 筛选搜索框下方的元素（y > 300）
    for el in clickable:
        rect = el.rect
        if rect['y'] > 300 and rect['y'] < 600:
            print(f"  点击搜索结果: y={rect['y']}")
            el.click()
            time.sleep(2)
            print("[OK] 已点击搜索结果")
            return True

    print("[FAIL] 未找到搜索结果")
    return False

def click_correct_show(driver, keyword):
    """点击正确的演出"""
    print(f"\n=== 第4步：点击正确的演出（包含'{keyword}'）===")

    try:
        # 使用唯一标识查找
        show = driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{keyword}")'
        )
        show.click()
        time.sleep(2)
        print(f"[OK] 已点击演出: {keyword}")
        return True
    except:
        print(f"[FAIL] 未找到包含'{keyword}'的演出")
        return False

def click_book_button(driver):
    """点击立即预订"""
    print("\n=== 第5步：点击立即预订 ===")

    try:
        book_btn = driver.find_element(
            AppiumBy.ID,
            "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl"
        )
        book_btn.click()
        time.sleep(3)
        print("[OK] 已点击立即预订，进入选票页面")
        return True
    except:
        print("[FAIL] 未找到立即预订按钮")
        return False

def select_session_and_ticket(driver):
    """选择场次和票档"""
    print("\n=== 第6步：智能选择场次和票档 ===")

    # 第一部分：选择有票的场次
    print("\n--- 6.1 选择有票的场次 ---")

    # 查找所有"无票"标记
    try:
        no_ticket_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("无票")'
        )
        no_ticket_positions = [el.rect['y'] for el in no_ticket_elements]
        print(f"  找到 {len(no_ticket_positions)} 个'无票'标记")
    except:
        no_ticket_positions = []
        print("  未找到'无票'标记")

    # 查找所有可点击的大方框（场次方框）
    clickable = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().clickable(true)'
    )

    session_boxes = []
    for el in clickable:
        rect = el.rect
        # 场次方框特征：在屏幕中上部，较大的方框
        if 200 < rect['y'] < 900 and rect['height'] > 80 and rect['width'] > 400:
            box = {
                'element': el,
                'y': rect['y'],
                'y_end': rect['y'] + rect['height']
            }
            session_boxes.append(box)

    print(f"  找到 {len(session_boxes)} 个场次方框")

    # 判断哪些场次有票
    available_sessions = []
    for i, box in enumerate(session_boxes):
        has_ticket = True
        for no_ticket_y in no_ticket_positions:
            if box['y'] <= no_ticket_y <= box['y_end']:
                has_ticket = False
                break

        if has_ticket:
            available_sessions.append(box)
            print(f"  场次 {i+1}: 有票 (y={box['y']})")
        else:
            print(f"  场次 {i+1}: 无票 (y={box['y']})")

    if not available_sessions:
        print("[FAIL] 所有场次都无票")
        return False

    # 点击第一个有票的场次
    print(f"\n  点击第一个有票的场次...")
    available_sessions[0]['element'].click()
    time.sleep(2)  # 关键：等待票档弹出
    print("[OK] 已点击场次，等待票档弹出")

    # 第二部分：选择有票的票档
    print("\n--- 6.2 选择有票的票档 ---")

    # 查找"票档"文字的位置，用于区分场次方框和票档方框
    try:
        ticket_class_labels = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("票档")'
        )
        if ticket_class_labels:
            ticket_class_label_y = ticket_class_labels[0].rect['y']
            print(f"  '票档'文字位置: y={ticket_class_label_y}")
        else:
            ticket_class_label_y = 600  # 默认值
            print("  未找到'票档'文字，使用默认值")
    except:
        ticket_class_label_y = 600
        print("  未找到'票档'文字，使用默认值")

    # 查找所有"缺货登记"标记
    try:
        out_of_stock_elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("缺货登记")'
        )
        out_of_stock_positions = [el.rect['y'] for el in out_of_stock_elements]
        print(f"  找到 {len(out_of_stock_positions)} 个'缺货登记'标记")
    except:
        out_of_stock_positions = []
        print("  未找到'缺货登记'标记")

    # 重新查找所有可点击元素（因为票档刚弹出）
    clickable = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().clickable(true)'
    )

    # 只选择在"票档"文字下方的方框
    ticket_boxes = []
    for el in clickable:
        rect = el.rect
        # 票档方框特征：在"票档"文字下方，中等大小方框
        if rect['y'] > ticket_class_label_y and 200 < rect['y'] < 1100:
            if rect['height'] > 50 and rect['width'] > 300:
                box = {
                    'element': el,
                    'y': rect['y'],
                    'y_end': rect['y'] + rect['height']
                }
                ticket_boxes.append(box)

    print(f"  找到 {len(ticket_boxes)} 个票档方框")

    # 判断哪些票档有票
    available_tickets = []
    for i, box in enumerate(ticket_boxes):
        has_ticket = True
        for out_of_stock_y in out_of_stock_positions:
            if box['y'] <= out_of_stock_y <= box['y_end']:
                has_ticket = False
                break

        if has_ticket:
            available_tickets.append(box)
            print(f"  票档 {i+1}: 有票 (y={box['y']})")
        else:
            print(f"  票档 {i+1}: 缺货 (y={box['y']})")

    if not available_tickets:
        print("[FAIL] 所有票档都缺货")
        return False

    # 点击第一个有票的票档
    print(f"\n  点击第一个有票的票档...")
    available_tickets[0]['element'].click()
    time.sleep(3)  # 等待进入下一页
    print("[OK] 已点击票档")

    return True

def analyze_current_page(driver):
    """分析当前页面"""
    print("\n=== 分析当前页面 ===")

    # 获取页面源码
    page_source = driver.page_source

    # 查找常见的页面标识
    keywords = [
        "选座", "座位", "确认订单", "购票人", "实名",
        "提交订单", "立即购买", "去支付", "选择观演人",
        "添加购票人", "身份信息", "数量", "张"
    ]

    found_keywords = []
    for keyword in keywords:
        if keyword in page_source:
            found_keywords.append(keyword)

    print(f"  页面包含关键词: {', '.join(found_keywords) if found_keywords else '无匹配关键词'}")

    # 查找所有可点击元素
    clickable = driver.find_elements(
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().clickable(true)'
    )
    print(f"  可点击元素数量: {len(clickable)}")

    # 查找所有文本元素
    text_elements = driver.find_elements(
        AppiumBy.CLASS_NAME,
        'android.widget.TextView'
    )

    print(f"  文本元素数量: {len(text_elements)}")
    print("\n  前20个文本元素内容:")
    for i, el in enumerate(text_elements[:20]):
        try:
            text = el.text
            if text and text.strip():
                rect = el.rect
                print(f"    {i+1}. '{text}' (y={rect['y']}, x={rect['x']})")
        except:
            pass

    # 保存页面截图
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/next_page_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"\n  页面截图已保存: {screenshot_path}")

    return found_keywords

def main():
    """主函数"""
    driver = None
    try:
        # 初始化
        driver = init_driver()

        # 运行完整流程
        restart_app(driver)

        search_show(driver, SEARCH_KEYWORD)

        if not click_search_result(driver):
            print("流程中断：搜索结果点击失败")
            return

        if not click_correct_show(driver, SEARCH_KEYWORD):
            print("流程中断：未找到正确的演出")
            return

        if not click_book_button(driver):
            print("流程中断：未找到立即预订按钮")
            return

        if not select_session_and_ticket(driver):
            print("流程中断：场次和票档选择失败")
            return

        # 分析下一页
        print("\n" + "="*60)
        print("已成功选择场次和票档！现在分析下一页...")
        print("="*60)

        found_keywords = analyze_current_page(driver)

        print("\n" + "="*60)
        print("流程完成！")
        print("="*60)
        print("\n下一步判断:")

        if "选座" in found_keywords or "座位" in found_keywords:
            print("  → 下一步可能是: 选座")
        elif "购票人" in found_keywords or "实名" in found_keywords or "选择观演人" in found_keywords:
            print("  → 下一步可能是: 选择购票人")
        elif "确认订单" in found_keywords or "提交订单" in found_keywords:
            print("  → 下一步可能是: 确认订单")
        elif "去支付" in found_keywords or "立即购买" in found_keywords:
            print("  → 下一步可能是: 支付")
        else:
            print("  → 下一步需要手动分析页面")

        print("\n[PAUSE] 程序将在30秒后自动关闭，请查看截图和日志...")
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
