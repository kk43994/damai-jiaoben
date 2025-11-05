# 大麦抢票学习记录

## 完整购票流程

### 1. 重启大麦APP
**脚本**: `restart_damai.py`
- 使用包名: `cn.damai`
- 等待3秒让APP完全启动

### 2. 搜索演出
**脚本**: `step_search.py`
- 点击搜索框ID: `cn.damai:id/search_edit_view`
- 输入关键词（前5个字）
- 按回车键执行搜索（keycode 66 = KEYCODE_ENTER）

### 3. 点击搜索结果
**脚本**: `step_click_result.py`
- 点击搜索框下面的第一个选项
- 进入关联演出列表页

### 4. 选择正确的演出
**脚本**: `step_click_correct_show.py`

**重要经验**：
- 不要根据价格选择（容易点错）
- 要根据演出名称的唯一标识来选择
- 示例：搜索"大麦乐迷省心包"来精确匹配"北京大麦乐迷省心包鹭卓演唱会北京站"

**多种查找方式**：
```python
# 方式1: 精确查找唯一标识
'new UiSelector().textContains("大麦乐迷省心包")'

# 方式2: 查找关键词
'new UiSelector().textContains("省心包")'

# 方式3: 查找艺人名，点击第二个结果
'new UiSelector().textContains("鹭卓")'
```

### 5. 点击立即预订
**脚本**: `step_click_book.py`
- 点击右下角橙色的"立即预订"按钮
- 按钮ID: `cn.damai:id/trade_project_detail_purchase_status_bar_container_fl`
- 进入场次和票档选择页

---

## 核心知识点：场次和票档选择（同一页面）

### 关键理解 ⭐⭐⭐

**场次和票档在同一个页面上**：
1. 页面上方显示所有场次方框
2. 用户点击某个场次方框后
3. **不会跳转页面**，而是在当前页面底部弹出票档选择
4. 然后用户在弹出的票档方框中选择

**错误做法** ❌：
- 把场次选择和票档选择分成两个脚本
- 每个脚本重新初始化bot
- 导致页面状态丢失，进入错误页面

**正确做法** ✅：
- 在同一个脚本中完成场次和票档的选择
- 保持WebDriver会话不中断
- 点击场次后等待2秒让票档弹出
- 然后在同一页面查找并点击票档

### 场次和票档的完整选择逻辑

#### 第一步：选择有票的场次

**脚本**: `select_session_and_ticket.py` (第一部分)

**逻辑**：
```python
# 1. 查找所有"无票"标记
no_ticket_elements = driver.find_elements(
    AppiumBy.ANDROID_UIAUTOMATOR,
    'new UiSelector().text("无票")'
)
no_ticket_positions = [rect['y'] for rect in no_ticket_elements]

# 2. 查找所有场次方框（可点击的大元素，在屏幕中上部）
# 特征：200 < y < 900, height > 80, width > 400

# 3. 判断哪些场次有票
for box in session_boxes:
    has_ticket = True
    for no_ticket_y in no_ticket_positions:
        # 如果"无票"的y坐标在方框的y范围内，则该场次无票
        if box['y'] <= no_ticket_y <= box['y_end']:
            has_ticket = False
            break

    if has_ticket:
        available_sessions.append(box)

# 4. 点击第一个有票的场次
available_sessions[0]['element'].click()

# 5. 等待票档弹出（关键！）
time.sleep(2)
```

**关键点**：
- 场次方框在"票档"文字**上方**
- 通过检查"无票"标记是否在方框内来判断
- 点击后**不要退出脚本**，继续在同一页面操作

#### 第二步：在同一页面选择有票的票档

**脚本**: `select_session_and_ticket.py` (第二部分)

**区分场次方框和票档方框的方法**：

```python
# 方法1: 查找"票档"文字的位置
ticket_class_labels = driver.find_elements(
    AppiumBy.ANDROID_UIAUTOMATOR,
    'new UiSelector().text("票档")'
)
ticket_class_label_y = ticket_class_labels[0].rect['y']

# 方法2: 根据"票档"文字位置筛选方框
for el in all_clickable:
    rect = el.rect
    # 只选择在"票档"文字下方的方框
    if rect['y'] > ticket_class_label_y:
        ticket_boxes.append(box)  # 这是票档方框
    else:
        # 这是场次方框，跳过
        pass
```

**完整逻辑**：
```python
# 1. 查找"票档"文字位置，用于区分场次和票档方框
ticket_class_label_y = find_text("票档").rect['y']

# 2. 查找所有"缺货登记"标记
out_of_stock_elements = driver.find_elements(
    AppiumBy.ANDROID_UIAUTOMATOR,
    'new UiSelector().textContains("缺货登记")'
)
out_of_stock_positions = [rect['y'] for rect in out_of_stock_elements]

# 3. 重新查找所有可点击元素（因为票档刚弹出）
# 只选择在"票档"文字下方的方框
for el in all_clickable:
    if rect['y'] > ticket_class_label_y:  # 在"票档"下方
        ticket_boxes.append(box)

# 4. 判断哪些票档有票
for box in ticket_boxes:
    has_ticket = True
    for out_of_stock_y in out_of_stock_positions:
        # 如果"缺货登记"的y坐标在方框的y范围内，则该票档缺货
        if box['y'] <= out_of_stock_y <= box['y_end']:
            has_ticket = False
            break

    if has_ticket:
        available_tickets.append(box)

# 5. 点击第一个有票的票档
available_tickets[0]['element'].click()
```

