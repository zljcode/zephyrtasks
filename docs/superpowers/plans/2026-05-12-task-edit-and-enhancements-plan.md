# 任务编辑与功能增强 — 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为"小猪桌面代办助手"新增编辑任务文本、任务计数、清空已完成、撤销操作四个功能。

**架构：** 方案 A 最小改动策略，直接在 `database.py`、`task_widgets.py`、`window.py` 三个文件中增量添加代码。不引入新文件，不重构现有架构。

**技术栈：** Python 3, PyQt5, SQLite

---

### 任务 1：Database 层 — 新增 update_task 和 clear_completed_tasks

**文件：**
- 修改：`database.py:55-70`（在 delete_task 之后新增方法）

- [ ] **步骤 1：添加 update_task 方法**

在 `delete_task` 方法之后、`get_all_tasks` 之前插入：

```python
    def update_task(self, task_id, title):
        """更新任务标题，返回受影响行数"""
        cursor = self.conn.execute(
            "UPDATE tasks SET title=? WHERE id=?", (title, task_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def clear_completed_tasks(self):
        """删除所有已完成任务，返回删除数量"""
        cursor = self.conn.execute("DELETE FROM tasks WHERE completed=1")
        self.conn.commit()
        return cursor.rowcount
```

- [ ] **步骤 2：验证 database 方法**

运行验证脚本：

```bash
python -c "
from database import Database
import os, tempfile
db = Database(os.path.join(tempfile.gettempdir(), 'test_zephyr.db'))
# 添加测试数据
db.add_task('测试任务1')
db.add_task('测试任务2')
tid = db.add_task('测试任务3')
# 测试更新
assert db.update_task(tid, '修改后的任务')
tasks = db.get_all_tasks()
assert any(t['title'] == '修改后的任务' for t in tasks), '更新失败'
# 测试切换和清空
db.toggle_task(tid)
assert db.clear_completed_tasks() == 1, '清空失败'
# 清理
db.close()
os.unlink(os.path.join(tempfile.gettempdir(), 'test_zephyr.db'))
print('OK - 所有 database 测试通过')
"
```

- [ ] **步骤 3：Commit**

```bash
git add database.py
git commit -m "feat: 数据库层新增 update_task 和 clear_completed_tasks 方法"
```

---

### 任务 2：TaskRowWidget — 双击编辑任务文本

**文件：**
- 修改：`task_widgets.py`（TaskRowWidget 类，约第 102-190 行）

- [ ] **步骤 1：添加 edited 信号和编辑输入框**

修改 TaskRowWidget 类：

在 `__init__` 中的 `self.delete_btn` 创建之后添加编辑输入框：

```python
class TaskRowWidget(QWidget):
    toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)
    edited = pyqtSignal(int, str)  # task_id, new_title

    def __init__(self, task_id, title, completed, created_at=None, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.setFixedHeight(44)
        self.setContentsMargins(12, 4, 12, 4)
        self.setCursor(Qt.ArrowCursor)
        if created_at:
            date_str = created_at[:16]
            self.setToolTip(f"创建于 {date_str}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.checkbox = CustomCheckBox()
        self.checkbox.setChecked(bool(completed))
        self.checkbox.stateChanged.connect(self._on_toggle)
        layout.addWidget(self.checkbox)

        self.title_label = QLabel(title)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._update_title_style(completed)
        layout.addWidget(self.title_label)

        # 编辑输入框（初始隐藏）
        self._edit_input = QLineEdit()
        self._edit_input.setVisible(False)
        self._edit_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._edit_input.setStyleSheet(
            'background: white; color: #3D3226; border: 1px solid #C87A5A; '
            'border-radius: 4px; padding: 2px 6px; '
            f'font: bold {self._BASE_FONT_SIZE}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif;'
        )
        self._edit_input.returnPressed.connect(self._on_edit_done)
        layout.addWidget(self._edit_input)

        self.delete_btn = DeleteButton()
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setVisible(False)
        layout.addWidget(self.delete_btn)

        self._separator_visible = True
```

- [ ] **步骤 2：添加双击事件和编辑方法**

在 TaskRowWidget 类中添加以下方法（在 `_on_delete` 之后）：

