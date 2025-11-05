# -*- coding: UTF-8 -*-
"""识别并点击有票的票档"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：识别并点击有票的票档")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "识别并点击有票的票档")

    # 等待页面加载
    time.sleep(2)

    # 0. 先找到"票档"两个字的位置，用于区分场次方框和票档方框
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
            BotLogger.warning("未找到'票档'文字，尝试查找包含'票档'的元素")
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

    # 1. 查找所有"缺货登记"标记
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

    # 2. 查找所有票档方框（可点击的元素，且在"票档"文字下方）
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
                # 票档方框特征：
                # 1. 较大的可点击区域
                # 2. 必须在"票档"文字的下方（y坐标大于票档文字的y坐标）
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
                        # 如果没找到"票档"文字，使用原逻辑
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

    # 3. 判断哪些票档有票（方框内没有"缺货登记"标记）
    BotLogger.info("\n判断哪些票档有票...")
    available_tickets = []

    for i, box in enumerate(ticket_boxes):
        has_ticket = True
        box_y_start = box['y']
        box_y_end = box['y_end']

        # 检查"缺货登记"标记是否在这个方框内
        for out_of_stock_y in out_of_stock_positions:
            # 如果"缺货登记"的y坐标在方框的范围内，则该票档缺货
            if box_y_start <= out_of_stock_y <= box_y_end:
                has_ticket = False
                BotLogger.warning(f"  票档{i+1} (y={box_y_start}-{box_y_end}) 缺货：内部有'缺货登记'标记(y={out_of_stock_y})")
                break

        if has_ticket:
            available_tickets.append(box)
            BotLogger.success(f"  ✓ 票档{i+1} (y={box_y_start}-{box_y_end}) 有票！")

    # 4. 点击第一个有票的票档
    if available_tickets:
        BotLogger.step(2, f"点击第一个有票的票档（共{len(available_tickets)}个有票票档）")

        selected = available_tickets[0]
        BotLogger.info(f"选择票档: y={selected['y']}-{selected['y_end']}")

        try:
            selected['element'].click()
            BotLogger.success("成功点击有票的票档！")
        except Exception as e:
            BotLogger.warning(f"点击失败: {e}")

        time.sleep(2)

        # 验证是否进入下一步
        BotLogger.info("验证是否进入下一步...")
        try:
            # 可能进入了实名购票人选择、或者确认订单等页面
            # 检查是否有"实名"、"购票人"、"确认"等关键词
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

    else:
        BotLogger.error("没有找到有票的票档！")
        BotLogger.info("所有票档可能都已缺货")

        # 列出所有文本元素帮助分析
        BotLogger.info("\n列出页面文本元素供分析...")
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
    print("票档选择完成！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
