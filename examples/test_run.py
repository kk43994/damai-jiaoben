# -*- coding: UTF-8 -*-
"""测试运行脚本"""
import sys
sys.path.insert(0, 'damai_appium')

print("=" * 60)
print("开始测试...")
print("=" * 60)

try:
    print("\n[1/3] 导入模块...")
    from damai_appium.damai_app_v2 import BotLogger, DamaiBot
    print("    [OK] 模块导入成功")

    print("\n[2/3] 测试日志系统...")
    BotLogger.info("这是一条INFO日志")
    BotLogger.success("这是一条SUCCESS日志")
    BotLogger.warning("这是一条WARNING日志")
    BotLogger.step(1, "测试步骤日志")
    print("    [OK] 日志系统正常")

    print("\n[3/3] 初始化Bot...")
    bot = DamaiBot()
    print("    [OK] Bot初始化成功!")

    print("\n" + "=" * 60)
    print("所有测试通过! 准备开始抢票流程...")
    print("=" * 60)

    # 运行抢票
    # bot.run_with_retry(max_retries=1)

except Exception as e:
    print(f"\n[ERROR] 测试失败: {e}")
    import traceback
    traceback.print_exc()
