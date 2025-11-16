# 抢票流程重构 V5 - 完整流程修复

## 修复时间
2025-11-15

## 问题描述

根据用户反馈,之前的抢票流程缺少了一个关键步骤:

**旧流程(错误)**:
1. 首页 → 点击搜索框
2. 搜索页 → 输入关键词搜索
3. **搜索结果页 → 直接点击目标演出名称** ❌ (跳过了一步)
4. 详情页 → 点击购买按钮

**问题**: 在搜索结果页(RESULT)显示的是多个不同演出,需要先点击第一个搜索结果进入特定演出的列表页(LIST),然后才能选择场次进入详情页(DETAIL)。

## 用户反馈原文

> "点击搜索框都是成功的第一次是正常输入了乌龙山伯爵 后面点击搜索框后没有点击第一个搜索结果 抢票流程还是有bug"
>
> "目前来说首页确认没有问题了 输入框正常点击也没有问题 点击输入框之后应该是搜索关键词 搜索关键词之后点击第一个搜索结果 点击搜索结果之后会进入到来演出列表页 演出列表页点击第一个最关联的演出 应该是这样的流程"
>
> "然后点击第一个相关演出后 应该是底下有一个橙色的按钮 方位我应该告诉过你了 点击之后才是选座界面"

## 解决方案

### 1. 新增页面状态: PageState.LIST

在 `damai_smart_ai.py` line 135-149:

```python
class PageState:
    """页面状态识别"""
    UNKNOWN = "未知"
    NOT_STARTED = "App未启动"
    LOADING = "加载中"
    HOME = "首页"
    SEARCH = "搜索页"
    RESULT = "搜索结果"
    LIST = "演出列表"  # 新增:点击搜索结果后的演出列表页
    DETAIL = "演出详情"
    SEAT = "选座页"
    ORDER = "订单页"
    # ...
```

### 2. 增强页面状态检测逻辑

在 `detect_page_state()` 方法中添加 LIST 页面检测 (line 289-304):

```python
# 5. 详情页 (有明确的购买/购票按钮) - 最高优先级
if any(keyword in text_str for keyword in ['立即购买', '立即预订', '立即抢购', '特惠选座', '选座购买']):
    return PageState.DETAIL
elif '演出详情' in text_str or '选择场次' in text_str:
    return PageState.DETAIL

# 6. 演出列表页 (点击搜索结果后,显示该演出的多个场次)
# 特征:有多个时间/场次,但没有"立即购买"按钮
elif '场次' in text_str or '剩余' in text_str or ('¥' in text_str and '演出' in text_str):
    # 如果没有立即购买等按钮,说明是列表页而不是详情页
    if not any(btn in text_str for btn in ['立即购买', '立即预订', '立即抢购']):
        return PageState.LIST

# 7. 搜索结果页 (搜索后的第一个页面,显示多个演出)
elif '搜索结果' in text_str or (len([t for t in texts if any(k in t['text'] for k in ['演出', '场馆', '时间'])]) > 3):
    return PageState.RESULT
```

**区分逻辑**:
- **RESULT 搜索结果页**: 多个不同的演出(乌龙山伯爵、其他演出...)
- **LIST 演出列表页**: 同一个演出的多个场次(有"场次"、"剩余"、价格信息,但没有"立即购买"按钮)
- **DETAIL 演出详情页**: 单个场次的详情(有"立即购买"等按钮)

### 3. 新增方法: `_click_first_search_result()`

位置: line 2974-3039

功能: 在搜索结果页(RESULT)点击第一个搜索结果,进入演出列表页(LIST)

```python
def _click_first_search_result(self, driver):
    """点击第一个搜索结果,进入演出列表页

    在搜索结果页(RESULT)点击第一个结果,进入该演出的列表页(LIST)
    """
    self.log("=== 点击第一个搜索结果 ===", "STEP")

    # 方法1: 查找第一个可点击的TextView(通常是演出标题)
    # - 跳过顶部200像素内的元素(标题栏)
    # - 找到第一个有文字且可见的TextView并点击

    # 方法2: 使用坐标点击屏幕中上部区域
    # - 坐标: (540, 350) - 第一个搜索结果的典型位置
```

