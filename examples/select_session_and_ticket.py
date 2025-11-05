# -*- coding: UTF-8 -*-
"""在同一页面上选择场次和票档"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：在同一页面上选择场次和票档")
print("=" * 60)

try:
    bot = DamaiBot()

    # ========== 第一步：选择有票的场次 ==========
    BotLogger.step(1, "识别并点击有票的场次")

    time.sleep(2)

    # 查找"无票"标记
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

    # 查找所有场次方框
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

    # 判断哪些场次有票
    BotLogger.info("\n判断哪些场次有票...")
    available_sessions = []

    for i, box in enumerate(session_boxes):
        has_ticket = True
        box_y_start = box['y']
        box_y_end = box['y_end']

        # 检查"无票"标记是否在这个方框内
        for no_ticket_y in no_ticket_positions:
            if box_y_start <= no_ticket_y <= box_y_end:
                has_ticket = False
                BotLogger.warning(f"  方框{i+1} (y={box_y_start}-{box_y_end}) 无票：内部有'无票'标记(y={no_ticket_y})")
                break

        if has_ticket:
            available_sessions.append(box)
            BotLogger.success(f"  ✓ 方框{i+1} (y={box_y_start}-{box_y_end}) 有票！")

    # 点击第一个有票的场次
    if not available_sessions:
        BotLogger.error("没有找到有票的场次！")
        raise Exception("没有有票的场次")

    BotLogger.step(2, f"点击第一个有票的场次（共{len(available_sessions)}个有票场次）")

    selected_session = available_sessions[0]
    BotLogger.info(f"选择场次方框: y={selected_session['y']}-{selected_session['y_end']}")

    try:
        selected_session['element'].click()
        BotLogger.success("成功点击有票的场次！")
    except Exception as e:
        BotLogger.warning(f"点击失败: {e}")
        raise

    # 等待票档弹出
    BotLogger.wait("等待票档弹出...")
    time.sleep(2)

    # ========== 第二步：在同一页面上选择有票的票档 ==========
    BotLogger.step(3, "识别并点击有票的票档")

    # 查找"票档"文字位置
    BotLogger.info("查找'票档'文字位置...")
    ticket_class_label_y = 0
    try:
        ticket_class_labels = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("票档")'
        )
        if ticket_class_labels:
            rect = ticket_class_labels[0].rect
            ticket_class_label_y = rect['y']
            BotLogger.info(f"找到'票档'文字: y={ticket_class_label_y}")
        else:
            ticket_class_labels = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("票档")'
            )
            if ticket_class_labels:
                rect = ticket_class_labels[0].rect
                ticket_class_label_y = rect['y']
                BotLogger.info(f"找到包含'票档'的文字: y={ticket_class_label_y}")
    except Exception as e:
        BotLogger.warning(f"查找'票档'文字失败: {e}")

    # 查找所有"缺货登记"标记
    BotLogger.info("\n查找所有'缺货登记'标记...")
    out_of_stock_positions = []
    try:
        out_of_stock_elements = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("缺货登记")'
        )
        BotLogger.info(f"找到 {len(out_of_stock_elements)} 个'缺货登记'标记")

        for i, el in enumerate(out_of_stock_elements):
            try:
                rect = el.rect
                out_of_stock_positions.append(rect['y'])
                BotLogger.info(f"  缺货登记{i+1}: y={rect['y']}")
            except:
                pass
    except Exception as e:
        BotLogger.warning(f"查找'缺货登记'标记失败: {e}")

    # 重新查找所有可点击元素（因为票档刚弹出）
    BotLogger.info("\n查找所有票档方框...")
    ticket_boxes = []
    try:
        all_clickable = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        BotLogger.info(f"找到 {len(all_clickable)} 个可点击元素")

        for i, el in enumerate(all_clickable):
            try:
                rect = el.rect
                # 票档方框特征：较大的可点击区域，且在"票档"文字下方
                if 200 < rect['y'] < 1100 and rect['height'] > 50 and rect['width'] > 300:
                    # 如果找到了"票档"文字，只选择在其下方的方框
                    if ticket_class_label_y > 0:
                        if rect['y'] > ticket_class_label_y:
                            ticket_boxes.append({
                                'element': el,
                                'y': rect['y'],
                                'height': rect['height'],
                                'y_end': rect['y'] + rect['height'],
                                'index': i
                            })
                            BotLogger.info(f"  票档方框{len(ticket_boxes)}: y={rect['y']}-{rect['y']+rect['height']}, height={rect['height']} (在'票档'文字下方)")
                        else:
                            BotLogger.debug(f"  跳过场次方框: y={rect['y']} (在'票档'文字上方)")
                    else:
                        # 如果没找到"票档"文字，只选择y坐标较大的方框（在下方的）
                        if rect['y'] > 700:  # 票档通常在页面下半部分
                            ticket_boxes.append({
                                'element': el,
                                'y': rect['y'],
                                'height': rect['height'],
                                'y_end': rect['y'] + rect['height'],
                                'index': i
                            })
                            BotLogger.info(f"  票档方框{len(ticket_boxes)}: y={rect['y']}-{rect['y']+rect['height']}, height={rect['height']}")
            except:
                pass

        BotLogger.info(f"找到 {len(ticket_boxes)} 个票档方框")

    except Exception as e:
        BotLogger.warning(f"查找票档方框失败: {e}")

    # 判断哪些票档有票
    BotLogger.info("\n判断哪些票档有票...")
    available_tickets = []

    for i, box in enumerate(ticket_boxes):
        has_ticket = True
        box_y_start = box['y']
        box_y_end = box['y_end']

        # 检查"缺货登记"标记是否在这个方框内
        for out_of_stock_y in out_of_stock_positions:
            if box_y_start <= out_of_stock_y <= box_y_end:
                has_ticket = False
                BotLogger.warning(f"  票档{i+1} (y={box_y_start}-{box_y_end}) 缺货：内部有'缺货登记'标记(y={out_of_stock_y})")
                break

        if has_ticket:
            available_tickets.append(box)
            BotLogger.success(f"  ✓ 票档{i+1} (y={box_y_start}-{box_y_end}) 有票！")

    # 点击第一个有票的票档
    if not available_tickets:
        BotLogger.error("没有找到有票的票档！")
        raise Exception("没有有票的票档")

    BotLogger.step(4, f"点击第一个有票的票档（共{len(available_tickets)}个有票票档）")

    selected_ticket = available_tickets[0]
    BotLogger.info(f"选择票档: y={selected_ticket['y']}-{selected_ticket['y_end']}")

    try:
        selected_ticket['element'].click()
        BotLogger.success("成功点击有票的票档！")
    except Exception as e:
        BotLogger.warning(f"点击失败: {e}")
        raise

    time.sleep(2)

    # 验证是否进入下一步
    BotLogger.info("验证是否进入下一步...")
    try:
        keywords = ["实名", "购票人", "确认订单", "提交订单", "立即购买"]
        found_keyword = False

        for keyword in keywords:
            elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{keyword}")'
            )
            if elements:
                BotLogger.success(f"成功进入下一步！发现'{keyword}'")
                found_keyword = True
                break

        if not found_keyword:
            BotLogger.info("已点击票档，等待页面响应...")

    except Exception as e:
        BotLogger.debug(f"验证时出错: {e}")

    print("\n" + "=" * 60)
    print("场次和票档选择完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
