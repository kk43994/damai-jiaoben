# -*- coding: UTF-8 -*-
"""步骤：点击搜索框并输入关键词"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：在首页搜索框搜索演出")
print("=" * 60)

try:
    bot = DamaiBot()

    # 1. 点击搜索框
    BotLogger.step(1, "点击首页搜索框")
    search_clicked = False

    # 方式1: 通过ID查找
    try:
        search_box = bot.driver.find_element(By.ID, "cn.damai:id/search_edit_view")
        search_box.click()
        search_clicked = True
        BotLogger.success("方式1成功: 通过ID找到搜索框")
    except Exception as e:
        BotLogger.debug(f"方式1失败: {e}")

    # 方式2: 通过文本查找
    if not search_clicked:
        try:
            search_elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("搜索").clickable(true)'
            )
            if search_elements:
                search_elements[0].click()
                search_clicked = True
                BotLogger.success("方式2成功: 通过文本找到搜索框")
        except Exception as e:
            BotLogger.debug(f"方式2失败: {e}")

    # 方式3: 查找EditText
    if not search_clicked:
        try:
            edit_texts = bot.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
            if edit_texts:
                edit_texts[0].click()
                search_clicked = True
                BotLogger.success("方式3成功: 通过EditText找到搜索框")
        except Exception as e:
            BotLogger.debug(f"方式3失败: {e}")

    if not search_clicked:
        BotLogger.error("所有方式都无法点击搜索框")
        raise Exception("无法点击搜索框")

    time.sleep(1)

    # 2. 输入关键词
    BotLogger.step(2, f"输入关键词: {bot.config.keyword}")
    try:
        # 查找输入框
        search_inputs = bot.driver.find_elements(By.CLASS_NAME, "android.widget.EditText")
        if search_inputs:
            # 先清空
            search_inputs[0].clear()
            time.sleep(0.3)
            # 输入关键词
            search_inputs[0].send_keys(bot.config.keyword)
            BotLogger.success("关键词输入成功")
        else:
            BotLogger.error("未找到输入框")
            raise Exception("未找到输入框")
    except Exception as e:
        BotLogger.error("输入失败", e)
        raise

    time.sleep(1)

    # 3. 执行搜索
    BotLogger.step(3, "执行搜索（按回车键）")
    bot.driver.press_keycode(66)  # KEYCODE_ENTER
    BotLogger.success("已按下回车键执行搜索")

    time.sleep(3)

    print("\n" + "=" * 60)
    print("搜索完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
