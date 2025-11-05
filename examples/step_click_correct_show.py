# -*- coding: UTF-8 -*-
"""步骤：点击正确的演出 - 北京大麦乐迷省心包鹭卓演唱会北京站"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击北京大麦乐迷省心包鹭卓演唱会北京站")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击'北京大麦乐迷省心包'演出")
    show_clicked = False

    # 等待页面加载
    time.sleep(1.5)

    # 方式1: 查找包含"大麦乐迷省心包"的元素
    try:
        BotLogger.info("方式1: 查找包含'大麦乐迷省心包'的演出...")
        results = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("大麦乐迷省心包")'
        )
        BotLogger.info(f"找到{len(results)}个包含'大麦乐迷省心包'的元素")

        if results:
            rect = results[0].rect
            text = results[0].text if hasattr(results[0], 'text') else ''
            BotLogger.info(f"演出: y={rect['y']}, text='{text[:50]}...'")

            # 尝试直接点击
            try:
                results[0].click()
                show_clicked = True
                BotLogger.success(f"方式1成功: 点击了演出")
            except:
                # 如果元素不可点击，点击其坐标
                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                show_clicked = True
                BotLogger.success(f"方式1成功: 点击了坐标 ({x}, {y})")

    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 查找包含"省心包"的元素
    if not show_clicked:
        try:
            BotLogger.info("方式2: 查找包含'省心包'的演出...")
            results = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("省心包")'
            )
            BotLogger.info(f"找到{len(results)}个包含'省心包'的元素")

            if results:
                rect = results[0].rect
                text = results[0].text if hasattr(results[0], 'text') else ''
                BotLogger.info(f"演出: y={rect['y']}, text='{text[:50]}...'")

                x = rect['x'] + rect['width'] // 2
                y = rect['y'] + rect['height'] // 2
                bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                show_clicked = True
                BotLogger.success(f"方式2成功: 点击了坐标 ({x}, {y})")

        except Exception as e:
            BotLogger.warning(f"方式2失败: {e}")

    # 方式3: 查找"鹭卓"相关结果，排除第一个，点击第二个
    if not show_clicked:
        try:
            BotLogger.info("方式3: 查找'鹭卓'演出，点击第二个...")
            results = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("鹭卓")'
            )
            BotLogger.info(f"找到{len(results)}个包含'鹭卓'的元素")

            if results and len(results) >= 2:
                rect = results[1].rect
                text = results[1].text if hasattr(results[1], 'text') else ''
                BotLogger.info(f"第二个演出: y={rect['y']}, text='{text[:50]}...'")

                # 点击第二个
                try:
                    results[1].click()
                    show_clicked = True
                    BotLogger.success(f"方式3成功: 点击了第二个鹭卓演出")
                except:
                    x = rect['x'] + rect['width'] // 2
                    y = rect['y'] + rect['height'] // 2
                    bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
                    show_clicked = True
                    BotLogger.success(f"方式3成功: 点击了坐标 ({x}, {y})")

        except Exception as e:
            BotLogger.warning(f"方式3失败: {e}")

    if not show_clicked:
        BotLogger.error("所有方式都无法点击演出")
        raise Exception("无法点击演出")

    BotLogger.wait("等待进入演出详情页...")
    time.sleep(3)

    # 验证是否进入正确的演出详情页
    try:
        BotLogger.info("验证是否进入正确的演出详情页...")
        # 检查是否有"省心包"或"鹭卓"关键词
        page_elements = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("省心包")'
        )
        if not page_elements:
            page_elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("鹭卓")'
            )

        if page_elements:
            BotLogger.success("已进入正确的演出详情页!")
        else:
            BotLogger.warning("可能未进入正确的演出详情页，请检查")

    except Exception as e:
        BotLogger.debug(f"验证页面时出错: {e}")

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
