# 📥 依赖下载指南

> **版本**: v2.2
> **更新日期**: 2025-11-17

---

## 🎯 两种获取方式

### 方式一：自动下载脚本（推荐）⭐

**优点**：
- ✅ 一键自动下载所有组件
- ✅ 自动解压到正确位置
- ✅ 无需手动操作
- ✅ 适合网络条件好的用户

**使用方法**：
1. 双击运行 `scripts\自动下载依赖.bat`
2. 等待下载完成（约5-15分钟，取决于网速）
3. 下载完成后，运行 `scripts\一键配置.bat`

**下载内容**：
- Python 3.11 便携版 (~25MB)
- Node.js 20.x 便携版 (~50MB)
- Android SDK Platform Tools (~10MB)
- Appium Settings APK (~5MB)
- UIAutomator2 Server APK (~2MB)

**总下载量**: 约 90-100MB

---

### 方式二：手动下载清单

**优点**：
- ✅ 可选择国内镜像源（更快）
- ✅ 可断点续传
- ✅ 适合网络不稳定的用户

---

## 📦 手动下载详细清单

### 1. Python 3.11 便携版

#### 官方下载
```
URL: https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
文件名: python-3.11.9-embed-amd64.zip
大小: ~25MB
```

#### 国内镜像（更快）
```
淘宝镜像:
https://registry.npmmirror.com/-/binary/python/3.11.9/python-3.11.9-embed-amd64.zip

华为镜像:
https://repo.huaweicloud.com/python/3.11.9/python-3.11.9-embed-amd64.zip
```

#### 安装步骤
1. 下载 `python-3.11.9-embed-amd64.zip`
2. 在项目根目录创建 `python-portable` 文件夹
3. 解压ZIP到 `python-portable\` 目录
4. 验证：`python-portable\python.exe` 文件存在

---

### 2. Node.js 20.x 便携版

#### 官方下载
```
URL: https://nodejs.org/dist/v20.11.1/node-v20.11.1-win-x64.zip
文件名: node-v20.11.1-win-x64.zip
大小: ~50MB
```

#### 国内镜像（更快）
```
淘宝镜像:
https://registry.npmmirror.com/-/binary/node/v20.11.1/node-v20.11.1-win-x64.zip

华为镜像:
https://repo.huaweicloud.com/nodejs/v20.11.1/node-v20.11.1-win-x64.zip
```

#### 安装步骤
1. 下载 `node-v20.11.1-win-x64.zip`
2. 解压ZIP
3. 将解压后的 `node-v20.11.1-win-x64` 文件夹重命名为 `nodejs-portable`
4. 移动到项目根目录
5. 验证：`nodejs-portable\node.exe` 文件存在

---

### 3. Android SDK Platform Tools

#### 官方下载
```
URL: https://dl.google.com/android/repository/platform-tools-latest-windows.zip
文件名: platform-tools-latest-windows.zip
大小: ~10MB
```

#### 国内镜像（更快）
```
AndroidDevTools:
https://www.androiddevtools.cn/

阿里云镜像:
https://mirrors.aliyun.com/android.googlesource.com/platform/prebuilts/fullsdk-windows/tools/
```

#### 安装步骤
1. 下载 `platform-tools-latest-windows.zip`
2. 在项目根目录创建 `android-sdk-tools` 文件夹
3. 解压ZIP到 `android-sdk-tools\` 目录
4. 验证：`android-sdk-tools\platform-tools\adb.exe` 文件存在

---

### 4. Appium Settings APK

#### 官方下载
```
GitHub Releases:
https://github.com/appium/io.appium.settings/releases

推荐版本: v5.0.0
直接下载:
https://github.com/appium/io.appium.settings/releases/download/v5.0.0/settings_apk-debug.apk

文件名: settings_apk-debug.apk
大小: ~5MB
```

#### 安装步骤
1. 下载 `settings_apk-debug.apk`
2. 重命名为 `appium-settings.apk`
3. 放到项目根目录
4. 验证：项目根目录有 `appium-settings.apk` 文件

---

### 5. UIAutomator2 Server APK

#### 官方下载
```
GitHub Releases:
https://github.com/appium/appium-uiautomator2-server/releases

推荐版本: v6.0.0
直接下载:
https://github.com/appium/appium-uiautomator2-server/releases/download/v6.0.0/appium-uiautomator2-server-v6.0.0.apk

文件名: appium-uiautomator2-server-v6.0.0.apk
大小: ~2MB
```

#### 安装步骤
1. 下载 `appium-uiautomator2-server-v6.0.0.apk`
2. 重命名为 `io.appium.uiautomator2.server.apk`
3. 放到项目根目录
4. 验证：项目根目录有 `io.appium.uiautomator2.server.apk` 文件

---

## 📂 最终目录结构

下载并解压后，项目目录应该是这样的：

```
ticket-purchase/
├── python-portable/              ← Python便携版
│   ├── python.exe
│   ├── python311.dll
│   └── ...
│
├── nodejs-portable/              ← Node.js便携版
│   ├── node.exe
│   ├── npm
│   └── ...
│
├── android-sdk-tools/            ← Android SDK工具
│   └── platform-tools/
│       ├── adb.exe
│       └── ...
│
├── appium-settings.apk           ← Appium Settings APK
├── io.appium.uiautomator2.server.apk  ← UIAutomator2 Server APK
│
├── scripts/                      ← 脚本目录
│   ├── 自动下载依赖.bat
│   ├── 一键配置.bat
│   ├── 一键启动.bat
│   └── 红手指配置.bat
│
└── damai_appium/                 ← 项目代码
    └── ...
