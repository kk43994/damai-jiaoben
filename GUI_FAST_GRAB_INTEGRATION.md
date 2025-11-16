# 🎯 GUI快速抢票功能集成方案

> **目标**: 将抢票功能分为两个阶段：场次导航 + 快速抢票
> **文件**: damai_smart_ai.py
> **新模块**: fast_grabber.py

---

## 📋 功能设计

### 阶段一：场次导航
- **原按钮**: "开始抢票" → 重命名为 **"场次导航"**
- **功能**:
  - 启动大麦App
  - 搜索演出
  - 进入演出详情页
  - 导航到票档场次选择页面
  - **停止在选择页面，等待用户设置坐标**

### 阶段二：快速抢票（新增）
- **新按钮**: **"开始抢票"**
- **前置条件**: 已完成场次导航
- **功能**:
  1. 点击场次坐标
  2. 点击票档坐标
  3. 快速循环点击购票按钮
  4. 检测页面变化→停止

---

## 🎨 GUI布局变更

### 新增：坐标设置面板

```
┌─ 抢票坐标设置 ──────────────────┐
│                                  │
│ 场次坐标: [___X___] [___Y___]   │  [📍从截图获取]
│ 票档坐标: [___X___] [___Y___]   │  [📍从截图获取]
│ 购票按钮: [___X___] [___Y___]   │  [📍从截图获取]
│                                  │
│ 点击间隔: [_0.1_]秒             │
│ 最大点击: [_100_]次             │
│ 检测间隔: [__5_]次/检查          │
│                                  │
│ [保存坐标配置] [加载坐标配置]    │
└──────────────────────────────────┘
```

### 修改：抢票控制按钮

**原设计**:
```
[开始抢票] [停止抢票]
```

**新设计**:
```
[场次导航] [开始抢票] [停止抢票]
  (阶段1)    (阶段2)
```

---

## 💻 代码实现方案

### 1. 导入新模块

```python
# 在文件开头添加
from damai_appium.fast_grabber import FastGrabber, GrabConfig
```

### 2. __init__ 中初始化

```python
def __init__(self, root):
    # ... 现有代码 ...

    # 快速抢票模块
    self.fast_grabber = None  # 连接后初始化

    # 抢票坐标配置
    self.grab_coords = {
        "session_x": tk.IntVar(value=360),
        "session_y": tk.IntVar(value=400),
        "price_x": tk.IntVar(value=360),
        "price_y": tk.IntVar(value=600),
        "buy_x": tk.IntVar(value=360),
        "buy_y": tk.IntVar(value=1100)
    }

    # 抢票参数
    self.click_interval = tk.DoubleVar(value=0.1)
    self.max_clicks = tk.IntVar(value=100)
    self.page_check_interval = tk.IntVar(value=5)
```

### 3. 添加坐标设置面板

