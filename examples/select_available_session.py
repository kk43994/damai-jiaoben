# -*- coding: UTF-8 -*-
"""识别并点击有票的场次"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：识别并点击有票的场次")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "识别有票的场次")

    # 等待页面加载
    time.sleep(2)

    # 1. 获取所有"无票"标记的位置
    BotLogger.info("步骤1: 查找所有'无票'标记...")
    no_ticket_positions = []
    try:
        no_ticket_elements = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("无票")'
        )
        BotLogger.info(f"找到 {len(no_ticket_elements)} 个'无票'标记")

        for i, el in enumerate(no_ticket_elements):
            try:
                rect = el.rect
                no_ticket_positions.append({
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height']
                })
                BotLogger.info(f"  无票{i+1}: y={rect['y']}")
            except:
                pass
    except Exception as e:
        BotLogger.warning(f"查找'无票'标记失败: {e}")

    # 2. 查找所有可点击的元素（可能是场次选项）
    BotLogger.info("\n步骤2: 查找所有可点击的场次...")
    clickable_sessions = []
    try:
        all_clickable = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        BotLogger.info(f"找到 {len(all_clickable)} 个可点击元素")

        for i, el in enumerate(all_clickable):
            try:
                rect = el.rect
                # 场次通常在屏幕中上部，是较大的可点击区域
                if 200 < rect['y'] < 900 and rect['height'] > 30:
                    clickable_sessions.append({
                        'element': el,
                        'rect': rect,
                        'index': i
                    })
                    BotLogger.debug(f"  可点击元素{i}: y={rect['y']}, size={rect['width']}x{rect['height']}")
            except:
                pass

        BotLogger.info(f"找到 {len(clickable_sessions)} 个可能的场次元素")

    except Exception as e:
        BotLogger.warning(f"查找可点击元素失败: {e}")

    # 3. 分析哪些场次有票（附近没有"无票"标记）
    BotLogger.info("\n步骤3: 识别有票的场次...")
    available_sessions = []

    for session in clickable_sessions:
        session_y = session['rect']['y']
        has_ticket = True

        # 检查这个场次附近是否有"无票"标记
        for no_ticket in no_ticket_positions:
            # 如果"无票"标记的y坐标与场次接近（上下150像素内），认为无票
            if abs(session_y - no_ticket['y']) < 150:
                has_ticket = False
                BotLogger.warning(f"  场次 y={session_y} 无票（附近有'无票'标记 y={no_ticket['y']}）")
                break

        if has_ticket:
            available_sessions.append(session)
            BotLogger.success(f"  ✓ 发现有票场次: y={session_y}")

    # 4. 点击第一个有票的场次
    if available_sessions:
        BotLogger.step(2, f"点击有票的场次（共找到{len(available_sessions)}个有票场次）")

        # 选择第一个有票的场次
        selected_session = available_sessions[0]
        session_rect = selected_session['rect']

        BotLogger.info(f"选择场次: y={session_rect['y']}, size={session_rect['width']}x{session_rect['height']}")

        try:
            # 尝试直接点击元素
            selected_session['element'].click()
            BotLogger.success(f"成功点击有票的场次！")
        except:
            # 如果直接点击失败，使用坐标点击
            x = session_rect['x'] + session_rect['width'] // 2
            y = session_rect['y'] + session_rect['height'] // 2
            bot.driver.execute_script('mobile: clickGesture', {'x': x, 'y': y})
            BotLogger.success(f"通过坐标点击了场次 ({x}, {y})")

        time.sleep(2)

        # 验证是否成功进入下一步
        BotLogger.info("验证是否进入下一步...")
        try:
            # 检查是否有票档、价格等元素（说明进入了票档选择页）
            price_elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("￥")'
            )
            if price_elements:
                BotLogger.success(f"成功进入票档选择页！发现{len(price_elements)}个价格元素")
            else:
                BotLogger.warning("可能未进入票档选择页")

        except Exception as e:
            BotLogger.debug(f"验证时出错: {e}")

    else:
        BotLogger.error("没有找到有票的场次！")
        BotLogger.info("可能的原因：")
        BotLogger.info("  1. 所有场次都无票")
        BotLogger.info("  2. 场次元素识别有误")
        BotLogger.info("  3. 页面结构与预期不同")

        # 尝试备用方案：列出所有TextView，帮助分析
        BotLogger.info("\n备用方案：列出所有文本元素供分析...")
        try:
            all_text = bot.driver.find_elements(By.CLASS_NAME, "android.widget.TextView")
            BotLogger.info(f"找到 {len(all_text)} 个文本元素:")
            for i, tv in enumerate(all_text[:15]):
                try:
                    text = tv.text if hasattr(tv, 'text') else ''
                    rect = tv.rect
                    if text:
                        BotLogger.info(f"  文本{i+1}: y={rect['y']}, text='{text}'")
                except:
                    pass
        except Exception as e:
            BotLogger.warning(f"获取文本元素失败: {e}")

    print("\n" + "=" * 60)
    print("场次选择完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
