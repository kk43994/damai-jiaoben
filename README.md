# 大麦抢票自动化系统

> **版本**: v2.2
> **最后更新**: 2025-11-17
> **状态**: ✅ 稳定版本 | 项目已整理

一个基于Selenium和Appium的大麦网抢票自动化工具，支持Web端和移动端抢票。

---

## ⚠️ 法律声明与免责条款

<div align="center">
<table>
<tr>
<td>

### 🚨 重要提示 🚨

**本项目为技术学习与研究项目，集成OCR识别和自动决策技术，仅供教学交流使用。**

#### 📜 使用声明

- ✅ **本项目完全开源免费**，托管于GitHub平台
- ✅ **仅供个人学习、技术研究、教学演示使用**
- ❌ **严禁用于任何违法犯罪活动**
- ❌ **严禁商业倒卖门票、恶意抢票**
- ❌ **严禁破坏平台公平秩序**
- ❌ **严禁通过学习本项目进行任何违反法律法规的行为**

#### ⚖️ 法律责任

根据《中华人民共和国刑法》及相关司法解释：
- 开发者已明确声明本项目用途和使用限制
- **使用者的一切违法违规行为由使用者本人承担全部法律责任**
- **与本项目开发者、贡献者无任何法律关系**
- 使用本项目即视为同意本声明的所有条款

#### 📋 合法使用场景

- ✅ 学习Python自动化技术
- ✅ 研究Appium移动端自动化
- ✅ 研究OCR文字识别技术
- ✅ 教学演示自动化决策流程
- ✅ 技术竞赛、课程作业

**⚠️ 请在使用前仔细阅读并遵守本声明 ⚠️**

</td>
</tr>
</table>
</div>

---

## 📑 快速导航

