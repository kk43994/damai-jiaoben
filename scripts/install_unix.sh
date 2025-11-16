#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "  大麦抢票系统 - Unix一键安装"
echo "  版本: v2.1.0"
echo "========================================"
echo ""

# 检测操作系统
OS_TYPE=$(uname -s)
echo "检测到操作系统: $OS_TYPE"
echo ""

# 检查Python
echo "[1/6] 检查Python环境..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "${GREEN}[OK]${NC} Python已安装: $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    echo -e "${GREEN}[OK]${NC} Python已安装: $PYTHON_VERSION"
else
    echo -e "${RED}[错误]${NC} 未检测到Python，请先安装Python 3.9+"
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "macOS安装命令: brew install python@3.9"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    fi
    exit 1
fi
echo ""

# 检查pip
echo "[2/6] 检查pip..."
if $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${GREEN}[OK]${NC} pip已安装"
else
    echo -e "${RED}[错误]${NC} pip未安装"
    exit 1
fi
echo ""

# 升级pip
echo "[3/6] 升级pip到最新版本..."
$PYTHON_CMD -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
echo ""

# 安装依赖
echo "[4/6] 安装项目依赖（使用清华镜像加速）..."
echo "这可能需要几分钟，请耐心等待..."
$PYTHON_CMD -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误]${NC} 依赖安装失败"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} 依赖安装成功"
echo ""

# 创建配置文件
echo "[5/6] 创建配置文件..."
if [ ! -f "damai_appium/config.jsonc" ]; then
    if [ -f "damai_appium/config.jsonc.example" ]; then
        cp damai_appium/config.jsonc.example damai_appium/config.jsonc
        echo -e "${GREEN}[OK]${NC} 已创建配置文件 damai_appium/config.jsonc"
        echo -e "${YELLOW}[提示]${NC} 请编辑此文件填入演出信息"
    else
        echo -e "${YELLOW}[提示]${NC} 未找到配置示例文件"
    fi
else
    echo -e "${YELLOW}[提示]${NC} 配置文件已存在，跳过创建"
fi
echo ""

# 检查Android SDK
echo "[6/6] 检查Android SDK..."
ANDROID_HOME_FOUND=0

if [ -n "$ANDROID_HOME" ]; then
    echo -e "${GREEN}[OK]${NC} 检测到 ANDROID_HOME: $ANDROID_HOME"
    ANDROID_HOME_FOUND=1
elif [ -n "$ANDROID_SDK_ROOT" ]; then
    echo -e "${GREEN}[OK]${NC} 检测到 ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT"
    ANDROID_HOME_FOUND=1
else
    echo -e "${YELLOW}[提示]${NC} 未检测到Android SDK环境变量"

    # 检查默认位置
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        DEFAULT_SDK="$HOME/Library/Android/sdk"
    else
        DEFAULT_SDK="$HOME/Android/Sdk"
    fi

    if [ -d "$DEFAULT_SDK" ]; then
        echo -e "${YELLOW}[提示]${NC} 在默认位置找到Android SDK: $DEFAULT_SDK"
        echo -e "${YELLOW}[建议]${NC} 请在 ~/.bashrc 或 ~/.zshrc 中添加:"
        echo "export ANDROID_HOME=$DEFAULT_SDK"
        echo "export PATH=\$PATH:\$ANDROID_HOME/platform-tools"
    else
        echo -e "${YELLOW}[提示]${NC} 如果需要使用真机或模拟器，请安装Android SDK"
        if [[ "$OS_TYPE" == "Darwin" ]]; then
            echo "macOS安装: brew install --cask android-platform-tools"
        fi
    fi
fi

# 检查ADB
if command -v adb &> /dev/null; then
    echo -e "${GREEN}[OK]${NC} ADB工具已配置"
    adb version | head -1
else
    echo -e "${YELLOW}[提示]${NC} ADB工具未配置到PATH"
    if [ $ANDROID_HOME_FOUND -eq 1 ]; then
        echo -e "${YELLOW}[建议]${NC} 添加到PATH: \$ANDROID_HOME/platform-tools"
    fi
fi
echo ""

# 检查Node.js和Appium
echo "[额外检查] Node.js和Appium..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}[OK]${NC} Node.js已安装: $NODE_VERSION"

    if command -v appium &> /dev/null; then
        APPIUM_VERSION=$(appium --version)
        echo -e "${GREEN}[OK]${NC} Appium已安装: $APPIUM_VERSION"
    else
        echo -e "${YELLOW}[提示]${NC} Appium未安装"
        echo "安装命令: npm install -g appium"
    fi
else
    echo -e "${YELLOW}[提示]${NC} Node.js未安装（运行Appium需要）"
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        echo "macOS安装: brew install node"
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        echo "Ubuntu/Debian: sudo apt install nodejs npm"
    fi
fi
echo ""

# 设置执行权限
chmod +x start_appium.sh 2>/dev/null || true

# 安装完成
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "下一步操作："
echo "1. 编辑配置文件: damai_appium/config.jsonc"
echo "2. 启动Appium: appium --port 4723 --allow-cors"
echo "3. 连接设备: adb devices"
echo "4. 运行程序: $PYTHON_CMD damai_smart_ai.py"
echo ""
echo "详细教程请查看: README.md"
echo ""

# 询问是否打开配置文件
read -p "是否现在打开配置文件编辑？(y/N): " OPEN_CONFIG
if [[ "$OPEN_CONFIG" =~ ^[Yy]$ ]]; then
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        open -e damai_appium/config.jsonc
    else
        ${EDITOR:-nano} damai_appium/config.jsonc
    fi
fi
