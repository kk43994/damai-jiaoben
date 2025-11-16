# 快速开始指南

> 5分钟快速上手大麦抢票系统

---

## 📦 方式一：一键安装（推荐）

### Windows用户

1. **下载项目**
   - 访问：https://kk43994.github.io/damai-jiaoben/
   - 点击"下载完整源码包"

2. **解压到任意目录**
   ```
   例如：C:\damai-jiaoben\
   ```

3. **双击运行安装脚本**
   ```
   install_windows.bat
   ```

4. **按照提示完成安装**
   - 脚本会自动检测Python
   - 自动安装所有依赖
   - 自动创建配置文件

### macOS/Linux用户

1. **下载项目**
   ```bash
   # 克隆仓库
   git clone https://github.com/kk43994/damai-jiaoben.git
   cd damai-jiaoben

   # 或下载ZIP并解压
   wget https://github.com/kk43994/damai-jiaoben/archive/refs/heads/master.zip
   unzip master.zip
   cd damai-jiaoben-master
   ```

2. **运行安装脚本**
   ```bash
   chmod +x install_unix.sh
   ./install_unix.sh
   ```

3. **按照提示完成安装**

---

## 🎯 方式二：手动安装

### 1. 克隆项目
```bash
git clone https://github.com/kk43994/damai-jiaoben.git
cd damai-jiaoben
```

### 2. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 3. 创建配置文件
```bash
cp damai_appium/config.jsonc.example damai_appium/config.jsonc
```

### 4. 编辑配置文件
编辑 `damai_appium/config.jsonc`：
```jsonc
{
  "server_url": "http://127.0.0.1:4723",
  "adb_port": "54588",
  "keyword": "你要抢的演出名称",
  "city": "城市名",
  "date": "日期",
  "price": "票价"
}
```

---

## 🚀 开始使用

### 1. 连接设备

**查看已连接设备**
```bash
adb devices
```

**连接云手机（如红手指）**
```bash
adb connect 127.0.0.1:端口号
```

### 2. 启动Appium

**Windows**
```cmd
start_appium.bat
```

**macOS/Linux**
```bash
appium --address 127.0.0.1 --port 4723 --allow-cors
```

### 3. 运行GUI程序

```bash
python damai_smart_ai.py
```

### 4. 在GUI中操作

1. 点击"刷新设备"检测设备
2. 点击"连接设备"
3. 填写演出信息（或使用配置文件）
4. 点击"开始抢票"

---

## 💡 配置说明

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `keyword` | 演出关键词 | "周杰伦演唱会" |
| `city` | 城市 | "北京" |
| `adb_port` | ADB端口 | "54588" |

### 可选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `date` | 日期 | "12月31日" |
| `price` | 票价 | "680" |
| `users` | 观演人列表 | ["张三", "李四"] |
| `if_commit_order` | 自动提交订单 | false |

---

## 🔧 常见问题

### Q: 找不到ADB设备？
**A:** 运行环境检查：
```bash
python environment_checker.py
```

或使用自动修复：
```bash
python connection_auto_fixer.py
```

### Q: Appium连接失败？
**A:**
1. 确认Appium正在运行
2. 检查端口4723是否被占用
3. 运行连接自动修复工具

### Q: Python依赖安装失败？
**A:** 使用国内镜像：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 📚 更多帮助

- 📖 [完整文档](README.md)
- 📝 [更新日志](CHANGELOG.md)
- 💬 [问题反馈](https://github.com/kk43994/damai-jiaoben/issues)
- 🌐 [在线下载页](https://kk43994.github.io/damai-jiaoben/)

---

## 🎉 完成！

现在你已经可以开始抢票了！

**祝抢票顺利！** 🎫