```python
def create_grab_coords_panel(self, parent):
    """创建抢票坐标设置面板"""

    coords_frame = ttk.LabelFrame(parent, text="抢票坐标设置", padding="10")
    coords_frame.pack(fill=tk.X, pady=(0, 10))

    # 场次坐标
    ttk.Label(coords_frame, text="场次坐标:").grid(row=0, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["session_x"], width=8).grid(row=0, column=1, padx=2)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["session_y"], width=8).grid(row=0, column=2, padx=2)
    ttk.Button(coords_frame, text="📍从截图获取", command=lambda: self.pick_coord_from_screenshot("session"), width=12).grid(row=0, column=3, padx=5)

    # 票档坐标
    ttk.Label(coords_frame, text="票档坐标:").grid(row=1, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["price_x"], width=8).grid(row=1, column=1, padx=2)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["price_y"], width=8).grid(row=1, column=2, padx=2)
    ttk.Button(coords_frame, text="📍从截图获取", command=lambda: self.pick_coord_from_screenshot("price"), width=12).grid(row=1, column=3, padx=5)

    # 购票按钮
    ttk.Label(coords_frame, text="购票按钮:").grid(row=2, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["buy_x"], width=8).grid(row=2, column=1, padx=2)
    ttk.Entry(coords_frame, textvariable=self.grab_coords["buy_y"], width=8).grid(row=2, column=2, padx=2)
    ttk.Button(coords_frame, text="📍从截图获取", command=lambda: self.pick_coord_from_screenshot("buy"), width=12).grid(row=2, column=3, padx=5)

    # 参数设置
    ttk.Separator(coords_frame, orient='horizontal').grid(row=3, column=0, columnspan=4, sticky='ew', pady=10)

    ttk.Label(coords_frame, text="点击间隔:").grid(row=4, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.click_interval, width=8).grid(row=4, column=1, padx=2)
    ttk.Label(coords_frame, text="秒").grid(row=4, column=2, sticky=tk.W)

    ttk.Label(coords_frame, text="最大点击:").grid(row=5, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.max_clicks, width=8).grid(row=5, column=1, padx=2)
    ttk.Label(coords_frame, text="次").grid(row=5, column=2, sticky=tk.W)

    ttk.Label(coords_frame, text="检测间隔:").grid(row=6, column=0, sticky=tk.W, pady=3)
    ttk.Entry(coords_frame, textvariable=self.page_check_interval, width=8).grid(row=6, column=1, padx=2)
    ttk.Label(coords_frame, text="次/检查").grid(row=6, column=2, sticky=tk.W)

    # 保存/加载按钮
    btn_frame = ttk.Frame(coords_frame)
    btn_frame.grid(row=7, column=0, columnspan=4, pady=(10, 0))

    ttk.Button(btn_frame, text="保存坐标配置", command=self.save_grab_coords, width=15).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="加载坐标配置", command=self.load_grab_coords, width=15).pack(side=tk.LEFT, padx=5)
```

### 4. 从截图获取坐标功能

```python
def pick_coord_from_screenshot(self, coord_type: str):
    """从当前截图点击获取坐标"""

    if not self.current_screenshot:
        self.log("请先连接设备查看截图", "WARNING")
        return

    self.log(f"请在截图上点击选择{coord_type}坐标...", "INFO")

    # 临时绑定点击事件
    def on_temp_click(event):
        # 计算真实坐标（考虑缩放）
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        if self.scale_1to1.get():
            # 换算到真实设备坐标
            real_x = int(canvas_x * self.target_width / self.display_width)
            real_y = int(canvas_y * self.target_height / self.display_height)
        else:
            real_x = int(canvas_x)
            real_y = int(canvas_y)

        # 设置坐标
        if coord_type == "session":
            self.grab_coords["session_x"].set(real_x)
            self.grab_coords["session_y"].set(real_y)
            self.log(f"场次坐标设置为: ({real_x}, {real_y})", "SUCCESS")
        elif coord_type == "price":
            self.grab_coords["price_x"].set(real_x)
            self.grab_coords["price_y"].set(real_y)
            self.log(f"票档坐标设置为: ({real_x}, {real_y})", "SUCCESS")
        elif coord_type == "buy":
            self.grab_coords["buy_x"].set(real_x)
            self.grab_coords["buy_y"].set(real_y)
            self.log(f"购票按钮坐标设置为: ({real_x}, {real_y})", "SUCCESS")

        # 解绑临时事件
        self.canvas.unbind("<Button-1>")
        # 恢复原有点击事件
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    # 绑定临时点击事件
    self.canvas.unbind("<Button-1>")
    self.canvas.bind("<Button-1>", on_temp_click)
```

### 5. 保存/加载坐标配置

