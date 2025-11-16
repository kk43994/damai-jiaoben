# 🧹 项目整理计划

> **创建时间**: 2025-11-17
> **目的**: 清理项目文件，整理归类，提升开发环境整洁度

---

## 📊 当前项目状态分析

### 文件统计

- **Markdown文档**: 71个（过多，需要归档）
- **截图文件**: 40+ PNG文件（临时调试截图）
- **Python模块**:
  - 核心模块: 11个（保留）
  - 废弃模块: 若干（需检查）
- **配置文件**: 多个临时配置文件
- **目录**: doc/, docs/, screenshots/, 页面样式/ 等

---

## 🎯 整理目标

1. ✅ **删除无用文件**（零风险项）
2. ✅ **归档历史文档**（开发过程文档）
3. ✅ **整理临时文件**（截图、配置、测试数据）
4. ✅ **重命名关键文件**（让文件名更清晰）
5. ✅ **创建规范目录结构**（便于后续维护）

---

## 📁 第1步：创建新的目录结构

### 新增目录

```
project-root/
├── docs/                      # 📚 所有文档（已存在，需整理）
│   ├── current/              # 当前版本文档（v2.2）
│   ├── development/          # 开发历史文档（归档）
│   ├── guides/               # 使用指南
│   └── api/                  # API文档
│
├── archive/                  # 🗄️ 归档文件
│   ├── screenshots/         # 历史截图
│   ├── configs/             # 历史配置
│   └── deprecated_code/     # 废弃代码
│
├── temp/                     # 🔧 临时文件（建议添加到.gitignore）
│   ├── debug/               # 调试文件
│   ├── test_data/           # 测试数据
│   └── screenshots/         # 临时截图
│
├── damai_appium/             # 📦 核心代码包（已存在）
├── tests/                    # ✅ 测试代码（如需要）
└── scripts/                  # 🛠️ 实用脚本
    ├── install_windows.bat
    └── start_appium.bat
```

**操作**:
```bash
mkdir -p archive/screenshots
mkdir -p archive/configs
mkdir -p archive/deprecated_code
mkdir -p temp/debug
mkdir -p temp/test_data
mkdir -p temp/screenshots
mkdir -p docs/current
mkdir -p docs/development
mkdir -p docs/guides
mkdir -p scripts
```

---

## 📝 第2步：整理Markdown文档（71个）

### 核心文档（保留在根目录）

**主要README**:
- ✅ `README.md` - 项目主README
- ✅ `QUICKSTART.md` - 快速开始指南
- ✅ `CHANGELOG.md` - 版本更新日志
- ✅ `CLAUDE.md` - Claude项目指令

**当前版本文档（移动到 docs/current/）**:
- ✅ `V2.2_USER_GUIDE.md` - v2.2用户指南
- ✅ `V2.2_FEATURES.md` - v2.2功能说明
- ✅ `V2.2_COMPLETION_SUMMARY.md` - v2.2完成总结
- ✅ `WEBDRIVER_HEALTH_MONITOR_GUIDE.md` - WebDriver健康监控指南
- ✅ `WEBDRIVER_AUTORECONNECT_COMPLETED.md` - WebDriver自动重连完成总结
- ✅ `FIRST_AID_TEST_GUIDE.md` - 急救箱测试指南
- ✅ `CONNECTION_OPTIMIZATION_COMPLETED.md` - 连接优化完成总结

**使用指南（移动到 docs/guides/）**:
- ✅ `GUI使用指南_重构版.md`
- ✅ `GUI测试指南_2025黎明南京.md`
- ✅ `快速启动指南_连接自动修复.md`
- ✅ `红手指使用指南.md`
- ✅ `红手指ADB端口_使用指南.md`
- ✅ `屏幕监控使用指南.md`
- ✅ `坐标方案使用指南.md`

### 开发历史文档（移动到 docs/development/）

