# -*- coding: UTF-8 -*-
"""点击有票的场次 - 修正版"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：点击有票的场次（修正版）")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "识别并点击有票的场次")

    # 等待页面加载
    time.sleep(2)

    # 1. 获取所有"无票"标记的位置
    BotLogger.info("查找所有'无票'标记...")
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
                no_ticket_positions.append(rect['y'])
                BotLogger.info(f"  无票标记{i+1}: y={rect['y']}")
            except:
                pass
    except Exception as e:
        BotLogger.warning(f"查找'无票'标记失败: {e}")

    # 2. 查找所有场次方框（可点击的大元素）
    BotLogger.info("\n查找所有场次方框...")
    session_boxes = []
    try:
        all_clickable = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        BotLogger.info(f"找到 {len(all_clickable)} 个可点击元素")

        for i, el in enumerate(all_clickable):
            try:
                rect = el.rect
                # 场次方框特征：较大的可点击区域，在屏幕中上部
                if 200 < rect['y'] < 900 and rect['height'] > 80 and rect['width'] > 400:
                    session_boxes.append({
                        'element': el,
                        'y': rect['y'],
                        'height': rect['height'],
                        'y_end': rect['y'] + rect['height'],
                        'index': i
                    })
                    BotLogger.info(f"  方框{len(session_boxes)}: y={rect['y']}-{rect['y']+rect['height']}, height={rect['height']}")
            except:
                pass

        BotLogger.info(f"找到 {len(session_boxes)} 个场次方框")

    except Exception as e:
        BotLogger.warning(f"查找场次方框失败: {e}")

    # 3. 判断哪些方框有票（方框内没有"无票"标记）
    BotLogger.info("\n判断哪些方框有票...")
    available_sessions = []

    for i, box in enumerate(session_boxes):
        has_ticket = True
        box_y_start = box['y']
        box_y_end = box['y_end']

        # 检查"无票"标记是否在这个方框内
        for no_ticket_y in no_ticket_positions:
            # 如果"无票"的y坐标在方框的范围内，则该方框无票
            if box_y_start <= no_ticket_y <= box_y_end:
                has_ticket = False
                BotLogger.warning(f"  方框{i+1} (y={box_y_start}-{box_y_end}) 无票：内部有'无票'标记(y={no_ticket_y})")
                break

        if has_ticket:
            available_sessions.append(box)
            BotLogger.success(f"  ✓ 方框{i+1} (y={box_y_start}-{box_y_end}) 有票！")

    # 4. 点击第一个有票的方框
    if available_sessions:
        BotLogger.step(2, f"点击第一个有票的场次（共{len(available_sessions)}个有票场次）")

        selected = available_sessions[0]
        BotLogger.info(f"选择场次方框: y={selected['y']}-{selected['y_end']}")

        try:
            selected['element'].click()
            BotLogger.success("成功点击有票的场次！")
        except Exception as e:
            BotLogger.warning(f"点击失败: {e}")

        time.sleep(2)

        # 验证是否进入下一步
        BotLogger.info("验证是否进入票档选择页...")
        try:
            # 检查是否有价格元素
            price_elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("￥")'
            )
            if price_elements and len(price_elements) > 0:
                BotLogger.success(f"成功进入票档选择页！发现{len(price_elements)}个价格元素")
            else:
                # 也可能显示为"选择票档"等文字
                ticket_class = bot.driver.find_elements(
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("票档")'
                )
                if ticket_class:
                    BotLogger.success("成功进入票档选择页！")
                else:
                    BotLogger.warning("可能未进入票档选择页，请检查")

        except Exception as e:
            BotLogger.debug(f"验证时出错: {e}")

    else:
        BotLogger.error("没有找到有票的场次！")
        BotLogger.info("所有场次可能都已售罄")

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