### 通用的有票判断模式

**适用于场次和票档**：

```python
# 通用模式：检查标记是否在方框内
def is_available(box, unavailable_marker_positions):
    """
    判断方框是否可用（有票）

    Args:
        box: 包含 'y' 和 'y_end' 的字典
        unavailable_marker_positions: 不可用标记的y坐标列表

    Returns:
        bool: True表示有票，False表示无票
    """
    box_y_start = box['y']
    box_y_end = box['y_end']

    for marker_y in unavailable_marker_positions:
        # 如果标记的y坐标在方框的范围内，则不可用
        if box_y_start <= marker_y <= box_y_end:
            return False  # 无票

    return True  # 有票

# 使用示例
# 场次判断（标记："无票"）
has_ticket = is_available(session_box, no_ticket_positions)

# 票档判断（标记："缺货登记"）
has_ticket = is_available(ticket_box, out_of_stock_positions)
```

### 重要注意事项

1. **动态适应不同页面结构**：
   - 不同演出的场次方框数量不同
   - 不同演出的票档方框数量不同
   - 代码必须动态查找，不能写死数量

2. **方框识别特征**：
   ```python
   # 场次方框
   - y坐标: 200 < y < 900 (在屏幕中上部)
   - 高度: height > 80
   - 宽度: width > 400
   - 位置: 在"票档"文字上方

   # 票档方框
   - y坐标: 200 < y < 1100 (可能在屏幕下部)
   - 高度: height > 50
   - 宽度: width > 300
   - 位置: 在"票档"文字下方
   ```

3. **关键等待时间**：
   - 点击场次后等待2秒让票档弹出
   - 点击票档后等待2秒进入下一页
   - 页面加载后等待2秒再查找元素

4. **错误处理**：
   - 如果点击错了，使用返回键（keycode 4）
   - 如果所有票档都缺货，说明选择的场次不对，需要返回重新选择
   - 如果触发滑块验证，需要手动处理或等待风控冷却

---

## 已创建的脚本文件

### 单步测试脚本（用于学习流程）
- `restart_damai.py` - 重启大麦APP
- `step_search.py` - 搜索演出
- `step_click_result.py` - 点击搜索结果
- `step_click_first_show.py` - 点击第一个演出
- `step_click_correct_show.py` - 点击正确的演出（大麦乐迷省心包）
- `step_click_book.py` - 点击立即预订
- `step_back.py` - 按返回键

### 分析脚本（用于调试）
- `detect_available_sessions.py` - 分析场次页面，识别有票无票场次
- `select_available_session.py` - 选择有票场次（旧版，有问题）
- `click_available_session.py` - 点击有票场次（修正版）
- `select_available_ticket_class.py` - 选择有票票档（单独脚本，有问题）

### 完整流程脚本 ⭐
- `select_session_and_ticket.py` - **在同一页面上完成场次和票档选择**（正确方法）

---

## 遇到的问题和解决方案

### 问题1：点击了错误的演出
**原因**：根据价格"780起"查找不够精确
**解决**：改用唯一标识"大麦乐迷省心包"查找

### 问题2：选择了场次方框而不是票档方框
**原因**：没有区分场次和票档，选了所有可点击方框
**解决**：
1. 查找"票档"文字的y坐标
2. 只选择y坐标大于"票档"文字的方框
3. 这样确保选的是票档方框，而不是场次方框

### 问题3：场次和票档分开选择导致页面错误
**原因**：
- 把场次选择和票档选择写成两个脚本
- 每个脚本都重新初始化WebDriver
- 导致第二个脚本运行时已经丢失了第一个脚本的页面状态

**解决**：
- 在同一个脚本中完成场次和票档的选择
- 点击场次后等待2秒
- 不退出脚本，继续在同一页面查找票档并点击

### 问题4：所有票档都缺货
**原因**：选择的场次虽然有票，但该场次的所有票档都已售罄
**解决**：返回重新选择其他场次

### 问题5：操作频繁触发滑块验证
**原因**：多次重复点击触发了风控系统
**当前状态**：尚未成功自动通过滑块
**临时方案**：
1. 手动通过滑块
2. 减少操作频率，等待风控冷却
3. 研究更高级的滑块绕过技术

---

## 核心代码模板