- [功能特性](#-功能特性)
- [系统要求](#-系统要求)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [版本更新](#-版本更新)
- [项目结构](#-项目结构)

---

## 🚀 功能特性

### 核心功能
- ✅ **智能抢票** - 自动选择城市、票价、场次、观演人员
- ✅ **双端支持** - Web端(Selenium) + 移动端(Appium)
- ✅ **自动修复** - 连接自动检测和修复(Appium/ADB/WebDriver)
- ✅ **GUI界面** - 图形化操作界面，简单易用
- ✅ **OCR识别** - PaddleOCR文字识别辅助决策
- ✅ **智能等待** - 优化等待策略，提升执行效率

### 性能指标
- ⚡ WebDriver连接: **4.66秒**
- ⚡ 完整抢票流程: **123秒** (11步骤)
- ✅ 成功率: **100%**
- 📦 核心代码: **8个文件** (精简架构)

---

## 📋 系统要求

### 基础环境
- **Python**: 3.9+
- **操作系统**: Windows / macOS / Linux

### 移动端抢票（必需）
- **Android SDK**: 已配置环境变量
- **Appium**: 3.1.0+
- **Android设备**: 真机或模拟器
- **ADB工具**: 已配置PATH

### 可选组件
- **Node.js**: 20.19.0+ (运行Appium Server)
- **PaddleOCR**: 文字识别支持

---

## 📁 项目结构

```
ticket-purchase/
├── damai_smart_ai.py                 # 🖥️ GUI主程序
├── damai_appium/                     # 📦 核心抢票模块
│   ├── damai_app_v2.py              # 🤖 抢票Bot核心引擎
│   ├── fast_grabber.py              # ⚡ v2.2快速抢票功能
│   ├── webdriver_health_monitor.py  # 🩺 WebDriver健康监控
│   ├── config.py                    # ⚙️ 配置管理
│   └── ...                          # 其他核心模块
├── connection_auto_fixer.py          # 🔧 连接自动修复
├── connection_first_aid.py           # 🏥 连接急救箱
├── environment_checker.py            # 🔍 环境检查器
├── docs/                             # 📚 文档目录
│   ├── current/                     # 当前版本文档（v2.2）
│   ├── development/                 # 开发历史文档
│   └── guides/                      # 使用指南
├── scripts/                          # 🛠️ 实用脚本
│   ├── install_windows.bat          # Windows安装脚本
│   ├── install_unix.sh              # Unix安装脚本
│   └── start_appium.bat             # Appium启动脚本
├── archive/                          # 🗄️ 归档文件
│   └── screenshots/                 # 历史截图
└── temp/                             # 🔧 临时文件
    ├── test_data/                   # 测试数据
    └── screenshots/                 # 临时截图
```

### 核心文件说明

| 文件 | 说明 |
|------|------|
| `damai_smart_ai.py` | GUI主程序，提供可视化操作界面 |
| `damai_appium/damai_app_v2.py` | v2.0稳定版抢票引擎 |
| `damai_appium/fast_grabber.py` | v2.2快速抢票功能 |
| `connection_auto_fixer.py` | 连接自动修复工具 |
| `connection_first_aid.py` | 连接急救箱（5维诊断） |
| `environment_checker.py` | 环境检查和依赖验证 |

### 文档导航

- 📖 **完整文档索引**: [docs/README.md](docs/README.md)
- 🚀 **快速开始**: [QUICKSTART.md](QUICKSTART.md)
- 📋 **更新日志**: [CHANGELOG.md](CHANGELOG.md)

---

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/kk43994/damai-jiaoben.git
cd damai-jiaoben
```

### 2. 安装依赖
```bash
# 使用pip安装
pip install -r requirements.txt

# 或使用Poetry（推荐）
poetry install
```

### 3. 配置文件
复制配置示例并修改：
```bash
cp damai_appium/config.jsonc.example damai_appium/config.jsonc
```

编辑 `config.jsonc` 填入演出信息：
```jsonc
{
  "server_url": "http://127.0.0.1:4723",
  "keyword": "演出名称",
  "city": "城市",
  "date": "日期",
  "price": "票价"
}
```

### 4. 启动Appium
```bash
# Windows
start_appium.bat

# macOS/Linux
appium --address 127.0.0.1 --port 4723 --allow-cors
```

### 5. 运行GUI
```bash
python damai_smart_ai.py
```

---

## 📱 使用指南

### GUI操作流程

1. **连接设备**
   - 点击"刷新设备"检测已连接设备
   - 或手动输入ADB端口
   - 点击"连接设备"

2. **配置抢票参数**
   - 填写演出关键词
   - 选择城市
   - 设置日期、票价等

3. **开始抢票**
   - 点击"开始抢票"
   - 观察日志输出
   - 等待流程完成

### 命令行使用

```python
from damai_appium import DamaiBot, Config

# 加载配置
config = Config.from_file("damai_appium/config.jsonc")

# 创建Bot实例
bot = DamaiBot(config)

# 执行抢票
bot.run()
```

---

## 📂 项目结构

```
damai-jiaoben/
├── damai_appium/              # 核心库
│   ├── damai_app_v2.py       # 核心Bot (v2.0)
│   ├── config.py             # 配置管理
│   ├── device_manager.py     # 设备管理器
│   └── config.jsonc          # 配置文件
│
├── damai_smart_ai.py         # GUI主程序
├── connection_auto_fixer.py  # 连接自动修复
├── environment_checker.py    # 环境检查器
├── smart_wait.py             # 智能等待模块
│
├── pyproject.toml            # 项目配置
├── requirements.txt          # Python依赖
├── CHANGELOG.md              # 更新日志
└── README_VERSION.md         # 版本信息
```

### 核心文件说明

| 文件 | 大小 | 功能描述 |
|------|------|---------|
| `damai_app_v2.py` | 87KB | 核心Bot实现，包含完整抢票流程 |
| `damai_smart_ai.py` | 236KB | GUI主程序，提供图形化操作界面 |
| `connection_auto_fixer.py` | 21KB | 自动检测和修复连接问题 |
| `smart_wait.py` | 15KB | 智能等待策略优化 |
| `device_manager.py` | 4KB | 设备管理和检测 |

---

## 🔄 版本更新

### v2.1.0 (2025-11-17) - 当前版本

#### ✨ 新增功能
- 连接自动修复工具 - 自动检测和修复Appium/ADB/WebDriver连接
- 智能等待模块 - 优化等待策略，提升执行效率
- 简化版设备管理器 - 为GUI提供设备管理支持

#### 🗑️ 重大清理
- 删除83个废弃文件（约1.5MB）
- 删除未使用的v3.0模块（10个文件）
- 删除examples示例目录（25个脚本）
- 删除tests测试目录（8个文件）
- 删除archive归档目录（27个旧测试）

#### 🔧 架构优化
- 从v3.0回退到稳定的v2.0架构
- 核心代码从73个文件精简至8个文件
- 移除测试配置，简化项目结构

#### ✅ 测试验证
- 完整抢票流程测试通过（11步骤）
- 成功率: 100%
- 总耗时: 123.39秒

详细更新记录请查看 [CHANGELOG.md](./CHANGELOG.md)

---

## 🎯 测试状态

| 测试步骤 | 状态 | 耗时 | 成功率 |
|---------|------|------|--------|
| 启动大麦App | ✅ | 7.89s | 100% |
| 处理首页弹窗 | ✅ | 3.43s | 100% |
| 城市切换 | ✅ | 16.35s | 100% |
| 打开搜索框 | ✅ | 9.85s | 100% |
| 搜索关键词 | ✅ | 12.00s | 100% |
| 点击搜索结果 | ✅ | 10.52s | 100% |
| 进入演出详情 | ✅ | 15.90s | 100% |
| 票档选择按钮 | ✅ | 4.42s | 100% |
| 立即抢票 | ✅ | 37.14s | 100% |
| 场次票档选择 | ✅ | 4.19s | 100% |
| 观演人处理 | ✅ | 1.70s | 100% |
| **总计** | **✅** | **123.39s** | **100%** |

---

## ⚙️ 高级配置

### 环境变量

```bash
# Android SDK路径
export ANDROID_HOME=/path/to/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME

# 添加到PATH
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools
```

### Appium配置

```bash
# 基础配置
appium --address 127.0.0.1 --port 4723 --allow-cors

# 高级配置（日志、性能优化）
appium --address 127.0.0.1 --port 4723 --allow-cors \
  --log-level info \
  --session-override \
  --relaxed-security
```

---

## 🐛 常见问题

### Q: 无法连接到设备
**A**: 运行环境检查器：
```bash
python environment_checker.py
```
或使用连接自动修复：
```bash
python connection_auto_fixer.py
```

### Q: OCR识别错误
**A**: OCR警告不影响核心功能，程序主要使用坐标点击。如需优化，请更新PaddleOCR版本。

### Q: WebDriver连接超时
**A**: 
1. 确保Appium Server正在运行
2. 检查端口4723是否被占用
3. 运行连接自动修复工具

---

## 📄 许可证

本项目仅供学习和研究使用，请勿用于商业用途。

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📞 联系方式

- GitHub: [@kk43994](https://github.com/kk43994)
- 项目地址: [damai-jiaoben](https://github.com/kk43994/damai-jiaoben)

---

**最后更新**: 2025-11-17 02:30  
**生成工具**: Claude Code  
**提交哈希**: 890b14e

---

## 📝 详细配置指南

### 配置文件说明

配置文件位于 `damai_appium/config.jsonc`，包含以下参数：

```jsonc
{
  // ===== 连接配置 =====
  "server_url": "http://127.0.0.1:4723",  // Appium服务器地址
  "adb_port": "54588",                     // ADB端口号（红手指云手机或模拟器）
  
  // ===== 演出信息 =====
  "keyword": "时间都去哪了",               // 演出关键词（必填）
  "city": "广州",                          // 演出城市（必填）
  "date": "12月21日",                      // 演出日期（可选）
  "price": "380",                          // 票价（可选）
  
  // ===== 购票配置 =====
  "users": ["张三", "李四"],              // 观演人列表（可选，不填则跳过）
  "price_index": 1,                        // 票价索引（从0开始，默认选择第1个）
  "if_commit_order": false                 // 是否自动提交订单（false=停在确认页）
}
```

### 参数详解

#### 1. server_url（Appium服务器地址）
- **默认值**: `http://127.0.0.1:4723`
- **说明**: Appium Server的访问地址
- **示例**: 
  - 本地: `http://127.0.0.1:4723`
  - 远程: `http://192.168.1.100:4723`

#### 2. adb_port（ADB端口）
- **默认值**: `54588`
- **说明**: Android设备的ADB端口号
- **获取方法**:
  ```bash
  # 查看已连接设备
  adb devices
  
  # 输出示例
  127.0.0.1:54588    device  # 这里的54588就是端口号
  ```
- **常见端口**:
  - 红手指云手机: `54588`, `58526`, `62726` 等
  - 雷电模拟器: `5555`, `5557`, `5559` 等
  - 夜神模拟器: `62001`
  - MuMu模拟器: `7555`

#### 3. keyword（演出关键词）
- **必填**: ✅
- **说明**: 在大麦App搜索框中输入的关键词
- **建议**: 使用演出名称或艺人名字
- **示例**:
  - `"周杰伦"`
  - `"五月天"`
  - `"时间都去哪了"`
  - `"德云社"`

#### 4. city（城市）
- **必填**: ✅
- **说明**: 演出所在城市
- **格式**: 中文城市名（不需要加"市"）
- **示例**:
  - `"北京"`
  - `"上海"`
  - `"广州"`
  - `"深圳"`
  - `"杭州"`

#### 5. date（日期）
- **可选**: 如果不填，会选择第一个可用日期
- **格式**: `"MM月DD日"` 或 `"星期X"`
- **示例**:
  - `"12月21日"`
  - `"1月1日"`
  - `"星期六"`

#### 6. price（票价）
- **可选**: 如果不填，会选择配置的price_index
- **格式**: 纯数字或带"元"
- **示例**:
  - `"380"`
  - `"680元"`
  - `"1280"`

#### 7. price_index（票价索引）
- **默认值**: `1`
- **说明**: 当price未设置时，按索引选择票档（从0开始）
- **示例**:
  - `0` - 选择第1档票价
  - `1` - 选择第2档票价
  - `2` - 选择第3档票价

#### 8. users（观演人列表）
- **可选**: 不填则跳过观演人选择
- **格式**: 字符串数组
- **说明**: 会按顺序选择观演人
- **示例**:
  ```jsonc
  "users": ["张三", "李四", "王五"]
  ```

#### 9. if_commit_order（是否提交订单）
- **默认值**: `false`
- **说明**: 
  - `false` - 停在订单确认页，需要手动提交
  - `true` - 自动点击提交订单（请谨慎使用！）

---

## 🔧 环境配置详细步骤

### Windows环境

#### 1. 安装Python
1. 下载Python 3.9+: https://www.python.org/downloads/
2. 安装时勾选 "Add Python to PATH"
3. 验证安装:
   ```cmd
   python --version
   ```

#### 2. 安装Android SDK
1. 下载Android Studio: https://developer.android.com/studio
2. 安装Android SDK
3. 配置环境变量:
   ```cmd
   # 系统环境变量
   ANDROID_HOME=C:\Users\你的用户名\AppData\Local\Android\Sdk
   ANDROID_SDK_ROOT=%ANDROID_HOME%
   
   # 添加到PATH
   %ANDROID_HOME%\platform-tools
   %ANDROID_HOME%\tools
   ```
4. 验证ADB:
   ```cmd
   adb version
   ```

#### 3. 安装Node.js和Appium
1. 下载Node.js 20.19.0+: https://nodejs.org/
2. 安装Appium:
   ```cmd
   npm install -g appium
   appium --version
   ```
3. 安装UiAutomator2驱动:
   ```cmd
   appium driver install uiautomator2
   ```

#### 4. 连接设备
**真机连接**:
1. 手机开启USB调试
2. 连接USB线
3. 验证: `adb devices`

**模拟器连接**:
1. 启动模拟器（雷电/夜神/MuMu）
2. 验证: `adb devices`

**红手指云手机**:
1. 在红手指控制台查看ADB端口
2. 连接: `adb connect 127.0.0.1:端口号`
3. 验证: `adb devices`

---

### macOS/Linux环境

#### 1. 安装Homebrew（仅macOS）
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. 安装依赖
```bash
# macOS
brew install python@3.9
brew install node
brew install --cask android-platform-tools

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip nodejs npm adb

# Linux (CentOS/RHEL)
sudo yum install python3 python3-pip nodejs npm android-tools
```

#### 3. 安装Appium
```bash
npm install -g appium
appium driver install uiautomator2
```

#### 4. 配置Android SDK
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export ANDROID_HOME=$HOME/Android/Sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export PATH=$PATH:$ANDROID_HOME/platform-tools
export PATH=$PATH:$ANDROID_HOME/tools

# 重新加载配置
source ~/.bashrc  # 或 source ~/.zshrc
```

---

## 🎮 使用场景示例

### 场景1: 本地Android手机抢票

1. **连接手机**
   ```bash
   adb devices  # 确认设备已连接
   ```

2. **启动Appium**
   ```bash
   appium
   ```

3. **配置config.jsonc**
   ```jsonc
   {
     "server_url": "http://127.0.0.1:4723",
     "adb_port": "设备序列号",  // 从 adb devices 获取
     "keyword": "周杰伦演唱会",
     "city": "北京",
     "date": "12月31日",
     "price": "680"
   }
   ```

4. **运行GUI**
   ```bash
   python damai_smart_ai.py
   ```

---

### 场景2: 红手指云手机抢票

1. **获取云手机信息**
   - 登录红手指控制台
   - 查看ADB连接端口（例如: 54588）

2. **连接云手机**
   ```bash
   adb connect 127.0.0.1:54588
   adb devices  # 确认连接成功
   ```

3. **配置config.jsonc**
   ```jsonc
   {
     "server_url": "http://127.0.0.1:4723",
     "adb_port": "54588",  // 红手指提供的端口
     "keyword": "五月天",
     "city": "上海"
   }
   ```

4. **启动抢票**
   ```bash
   # 启动Appium
   start_appium.bat
   
   # 启动GUI
   python damai_smart_ai.py
   ```

---

### 场景3: 模拟器批量测试

1. **启动多个模拟器实例**
   ```bash
   # 雷电模拟器
   # 实例1: 端口5555
   # 实例2: 端口5557
   
   adb devices
   # 输出:
   # 127.0.0.1:5555    device
   # 127.0.0.1:5557    device
   ```

2. **为每个实例创建配置**
   ```bash
   # config_instance1.jsonc
   {
     "server_url": "http://127.0.0.1:4723",
     "adb_port": "5555",
     "keyword": "演出A"
   }
   
   # config_instance2.jsonc
   {
     "server_url": "http://127.0.0.1:4724",  // 注意端口不同
     "adb_port": "5557",
     "keyword": "演出B"
   }
   ```

3. **启动多个Appium实例**
   ```bash
   # 终端1
   appium --port 4723
   
   # 终端2
   appium --port 4724
   ```

---

## 🛠️ 故障排除

### 问题1: adb devices不显示设备

**解决方案**:
```bash
# 1. 重启ADB服务
adb kill-server
adb start-server

# 2. 检查驱动（Windows）
# - 打开设备管理器
# - 查看是否有未识别设备
# - 更新驱动程序

# 3. 检查USB调试（真机）
# - 手机设置 > 开发者选项 > USB调试（开启）
# - 手机设置 > 开发者选项 > USB安装（开启）
```

---

### 问题2: Appium连接超时

**解决方案**:
```bash
# 1. 检查Appium是否运行
netstat -ano | findstr "4723"  # Windows
lsof -i :4723                  # macOS/Linux

# 2. 检查防火墙
# - 允许4723端口通过防火墙

# 3. 使用连接自动修复工具
python connection_auto_fixer.py
```

---

### 问题3: 大麦App无法启动

**解决方案**:
```bash
# 1. 手动安装大麦App
adb install damai.apk

# 2. 检查App包名
adb shell pm list packages | grep damai
# 应该显示: package:cn.damai

# 3. 手动启动测试
adb shell am start -n cn.damai/.MainActivity
```

---

### 问题4: OCR识别大量报错

**说明**: OCR报错不影响核心功能，程序主要使用坐标点击。

**可选优化**:
```bash
# 升级PaddleOCR
pip install --upgrade paddleocr paddlepaddle

# 或禁用OCR（修改代码）
# 在 damai_smart_ai.py 中注释掉OCR相关代码
```

---

## 📚 更多资源

- [详细更新日志](./CHANGELOG.md)
- [版本信息](./README_VERSION.md)
- [项目Wiki](https://github.com/kk43994/damai-jiaoben/wiki)（待建）

---

**配置文档更新时间**: 2025-11-17 02:35