```python
def save_grab_coords(self):
    """保存抢票坐标配置"""
    config = {
        "session_x": self.grab_coords["session_x"].get(),
        "session_y": self.grab_coords["session_y"].get(),
        "price_x": self.grab_coords["price_x"].get(),
        "price_y": self.grab_coords["price_y"].get(),
        "buy_x": self.grab_coords["buy_x"].get(),
        "buy_y": self.grab_coords["buy_y"].get(),
        "click_interval": self.click_interval.get(),
        "max_clicks": self.max_clicks.get(),
        "page_check_interval": self.page_check_interval.get()
    }

    try:
        with open("grab_coords.json", 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        self.log("坐标配置已保存", "SUCCESS")
    except Exception as e:
        self.log(f"保存失败: {e}", "ERROR")

def load_grab_coords(self):
    """加载抢票坐标配置"""
    try:
        with open("grab_coords.json", 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.grab_coords["session_x"].set(config.get("session_x", 360))
        self.grab_coords["session_y"].set(config.get("session_y", 400))
        self.grab_coords["price_x"].set(config.get("price_x", 360))
        self.grab_coords["price_y"].set(config.get("price_y", 600))
        self.grab_coords["buy_x"].set(config.get("buy_x", 360))
        self.grab_coords["buy_y"].set(config.get("buy_y", 1100))
        self.click_interval.set(config.get("click_interval", 0.1))
        self.max_clicks.set(config.get("max_clicks", 100))
        self.page_check_interval.set(config.get("page_check_interval", 5))

        self.log("坐标配置已加载", "SUCCESS")
    except FileNotFoundError:
        self.log("未找到配置文件", "WARNING")
    except Exception as e:
        self.log(f"加载失败: {e}", "ERROR")
```

### 6. 修改按钮

```python
# 修改原有的抢票按钮为"场次导航"
self.navigate_btn = ttk.Button(
    btn_frame,
    text="场次导航",  # 改名
    command=self.navigate_to_session_page,  # 改为导航功能
    width=12
)
self.navigate_btn.pack(side=tk.LEFT, padx=5)

# 新增"开始抢票"按钮
self.grab_btn = ttk.Button(
    btn_frame,
    text="开始抢票",
    command=self.start_fast_grab,
    width=12,
    state=tk.DISABLED  # 默认禁用，完成导航后启用
)
self.grab_btn.pack(side=tk.LEFT, padx=5)

# 停止按钮
self.stop_grab_btn = ttk.Button(
    btn_frame,
    text="停止抢票",
    command=self.stop_grab_ticket,
    width=12,
    state=tk.DISABLED
)
self.stop_grab_btn.pack(side=tk.LEFT, padx=5)
```

### 7. 场次导航功能

```python
def navigate_to_session_page(self):
    """导航到场次选择页面（原抢票功能，但不执行抢票）"""

    if not self.bot:
        self.log("请先连接设备", "WARNING")
        return

    if self.grabbing:
        self.log("正在执行任务，请等待完成", "WARNING")
        return

    self.grabbing = True
    self.navigate_btn.config(state=tk.DISABLED)

    def navigate_task():
        try:
            self.log("=" * 60, "INFO")
            self.log("开始场次导航", "INFO")
            self.log("=" * 60, "INFO")

            # 执行原有的导航流程（不包括抢票）
            # 1. 搜索演出
            self.log("[1/3] 搜索演出...", "INFO")
            self.bot.search_performance(self.keyword_var.get())
            time.sleep(2)

            # 2. 进入详情页
            self.log("[2/3] 进入演出详情页...", "INFO")
            self.bot.enter_performance_detail()
            time.sleep(2)

            # 3. 导航到场次选择页
            self.log("[3/3] 导航到场次选择页...", "INFO")
            # 点击"选择场次"或类似按钮
            # ... 根据实际App流程调整 ...

            self.log("=" * 60, "SUCCESS")
            self.log("✓ 场次导航完成！", "SUCCESS")
            self.log("请在截图上设置抢票坐标，然后点击'开始抢票'", "SUCCESS")
            self.log("=" * 60, "SUCCESS")

            # 启用"开始抢票"按钮
            self.grab_btn.config(state=tk.NORMAL)

        except Exception as e:
            self.log(f"导航失败: {e}", "ERROR")
        finally:
            self.grabbing = False
            self.navigate_btn.config(state=tk.NORMAL)

    thread = threading.Thread(target=navigate_task, daemon=True)
    thread.start()
```