### 4. 新增方法: `_click_first_show_in_list()`

位置: line 3041-3137

功能: 在演出列表页(LIST)点击第一个相关演出,进入详情页(DETAIL)

```python
def _click_first_show_in_list(self, driver, keyword):
    """在演出列表页点击第一个相关演出

    在演出列表页(LIST)点击第一个与关键词相关的演出,进入详情页(DETAIL)

    Args:
        keyword: 演出关键词(用于验证)
    """
    self.log(f"=== 在列表页点击第一个相关演出: '{keyword}' ===", "STEP")

    # 方法1: 查找包含关键词的TextView
    # - 使用关键词前3个字进行匹配
    # - 排除顶部标题栏

    # 方法2: 点击第一个演出项(不管是否包含关键词)

    # 方法3: 使用坐标点击 (540, 400)
```

### 5. 重构抢票主流程

在 `start_grab_ticket()` 方法中 (line 1825-1863):

**新流程**:
```
步骤1-4: (保持不变)首页确认、点击搜索框、输入关键词

步骤5: 点击第一个搜索结果 ✨ 新增
  └─ 调用 _click_first_search_result(driver)

步骤6: 验证进入演出列表页(LIST) ✨ 新增
  └─ _verify_page_state(driver, PageState.LIST, ...)
  └─ 如果直接进入详情页,跳过步骤7

步骤7: 在列表页点击第一个相关演出 ✨ 新增
  └─ 调用 _click_first_show_in_list(driver, show_name)

步骤8: 验证进入详情页(DETAIL) ✨ 修改(原步骤6)
  └─ _verify_page_state(driver, PageState.DETAIL, ...)

步骤9: 点击购买按钮 (原步骤7)

步骤10: 保存截图 (原步骤8)
```

## 关键代码片段

### 流程代码 (line 1825-1863)

```python
# 步骤5: 点击第一个搜索结果(进入演出列表页)
self.log("="*60, "STEP")
self.log("[步骤5] 点击第一个搜索结果", "STEP")
self._click_first_search_result(driver)

# 步骤6: 验证进入演出列表页
self.log("="*60, "STEP")
self.log("[步骤6] 验证进入演出列表页", "STEP")
success, page_state, texts = self._verify_page_state(
    driver,
    PageState.LIST,
    "进入演出列表页",
    timeout=10
)

if not success:
    self.log(f"未进入演出列表页,当前: {page_state}", "WARN")
    # 可能直接进入了详情页,继续执行
    if page_state == PageState.DETAIL:
        self.log("已直接进入详情页,跳过列表页步骤", "INFO")
        is_detail = True
    else:
        raise Exception(f"点击搜索结果后状态异常: {page_state}")
else:
    # 步骤7: 在演出列表页点击第一个相关演出
    self.log("="*60, "STEP")
    self.log("[步骤7] 点击第一个相关演出", "STEP")
    self._click_first_show_in_list(driver, show_name)

    # 步骤8: 等待详情页
    self.log("="*60, "STEP")
    self.log("[步骤8] 等待进入详情页", "STEP")
    success, page_state, texts = self._verify_page_state(
        driver,
        PageState.DETAIL,
        "进入详情页",
        timeout=10
    )
    is_detail = success
```

## 新流程图

```
┌─────────┐
│  首页   │
│ (HOME)  │
└────┬────┘
     │ 点击搜索框
     ▼
┌─────────┐
│ 搜索页  │
│(SEARCH) │
└────┬────┘
     │ 输入关键词并搜索
     ▼
┌──────────┐
│搜索结果页│ ← 显示多个不同演出
│ (RESULT) │
└────┬─────┘
     │ ✨ 点击第一个搜索结果 (新增步骤)
     ▼
┌──────────┐
│演出列表页│ ← 显示该演出的多个场次
│  (LIST)  │   (场次、剩余票数、价格)
└────┬─────┘
     │ ✨ 点击第一个相关演出 (新增步骤)
     ▼
┌──────────┐
│演出详情页│ ← 单个场次的详细信息
│ (DETAIL) │   (立即购买按钮)
└────┬─────┘
     │ 点击购买按钮
     ▼
┌──────────┐
│  选座页  │
│  (SEAT)  │
└──────────┘
```

