@echo off
chcp 65001 >nul
title 移动端自动化测试 - 自动下载依赖工具
color 0B

echo ╔═══════════════════════════════════════════════════════╗
echo ║           自动下载依赖工具 v2.2                         ║
echo ║         (移动端自动化测试演示框架)                       ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo 📦 本工具将自动下载以下组件：
echo.
echo    1. Python 3.11 便携版 (~25MB)
echo    2. Node.js 20.x 便携版 (~50MB)
echo    3. Android SDK Platform Tools (~10MB)
echo    4. Appium Settings APK (~5MB)
echo    5. UIAutomator2 Server APK (~2MB)
echo.
echo 📊 预计下载总量：约 90-100MB
echo ⏱️  预计耗时：5-15分钟（取决于网速）
echo.
echo ⚠️  注意事项：
echo    - 需要稳定的网络连接
echo    - 建议关闭代理或VPN以提高下载速度
echo    - 下载过程中请勿关闭此窗口
echo.

pause

:: 获取项目根目录
cd /d "%~dp0.."
set PROJECT_ROOT=%CD%

:: 创建下载目录
if not exist "%PROJECT_ROOT%\downloads" mkdir "%PROJECT_ROOT%\downloads"
cd /d "%PROJECT_ROOT%\downloads"

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              开始下载依赖组件...                        ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查curl是否可用
where curl >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 未找到curl命令
    echo.
    echo 💡 请使用以下方法之一：
    echo    1. 升级到Windows 10 1803及以上版本（内置curl）
    echo    2. 手动下载组件（参考下方链接）
    echo.
    goto MANUAL_DOWNLOAD
)

echo [✓] curl命令可用
echo.

:: =================================================================
:: 1. 下载 Python 3.11 便携版
:: =================================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [1/5] 下载 Python 3.11 便携版...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
set PYTHON_FILE=python-3.11.9-embed-amd64.zip

if not exist "%PYTHON_FILE%" (
    echo [*] 正在下载: %PYTHON_FILE%
    echo [*] URL: %PYTHON_URL%
    curl -L -o "%PYTHON_FILE%" "%PYTHON_URL%"

    if %errorlevel% == 0 (
        echo [✓] Python 下载成功
    ) else (
        echo [✗] Python 下载失败
    )
) else (
    echo [✓] Python 已存在，跳过下载
)
echo.

:: =================================================================
:: 2. 下载 Node.js 20.x 便携版
:: =================================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [2/5] 下载 Node.js 20.x 便携版...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set NODEJS_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip
set NODEJS_FILE=node-v20.11.1-win-x64.zip

if not exist "%NODEJS_FILE%" (
    echo [*] 正在下载: %NODEJS_FILE%
    echo [*] URL: %NODEJS_URL%
    curl -L -o "%NODEJS_FILE%" "%NODEJS_URL%"

    if %errorlevel% == 0 (
        echo [✓] Node.js 下载成功
    ) else (
        echo [✗] Node.js 下载失败
    )
) else (
    echo [✓] Node.js 已存在，跳过下载
)
echo.

:: =================================================================
:: 3. 下载 Android SDK Platform Tools
:: =================================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [3/5] 下载 Android SDK Platform Tools...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set SDK_URL=https://dl.google.com/android/repository/platform-tools-latest-windows.zip
set SDK_FILE=platform-tools-latest-windows.zip

if not exist "%SDK_FILE%" (
    echo [*] 正在下载: %SDK_FILE%
    echo [*] URL: %SDK_URL%
    curl -L -o "%SDK_FILE%" "%SDK_URL%"

    if %errorlevel% == 0 (
        echo [✓] Android SDK 下载成功
    ) else (
        echo [✗] Android SDK 下载失败
    )
) else (
    echo [✓] Android SDK 已存在，跳过下载
)
echo.

:: =================================================================
:: 4. 下载 Appium Settings APK
:: =================================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [4/5] 下载 Appium Settings APK...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set SETTINGS_URL=https://github.com/appium/io.appium.settings/releases/download/v5.0.0/settings_apk-debug.apk
set SETTINGS_FILE=appium-settings.apk

if not exist "%SETTINGS_FILE%" (
    echo [*] 正在下载: %SETTINGS_FILE%
    echo [*] URL: %SETTINGS_URL%
    curl -L -o "%SETTINGS_FILE%" "%SETTINGS_URL%"

    if %errorlevel% == 0 (
        echo [✓] Appium Settings 下载成功
        copy "%SETTINGS_FILE%" "%PROJECT_ROOT%\appium-settings.apk" >nul
    ) else (
        echo [✗] Appium Settings 下载失败
    )
) else (
    echo [✓] Appium Settings 已存在，跳过下载
    copy "%SETTINGS_FILE%" "%PROJECT_ROOT%\appium-settings.apk" >nul
)
echo.

