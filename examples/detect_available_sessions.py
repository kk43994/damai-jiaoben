# -*- coding: UTF-8 -*-
"""识别有票的场次"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy

print("=" * 60)
print("步骤：识别有票的场次")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "分析场次页面，识别有票和无票的场次")

    # 等待页面加载
    time.sleep(2)

    # 1. 查找所有"无票"标记
    BotLogger.info("查找所有'无票'标记...")
    no_ticket_elements = []
    try:
        no_ticket_elements = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().text("无票")'
        )
        BotLogger.info(f"找到 {len(no_ticket_elements)} 个'无票'标记")

        for i, el in enumerate(no_ticket_elements):
            try:
                rect = el.rect
                BotLogger.info(f"  无票标记{i+1}: 位置 y={rect['y']}")
            except:
                pass
    except Exception as e:
        BotLogger.warning(f"查找'无票'标记失败: {e}")

    # 2. 查找所有可能的场次元素（通常包含日期、时间、星期等）
    BotLogger.info("\n查找所有场次元素...")
    all_clickable = []
    try:
        # 查找所有可点击的元素
        all_clickable = bot.driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().clickable(true)'
        )
        BotLogger.info(f"找到 {len(all_clickable)} 个可点击元素")
    except Exception as e:
        BotLogger.warning(f"查找可点击元素失败: {e}")

    # 3. 查找所有包含日期格式的文本（可能是场次）
    BotLogger.info("\n查找包含日期的元素...")
    date_patterns = ["11.16", "11.17", "11月", "周", "星期"]
    session_candidates = []

    for pattern in date_patterns:
        try:
            elements = bot.driver.find_elements(
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{pattern}")'
            )
            for el in elements:
                try:
                    rect = el.rect
                    text = el.text if hasattr(el, 'text') else ''
                    session_candidates.append({
                        'element': el,
                        'rect': rect,
                        'text': text,
                        'y': rect['y']
                    })
                except:
                    pass
        except:
            pass

    BotLogger.info(f"找到 {len(session_candidates)} 个可能的场次元素")
    for i, session in enumerate(session_candidates[:10]):  # 只显示前10个
        BotLogger.info(f"  场次候选{i+1}: y={session['y']}, text='{session['text'][:30]}'")

    # 4. 分析哪些场次有票（没有对应的"无票"标记）
    BotLogger.info("\n分析有票的场次...")
    available_sessions = []

    # 获取所有"无票"标记的y坐标
    no_ticket_y_positions = []
    for el in no_ticket_elements:
        try:
            rect = el.rect
            no_ticket_y_positions.append(rect['y'])
        except:
            pass

    # 检查每个场次是否有票
    for session in session_candidates:
        has_ticket = True
        session_y = session['y']

        # 如果场次附近（上下100像素范围内）有"无票"标记，则认为无票
        for no_ticket_y in no_ticket_y_positions:
            if abs(session_y - no_ticket_y) < 100:
                has_ticket = False
                BotLogger.debug(f"  场次 y={session_y} 无票（附近有'无票'标记 y={no_ticket_y}）")
                break

        if has_ticket:
            available_sessions.append(session)
            BotLogger.success(f"  ✓ 有票场次: y={session_y}, text='{session['text'][:30]}'")

    BotLogger.info(f"\n总结: 找到 {len(available_sessions)} 个有票的场次")

    # 5. 列出所有页面元素，帮助分析
    BotLogger.info("\n===== 页面元素详细信息 =====")
    try:
        all_elements = bot.driver.find_elements(By.XPATH, '//*')
        BotLogger.info(f"页面总共有 {len(all_elements)} 个元素")

        # 查找所有TextView
        textviews = bot.driver.find_elements(By.CLASS_NAME, "android.widget.TextView")
        BotLogger.info(f"\n找到 {len(textviews)} 个TextView:")
        for i, tv in enumerate(textviews[:20]):  # 只显示前20个
            try:
                rect = tv.rect
                text = tv.text if hasattr(tv, 'text') else ''
                if text:  # 只显示有文本的
                    BotLogger.info(f"  TextView{i+1}: y={rect['y']}, text='{text}'")
            except:
                pass

    except Exception as e:
        BotLogger.warning(f"获取页面元素失败: {e}")

    print("\n" + "=" * 60)
    print("场次分析完成！")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