**优化和修复总结**:
- `OPTIMIZATION_SUMMARY.md`
- `INTEGRATION_SUMMARY.md`
- `REFACTORING_SUMMARY.md`
- `SIMPLIFICATION_COMPLETE.md`
- `MONITOR_FIX_SUMMARY.md`
- `PAGE_DETECTION_FIX_SUMMARY.md`
- `GUI优化总结.md`
- `最终优化总结.md`
- `完善总结.md`
- `流程优化总结_健壮机制.md`
- `搜索功能修复总结.md`

**技术方案和修复文档**:
- `ANDROID_APP_SOLUTION.md`
- `ANDROID_SDK_FIX.md`
- `FIX_SEARCH_BOX.md`
- `FLOW_LOGIC_FIX.md`
- `FLOW_REFACTOR_V5.md`
- `UDID_SYNC_FIX.md`
- `WEBDRIVER_FIX_INTEGRATION.md`
- `WEBDRIVER_PAGE_STATE_FIX.md`
- `WEBDRIVER_OPTIMIZATION_GUIDE.md`
- `TICKET_FLOW_COORDS.md`
- `CONNECTION_OPTIMIZATION_PLAN.md`
- `GRAB_TICKET_OPTIMIZATION.md`
- `SMART_OPTIMIZATION_INTEGRATION.md`

**功能说明文档**:
- `ADB自动修复功能说明.md`
- `连接自动修复功能说明.md`
- `WEBDRIVER_检测按钮说明.md`
- `WebDriver检测按钮_快速指南.md`

**测试和交付文档**:
- `TEST_GUIDE.md`
- `TEST_REPORT_v4.md`
- `TEST_RESULTS.md`
- `测试报告.md`
- `测试报告_ADB自动修复.md`
- `完整流程测试指南.md`
- `今日交付总结.md`
- `客户交付说明.md`

**进度和学习文档**:
- `PROGRESS.md`
- `FIRST_AID_PROGRESS.md`
- `GITHUB_PAGES_UPDATE.md`
- `learning_log.md`
- `xuexijilu.md`
- `完整抢票流程_学习总结.md`

**集成指南**:
- `集成指南.md`
- `GUI_FAST_GRAB_INTEGRATION.md`
- `GUI_FAST_GRAB_COMPLETION.md`
- `流程恢复集成总结.md`
- `流程修复总结_v5.md`

**其他历史文档**:
- `README_VERSION.md`
- `README_抢票脚本.md`
- `USAGE_GUIDE.md` (已被v2.2指南替代)
- `方案可行性分析.md`
- `项目优化建议.md`
- `页面识别优化_基于真实截图.md`

### 可能删除的文档（重复或过时）

**需要确认是否删除**:
- `README_VERSION.md` - 如果内容已合并到CHANGELOG.md
- `README_抢票脚本.md` - 如果已被新README替代
- `xuexijilu.md` - 如果与learning_log.md重复

---

## 🖼️ 第3步：整理截图文件（40+ PNG）

### 临时调试截图（移动到 temp/screenshots/）

```
移动所有以下模式的文件到 temp/screenshots/:
- diagnose_*.png (诊断截图)
- grab_ticket_*.png (抢票截图)
- *uuid*.png (临时UUID命名的截图)
- test_*.png (测试截图)
- debug_*.png (调试截图)
- error_screenshot.png
- screen_current.png
- demo_final.png

具体文件列表:
- 28acd40a-06a6-41be-a495-b8bbd0af9953.png
- 6e429a41-e695-4f0e-a88e-807dd9e837a0.png
- 7ca997df-14f5-4a49-a359-0b0b98c5e548.png
- e673d7d2-121e-44f2-8f31-b621ff20d017.png
- ea0efdd3-0b69-451a-a131-b92a0ea8b865.png
- diagnose_首页_*.png (约12个)
- diagnose_演出列表_*.png (约4个)
- diagnose_未知_*.png (约2个)
- grab_ticket_*.png (约15个)
- test_screenshot_v2.png
- test_final_v3.png
- test_final_v4.png
- test_search_results_failed.png
- debug_homepage.png
- error_screenshot.png
- demo_final.png
- wulongshan_order.png
- C:UserszhoukDesktopticket-purchasescreen_current.png
```

