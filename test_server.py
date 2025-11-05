#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
长连测试服务器 - 常驻进程，持有Appium会话，提供HTTP接口
启动：python test_server.py
使用：curl http://localhost:8000/search?keyword=鹭卓
"""
import time
import traceback
from typing import Optional
from fastapi import FastAPI, HTTPException
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
import uvicorn

# 配置
APPIUM_URL = "http://127.0.0.1:4723"
UDID = "127.0.0.1:53910"
PKG = "cn.damai"

# 全局driver
driver = None

# FastAPI应用
app = FastAPI(title="大麦测试服务器", version="1.0")

def log(msg):
    """日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def init_driver():
    """初始化driver（仅一次）"""
    global driver
    if driver is not None:
        try:
            driver.current_activity
            log("[复用] Driver已存在")
            return driver
        except:
            log("[重连] Driver已失效，重新创建")
            driver = None

    log("[初始化] 创建Appium会话...")
    opts = UiAutomator2Options()
    opts.set_capability("platformName", "Android")
    opts.set_capability("automationName", "UiAutomator2")
    opts.set_capability("udid", UDID)
    opts.set_capability("appPackage", PKG)
    opts.set_capability("noReset", True)
    opts.set_capability("newCommandTimeout", 600)
    opts.set_capability("adbExecTimeout", 120000)
    opts.set_capability("uiautomator2ServerLaunchTimeout", 60000)
    opts.set_capability("uiautomator2ServerInstallTimeout", 120000)

    driver = webdriver.Remote(APPIUM_URL, options=opts)
    driver.update_settings({"waitForIdleTimeout": 0})
    log("[OK] 会话已创建")
    return driver

@app.on_event("startup")
async def startup():
    """启动时初始化driver"""
    log("="*60)
    log("大麦测试服务器启动")
    log("="*60)
    init_driver()
    log("[OK] 服务器就绪")
    log("API文档: http://localhost:8000/docs")
    log("="*60)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "大麦测试服务器",
        "version": "1.0",
        "docs": "http://localhost:8000/docs",
        "status": "driver已连接" if driver else "driver未初始化"
    }

