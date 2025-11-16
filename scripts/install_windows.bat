@echo off
chcp 65001 >nul
echo ========================================
echo   大麦抢票系统 - Windows一键安装
echo   版本: v2.1.0
echo ========================================
echo.

:: 检查Python
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo [OK] Python已安装
echo.

:: 检查pip
echo [2/6] 检查pip...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] pip未安装
    pause
    exit /b 1
)
echo [OK] pip已安装
echo.

:: 升级pip
echo [3/6] 升级pip到最新版本...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo.

:: 安装依赖
echo [4/6] 安装项目依赖（使用清华镜像加速）...
echo 这可能需要几分钟，请耐心等待...
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [OK] 依赖安装成功
echo.

:: 创建配置文件
echo [5/6] 创建配置文件...
if not exist "damai_appium\config.jsonc" (
    if exist "damai_appium\config.jsonc.example" (
        copy "damai_appium\config.jsonc.example" "damai_appium\config.jsonc" >nul
        echo [OK] 已创建配置文件 damai_appium\config.jsonc
        echo [提示] 请编辑此文件填入演出信息
    ) else (
        echo [提示] 未找到配置示例文件
    )
) else (
    echo [提示] 配置文件已存在，跳过创建
)
echo.

:: 检查Android SDK
echo [6/6] 检查Android SDK...
set ANDROID_HOME_FOUND=0

:: 检查环境变量
if defined ANDROID_HOME (
    echo [OK] 检测到 ANDROID_HOME: %ANDROID_HOME%
    set ANDROID_HOME_FOUND=1
) else if defined ANDROID_SDK_ROOT (
    echo [OK] 检测到 ANDROID_SDK_ROOT: %ANDROID_SDK_ROOT%
    set ANDROID_HOME_FOUND=1
) else (
    echo [提示] 未检测到Android SDK环境变量
    set "DEFAULT_SDK=%LOCALAPPDATA%\Android\Sdk"
    if exist "!DEFAULT_SDK!" (
        echo [提示] 在默认位置找到Android SDK: !DEFAULT_SDK!
        echo [建议] 请设置环境变量 ANDROID_HOME=!DEFAULT_SDK!
    ) else (
        echo [提示] 如果需要使用真机或模拟器，请安装Android SDK
        echo 下载地址: https://developer.android.com/studio
    )
)

:: 检查ADB
adb version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] ADB工具已配置
    adb version | findstr "Android Debug Bridge"
) else (
    echo [提示] ADB工具未配置到PATH
    if %ANDROID_HOME_FOUND% equ 1 (
        echo [建议] 添加到PATH: %%ANDROID_HOME%%\platform-tools
    )
)
echo.

:: 安装完成
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步操作：
echo 1. 编辑配置文件: damai_appium\config.jsonc
echo 2. 启动Appium: start_appium.bat
echo 3. 连接设备: adb devices
echo 4. 运行程序: python damai_smart_ai.py
echo.
echo 详细教程请查看: README.md
echo.

:: 询问是否打开配置文件
set /p OPEN_CONFIG="是否现在打开配置文件？(Y/N): "
if /i "%OPEN_CONFIG%"=="Y" (
    notepad damai_appium\config.jsonc
)

pause
