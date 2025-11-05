# -*- coding: UTF-8 -*-
"""步骤：优化的滑块验证处理 - 使用贝塞尔曲线模拟真实轨迹"""
import sys
import time
import random
import math
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

print("=" * 60)
print("步骤：优化的滑块验证处理")
print("=" * 60)

def bezier_track(distance, steps=30):
    """生成贝塞尔曲线轨迹，模拟真实人类滑动"""
    tracks = []

    # 控制点，模拟加速-减速过程
    # 前1/4加速，中间1/2匀速，后1/4减速
    p0 = 0
    p1 = distance * 0.25
    p2 = distance * 0.75
    p3 = distance

    for i in range(steps):
        t = i / (steps - 1)  # 0 到 1

        # 三次贝塞尔曲线公式
        x = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3

        # 添加一些随机抖动，模拟手指的微小晃动
        jitter = random.uniform(-2, 2)

        tracks.append({
            'x': int(x + jitter),
            'y': random.randint(-2, 2),  # Y轴随机抖动
            'delay': random.uniform(0.01, 0.03)  # 随机延迟
        })

    return tracks

try:
    bot = DamaiBot()

    BotLogger.step(1, "优化的滑块验证处理")

    # 等待滑块加载
    time.sleep(2)

    # 获取屏幕尺寸
    screen_size = bot.driver.get_window_size()
    screen_width = screen_size['width']
    screen_height = screen_size['height']

    BotLogger.info(f"屏幕尺寸: {screen_width}x{screen_height}")

    # 方法1: 尝试查找滑块元素
    slider_found = False
    slider_x = None
    slider_y = None

    try:
        BotLogger.info("查找滑块元素...")

        # 尝试多种方式查找滑块
        possible_classes = [
            "android.widget.ImageView",
            "android.widget.Button",
            "android.view.View"
        ]

        for class_name in possible_classes:
            elements = bot.driver.find_elements(By.CLASS_NAME, class_name)
            BotLogger.info(f"找到 {len(elements)} 个 {class_name} 元素")

            for el in elements:
                try:
                    rect = el.rect
                    # 滑块特征：较小、在屏幕中间高度、靠左
                    if (30 < rect['width'] < 100 and
                        30 < rect['height'] < 100 and
                        rect['x'] < 150 and
                        300 < rect['y'] < 800):
                        slider_x = rect['x'] + rect['width'] // 2
                        slider_y = rect['y'] + rect['height'] // 2
                        slider_found = True
                        BotLogger.success(f"找到滑块! 位置: ({slider_x}, {slider_y}), 大小: {rect['width']}x{rect['height']}")
                        break
                except:
                    continue

            if slider_found:
                break

    except Exception as e:
        BotLogger.debug(f"查找滑块元素时出错: {e}")

    # 如果没找到滑块，使用估算位置
    if not slider_found:
        BotLogger.warning("未找到滑块元素，使用估算位置")
        slider_x = 80  # 估算滑块在左侧
        slider_y = screen_height // 2  # 屏幕中间高度

    # 计算拖动距离（拖到屏幕右侧，留一点边距）
    end_x = screen_width - 60
    distance = end_x - slider_x

    BotLogger.info(f"滑块起点: ({slider_x}, {slider_y})")
    BotLogger.info(f"滑块终点: ({end_x}, {slider_y})")
    BotLogger.info(f"拖动距离: {distance}px")

    # 生成贝塞尔曲线轨迹
    BotLogger.info("生成贝塞尔曲线轨迹...")
    tracks = bezier_track(distance, steps=25)

    # 使用W3C Actions API执行拖动
    BotLogger.info("开始拖动滑块...")

    actions = ActionChains(bot.driver)
    touch_input = PointerInput(interaction.POINTER_TOUCH, "touch")
    actions.w3c_actions = ActionBuilder(bot.driver, mouse=touch_input)

    # 移动到滑块位置
    actions.w3c_actions.pointer_action.move_to_location(slider_x, slider_y)
    actions.w3c_actions.pointer_action.pointer_down()
    actions.w3c_actions.pointer_action.pause(random.uniform(0.1, 0.2))  # 按下后短暂停留

    # 按照贝塞尔曲线轨迹移动
    for i, track in enumerate(tracks):
        current_x = slider_x + track['x']
        current_y = slider_y + track['y']

        actions.w3c_actions.pointer_action.move_to_location(current_x, current_y)
        actions.w3c_actions.pointer_action.pause(track['delay'])

        if i % 5 == 0:  # 每5步打印一次进度
            BotLogger.debug(f"移动到: ({current_x}, {current_y}), 进度: {i+1}/{len(tracks)}")

    # 到达终点后，稍微停顿再松开
    actions.w3c_actions.pointer_action.pause(random.uniform(0.05, 0.1))
    actions.w3c_actions.pointer_action.release()

    # 执行动作
    actions.perform()

    BotLogger.success("滑块拖动完成!")

    # 等待验证结果
    BotLogger.wait("等待滑块验证结果...")
    time.sleep(3)

    # 检查是否还在滑块页面
    try:
        # 如果还能找到滑块，说明验证失败
        slider_elements = bot.driver.find_elements(By.CLASS_NAME, "android.widget.ImageView")
        still_on_slider = False
        for el in slider_elements:
            try:
                rect = el.rect
                if (30 < rect['width'] < 100 and rect['x'] < 150 and 300 < rect['y'] < 800):
                    still_on_slider = True
                    break
            except:
                continue

        if still_on_slider:
            BotLogger.warning("似乎还在滑块页面，验证可能失败")
        else:
            BotLogger.success("已离开滑块页面，验证可能成功!")

    except Exception as e:
        BotLogger.debug(f"检查页面状态时出错: {e}")

    print("\n" + "=" * 60)
    print("滑块处理完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