```python
    def mouseDoubleClickEvent(self, event):
        """双击任务行文字进入编辑模式"""
        if event.button() == Qt.LeftButton:
            # 排除复选框区域
            if event.pos().x() > 30:  # checkbox 宽度 + margin
                self._enter_edit_mode()
        super().mouseDoubleClickEvent(event)

    def _enter_edit_mode(self):
        self._edit_input.setText(self.title_label.text())
        self._edit_input.setVisible(True)
        self._edit_input.setFocus()
        self._edit_input.selectAll()
        self.title_label.setVisible(False)

    def _exit_edit_mode(self, save):
        if save:
            new_title = self._edit_input.text().strip()
            if new_title and new_title != self.title_label.text():
                self.edited.emit(self.task_id, new_title)
        self._edit_input.setVisible(False)
        self.title_label.setVisible(True)

    def _on_edit_done(self):
        self._exit_edit_mode(True)
```

- [ ] **步骤 3：添加 Esc 键取消编辑**

修改 `_edit_input` 的初始化，添加 keyPressEvent 处理。由于 QLineEdit 无法直接重写（使用 lambda/eventFilter），改用 `installEventFilter` 方案。在 `__init__` 中添加：

```python
        self._edit_input.installEventFilter(self)
```

在 TaskRowWidget 中添加：

```python
    def eventFilter(self, obj, event):
        from PyQt5.QtCore import QEvent
        if obj == self._edit_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self._exit_edit_mode(False)
                return True
        return super().eventFilter(obj, event)
```

- [ ] **步骤 4：更新 set_scale 支持编辑输入框**

在 `set_scale` 方法末尾添加：

```python
        edit_fs = max(10, round(self._BASE_FONT_SIZE * scale))
        self._edit_input.setStyleSheet(
            'background: white; color: #3D3226; border: 1px solid #C87A5A; '
            'border-radius: 4px; padding: 2px 6px; '
            f'font: bold {edit_fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif;'
        )
```

- [ ] **步骤 5：验证编辑功能**

首先验证 Python 语法：

```bash
python -c "from task_widgets import TaskRowWidget; print('Import OK')"
```

- [ ] **步骤 6：Commit**

```bash
git add task_widgets.py
git commit -m "feat: TaskRowWidget 双击进入编辑模式，Enter保存/Esc取消"
```

---

### 任务 3：MainWindow — 标题栏任务计数 + 连接编辑信号

**文件：**
- 修改：`window.py`（标题区域、_add_task_row、_refresh_tasks、_update_scale）

- [ ] **步骤 1：添加 counter_label 并重构标题区域**

将 `_init_ui` 中标题部分（第 47-57 行）改为水平布局容器：

`_init_ui` 中，替换：

```python
        # Title
        self.title_label = QLabel("🐷 桌面代办", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(36)
        self.title_label.setStyleSheet(
            'font: bold 15px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #3D3226; background: transparent; padding-top: 6px;'
        )
        self.title_label._base_font_size = 15
        self.title_label._base_height = 36
        main_layout.addWidget(self.title_label)
```

改为：

```python
        # Title row: centered title + right-aligned counter
        title_container = QWidget(self)
        title_container.setStyleSheet("background: transparent;")
        title_row = QHBoxLayout(title_container)
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(0)

        self.title_label = QLabel("🐷 桌面代办", self)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFixedHeight(36)
        self.title_label.setStyleSheet(
            'font: bold 15px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #3D3226; background: transparent; padding-top: 6px;'
        )
        self.title_label._base_font_size = 15
        self.title_label._base_height = 36

        title_row.addStretch()
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        self.counter_label = QLabel(self)
        self.counter_label.setStyleSheet(
            'font: bold 11px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #B0A090; background: transparent; padding-top: 6px; padding-right: 6px;'
        )
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.counter_label.setFixedWidth(36)
        self.counter_label._base_font_size = 11
        title_row.addWidget(self.counter_label)

        main_layout.addWidget(title_container)
```

- [ ] **步骤 2：添加 _update_counter 方法**

在 `_refresh_tasks` 方法之后添加：

```python
    def _update_counter(self, tasks):
        total = len(tasks)
        pending = sum(1 for t in tasks if not t["completed"])
        if total > 0:
            self.counter_label.setText(f"{pending}/{total}")
        else:
            self.counter_label.setText("")
```

- [ ] **步骤 3：修改 _add_task_row 连接 edited 信号**

在 `_add_task_row`（第 116-121 行）中添加 `edited` 信号连接：

