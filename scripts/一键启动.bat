@echo off
chcp 65001 >nul
title 移动端自动化测试 - 一键启动
color 0A

echo ╔═══════════════════════════════════════════════════════╗
echo ║         移动端自动化测试演示 v2.2 - 一键启动            ║
echo ║                (Appium技术学习项目)                     ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo ⚠️  本项目仅供技术学习使用，严禁商业倒票等违法行为
echo.

:: 获取项目根目录
cd /d "%~dp0.."
set PROJECT_ROOT=%CD%

:: 加载环境配置
if exist "%PROJECT_ROOT%\.env.bat" (
    call "%PROJECT_ROOT%\.env.bat"
    echo [✓] 已加载环境配置
) else (
    echo [!] 未找到环境配置文件
    echo.
    echo 💡 请先运行 "一键配置.bat" 进行环境配置
    echo.
    pause
    exit /b 1
)

:: 配置PATH环境变量
if defined PYTHON_HOME (
    set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
)

if defined NODE_HOME (
    set PATH=%NODE_HOME%;%PATH%
)

if defined ANDROID_SDK_ROOT (
    set PATH=%ANDROID_SDK_ROOT%\platform-tools;%PATH%
)

if exist "%PROJECT_ROOT%\appium" (
    set PATH=%PROJECT_ROOT%\appium;%PATH%
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              第1步：启动Appium服务器                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查Appium是否已在运行
tasklist /FI "IMAGENAME eq node.exe" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [!] 检测到Node.js进程正在运行
    echo.
    set /p KILL_NODE="是否终止现有Node.js进程? (Y/N): "
    if /i "%KILL_NODE%"=="Y" (
        echo [*] 正在终止Node.js进程...
        taskkill /F /IM node.exe /T >nul 2>&1
        timeout /t 2 /nobreak >nul
        echo [✓] 已终止
    )
)

echo [*] 正在启动Appium服务器...
echo.
echo 📡 Appium配置:
echo    - 地址: http://127.0.0.1:4723
echo    - 允许跨域: 是
echo.

:: 启动Appium（后台运行）
start /B "Appium Server" appium --address 127.0.0.1 --port 4723 --allow-cors 2>appium.log

:: 等待Appium启动
echo [*] 等待Appium服务器启动...
timeout /t 5 /nobreak >nul

:: 检查Appium是否成功启动
tasklist /FI "IMAGENAME eq node.exe" 2>NUL | find /I /N "node.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [✓] Appium服务器已启动
) else (
    echo [✗] Appium服务器启动失败
    echo.
    echo 💡 可能原因：
    echo    1. Appium未正确安装（运行 "一键配置.bat" 重新配置）
    echo    2. 端口4723被占用（关闭其他Appium实例）
    echo    3. 查看appium.log了解详细错误
    echo.
    pause
    exit /b 1
)

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║              第2步：启动GUI控制面板                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查GUI程序是否存在
if not exist "%PROJECT_ROOT%\damai_smart_ai.py" (
    echo [✗] 未找到GUI程序：damai_smart_ai.py
    pause
    exit /b 1
)

echo [*] 正在启动GUI控制面板...
echo.

:: 进入项目根目录
cd "%PROJECT_ROOT%"

:: 启动GUI程序
python damai_smart_ai.py

:: GUI程序退出后的清理工作
echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║                   清理和退出                            ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo [*] GUI程序已退出
echo.

:: 询问是否终止Appium服务器
set /p KEEP_APPIUM="是否保持Appium服务器运行? (Y/N): "
if /i "%KEEP_APPIUM%"=="N" (
    echo [*] 正在终止Appium服务器...
    taskkill /F /IM node.exe /T >nul 2>&1
    echo [✓] Appium服务器已终止
) else (
    echo [*] Appium服务器继续运行
    echo    提示：可手动运行此脚本再次启动GUI
)

echo.
echo [✓] 程序已安全退出
echo.
pause