:: =================================================================
:: 5. 下载 UIAutomator2 Server APK
:: =================================================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [5/5] 下载 UIAutomator2 Server APK...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set UIAUTOMATOR2_URL=https://github.com/appium/appium-uiautomator2-server/releases/download/v6.0.0/appium-uiautomator2-server-v6.0.0.apk
set UIAUTOMATOR2_FILE=io.appium.uiautomator2.server.apk

if not exist "%UIAUTOMATOR2_FILE%" (
    echo [*] 正在下载: %UIAUTOMATOR2_FILE%
    echo [*] URL: %UIAUTOMATOR2_URL%
    curl -L -o "%UIAUTOMATOR2_FILE%" "%UIAUTOMATOR2_URL%"

    if %errorlevel% == 0 (
        echo [✓] UIAutomator2 Server 下载成功
        copy "%UIAUTOMATOR2_FILE%" "%PROJECT_ROOT%\io.appium.uiautomator2.server.apk" >nul
    ) else (
        echo [✗] UIAutomator2 Server 下载失败
    )
) else (
    echo [✓] UIAutomator2 Server 已存在，跳过下载
    copy "%UIAUTOMATOR2_FILE%" "%PROJECT_ROOT%\io.appium.uiautomator2.server.apk" >nul
)
echo.

:: =================================================================
:: 解压文件
:: =================================================================
echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              正在解压下载的文件...                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查PowerShell是否可用
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] 未找到PowerShell，无法自动解压
    goto MANUAL_EXTRACT
)

:: 解压 Python
if exist "%PYTHON_FILE%" (
    if not exist "%PROJECT_ROOT%\python-portable" (
        echo [*] 正在解压 Python...
        powershell -Command "Expand-Archive -Path '%PYTHON_FILE%' -DestinationPath '%PROJECT_ROOT%\python-portable' -Force"
        echo [✓] Python 解压完成
    ) else (
        echo [✓] Python 已解压，跳过
    )
)

:: 解压 Node.js
if exist "%NODEJS_FILE%" (
    if not exist "%PROJECT_ROOT%\nodejs-portable" (
        echo [*] 正在解压 Node.js...
        powershell -Command "Expand-Archive -Path '%NODEJS_FILE%' -DestinationPath '%PROJECT_ROOT%\nodejs-temp' -Force"
        move "%PROJECT_ROOT%\nodejs-temp\node-v20.11.1-win-x64" "%PROJECT_ROOT%\nodejs-portable" >nul
        rd /s /q "%PROJECT_ROOT%\nodejs-temp"
        echo [✓] Node.js 解压完成
    ) else (
        echo [✓] Node.js 已解压，跳过
    )
)

:: 解压 Android SDK
if exist "%SDK_FILE%" (
    if not exist "%PROJECT_ROOT%\android-sdk-tools" (
        echo [*] 正在解压 Android SDK...
        powershell -Command "Expand-Archive -Path '%SDK_FILE%' -DestinationPath '%PROJECT_ROOT%\android-sdk-tools' -Force"
        echo [✓] Android SDK 解压完成
    ) else (
        echo [✓] Android SDK 已解压，跳过
    )
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              下载和解压完成！                           ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo ✅ 所有依赖组件已下载并解压完成！
echo.
echo 📋 下载的文件保存在：
echo    %PROJECT_ROOT%\downloads\
echo.
echo 📦 已安装的组件：
echo    ✓ python-portable/
echo    ✓ nodejs-portable/
echo    ✓ android-sdk-tools/
echo    ✓ appium-settings.apk
echo    ✓ io.appium.uiautomator2.server.apk
echo.
echo 🚀 下一步操作：
echo.
echo    1. 运行 "一键配置.bat" 完成环境配置
echo    2. 运行 "一键启动.bat" 启动程序
echo.
pause
exit /b 0

:MANUAL_DOWNLOAD
echo ╔═══════════════════════════════════════════════════════╗
echo ║              手动下载链接                              ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo 请手动下载以下组件：
echo.
echo 1. Python 3.11 便携版：
echo    https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
echo    解压到: python-portable\
echo.
echo 2. Node.js 20.x 便携版：
echo    https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip
echo    解压到: nodejs-portable\
echo.
echo 3. Android SDK Platform Tools：
echo    https://dl.google.com/android/repository/platform-tools-latest-windows.zip
echo    解压到: android-sdk-tools\
echo.
echo 4. Appium Settings APK：
echo    https://github.com/appium/io.appium.settings/releases/latest
echo    保存为: appium-settings.apk
echo.
echo 5. UIAutomator2 Server APK：
echo    https://github.com/appium/appium-uiautomator2-server/releases/latest
echo    保存为: io.appium.uiautomator2.server.apk
echo.
pause
exit /b 1

:MANUAL_EXTRACT
echo.
echo [!] 请手动解压下载的文件到对应目录：
echo.
echo    %PYTHON_FILE% → python-portable\
echo    %NODEJS_FILE% → nodejs-portable\
echo    %SDK_FILE% → android-sdk-tools\
echo.
pause
exit /b 0
