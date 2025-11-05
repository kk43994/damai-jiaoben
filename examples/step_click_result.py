# -*- coding: UTF-8 -*-
"""步骤：点击搜索结果第一个选项"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击搜索结果第一个选项")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击搜索结果第一个选项")
    result_clicked = False

    # 等待搜索结果加载
    time.sleep(2)

    # 方式1: 查找包含关键词的TextView
    try:
        search_text = bot.config.keyword[:5] if len(bot.config.keyword) > 5 else bot.config.keyword
        BotLogger.info(f"查找包含'{search_text}'的搜索结果...")
        results = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{search_text}")'
        )
        BotLogger.info(f"找到{len(results)}个匹配结果")

        if results:
            # 找到在屏幕上部的第一个结果
            for i, result in enumerate(results[:10]):
                try:
                    rect = result.rect
                    text = result.text if hasattr(result, 'text') else ''
                    BotLogger.info(f"结果{i}: y={rect['y']}, text='{text[:30]}...'")
                    if 50 < rect['y'] < 1000:
                        result.click()
                        result_clicked = True
                        BotLogger.success(f"点击了第一个搜索结果，y={rect['y']}")
                        break
                except Exception as e:
                    BotLogger.debug(f"结果{i}点击失败: {e}")
                    continue
    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 点击第一个可点击的列表项
    if not result_clicked:
        try:
            BotLogger.info("方式2: 查找可点击的列表项...")
            clickables = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )
            # 找到在屏幕上部的元素
            for i, el in enumerate(clickables[:15]):
                try:
                    rect = el.rect
                    if 150 < rect['y'] < 600:
                        el.click()
                        result_clicked = True
                        BotLogger.success(f"点击了可点击元素，y={rect['y']}")
                        break
                except:
                    continue
        except Exception as e:
            BotLogger.warning(f"方式2失败: {e}")

    if not result_clicked:
        BotLogger.error("无法点击搜索结果")
        raise Exception("无法点击搜索结果")

    BotLogger.wait("等待进入详情页...")
    time.sleep(3)

    print("\n" + "=" * 60)
    print("搜索结果点击完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
