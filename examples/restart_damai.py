# -*- coding: UTF-8 -*-
"""重启大麦APP"""
import sys
sys.path.insert(0, 'damai_appium')

from damai_appium.damai_app_v2 import BotLogger, DamaiBot

print("=" * 60)
print("重启大麦APP")
print("=" * 60)

try:
    bot = DamaiBot()

    # 关闭大麦
    BotLogger.info("关闭大麦APP...")
    bot.driver.terminate_app("cn.damai")
    import time
    time.sleep(2)
    BotLogger.success("大麦APP已关闭")

    # 启动大麦
    BotLogger.info("启动大麦APP...")
    bot.driver.activate_app("cn.damai")
    time.sleep(3)
    BotLogger.success("大麦APP已启动")

    print("\n" + "=" * 60)
    print("大麦APP重启完成！")
    print("=" * 60)

    # 保持连接
    input("\n按回车键关闭...")
    bot.driver.quit()

except Exception as e:
    print(f"\n[ERROR] 重启失败: {e}")
    import traceback
    traceback.print_exc()