@app.get("/reset")
async def reset_homepage():
    """重置到首页"""
    try:
        global driver
        if not driver:
            init_driver()

        log("[重置] 返回首页...")
        for _ in range(5):
            driver.press_keycode(4)  # BACK
            time.sleep(0.3)

        driver.activate_app(PKG)
        time.sleep(2)
        log("[OK] 已返回首页")

        return {"status": "success", "message": "已返回首页"}

    except Exception as e:
        log(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/city")
async def select_city(city: str = "北京"):
    """选择城市"""
    try:
        global driver
        if not driver:
            init_driver()

        log(f"[城市] 切换到: {city}")

        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/home_city")
        if els:
            current = els[0].text or ""
            log(f"  当前: {current}")

            if city in current:
                return {"status": "success", "message": f"已是{city}"}

            els[0].click()
            time.sleep(0.5)

            # 输入搜索
            input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            if input_els:
                input_els[0].send_keys(city)
                time.sleep(0.8)

                # 从结果中点击
                city_results = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                for result in city_results:
                    try:
                        text = result.text or ""
                        if city in text:
                            result.click()
                            time.sleep(0.5)
                            log(f"[OK] 已切换到{city}")
                            return {"status": "success", "message": f"已切换到{city}"}
                    except:
                        continue

        return {"status": "failed", "message": "切换失败"}

    except Exception as e:
        log(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search(keyword: str):
    """搜索演出"""
    try:
        global driver
        if not driver:
            init_driver()

        log(f"[搜索] 关键词: {keyword}")

        # 1. 点击搜索框
        els = driver.find_elements(AppiumBy.ID, f"{PKG}:id/homepage_header_search_layout")
        if els:
            els[0].click()
            time.sleep(1)
            log("  [OK] 进入搜索页")
        else:
            return {"status": "failed", "message": "未找到搜索框"}

        # 2. 输入关键词
        input_els = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
        if input_els:
            input_els[0].clear()
            time.sleep(0.2)
            input_els[0].send_keys(keyword)
            time.sleep(0.5)
            log(f"  [OK] 已输入")
        else:
            return {"status": "failed", "message": "未找到输入框"}

        # 3. 搜索
        driver.press_keycode(66)
        time.sleep(1)
        log("  [OK] 搜索完成")

        # 4. 关闭键盘（重要！）
        try:
            driver.hide_keyboard()
            time.sleep(0.5)
            log("  [OK] 已关闭键盘")
        except:
            # 如果键盘已经关闭，按返回键
            try:
                driver.press_keycode(4)
                time.sleep(0.5)
            except:
                pass

        # 5. 等待结果加载
        time.sleep(1.5)

        # 6. 保存截图
        img = driver.get_screenshot_as_png()
        filename = "api_search_results.png"
        with open(filename, "wb") as f:
            f.write(img)

        return {
            "status": "success",
            "message": "搜索完成",
            "screenshot": filename
        }

    except Exception as e:
        log(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/click")
async def click_show(index: int = 0, keyword: Optional[str] = None):
    """点击演出列表中的某一项"""
    try:
        global driver
        if not driver:
            init_driver()

        log(f"[点击] 索引={index}, 关键词={keyword}")
        time.sleep(1)

        # 查找演出项
        item_ids = [
            f"{PKG}:id/item_project_title",
            f"{PKG}:id/project_title",
            f"{PKG}:id/title",
        ]

        found_items = []
        for item_id in item_ids:
            try:
                els = driver.find_elements(AppiumBy.ID, item_id)
                if els:
                    found_items.extend(els)
                    log(f"  找到 {len(els)} 个")
                    break
            except:
                pass

        # 通过文本查找
        if not found_items and keyword:
            log("  通过关键词查找...")
            els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{keyword}")')
            if els:
                found_items.extend(els)

        if found_items:
            if keyword:
                # 查找包含关键词的
                for item in found_items:
                    text = item.text or ""
                    if keyword in text:
                        log(f"  点击: {text[:30]}...")
                        item.click()
                        time.sleep(2)

                        # 保存截图
                        img = driver.get_screenshot_as_png()
                        with open("api_detail_page.png", "wb") as f:
                            f.write(img)

                        return {
                            "status": "success",
                            "message": f"已点击: {text[:30]}",
                            "screenshot": "api_detail_page.png"
                        }
            else:
                # 点击指定索引
                if index < len(found_items):
                    text = found_items[index].text or ""
                    log(f"  点击: {text[:30]}...")
                    found_items[index].click()
                    time.sleep(2)

                    # 保存截图
                    img = driver.get_screenshot_as_png()
                    with open("api_detail_page.png", "wb") as f:
                        f.write(img)

                    return {
                        "status": "success",
                        "message": f"已点击第{index}个: {text[:30]}",
                        "screenshot": "api_detail_page.png"
                    }

        return {"status": "failed", "message": "未找到演出项"}

    except Exception as e:
        log(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/screenshot")
async def take_screenshot(filename: str = "api_screenshot.png"):
    """截图"""
    try:
        global driver
        if not driver:
            init_driver()

        img = driver.get_screenshot_as_png()
        with open(filename, "wb") as f:
            f.write(img)

        log(f"[截图] {filename}")
        return {"status": "success", "filename": filename}

    except Exception as e:
        log(f"[ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取当前状态"""
    try:
        global driver
        if not driver:
            return {"status": "no_driver", "message": "Driver未初始化"}

        activity = driver.current_activity
        return {
            "status": "connected",
            "activity": activity,
            "package": PKG,
            "udid": UDID
        }

    except Exception as e:
        return {"status": "disconnected", "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