### 8. 快速抢票功能

```python
def start_fast_grab(self):
    """开始快速抢票"""

    if not self.bot or not self.bot.driver:
        self.log("请先连接设备", "WARNING")
        return

    if self.grabbing:
        self.log("正在执行任务，请等待完成", "WARNING")
        return

    self.grabbing = True
    self.grab_btn.config(state=tk.DISABLED)
    self.stop_grab_btn.config(state=tk.NORMAL)

    def grab_task():
        try:
            # 初始化FastGrabber
            if not self.fast_grabber:
                self.fast_grabber = FastGrabber(self.bot.driver, logger=BotLogger)

            # 创建配置
            config = GrabConfig(
                session_x=self.grab_coords["session_x"].get(),
                session_y=self.grab_coords["session_y"].get(),
                price_x=self.grab_coords["price_x"].get(),
                price_y=self.grab_coords["price_y"].get(),
                buy_x=self.grab_coords["buy_x"].get(),
                buy_y=self.grab_coords["buy_y"].get(),
                click_interval=self.click_interval.get(),
                max_clicks=self.max_clicks.get(),
                page_check_interval=self.page_check_interval.get()
            )

            # 执行快速抢票
            success, message = self.fast_grabber.start_grab(
                config,
                on_progress=lambda msg: self.log(msg, "INFO")
            )

            if success:
                self.log("=" * 60, "SUCCESS")
                self.log("🎉 抢票成功！", "SUCCESS")
                self.log(message, "SUCCESS")
                self.log("=" * 60, "SUCCESS")

                # 播放成功音效
                if hasattr(self, 'sound_notifier'):
                    self.sound_notifier.play_ticket_grabbed()
            else:
                self.log("=" * 60, "ERROR")
                self.log("抢票未成功", "WARNING")
                self.log(message, "WARNING")
                self.log("=" * 60, "ERROR")

            # 打印统计
            self.fast_grabber.print_statistics()

        except Exception as e:
            self.log(f"抢票出错: {e}", "ERROR")
        finally:
            self.grabbing = False
            self.grab_btn.config(state=tk.NORMAL)
            self.stop_grab_btn.config(state=tk.DISABLED)

    thread = threading.Thread(target=grab_task, daemon=True)
    thread.start()
```

---

## 📊 用户使用流程

```
1. 连接设备
   ↓
2. 填写演出信息（关键词、城市等）
   ↓
3. 点击【场次导航】
   ↓  (自动执行：搜索→进入详情→到达场次选择页)
   ↓
4. 在截图上设置坐标
   - 点击"📍从截图获取"按钮
   - 在截图上点击场次位置
   - 在截图上点击票档位置
   - 在截图上点击购票按钮位置
   ↓
5. (可选) 调整参数
   - 点击间隔
   - 最大点击次数
   - 页面检测间隔
   ↓
6. (可选) 保存坐标配置
   ↓
7. 点击【开始抢票】
   ↓  (自动执行：选场次→选票档→快速点击购票按钮)
   ↓
8. 等待页面变化（成功进入下一页）
   ↓
9. 抢票完成！🎉
```

---

## ✅ 优势

1. **分离关注点**: 导航和抢票分开，更清晰
2. **用户可控**: 用户可以手动设置关键坐标
3. **灵活调整**: 可以调整点击速度和检测频率
4. **可保存配置**: 不同演出可以保存不同的坐标配置
5. **实时反馈**: 显示点击进度和页面变化状态

---

## 🎯 实施计划

1. ✅ 创建 `fast_grabber.py` 核心模块
2. ⏳ 修改GUI添加坐标设置面板
3. ⏳ 修改按钮和事件处理
4. ⏳ 测试功能
5. ⏳ 文档更新

---

这个设计让用户有更多控制权，同时保持了自动化的便利性！ 🚀