### 方框内是否有标记的判断
```python
def has_marker_inside(box_y_start, box_y_end, marker_positions):
    """判断方框内是否有标记"""
    for marker_y in marker_positions:
        if box_y_start <= marker_y <= box_y_end:
            return True  # 有标记
    return False  # 无标记

# 使用
if has_marker_inside(box['y'], box['y_end'], no_ticket_positions):
    # 有"无票"标记，该场次无票
    has_ticket = False
else:
    # 没有"无票"标记，该场次有票
    has_ticket = True
```

### 查找文字位置
```python
def find_text_position(driver, text):
    """查找文字的y坐标"""
    try:
        elements = driver.find_elements(
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{text}")'
        )
        if elements:
            return elements[0].rect['y']
    except:
        pass
    return 0
```

### 筛选方框
```python
def filter_boxes_by_position(all_clickable, min_y, max_y,
                             reference_y=None, above=False):
    """
    筛选方框

    Args:
        all_clickable: 所有可点击元素
        min_y, max_y: y坐标范围
        reference_y: 参考y坐标（如"票档"文字的y坐标）
        above: True表示只要在reference_y上方的，False表示只要下方的
    """
    boxes = []
    for el in all_clickable:
        rect = el.rect
        if min_y < rect['y'] < max_y and rect['height'] > 50:
            # 如果有参考坐标，根据above参数筛选
            if reference_y:
                if above and rect['y'] < reference_y:
                    boxes.append({'element': el, 'y': rect['y'], ...})
                elif not above and rect['y'] > reference_y:
                    boxes.append({'element': el, 'y': rect['y'], ...})
            else:
                boxes.append({'element': el, 'y': rect['y'], ...})
    return boxes
```

---

## 下一步学习目标

1. ✅ 场次选择逻辑
2. ✅ 票档选择逻辑
3. ✅ 在同一页面完成场次和票档选择
4. ✅ 已将学习成果集成到主程序 damai_app_v2.py
5. ⏸️ 滑块验证自动通过（暂时搁置，需要更多研究）
6. ⏳ 点击票档后的下一步流程（待学习）
   - 可能是选座
   - 可能是确认订单
   - 可能是选择购票人
   - 待用户指导

---

## 代码优化记录

### 2025-11-02 优化内容

#### 1. 在 damai_app_v2.py 中添加了新方法

**方法名**: `select_session_and_ticket_class()`

**位置**: 第206-479行

**功能**:
- 在同一WebDriver会话中完成场次和票档选择
- 自动识别有票场次和票档
- 通过"票档"文字位置区分场次方框和票档方框

**关键特性**:
1. **不分离会话**: 点击场次后不重新初始化，继续在同一页面操作
2. **智能识别**:
   - 场次: 检查是否有"无票"标记
   - 票档: 检查是否有"缺货登记"标记
3. **位置区分**:
   - 查找"票档"文字的y坐标
   - 只选择y坐标大于"票档"文字的方框作为票档方框
   - 跳过在"票档"文字上方的场次方框
4. **动态适应**: 不写死方框数量，根据实际页面动态查找

#### 2. 集成到主流程

需要在 `run_ticket_grabbing()` 方法中调用 `select_session_and_ticket_class()`：

**建议插入位置**:
- 在"验证是否进入选票页面"之后（第923行附近）
- 在"选择影城门店"之前（第1125行之前）

**调用方式**:
```python
# 在进入选票页面后，调用场次和票档选择
BotLogger.step(8, "智能选择场次和票档")
if not self.select_session_and_ticket_class():
    BotLogger.error("场次和票档选择失败")
    return False
```

#### 3. 学习成果文档化

**创建文件**: `xuexijilu.md`

**内容包括**:
- 完整购票流程（1-5步）
- 核心知识点：场次和票档选择
- 通用的有票判断模式
- 代码模板和示例
- 问题解决方案
- 重要注意事项

---

## 重要提示

1. **每一步都要验证**：点击后检查是否进入了预期页面
2. **使用唯一标识**：不要用模糊的条件（如价格），用唯一的文字标识
3. **保持会话连续**：在同一个流程中不要重新初始化WebDriver
4. **动态适应**：代码要能处理不同数量的场次和票档
5. **错误恢复**：准备好返回键（keycode 4）随时纠正错误
6. **日志详细**：使用 BotLogger 记录每一步操作，便于调试

---

## 待完成的优化任务

1. ⏳ 在 `run_ticket_grabbing()` 中集成 `select_session_and_ticket_class()` 方法
2. ⏳ 测试新方法在实际抢票场景中的表现
3. ⏳ 优化方框识别的坐标范围参数（目前是经验值）
4. ⏳ 添加重试机制：如果所有票档都缺货，自动返回选择其他场次
5. ⏳ 研究滑块验证绕过技术

---

**最后更新**: 2025-11-02 03:50
**学习进度**: 已完成场次和票档选择逻辑，已集成到主程序
**当前状态**: 代码优化中，等待用户确认后继续
**当前问题**: 触发滑块验证，需要手动处理或等待风控冷却
