# -*- coding: UTF-8 -*-
"""步骤：点击关联演出的第一个"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击关联演出的第一个")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击关联演出列表的第一个演出")
    show_clicked = False

    # 等待页面加载
    time.sleep(1.5)

    # 方式1: 查找包含关键词的元素
    try:
        search_text = bot.config.keyword[:5] if len(bot.config.keyword) > 5 else bot.config.keyword
        BotLogger.info(f"查找包含'{search_text}'的演出...")
        results = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{search_text}")'
        )
        BotLogger.info(f"找到{len(results)}个匹配的演出")

        if results:
            # 点击第一个演出
            for i, result in enumerate(results[:5]):
                try:
                    rect = result.rect
                    text = result.text if hasattr(result, 'text') else ''
                    BotLogger.info(f"演出{i}: y={rect['y']}, text='{text[:30]}...'")
                    # 点击第一个找到的演出（通常在上部）
                    if rect['y'] > 100:  # 避免标题栏
                        result.click()
                        show_clicked = True
                        BotLogger.success(f"点击了第一个演出，y={rect['y']}")
                        break
                except Exception as e:
                    BotLogger.debug(f"演出{i}点击失败: {e}")
                    continue
    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 查找可点击的卡片/列表项
    if not show_clicked:
        try:
            BotLogger.info("方式2: 查找可点击的演出卡片...")
            # 查找可点击的元素，通常演出项是可点击的
            clickables = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )
            BotLogger.info(f"找到{len(clickables)}个可点击元素")

            # 点击在屏幕上部的第一个大元素（演出卡片通常较大）
            for i, el in enumerate(clickables[:20]):
                try:
                    rect = el.rect
                    # 演出卡片通常比较大，且在屏幕中上部
                    if 200 < rect['y'] < 800 and rect['height'] > 50:
                        BotLogger.info(f"可点击元素{i}: y={rect['y']}, height={rect['height']}")
                        el.click()
                        show_clicked = True
                        BotLogger.success(f"点击了演出卡片，y={rect['y']}")
                        break
                except Exception as e:
                    BotLogger.debug(f"元素{i}点击失败: {e}")
                    continue
        except Exception as e:
            BotLogger.warning(f"方式2失败: {e}")

    if not show_clicked:
        BotLogger.error("无法点击第一个演出")
        raise Exception("无法点击第一个演出")

    BotLogger.wait("等待进入演出详情页...")
    time.sleep(3)

    print("\n" + "=" * 60)
    print("演出点击完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