### 文档用截图（移动到 docs/current/images/ 或保留）

```
可能需要保留的截图（用于文档说明）:
- api_detail_page.png
- api_search_results.png
- search_results_list.png
- detail_page_success.png
- search_北京_*.png
- search_广州_*.png
- search_温州_*.png

建议：
1. 检查这些截图是否在文档中被引用
2. 如果被引用，移动到 docs/current/images/
3. 如果未被引用，移动到 archive/screenshots/
```

---

## 📄 第4步：整理临时配置和数据文件

### 临时配置文件（移动到 temp/test_data/）

```
- devices.json (临时设备列表)
- last_config.json (上次配置缓存)
- coordinates.json (如果存在)
- current_page_source.xml (如果存在)
- debug_*.xml (如果存在)
- *.xml (除了coverage.xml)
```

### 保留的配置文件

```
✅ damai_appium/config.json - 核心配置
✅ damai_appium/config.jsonc - 带注释的配置模板
✅ damai_appium/test_devices.json - 测试设备配置（如果在用）
```

---

## 🐍 第5步：清理废弃的Python模块

### 检查根目录Git未跟踪的Python文件

根据git status，以下文件**未被git跟踪**，需要确认：

```python
# 在damai_appium/目录中，根据git status显示：
?? damai_appium/constants.py
?? damai_appium/damai_bot_refactored.py
?? damai_appium/element_finder.py
?? damai_appium/flow_recovery.py
?? damai_appium/navigation_helper.py
?? damai_appium/page_state_detector.py
?? damai_appium/popup_handler.py
?? damai_appium/ticket_selector.py
?? damai_appium/webdriver_manager.py
```

**建议处理方案**:

#### 可以安全删除的（v3.0废弃模块）:
```
根据之前的开发历史，这些是v3.0重构版本的模块，
项目已回退到v2.0稳定版本，因此可以移动到archive/deprecated_code/:

- damai_appium/constants.py
- damai_appium/damai_bot_refactored.py
- damai_appium/element_finder.py
- damai_appium/popup_handler.py
- damai_appium/navigation_helper.py
- damai_appium/ticket_selector.py
- damai_appium/page_state_detector.py
- damai_appium/flow_recovery.py
- damai_appium/webdriver_manager.py (部分功能已整合到health_monitor)
```

#### 保留的核心模块（v2.0 + 新增增强）:
```
✅ damai_appium/__init__.py
✅ damai_appium/config.py
✅ damai_appium/config_templates.py
✅ damai_appium/damai_app_v2.py - 核心Bot
✅ damai_appium/countdown_timer.py
✅ damai_appium/device_manager.py - 简化版设备管理
✅ damai_appium/error_handler.py
✅ damai_appium/fast_grabber.py - v2.2快速抢票
✅ damai_appium/sound_notifier.py
✅ damai_appium/ticket_strategy.py
✅ damai_appium/webdriver_health_monitor.py - 新增健康监控

根目录核心模块:
✅ connection_auto_fixer.py - 连接自动修复
✅ connection_first_aid.py - 连接急救箱
✅ damai_smart_ai.py - GUI主程序
✅ environment_checker.py - 环境检查
✅ smart_wait.py - 智能等待
```

---

## 📝 第6步：重命名文件以反映功能

### 建议重命名的文件

```bash
# 配置相关
damai_appium/config.jsonc → damai_appium/config.jsonc.example
  (更明确表示这是配置示例模板)

# 启动脚本移动
install_windows.bat → scripts/install_windows.bat
start_appium.bat → scripts/start_appium.bat
```

### 保持现有命名的文件

