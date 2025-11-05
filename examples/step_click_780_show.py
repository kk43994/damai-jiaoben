# -*- coding: UTF-8 -*-
"""步骤：点击第二个演出（780起的那场）"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击第二个演出（780起）")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击第二个演出（780起的那场）")
    show_clicked = False

    # 等待页面加载
    time.sleep(1.5)

    # 方式1: 查找包含"780"的元素及其附近的可点击区域
    try:
        BotLogger.info("方式1: 查找包含'780'的演出...")
        price_elements = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("780")'
        )
        BotLogger.info(f"找到{len(price_elements)}个包含'780'的元素")

        if price_elements:
            # 获取价格元素的位置
            price_rect = price_elements[0].rect
            BotLogger.info(f"780元素位置: y={price_rect['y']}")

            # 在价格元素附近查找可点击的元素（演出卡片）
            clickables = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )

            for el in clickables:
                try:
                    rect = el.rect
                    # 找到与价格元素y坐标接近的可点击元素
                    if abs(rect['y'] - price_rect['y']) < 200 and rect['height'] > 50:
                        el.click()
                        show_clicked = True
                        BotLogger.success(f"方式1成功: 点击了780起的演出卡片，y={rect['y']}")
                        break
                except:
                    continue

    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 直接查找所有相关演出，点击第二个
    if not show_clicked:
        try:
            BotLogger.info("方式2: 查找所有相关演出，点击第二个...")
            search_text = bot.config.keyword[:5] if len(bot.config.keyword) > 5 else bot.config.keyword
            results = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{search_text}")'
            )
            BotLogger.info(f"找到{len(results)}个匹配的演出")

            if results and len(results) >= 2:
                # 点击第二个演出
                rect = results[1].rect
                text = results[1].text if hasattr(results[1], 'text') else ''
                BotLogger.info(f"第二个演出: y={rect['y']}, text='{text[:30]}...'")

                # 点击这个元素或其父元素
                try:
                    results[1].click()
                    show_clicked = True
                    BotLogger.success(f"方式2成功: 点击了第二个演出，y={rect['y']}")
                except:
                    # 如果元素不可点击，尝试点击其坐标位置
                    x = rect['x'] + rect['width'] // 2
                    y = rect['y'] + rect['height'] // 2
                    bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                    show_clicked = True
                    BotLogger.success(f"方式2成功: 点击了坐标 ({x}, {y})")

        except Exception as e:
            BotLogger.warning(f"方式2失败: {e}")

    # 方式3: 查找所有大的可点击卡片，点击第二个
    if not show_clicked:
        try:
            BotLogger.info("方式3: 查找所有演出卡片，点击第二个...")
            clickables = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().clickable(true)'
            )

            # 筛选在屏幕中上部的大元素（可能是演出卡片）
            valid_shows = []
            for el in clickables:
                try:
                    rect = el.rect
                    # 演出卡片特征：较大、在屏幕中上部
                    if 200 < rect['y'] < 900 and rect['height'] > 80 and rect['width'] > 200:
                        valid_shows.append(el)
                        BotLogger.debug(f"找到演出卡片: y={rect['y']}, size={rect['width']}x{rect['height']}")
                except:
                    continue

            # 点击第二个
            if len(valid_shows) >= 2:
                valid_shows[1].click()
                show_clicked = True
                BotLogger.success("方式3成功: 点击了第二个演出卡片")
            else:
                BotLogger.warning(f"只找到{len(valid_shows)}个演出卡片")

        except Exception as e:
            BotLogger.warning(f"方式3失败: {e}")

    if not show_clicked:
        BotLogger.error("所有方式都无法点击第二个演出")
        raise Exception("无法点击第二个演出")

    BotLogger.wait("等待进入演出详情页...")
    time.sleep(3)

    print("\n" + "=" * 60)
    print("第二个演出（780起）点击完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
