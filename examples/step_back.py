# -*- coding: UTF-8 -*-
"""步骤：按返回键退回上一页"""
import sys
import time
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot

print("=" * 60)
print("步骤：按返回键退回上一页")
print("=" * 60)

try:
    bot = DamaiBot()

    BotLogger.step(1, "按返回键退回上一个页面")

    # 按返回键
    bot.driver.press_keycode(4)  # KEYCODE_BACK
    BotLogger.success("已按返回键")

    time.sleep(1.5)

    print("\n" + "=" * 60)
    print("已退回上一页！等待下一步指令...")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 操作失败: {e}")
    import traceback
    traceback.print_exc()