```python
    def _add_task_row(self, task):
        row = TaskRowWidget(task["id"], task["title"], task["completed"], task.get("created_at"))
        row.toggled.connect(self._on_task_toggled)
        row.deleted.connect(self._on_task_deleted)
        row.edited.connect(self._on_task_edited)
        insert_index = self.list_layout.count() - 1
        self.list_layout.insertWidget(insert_index, row)
```

- [ ] **步骤 4：添加 _on_task_edited 槽函数**

在 `_on_task_deleted` 之后添加：

```python
    def _on_task_edited(self, task_id, new_title):
        self.db.update_task(task_id, new_title)
        self._refresh_tasks()
```

- [ ] **步骤 5：修改 _refresh_tasks 调用 _update_counter**

在 `_refresh_tasks`（第 123-132 行）中添加计数器更新：

```python
    def _refresh_tasks(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        tasks = self.db.get_all_tasks()
        for task in tasks:
            self._add_task_row(task)
        self._update_counter(tasks)
```

- [ ] **步骤 6：更新 _load_tasks**

在 `_load_tasks` 中添加初始计数器显示：

```python
    def _load_tasks(self):
        tasks = self.db.get_all_tasks()
        for task in tasks:
            self._add_task_row(task)
        self._update_counter(tasks)
```

- [ ] **步骤 7：更新 _update_scale 中的标题缩放**

`_update_scale` 中标题部分（第 236-243 行）保持不变（仍通过 title_label 引用），在末尾添加 counter 缩放：

```python
        # Counter label scale
        cfs = max(9, round(self.counter_label._base_font_size * scale))
        self.counter_label.setStyleSheet(
            f'font: bold {cfs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #B0A090; background: transparent; padding-top: 6px; padding-right: 6px;'
        )
```

- [ ] **步骤 8：验证语法和导入**

```bash
python -c "from window import MainWindow; print('Import OK')"
```

- [ ] **步骤 9：Commit**

```bash
git add window.py
git commit -m "feat: 标题栏任务计数 + 连接编辑信号到 MainWindow"
```

---

### 任务 4：MainWindow — 清空已完成任务按钮

**文件：**
- 修改：`window.py`（底部区域）

- [ ] **步骤 1：修改底部布局**

将 `_init_ui` 中底部加号按钮部分（第 94-102 行）改为水平行布局：

```python
        # Separator line above bottom row
        sep_bottom = QWidget(self)
        sep_bottom.setFixedHeight(1)
        sep_bottom.setStyleSheet("background: rgba(0,0,0,25); margin: 0 8px;")
        main_layout.addWidget(sep_bottom)

        # Bottom row: clear button + add button
        bottom_row = QWidget(self)
        bottom_row.setStyleSheet("background: transparent;")
        bottom_layout = QHBoxLayout(bottom_row)
        bottom_layout.setContentsMargins(12, 0, 12, 0)
        bottom_layout.setSpacing(0)

        self.clear_btn = QLabel("清空已完成", self)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(
            'font: 12px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #B0A090; background: transparent; padding: 4px 0;'
        )
        self.clear_btn._base_font_size = 12
        bottom_layout.addWidget(self.clear_btn)
        bottom_layout.addStretch()

        self.add_btn = AddButton()
        self.add_btn.clicked.connect(self._show_input)
        bottom_layout.addWidget(self.add_btn)

        main_layout.addWidget(bottom_row)
```

注意：删除原有的 `self.add_btn = AddButton()` 和 `main_layout.addWidget(self.add_btn)` 两行（原第 100-102 行）。

- [ ] **步骤 2：添加 _update_clear_btn 方法**

在 `_update_counter` 之后添加：

```python
    def _update_clear_btn(self, tasks):
        completed_count = sum(1 for t in tasks if t["completed"])
        if completed_count > 0:
            self.clear_btn.setText(f"清空 {completed_count} 项已完成")
            self.clear_btn.setStyleSheet(
                f'font: 12px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #C8553D; background: transparent; padding: 4px 0;'
            )
            self.clear_btn.setEnabled(True)
        else:
            self.clear_btn.setText("清空已完成")
            self.clear_btn.setStyleSheet(
                f'font: 12px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #B0A090; background: transparent; padding: 4px 0;'
            )
            self.clear_btn.setEnabled(False)
```

- [ ] **步骤 3：添加 clear_btn 点击处理**

在 `_init_ui` 中，`bottom_layout.addWidget(self.clear_btn)` 之前添加：