```
✅ damai_smart_ai.py - 已是清晰的GUI主程序名
✅ connection_auto_fixer.py - 清晰的功能命名
✅ connection_first_aid.py - 清晰的功能命名
✅ environment_checker.py - 清晰的功能命名
```

---

## 📚 第7步：更新项目文档

### 更新README.md

添加清晰的项目结构说明:

```markdown
## 📁 项目结构

```
ticket-purchase/
├── damai_smart_ai.py          # GUI主程序
├── damai_appium/              # 核心抢票模块
│   ├── damai_app_v2.py       # 抢票Bot核心
│   ├── fast_grabber.py       # 快速抢票功能
│   ├── webdriver_health_monitor.py  # WebDriver健康监控
│   └── ...
├── connection_auto_fixer.py   # 连接自动修复
├── connection_first_aid.py    # 连接急救箱
├── docs/                      # 📚 文档
│   ├── current/              # 当前版本文档
│   ├── development/          # 开发历史
│   └── guides/               # 使用指南
├── scripts/                   # 🛠️ 脚本
└── archive/                   # 🗄️ 归档文件
```
```

### 创建docs/README.md

创建文档索引:

```markdown
# 文档索引

## 📖 当前版本文档 (v2.2)

- [用户指南](current/V2.2_USER_GUIDE.md)
- [功能说明](current/V2.2_FEATURES.md)
- [WebDriver健康监控指南](current/WEBDRIVER_HEALTH_MONITOR_GUIDE.md)
- [急救箱测试指南](current/FIRST_AID_TEST_GUIDE.md)

## 📚 使用指南

- [GUI使用指南](guides/GUI使用指南_重构版.md)
- [快速启动指南](guides/快速启动指南_连接自动修复.md)
- [红手指使用指南](guides/红手指使用指南.md)

## 🔧 开发文档

参见 [development/](development/) 目录
```

---

## ⚠️ 安全检查清单

执行前务必确认:

- [ ] 所有被移动的Python文件都不在git跟踪中（未跟踪的才能安全移动）
- [ ] 核心模块（damai_app_v2.py等）保持不动
- [ ] README.md等核心文档保留在根目录
- [ ] 移动前先创建目标目录
- [ ] 配置文件（config.json）不被误删

---

## 🎯 执行顺序

1. ✅ 创建新目录结构
2. ✅ 移动Markdown文档到对应目录
3. ✅ 移动截图文件到temp/archive
4. ✅ 移动临时配置文件
5. ✅ 移动废弃Python模块到archive
6. ✅ 重命名必要文件
7. ✅ 更新README和文档索引
8. ✅ 验证项目可正常运行

---

## 📊 预期结果

### 清理前

```
根目录: 100+ 文件（混乱）
- 71个MD文档
- 40+ PNG截图
- 5个核心.py
- 若干临时配置
```

### 清理后

```
根目录: 约15个核心文件（清爽）
- 4个核心MD文档（README, QUICKSTART, CHANGELOG, CLAUDE）
- 5个核心.py模块
- damai_appium/ 核心代码包
- docs/ 所有文档（分类清晰）
- archive/ 归档内容
- temp/ 临时文件
- scripts/ 脚本文件
```

---

## ❓ 需要您确认的问题

1. **废弃Python模块处理**
   - 是否同意将v3.0模块移动到archive/deprecated_code/?
   - 还是完全删除这些文件?

2. **文档归档策略**
   - 是否同意将开发历史文档移动到docs/development/?
   - 是否有特定文档需要保留在根目录?

3. **截图文件处理**
   - 临时截图移动到temp/screenshots/（建议添加到.gitignore）
   - 文档用截图移动到docs/current/images/
   - 是否同意?

4. **临时文件处理**
   - devices.json, last_config.json 移动到temp/test_data/
   - 是否同意?

---

**请审核以上计划，确认后我将开始执行整理工作！**

如有任何调整需求，请告知！
