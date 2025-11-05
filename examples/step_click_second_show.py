# -*- coding: UTF-8 -*-
"""步骤：点击第二个演出"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击第二个演出")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击演出列表中的第二个演出")
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

        if results and len(results) >= 2:
            # 点击第二个演出
            try:
                rect = results[1].rect
                text = results[1].text if hasattr(results[1], 'text') else ''
                BotLogger.info(f"第二个演出: y={rect['y']}, text='{text[:30]}...'")

                results[1].click()
                show_clicked = True
                BotLogger.success(f"点击了第二个演出，y={rect['y']}")
            except Exception as e:
                BotLogger.debug(f"点击第二个演出失败: {e}")

    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 查找可点击的卡片，点击第二个
    if not show_clicked:
        try:
            BotLogger.info("方式2: 查找可点击的演出卡片...")
            clickables = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )
            BotLogger.info(f"找到{len(clickables)}个可点击元素")

            # 筛选在屏幕中上部的大元素
            valid_shows = []
            for el in clickables:
                try:
                    rect = el.rect
                    # 演出卡片通常比较大，且在屏幕中上部
                    if 200 < rect['y'] < 800 and rect['height'] > 50:
                        valid_shows.append(el)
                        BotLogger.debug(f"找到演出卡片: y={rect['y']}, height={rect['height']}")
                except:
                    continue

            # 点击第二个
            if len(valid_shows) >= 2:
                valid_shows[1].click()
                show_clicked = True
                BotLogger.success("点击了第二个演出卡片")
            else:
                BotLogger.warning(f"只找到{len(valid_shows)}个演出卡片，需要至少2个")

        except Exception as e:
            BotLogger.warning(f"方式2失败: {e}")

    if not show_clicked:
        BotLogger.error("无法点击第二个演出")
        raise Exception("无法点击第二个演出")

    BotLogger.wait("等待进入演出详情页...")
    time.sleep(3)

    print("\n" + "=" * 60)
    print("第二个演出点击完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