使用 event filter 方式处理 QLabel 点击，或者在 `_init_ui` 最后添加：

```python
        self.clear_btn.mousePressEvent = self._on_clear_click
```

- [ ] **步骤 4：添加 _on_clear_click 和 _on_clear_completed 方法**

```python
    def _on_clear_click(self, event):
        if event.button() == Qt.LeftButton and self.clear_btn.isEnabled():
            self._on_clear_completed()

    def _on_clear_completed(self):
        count = self.db.clear_completed_tasks()
        if count > 0:
            self._refresh_tasks()
```

- [ ] **步骤 5：在 _refresh_tasks 和 _load_tasks 中更新 clear_btn**

`_refresh_tasks` 末尾加上：
```python
        self._update_clear_btn(tasks)
```

`_load_tasks` 末尾加上：
```python
        self._update_clear_btn(tasks)
```

- [ ] **步骤 6：更新 _update_scale 中 clear_btn 缩放**

在 `_update_scale` 末尾添加：

```python
        # Clear button scale
        cbfs = max(10, round(self.clear_btn._base_font_size * scale))
        completed_count = sum(1 for t in self.db.get_all_tasks() if t["completed"])
        if completed_count > 0:
            self.clear_btn.setStyleSheet(
                f'font: {cbfs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #C8553D; background: transparent; padding: 4px 0;'
            )
        else:
            self.clear_btn.setStyleSheet(
                f'font: {cbfs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #B0A090; background: transparent; padding: 4px 0;'
            )
```

同时需要清除旧的 `self.add_btn.set_scale(scale)` 调用 — 保留不变。

- [ ] **步骤 7：验证**

```bash
python -c "from window import MainWindow; print('Import OK')"
```

- [ ] **步骤 8：Commit**

```bash
git add window.py
git commit -m "feat: 底部清空已完成任务按钮"
```

---

### 任务 5：MainWindow — 撤销操作（Toast + Ctrl+Z）

**文件：**
- 修改：`window.py`

- [ ] **步骤 1：在 _init_ui 中添加 Toast 组件**

在 `_init_ui` 中，`main_layout.addWidget(bottom_row)` 之前（即底部行上方）添加：

```python
        # Toast notification for undo
        self.toast = QWidget(self)
        self.toast.setVisible(False)
        self.toast.setStyleSheet(
            "background: rgba(61, 50, 38, 220); border-radius: 6px;"
        )
        toast_layout = QHBoxLayout(self.toast)
        toast_layout.setContentsMargins(10, 6, 10, 6)
        toast_layout.setSpacing(8)

        self.toast_msg = QLabel(self)
        self.toast_msg.setStyleSheet(
            'color: #FAF6F0; font-size: 12px; background: transparent;'
        )
        toast_layout.addWidget(self.toast_msg)

        toast_layout.addStretch()

        self.toast_undo = QLabel("撤销", self)
        self.toast_undo.setCursor(Qt.PointingHandCursor)
        self.toast_undo.setStyleSheet(
            'color: #C87A5A; font-size: 12px; font-weight: bold; background: transparent;'
        )
        toast_layout.addWidget(self.toast_undo)

        self.toast_opacity = QGraphicsOpacityEffect(self.toast)
        self.toast_opacity.setOpacity(0.0)
        self.toast.setGraphicsEffect(self.toast_opacity)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        main_layout.addWidget(self.toast)
```

需要引入 `QTimer` 和 `QGraphicsOpacityEffect`：
```python
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QTimer
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QFont, QLinearGradient, QBrush
```

以及添加 `QGraphicsOpacityEffect` 的导入：
现有的 `from PyQt5.QtWidgets import` 中已有 `QGraphicsOpacityEffect`（在 task_widgets.py 中）。但 window.py 未导入它，需要添加到 window.py：

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy,
    QSizeGrip, QLabel, QApplication, QGraphicsOpacityEffect,
)
```

- [ ] **步骤 2：添加撤销相关方法和成员变量**

在 `__init__` 的 `self._init_ui()` 之前添加：

```python
        self._last_action = None  # {"action": "delete"|"toggle", "task": {...}}
        self._toast_timer = None
