@echo off
REM 大麦抢票 - Appium服务器启动脚本
REM 此脚本设置Android SDK环境变量并启动Appium服务器

echo ============================================================
echo 大麦抢票 - Appium服务器启动脚本
echo ============================================================
echo.

REM 设置Android SDK环境变量
set ANDROID_HOME=C:\Users\zhouk\AppData\Local\Android\Sdk
set ANDROID_SDK_ROOT=C:\Users\zhouk\AppData\Local\Android\Sdk

echo [1/3] 设置环境变量...
echo   ANDROID_HOME=%ANDROID_HOME%
echo   ANDROID_SDK_ROOT=%ANDROID_SDK_ROOT%
echo.

echo [2/3] 检查ADB连接...
adb devices
echo.

echo [3/3] 启动Appium服务器...
echo   地址: 127.0.0.1:4723
echo   CORS: 已启用
echo.
echo Appium服务器正在启动中...
echo 请保持此窗口打开!
echo.

REM 启动Appium(前台运行,显示日志)
appium --address 127.0.0.1 --port 4723 --allow-cors
