# 任务编辑与功能增强 — 设计说明

日期: 2026-05-12 | 状态: 已确认

## 概述

为"小猪桌面代办助手"新增 4 个功能：编辑任务文本、任务计数、清空已完成任务、撤销操作。采用最小改动策略（方案 A），直接往现有文件中添加代码，不重构架构。

## 功能详述

### 1. 编辑任务文本

**触发**: 双击任务行标题 Label
**交互**: Label 原地切换为 QLineEdit，文字全选，Enter 保存 / Esc 取消
**实现位置**: `task_widgets.py` — TaskRowWidget 新增双击处理和编辑态切换

- 进入编辑: Label.hide() + 创建 QLineEdit 插入原 Label 位置
- 保存: 发射 `edited(int, str)` 信号 → MainWindow → db.update_task()
- 取消: 恢复 Label 显示，不做修改
- 空文本处理: 视为删除，弹出确认（或忽略保存，保留原标题）
- 已完成任务的文本也可编辑

### 2. 任务计数

**位置**: 标题栏右侧，格式 `${未完成数}/${总数}`（如 "2/5"）
**更新时机**: 任务增删、切换完成状态后刷新
**样式**: 小号字体，暖色系，与标题协调
**实现**: `window.py` 标题栏 QLabel 右侧添加计数 QLabel

### 3. 清空已完成任务

**位置**: 列表底部、加号按钮左侧，文字按钮 "清空 x 项已完成"
**显示逻辑**: 常驻显示，x=0 时文字灰色不可点击，x>0 时正常可点击
**点击效果**: db.clear_completed() → refresh 列表 → 更新计数
**实现**: `window.py` 底部栏添加 QLabel 按钮

### 4. 撤销操作

**触发方式**:
- 底部 Toast 弹出（如 "已删除「xxx」"），右侧有 "撤销" 链接可点击，2 秒后自动消失
- Ctrl+Z 快捷键

**撤销范围**: 仅撤销上一次删除或完成/取消完成操作（不包含编辑、清空）
**实现**: `window.py` 维护 `_last_action` 字典，记录操作类型和任务完整数据
**Toast 实现**: QLabel 叠加在窗口底部，带淡入淡出动画

## 数据库变更

`database.py` 新增方法:

```python
def update_task(self, task_id: int, title: str) -> bool:
    """更新任务标题，返回是否成功"""

def clear_completed_tasks(self) -> int:
    """删除所有已完成任务，返回删除数量"""
```

## 信号流转

```
TaskRowWidget.doubleClick           → 进入编辑态
TaskRowWidget.edited(int, str)      → MainWindow._on_task_edited() → db.update_task() → refresh
AddButton.clicked                   → 现有流程不变
DeleteButton.clicked                → TaskRowWidget.deleted → MainWindow._on_task_deleted()
                                        └─ 保存 _last_action → 显示 Toast
CustomCheckBox.toggled              → TaskRowWidget.toggled → MainWindow._on_task_toggled()
                                        └─ 保存 _last_action → 显示 Toast
MainWindow keyPress Ctrl+Z          → MainWindow._on_undo() → 恢复 _last_action
"清空已完成"点击                     → MainWindow._on_clear_completed() → db.clear_completed()
```

## 涉及文件

| 文件 | 改动 |
|------|------|
| `task_widgets.py` | TaskRowWidget 增加双击编辑、edited 信号 |
| `window.py` | 计数 QLabel、清空按钮、撤销逻辑、Toast、Ctrl+Z |
| `database.py` | update_task()、clear_completed_tasks() |

## 边界情况

- 编辑任务文本为空 → 忽略保存，恢复原标题
- 双击已完成任务的文字 → 也允许编辑
- 连续操作两次 → 撤销仅恢复最近一次
- 清空已完成时存在 0 项 → 按钮灰色不可点击
- Toast 尚未消失时新操作 → 旧 Toast 立即替换为新 Toast
- 编辑模式下按 Ctrl+Z → 由输入框处理，不触发撤销

## 测试要点

- 双击进入编辑 → 修改文字 → Enter 确认 → 数据库和 UI 均更新
- 双击进入编辑 → Esc 取消 → 文字不变
- 计数随增删改完成状态实时更新
- 清空按钮在有/无已完成任务时的状态正确
- 删除后 Toast 出现 → 点击撤销 → 任务恢复
- Ctrl+Z 可撤销删除和完成操作