## 健壮性改进

### 1. 多种点击策略

每个新方法都实现了3种点击策略,依次尝试:

**`_click_first_search_result()`**:
1. 方法1: 查找第一个有效的TextView并点击
2. 方法2: 使用坐标点击 (540, 350)
3. 如果都失败,抛出异常

**`_click_first_show_in_list()`**:
1. 方法1: 查找包含关键词的TextView
2. 方法2: 点击第一个有效的演出项
3. 方法3: 使用坐标点击 (540, 400)

### 2. 页面状态验证

在每个关键步骤后都验证页面状态:
- 搜索后 → 验证RESULT页
- 点击搜索结果后 → 验证LIST页
- 点击演出后 → 验证DETAIL页

### 3. 容错处理

```python
if not success:
    self.log(f"未进入演出列表页,当前: {page_state}", "WARN")
    # 可能直接进入了详情页,继续执行
    if page_state == PageState.DETAIL:
        self.log("已直接进入详情页,跳过列表页步骤", "INFO")
        is_detail = True
    else:
        raise Exception(f"点击搜索结果后状态异常: {page_state}")
```

如果点击搜索结果后直接进入了详情页(某些演出可能只有一个场次),会跳过列表页步骤继续执行。

### 4. 详细日志

每个步骤都有明确的日志输出:
```
============================================================
[步骤5] 点击第一个搜索结果
=== 点击第一个搜索结果 ===
方法1: 查找第一个演出标题...
找到第一个搜索结果: '乌龙山伯爵...'
✓ 点击成功
============================================================
[步骤6] 验证进入演出列表页
...
```

## 测试验证

### 语法检查
```bash
python -m py_compile damai_smart_ai.py
```
✅ 通过

### 预期执行流程

1. **首页** → 检测到"首页"/"发现"/"我的"
2. **点击搜索框** → 进入搜索页,检测到EditText输入框
3. **输入关键词** → 输入"乌龙山伯爵"并搜索
4. **搜索结果页** → 检测到多个演出项
5. **点击第一个结果** → 点击"乌龙山伯爵"
6. **演出列表页** → 检测到"场次"/"剩余"/价格,但没有"立即购买"
7. **点击第一个演出** → 选择第一个场次
8. **演出详情页** → 检测到"立即购买"按钮
9. **点击购买按钮** → 进入选座页
10. **保存截图** → 完成

## 文件变更

### damai_smart_ai.py

| 行号 | 变更类型 | 说明 |
|------|---------|------|
| 143 | 新增 | `LIST = "演出列表"` 页面状态 |
| 289-304 | 修改 | 增强 `detect_page_state()` - 添加LIST页检测逻辑 |
| 2974-3039 | 新增 | `_click_first_search_result()` 方法 |
| 3041-3137 | 新增 | `_click_first_show_in_list()` 方法 |
| 1825-1863 | 重构 | 抢票主流程 - 添加步骤5-8 |
| 1866-1869 | 修改 | 步骤编号调整为9-10 |

## 向后兼容

- 保留了原有的 `_click_target_show()` 方法,未删除
- 如果某些演出直接进入详情页,会自动跳过列表页步骤
- 页面状态检测的优先级经过精心设计,不会误判

## 下一步

1. **实际测试**: 在真实设备上运行完整流程
2. **弹窗处理**: 确保在每个步骤都能正确处理弹窗
3. **性能优化**: 根据测试结果调整等待时间和重试策略
4. **日志分析**: 观察实际执行时的页面状态检测准确性

## 修复人员

Claude Code (Sonnet 4.5)

## 用户确认

待用户测试确认流程是否符合实际App行为。