```

- [ ] **步骤 3：添加 Toast 显示/隐藏方法**

```python
    def _show_toast(self, message):
        self.toast_msg.setText(message)
        self.toast.setVisible(True)
        self._animate_toast_opacity(1.0)
        self._toast_timer.start(2500)

    def _hide_toast(self):
        self._animate_toast_opacity(0.0)
        self._toast_timer.stop()
        # 延迟隐藏以等待动画完成
        QTimer.singleShot(150, lambda: self.toast.setVisible(False))

    def _animate_toast_opacity(self, target):
        anim = QPropertyAnimation(self.toast_opacity, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(self.toast_opacity.opacity())
        anim.setEndValue(target)
        anim.start()
```

需要导入 `QPropertyAnimation`：
```python
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QTimer, QPropertyAnimation
```

- [ ] **步骤 4：修改 _on_task_deleted 保存撤销信息**

```python
    def _on_task_deleted(self, task_id):
        tasks = self.db.get_all_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task:
            self._last_action = {"action": "delete", "task": task}
        self.db.delete_task(task_id)
        self._refresh_tasks()
        if task:
            self._show_toast(f"已删除「{task['title']}」")
```

**重要**：必须先在 `get_all_tasks` 中找到任务，再删除。因为删除后就查不到了。

- [ ] **步骤 5：修改 _on_task_toggled 保存撤销信息**

```python
    def _on_task_toggled(self, task_id):
        tasks = self.db.get_all_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        self.db.toggle_task(task_id)
        self._refresh_tasks()
        if task:
            self._last_action = {"action": "toggle", "task": task}
            new_state = "已完成" if not task["completed"] else "已恢复"
            self._show_toast(f"「{task['title']}」{new_state}")
```

- [ ] **步骤 6：添加撤销实现方法**

```python
    def _on_undo(self):
        if self._last_action is None:
            return
        action = self._last_action
        self._last_action = None
        if action["action"] == "delete":
            # 重新插入被删除的任务
            self.db.add_task(action["task"]["title"])
            self._refresh_tasks()
            self._show_toast("已撤销删除")
        elif action["action"] == "toggle":
            # 恢复原来的完成状态
            self.db.toggle_task(action["task"]["id"])
            self._refresh_tasks()
            self._show_toast("已撤销")
```

- [ ] **步骤 7：连接 Toast 撤销点击和 Ctrl+Z 快捷键**

在 `_init_ui` 末尾添加：

```python
        self.toast_undo.mousePressEvent = lambda e: self._on_undo() if e.button() == Qt.LeftButton else None
```

重写 MainWindow 的 `keyPressEvent`：

```python
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            self._on_undo()
            return
        super().keyPressEvent(event)
```

- [ ] **步骤 8：验证**

```bash
python -c "from window import MainWindow; print('Import OK')"
```

- [ ] **步骤 9：Commit**

```bash
git add window.py
git commit -m "feat: 撤销操作 — Toast 提示 + Ctrl+Z 快捷键"
```

---

### 任务 6：集成验证 — 启动应用手动测试

**文件：** 无

- [ ] **步骤 1：语法全面检查**

```bash
python -m py_compile database.py && echo "database OK"
python -m py_compile task_widgets.py && echo "task_widgets OK"
python -m py_compile window.py && echo "window OK"
python -m py_compile main.py && echo "main OK"
```

- [ ] **步骤 2：启动应用进行手动测试**

```bash
python main.py
```

手动验证清单：
- [ ] 双击任务文字 → 进入编辑模式，文字全选
- [ ] 修改文字后 Enter → 文字更新，计数器正确
- [ ] 编辑中按 Esc → 文字不变，恢复原标题
- [ ] 标题栏显示 `${pending}/${total}` 计数
- [ ] 勾选完成任务 → 计数更新
- [ ] 底部显示 "清空 N 项已完成" (红色可点击) 或 "清空已完成" (灰色不可点)
- [ ] 点击清空 → 所有已完成任务消失
- [ ] 删除任务 → 底部弹出 Toast "已删除「xxx」 撤销"
- [ ] 点击撤销 → 任务恢复
- [ ] 完成/取消完成任务 → Toast 提示
- [ ] Ctrl+Z → 撤销上一次操作
- [ ] 窗口缩放 → 所有新 UI 元素字体跟随缩放
- [ ] 边缘隐藏/恢复 → 功能正常

- [ ] **步骤 3：修复发现的问题并 Commit**

如有问题，修复后：

```bash
git add -A
git commit -m "fix: 集成测试中发现的问题修复"
```

---

### 完成

所有功能实现完毕后的最终验证：

```bash
python main.py
git log --oneline -6
```