```

---

## 🐍 Python依赖包安装

### 方式一：使用一键配置脚本（推荐）

完成上述组件下载后：
```batch
双击运行: scripts\一键配置.bat
```

脚本会自动执行：
```bash
python -m pip install -r requirements.txt
```

### 方式二：手动安装

```bash
# 方法1：使用pip直接安装
pip install -r requirements.txt

# 方法2：使用国内镜像源（更快）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 方法3：逐个安装
pip install appium-python-client==3.1.1
pip install paddleocr==2.7.3
pip install paddlepaddle==2.6.0
pip install opencv-python==4.8.1.78
pip install Pillow==10.1.0
```

### requirements.txt 内容

```txt
# Appium客户端
appium-python-client==3.1.1

# OCR识别
paddleocr==2.7.3
paddlepaddle==2.6.0

# 图像处理
opencv-python==4.8.1.78
Pillow==10.1.0

# 其他工具
requests>=2.31.0
```

---

## 🔧 Appium和驱动安装

### 方式一：使用一键配置脚本

```batch
双击运行: scripts\一键配置.bat
```

### 方式二：手动安装

```bash
# 1. 配置环境变量
set PATH=%CD%\nodejs-portable;%PATH%

# 2. 安装Appium（全局）
npm install -g appium

# 3. 安装UiAutomator2驱动
appium driver install uiautomator2

# 4. 验证安装
appium --version
appium driver list
```

### 使用国内镜像（更快）

```bash
# 配置npm使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 安装Appium
npm install -g appium

# 安装驱动
appium driver install uiautomator2
```

---

## ✅ 安装验证

### 运行环境检查器

```bash
python environment_checker.py
```

### 手动验证

```bash
# 验证Python
python --version
# 应输出: Python 3.11.9

# 验证Node.js
node --version
# 应输出: v20.11.1

# 验证npm
npm --version
# 应输出: 10.x.x

# 验证ADB
adb version
# 应输出: Android Debug Bridge version x.x.x

# 验证Appium
appium --version
# 应输出: 2.x.x

# 验证Appium驱动
appium driver list
# 应显示: uiautomator2@x.x.x [installed]
```

---

## 🌐 国内镜像源推荐

### Python镜像源

```bash
# 清华大学镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 阿里云镜像
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 中国科技大学镜像
pip config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple/
```

### npm镜像源

```bash
# 淘宝镜像（推荐）
npm config set registry https://registry.npmmirror.com

# 华为镜像
npm config set registry https://repo.huaweicloud.com/repository/npm/

# 腾讯镜像
npm config set registry https://mirrors.cloud.tencent.com/npm/
```

---

## ❓ 常见问题

### Q1: 下载速度很慢怎么办？

**A:** 使用国内镜像源：
- Python组件：使用淘宝镜像或华为镜像
- Node.js组件：使用淘宝镜像或华为镜像
- pip包：配置清华或阿里云镜像
- npm包：配置淘宝镜像

### Q2: GitHub下载APK很慢？

**A:** 使用镜像站：
```
GitHub镜像站:
https://ghproxy.com/
https://mirror.ghproxy.com/

使用方法：
将GitHub URL前缀改为镜像站地址
例如：
https://ghproxy.com/https://github.com/appium/io.appium.settings/releases/...
```

### Q3: 自动下载脚本失败？

**A:** 可能原因：
1. 网络连接问题 → 检查网络，使用手动下载
2. curl命令不可用 → 升级Windows 10或手动下载
3. 防火墙阻止 → 暂时关闭防火墙或添加白名单

### Q4: 解压失败？

**A:**
- 确保有足够磁盘空间（至少2GB）
- 使用管理员权限运行脚本
- 手动解压ZIP文件到对应目录

### Q5: pip install失败？

**A:** 常见解决方案：
```bash
# 1. 升级pip
python -m pip install --upgrade pip

# 2. 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 忽略SSL验证（不推荐，仅作为最后手段）
pip install -r requirements.txt --trusted-host pypi.tuna.tsinghua.edu.cn
```

### Q6: npm install -g appium失败？

**A:**
```bash
# 1. 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 2. 清除缓存
npm cache clean --force

# 3. 重新安装
npm install -g appium
```

---

## 📞 获取帮助

### 下载问题
- 查看本文档的国内镜像源部分
- 查看常见问题解答

### 安装问题
- 运行环境检查器：`python environment_checker.py`
- 查看：`docs/guides/完整安装教程_小白版.md`

### 配置问题
- 查看：`PORTABLE_PACKAGE_GUIDE.md`
- 查看：`docs/guides/详细使用教程_GUI操作指南.md`

---

## 🎉 下载完成后

运行以下脚本完成配置：

1. **首次配置**: `scripts\一键配置.bat`
2. **启动程序**: `scripts\一键启动.bat`
3. **红手指连接**: `scripts\红手指配置.bat`

详细使用教程请查看：`docs/guides/详细使用教程_GUI操作指南.md`

---

**📅 文档版本**: v2.2
**📝 更新日期**: 2025-11-17
**👤 维护者**: Claude Code
