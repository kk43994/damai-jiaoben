# -*- coding: UTF-8 -*-
"""步骤：处理滑块验证"""
import sys
import time
import random
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

print("=" * 60)
print("步骤：处理滑块验证")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "检测并处理滑块验证")

    # 等待滑块加载
    time.sleep(2)

    # 方式1: 查找滑块元素并拖动
    try:
        BotLogger.info("查找滑块元素...")

        # 尝试查找可能的滑块元素
        # 滑块通常是可拖动的ImageView或Button
        possible_selectors = [
            'new UiSelector().className("android.widget.ImageView").clickable(true)',
            'new UiSelector().className("android.widget.Button")',
            'new UiSelector().descriptionContains("滑块")',
            'new UiSelector().descriptionContains("slider")',
        ]

        slider = None
        for selector in possible_selectors:
            try:
                elements = bot.driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, selector)
                if elements:
                    # 查找在屏幕中间偏左的元素（滑块起始位置）
                    for el in elements:
                        rect = el.rect
                        BotLogger.info(f"找到可能的滑块: x={rect['x']}, y={rect['y']}, w={rect['width']}, h={rect['height']}")
                        # 滑块通常在屏幕中间高度，左侧位置
                        if 300 < rect['y'] < 900 and rect['x'] < 200:
                            slider = el
                            BotLogger.success(f"找到滑块元素！位置: ({rect['x']}, {rect['y']})")
                            break
                if slider:
                    break
            except Exception as e:
                BotLogger.debug(f"尝试选择器失败: {e}")
                continue

        if slider:
            # 获取滑块位置和屏幕宽度
            rect = slider.rect
            start_x = rect['x'] + rect['width'] // 2
            start_y = rect['y'] + rect['height'] // 2

            # 获取屏幕宽度，拖动到右侧（留一点边距）
            screen_size = bot.driver.get_window_size()
            end_x = screen_size['width'] - 50
            end_y = start_y

            distance = end_x - start_x

            BotLogger.info(f"准备拖动滑块: 从({start_x}, {start_y}) 到 ({end_x}, {end_y}), 距离={distance}")

            # 使用W3C Actions API进行更真实的拖动
            actions = ActionChains(bot.driver)

            # 方法1: 使用模拟真人的拖动轨迹
            BotLogger.info("使用模拟真人轨迹拖动...")

            # 移动到滑块
            actions.w3c_actions = ActionBuilder(bot.driver, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
            actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pause(0.1)

            # 模拟真人拖动：分段拖动，速度不均匀
            steps = 15  # 分15步拖动
            for i in range(1, steps + 1):
                # 计算当前步骤的位置
                progress = i / steps
                # 添加一些随机抖动，模拟真人
                x_offset = int(distance * progress) + random.randint(-3, 3)
                y_offset = random.randint(-2, 2)

                current_x = start_x + x_offset
                current_y = start_y + y_offset

                actions.w3c_actions.pointer_action.move_to_location(current_x, current_y)
                # 随机停顿时间
                actions.w3c_actions.pause(random.uniform(0.01, 0.03))

            # 松开滑块
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()

            BotLogger.success("滑块拖动完成！")
            time.sleep(2)

        else:
            BotLogger.warning("未找到滑块元素，尝试备用方案...")

            # 方式2: 直接在屏幕上模拟滑动手势
            BotLogger.info("使用屏幕坐标模拟滑动...")
            screen_size = bot.driver.get_window_size()

            # 假设滑块在屏幕中间高度，从左侧滑到右侧
            start_x = 100
            start_y = screen_size['height'] // 2
            end_x = screen_size['width'] - 100
            end_y = start_y

            bot.driver.execute_script('mobile: swipeGesture', {
                'left': start_x,
                'top': start_y,
                'width': end_x - start_x,
                'height': 0,
                'direction': 'right',
                'percent': 1.0,
                'speed': 500  # 中等速度
            })

            BotLogger.success("滑动手势完成！")
            time.sleep(2)

    except Exception as e:
        BotLogger.error("处理滑块时出错", e)
        # 继续尝试

    BotLogger.wait("等待验证结果...")
    time.sleep(2)

    print("\n" + "=" * 60)
    print("滑块验证处理完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
