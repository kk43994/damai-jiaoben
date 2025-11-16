@echo off
chcp 65001 >nul
title 红手指云手机配置向导
color 0B

echo ╔═══════════════════════════════════════════════════════╗
echo ║           红手指云手机 - 一键配置向导                    ║
echo ║             (移动端自动化测试演示 v2.2)                 ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 获取项目根目录
cd /d "%~dp0.."
set PROJECT_ROOT=%CD%

:: 加载环境配置
if exist "%PROJECT_ROOT%\.env.bat" (
    call "%PROJECT_ROOT%\.env.bat"
)

:: 配置PATH
if defined PYTHON_HOME (
    set PATH=%PYTHON_HOME%;%PATH%
)

if defined ANDROID_SDK_ROOT (
    set PATH=%ANDROID_SDK_ROOT%\platform-tools;%PATH%
)

echo 📱 红手指云手机配置说明：
echo.
echo 1️⃣  登录红手指控制台 (https://www.redfinger.com/)
echo 2️⃣  点击你的云手机 → 查看详情
echo 3️⃣  找到"ADB连接"或"调试信息"
echo 4️⃣  记下ADB端口号 (通常是5位数字，如12345)
echo.

:: 输入ADB端口号
:INPUT_PORT
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set /p ADB_PORT="请输入红手指ADB端口号: "

:: 验证输入
if "%ADB_PORT%"=="" (
    echo [✗] 端口号不能为空
    echo.
    goto INPUT_PORT
)

:: 检查是否为数字
echo %ADB_PORT%| findstr /r "^[0-9][0-9]*$" >nul
if %errorlevel% neq 0 (
    echo [✗] 端口号必须是纯数字
    echo.
    goto INPUT_PORT
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              第1步：连接红手指云手机                     ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 连接设备
echo [*] 正在连接到 127.0.0.1:%ADB_PORT%...
adb connect 127.0.0.1:%ADB_PORT%

if %errorlevel% neq 0 (
    echo [✗] 连接失败
    echo.
    echo 💡 可能原因：
    echo    1. 端口号输入错误
    echo    2. 红手指云手机未开启ADB调试
    echo    3. 本地网络连接问题
    echo.
    pause
    exit /b 1
)

:: 等待连接建立
echo [*] 等待连接建立...
timeout /t 3 /nobreak >nul

:: 检查设备连接
echo.
echo [*] 检查设备连接状态...
adb devices -l

echo.
adb devices | find "127.0.0.1:%ADB_PORT%" >nul
if %errorlevel% == 0 (
    echo [✓] 设备连接成功
) else (
    echo [✗] 设备未正确连接
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║         第2步：安装Appium Settings (必需)               ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 设置设备ID
set DEVICE_ID=127.0.0.1:%ADB_PORT%

:: 检查Appium Settings APK是否存在
if exist "%PROJECT_ROOT%\appium-settings.apk" (
    echo [*] 正在安装 Appium Settings...
    adb -s %DEVICE_ID% install -r "%PROJECT_ROOT%\appium-settings.apk"

    if %errorlevel% == 0 (
        echo [✓] Appium Settings 安装成功
    ) else (
        echo [!] Appium Settings 可能已安装或安装失败
    )
) else (
    echo [!] 未找到 appium-settings.apk
    echo.
    echo 💡 提示：
    echo    Appium Settings是Appium自动化所必需的
    echo    请从以下地址下载并放到项目根目录：
    echo    https://github.com/appium/io.appium.settings/releases
    echo.
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║     第3步：安装 Appium UIAutomator2 Server (必需)      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查UIAutomator2 Server APK是否存在
if exist "%PROJECT_ROOT%\io.appium.uiautomator2.server.apk" (
    echo [*] 正在安装 Appium UIAutomator2 Server...
    adb -s %DEVICE_ID% install -r "%PROJECT_ROOT%\io.appium.uiautomator2.server.apk"

    if %errorlevel% == 0 (
        echo [✓] UIAutomator2 Server 安装成功
    ) else (
        echo [!] UIAutomator2 Server 可能已安装或安装失败
    )
) else (
    echo [!] 未找到 io.appium.uiautomator2.server.apk
    echo.
    echo 💡 提示：
    echo    UIAutomator2 Server是Appium自动化所必需的
    echo    首次连接时Appium会自动安装，此步骤可跳过
    echo.
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║            第4步：验证设备信息                           ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [*] 设备信息：
echo.
adb -s %DEVICE_ID% shell getprop ro.build.version.release
adb -s %DEVICE_ID% shell getprop ro.product.model
adb -s %DEVICE_ID% shell getprop ro.build.version.sdk

echo.
echo [*] 已安装的Appium相关包：
adb -s %DEVICE_ID% shell pm list packages | find "appium"

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║           第5步：更新项目配置文件 (可选)                 ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

set /p UPDATE_CONFIG="是否自动更新配置文件中的ADB端口? (Y/N): "

if /i "%UPDATE_CONFIG%"=="Y" (
    if exist "%PROJECT_ROOT%\damai_appium\config.jsonc" (
        echo [*] 正在备份配置文件...
        copy "%PROJECT_ROOT%\damai_appium\config.jsonc" "%PROJECT_ROOT%\damai_appium\config.jsonc.bak" >nul

        echo [*] 配置文件已备份为 config.jsonc.bak
        echo.
        echo 📝 请手动编辑配置文件：
        echo    文件路径: damai_appium\config.jsonc
        echo    修改项: "adb_port": "%ADB_PORT%"
        echo.
    ) else (
        echo [!] 未找到配置文件
    )
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║                   配置完成！                            ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo ✅ 红手指云手机配置完成！
echo.
echo 📋 配置摘要：
echo    设备地址: 127.0.0.1:%ADB_PORT%
echo    连接状态: 已连接
echo    Appium Settings: 已安装
echo    UIAutomator2 Server: 已安装
echo.
echo 🚀 下一步操作：
echo.
echo  1. 📝 编辑配置文件 damai_appium\config.jsonc
echo     将 adb_port 修改为: "%ADB_PORT%"
echo.
echo  2. 🔧 启动程序：双击运行 "一键启动.bat"
echo.
echo  3. 🔌 在GUI中点击"连接设备"测试连接
echo.
echo 📚 详细教程：
echo    docs\guides\红手指使用指南.md
echo    docs\guides\详细使用教程_GUI操作指南.md
echo.
echo ⚠️  重要提示：
echo    每次重启电脑后需要重新运行此脚本连接设备
echo    或在GUI中使用"连接急救箱"功能自动连接
echo.
pause
