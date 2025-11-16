# 搜索框点击问题修复方案

**问题**: 抢票流程卡在搜索框这一步
**原因**: 搜索框坐标可能不准确或页面元素查找失败

---

## 快速修复方法

### 方法1: 使用固定坐标（最快）

当前代码在 `damai_smart_ai.py` line 3230 有一个搜索框坐标：
```python
SEARCH_ENTRY_COORD = (315, 97)  # 搜索入口坐标
```

**您说的坐标是 339.99**，需要修改为：
```python
SEARCH_ENTRY_COORD = (340, 100)  # 修改后的坐标
```

### 方法2: 在GUI中手动点击搜索框

1. 在GUI监控界面中，看到大麦App首页
2. 手动点击搜索框激活它
3. 然后让脚本继续

### 方法3: 使用坐标管理器（推荐）

如果有 `coordinates.json` 文件，可以在其中配置：
```json
{
  "search_box": {
    "x": 340,
    "y": 100,
    "description": "首页搜索框"
  }
}
```

---

## 详细修复步骤

### 步骤1: 确定正确的搜索框坐标

在GUI中：
1. 连接设备并开始监控
2. 在大麦App首页，移动鼠标到搜索框
3. 查看GUI底部显示的坐标
4. 记录这个坐标（例如: 340, 100）

### 步骤2: 修改代码

找到 `damai_smart_ai.py` 中的 `_goto_search_page` 函数（约在 line 3223），修改坐标：

**修改前**:
```python
SEARCH_ENTRY_COORD = (315, 97)  # 搜索入口坐标
```

**修改后**:
```python
SEARCH_ENTRY_COORD = (340, 100)  # 修改为正确坐标
```

### 步骤3: 增加重试逻辑

在坐标点击部分增加日志输出，方便调试：

```python
# 坐标兜底 - 优先使用手动教学验证的坐标
if attempt == 1:  # 第2次尝试用坐标
    self.log(f"尝试使用坐标点击: {SEARCH_ENTRY_COORD}", "WARN")
    coords_to_try = [
        SEARCH_ENTRY_COORD,  # 手动验证的坐标(优先)
        (340, 100),  # 备用坐标1
        (360, 100),  # 备用坐标2
        (300, 100),  # 备用坐标3
    ]
```

---

## 临时解决方案

如果不想修改代码，可以：

1. **停止当前抢票**（点击"停止抢票"按钮）
2. **手动在设备上点击搜索框**
3. **输入关键词"2025黎明"**
4. **手动点击搜索**
5. **让脚本从步骤5继续**

---

## 调试技巧

### 1. 检查当前页面
```python
# 在日志中查看
page_source = driver.page_source
print("搜索框" in page_source)
```

### 2. 尝试多个定位方式

当前代码已经尝试了多种方式：
- ID: `cn.damai:id/homepage_header_search_layout`
- ID: `cn.damai:id/home_search_btn`
- UiSelector: 文本包含"搜索"
- 坐标点击

### 3. 截图保存
在点击前后保存截图，对比分析：
```python
driver.get_screenshot_as_file("before_click.png")
# 点击操作
driver.get_screenshot_as_file("after_click.png")
```

---

## 建议的完整修复代码

我可以帮您修改 `_goto_search_page` 函数，添加更robust的坐标点击逻辑。
需要我现在修改吗？

---

## 当前状态说明

从日志看：
```
[21:17:10.612] [STEP] === 点击搜索框 ===
```

程序已经进入搜索框点击步骤，但可能：
1. 元素查找失败
2. 坐标点击失败
3. 页面加载未完成

**建议**: 先使用方法1修改坐标为 `(340, 100)`，然后重新运行。
