# -*- coding: UTF-8 -*-
"""步骤：点击立即预订按钮"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击右下角立即预订按钮")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "点击右下角的橙色'立即预订'按钮")
    book_clicked = False

    # 等待页面加载
    time.sleep(1.5)

    # 方式1: 查找包含"立即预订"的按钮
    try:
        BotLogger.info("方式1: 查找'立即预订'按钮...")
        buttons = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textMatches(".*立即预订.*|.*立即.*|.*预订.*")'
        )
        BotLogger.info(f"找到{len(buttons)}个匹配按钮")

        if buttons:
            # 优先找右下角的按钮（y值较大）
            for i, btn in enumerate(buttons):
                try:
                    rect = btn.rect
                    text = btn.text if btn.text else "[无文本]"
                    BotLogger.info(f"按钮{i}: '{text}', x={rect['x']}, y={rect['y']}")

                    # 右下角按钮：y值大（底部），x值可能在右侧或中间
                    if rect['y'] > 800:  # 底部区域
                        btn.click()
                        book_clicked = True
                        BotLogger.success(f"方式1成功: 点击了底部'{text}'按钮，y={rect['y']}")
                        break
                except Exception as e:
                    BotLogger.debug(f"按钮{i}点击失败: {e}")
                    continue

            # 如果没有找到底部按钮，点击第一个
            if not book_clicked and buttons:
                buttons[0].click()
                book_clicked = True
                text = buttons[0].text if buttons[0].text else "[无文本]"
                BotLogger.success(f"方式1成功: 点击了'{text}'按钮")
    except Exception as e:
        BotLogger.warning(f"方式1失败: {e}")

    # 方式2: 通过ID查找（大麦常用的购票按钮ID）
    if not book_clicked:
        try:
            BotLogger.info("方式2: 通过ID查找购票按钮...")
            btn = bot.driver.find_element(By.ID, "cn.damai:id/trade_project_detail_purchase_status_bar_container_fl")
            btn.click()
            book_clicked = True
            BotLogger.success("方式2成功: 通过ID点击了预订按钮")
        except Exception as e:
            BotLogger.debug(f"方式2失败: {e}")

    # 方式3: 点击屏幕右下角位置
    if not book_clicked:
        try:
            BotLogger.info("方式3: 点击屏幕右下角位置...")
            screen_size = bot.driver.get_window_size()
            x = screen_size['width'] - 100  # 右侧
            y = screen_size['height'] - 100  # 底部
            bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
            book_clicked = True
            BotLogger.success(f"方式3成功: 点击了右下角位置 ({x}, {y})")
        except Exception as e:
            BotLogger.warning(f"方式3失败: {e}")

    if not book_clicked:
        BotLogger.error("无法点击立即预订按钮")
        raise Exception("无法点击立即预订按钮")

    BotLogger.wait("等待进入场次选择页...")
    time.sleep(2)

    print("\n" + "=" * 60)
    print("立即预订按钮点击完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
