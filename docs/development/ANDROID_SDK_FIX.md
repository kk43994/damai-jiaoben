# Android SDK 环境变量问题修复指南

## 问题描述

在使用Appium连接设备时,出现以下错误:
```
Neither ANDROID_HOME nor ANDROID_SDK_ROOT environment variable was exported.
```

## 问题原因

Appium服务器在启动时没有继承`ANDROID_HOME`和`ANDROID_SDK_ROOT`环境变量,导致UiAutomator2驱动无法找到Android SDK。

## 解决方案

### 方案1: 使用提供的启动脚本(推荐)

直接双击运行 `start_appium.bat` 脚本,该脚本会:
1. 自动设置`ANDROID_HOME`和`ANDROID_SDK_ROOT`环境变量
2. 检查ADB连接状态
3. 启动Appium服务器

**使用步骤:**
1. 关闭当前运行的Appium服务器(如果有)
2. 双击运行 `start_appium.bat`
3. 保持窗口打开
4. 在GUI中点击"连接设备"

### 方案2: 手动在命令行启动

在命令提示符(CMD)中执行以下命令:

```cmd
set ANDROID_HOME=C:\Users\zhouk\AppData\Local\Android\Sdk
set ANDROID_SDK_ROOT=C:\Users\zhouk\AppData\Local\Android\Sdk
appium --address 127.0.0.1 --port 4723 --allow-cors
```

### 方案3: 设置系统环境变量(永久方案)

1. 右键"此电脑" → 属性 → 高级系统设置
2. 点击"环境变量"
3. 在"系统变量"中添加:
   - 变量名: `ANDROID_HOME`
   - 变量值: `C:\Users\zhouk\AppData\Local\Android\Sdk`
4. 添加第二个变量:
   - 变量名: `ANDROID_SDK_ROOT`
   - 变量值: `C:\Users\zhouk\AppData\Local\Android\Sdk`
5. 点击"确定"保存
6. **重启电脑**(或重启所有命令行和Appium Desktop)
7. 重新启动Appium服务器

## 代码修复

已修复以下文件,确保程序自动启动Appium时会传递环境变量:

1. `environment_checker.py` - 环境检查器启动Appium的逻辑
2. `auto_fix_webdriver.py` - WebDriver自动修复工具启动Appium的逻辑

修复内容: 在调用`subprocess.Popen`启动Appium时,添加`env`参数传递包含Android SDK路径的环境变量。

## 验证修复

启动Appium后,在GUI中点击"连接设备",如果看到以下日志,说明问题已解决:
```
[步骤5/5] 初始化Appium连接...
  - 正在创建WebDriver会话...
✓ 连接成功!
```

## 故障排查

如果问题仍然存在:

1. 确认Android SDK路径是否正确:
   ```cmd
   dir C:\Users\zhouk\AppData\Local\Android\Sdk\platform-tools
   ```
   应该能看到 `adb.exe`

2. 检查Appium是否使用了正确的环境变量:
   - 查看Appium启动日志
   - 确认ADB设备已连接: `adb devices`

3. 确保没有其他Appium实例在运行:
   ```cmd
   tasklist | findstr node.exe
   ```

4. 重启Appium服务器并重试

## 相关文件

- `start_appium.bat` - Appium启动脚本
- `environment_checker.py` - 环境检查和自动修复
- `auto_fix_webdriver.py` - WebDriver连接自动修复
- `damai_gui.py` - GUI主程序

## 注意事项

- 使用 `start_appium.bat` 启动时,请保持窗口打开
- 如果更改了Android SDK安装路径,需要修改脚本中的路径
- GUI程序的"自动修复"功能现在会自动设置环境变量
