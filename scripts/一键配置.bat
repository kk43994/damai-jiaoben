@echo off
chcp 65001 >nul
title 移动端自动化测试 - 环境配置向导
color 0A

echo ╔═══════════════════════════════════════════════════════╗
echo ║     移动端自动化测试演示 v2.2 - 环境配置向导           ║
echo ║                 (Appium技术学习项目)                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo ⚠️  重要提示：本项目仅供技术学习和研究使用
echo ❌  严禁用于商业倒票、破坏平台秩序等违法行为
echo.
pause
echo.

:: 设置编码
set PYTHONIOENCODING=utf-8

:: 获取脚本所在目录的父目录（项目根目录）
cd /d "%~dp0.."
set PROJECT_ROOT=%CD%

echo ╔═══════════════════════════════════════════════════════╗
echo ║                  第1步：配置环境变量                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 配置便携式Python路径
if exist "%PROJECT_ROOT%\python-portable" (
    echo [✓] 发现Python便携版
    set PYTHON_HOME=%PROJECT_ROOT%\python-portable
    set PATH=%PYTHON_HOME%;%PYTHON_HOME%\Scripts;%PATH%
) else (
    echo [!] 未发现Python便携版，将使用系统Python
)

:: 配置便携式Node.js路径
if exist "%PROJECT_ROOT%\nodejs-portable" (
    echo [✓] 发现Node.js便携版
    set NODE_HOME=%PROJECT_ROOT%\nodejs-portable
    set PATH=%NODE_HOME%;%PATH%
) else (
    echo [!] 未发现Node.js便携版，将使用系统Node.js
)

:: 配置Android SDK工具路径
if exist "%PROJECT_ROOT%\android-sdk-tools" (
    echo [✓] 发现Android SDK工具
    set ANDROID_SDK_ROOT=%PROJECT_ROOT%\android-sdk-tools
    set PATH=%ANDROID_SDK_ROOT%\platform-tools;%PATH%
) else (
    echo [!] 未发现Android SDK工具，将使用系统配置
)

:: 配置Appium路径
if exist "%PROJECT_ROOT%\appium" (
    echo [✓] 发现Appium便携版
    set PATH=%PROJECT_ROOT%\appium;%PATH%
) else (
    echo [!] 未发现Appium便携版，将使用全局安装的Appium
)

echo.
echo [√] 环境变量配置完成
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║                  第2步：验证运行环境                    ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检测Python
echo [1/4] 检测Python环境...
python --version 2>nul
if %errorlevel% == 0 (
    echo [✓] Python检测成功
) else (
    echo [✗] Python未安装或未配置
    echo.
    echo ⚠️  请确保已安装Python 3.8+或下载完整懒人包
    pause
    exit /b 1
)

:: 检测Node.js
echo.
echo [2/4] 检测Node.js环境...
node --version 2>nul
if %errorlevel% == 0 (
    echo [✓] Node.js检测成功
) else (
    echo [✗] Node.js未安装或未配置
    echo.
    echo ⚠️  请确保已安装Node.js 16+或下载完整懒人包
    pause
    exit /b 1
)

:: 检测ADB
echo.
echo [3/4] 检测ADB工具...
adb version 2>nul
if %errorlevel% == 0 (
    echo [✓] ADB工具检测成功
) else (
    echo [✗] ADB工具未安装或未配置
    echo.
    echo ⚠️  请确保已安装Android SDK或下载完整懒人包
    pause
    exit /b 1
)

:: 检测Appium
echo.
echo [4/4] 检测Appium...
appium --version 2>nul
if %errorlevel% == 0 (
    echo [✓] Appium检测成功
) else (
    echo [!] Appium未检测到，正在尝试安装...
    echo.
    echo 安装Appium及UiAutomator2驱动...
    call npm install -g appium
    call appium driver install uiautomator2

    if %errorlevel% == 0 (
        echo [✓] Appium安装成功
    ) else (
        echo [✗] Appium安装失败
        pause
        exit /b 1
    )
)

echo.
echo [√] 运行环境验证完成
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║                 第3步：安装Python依赖                   ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 进入项目目录
cd "%PROJECT_ROOT%"

:: 检查requirements.txt是否存在
if not exist "requirements.txt" (
    echo [✗] 未找到requirements.txt文件
    pause
    exit /b 1
)

echo [*] 正在安装Python依赖包，请稍候...
echo.

:: 升级pip
python -m pip install --upgrade pip

:: 安装依赖
python -m pip install -r requirements.txt

if %errorlevel% == 0 (
    echo.
    echo [✓] Python依赖安装成功
) else (
    echo.
    echo [✗] Python依赖安装失败
    pause
    exit /b 1
)

echo.
echo [√] 依赖安装完成
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║                 第4步：配置文件检查                      ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 检查配置文件
if not exist "damai_appium\config.jsonc" (
    if exist "damai_appium\config.jsonc.example" (
        echo [*] 复制配置文件模板...
        copy "damai_appium\config.jsonc.example" "damai_appium\config.jsonc"
        echo [√] 配置文件已创建
        echo.
        echo 📝 请编辑 damai_appium\config.jsonc 填写你的配置
    ) else (
        echo [!] 未找到配置文件模板
    )
) else (
    echo [✓] 配置文件已存在
)

echo.
echo [√] 配置文件检查完成
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║                第5步：创建环境配置文件                   ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

:: 创建环境配置文件（保存环境变量配置供一键启动使用）
echo :: 自动生成的环境配置文件 > "%PROJECT_ROOT%\.env.bat"
echo set PROJECT_ROOT=%PROJECT_ROOT% >> "%PROJECT_ROOT%\.env.bat"

if exist "%PROJECT_ROOT%\python-portable" (
    echo set PYTHON_HOME=%PROJECT_ROOT%\python-portable >> "%PROJECT_ROOT%\.env.bat"
)

if exist "%PROJECT_ROOT%\nodejs-portable" (
    echo set NODE_HOME=%PROJECT_ROOT%\nodejs-portable >> "%PROJECT_ROOT%\.env.bat"
)

if exist "%PROJECT_ROOT%\android-sdk-tools" (
    echo set ANDROID_SDK_ROOT=%PROJECT_ROOT%\android-sdk-tools >> "%PROJECT_ROOT%\.env.bat"
)

echo set PYTHONIOENCODING=utf-8 >> "%PROJECT_ROOT%\.env.bat"

echo [✓] 环境配置文件已创建
echo.

echo ╔═══════════════════════════════════════════════════════╗
echo ║                   配置完成！                            ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo ✅ 所有配置已完成，您现在可以：
echo.
echo  1. 📝 编辑配置文件：damai_appium\config.jsonc
echo  2. 🔌 配置红手指云手机：双击运行 "红手指配置.bat"
echo  3. 🚀 启动程序：双击运行 "一键启动.bat"
echo.
echo 📚 详细教程：docs\guides\完整安装教程_小白版.md
echo 📖 使用指南：docs\guides\详细使用教程_GUI操作指南.md
echo.
echo ⚠️  重要提示：
echo    本项目仅供技术学习和研究使用
echo    严禁用于商业倒票、破坏平台秩序等违法行为
echo.
pause
