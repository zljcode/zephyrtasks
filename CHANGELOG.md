# 小猪桌面代办助手 — 改动记录

## UI 主题

- 背景从暗色 `rgba(30,30,30,225)` 改为暖白半透明 `rgba(248,245,241,230)`（#f8f5f1）
- 添加柔和阴影：外层 `adjusted(-2,-2,2,2)` 半透明黑色圆角矩形
- 边框从亮白色细线改为极淡黑色 `rgba(0,0,0,15)` 细线
- 整体圆角 10px，阴影圆角 14px
- 输入框背景同步改为 `rgba(248,245,241,0.9)`

## 字体

- 全局字体族改为 `"幼圆", "YouYuan"` 优先，可爱圆润风格，回退 Segoe UI → PingFang SC → sans-serif
- 任务文字加大：14px → 16px，加粗
- 标题 15px 加粗
- 输入框 16px 加粗
- 字体跟随窗口缩放：拉伸窗口时标题、任务文字、输入框、加号按钮的字体和高度按比例缩放（基准：窗口默认高度 380px）

## 新增标题与分隔线

- 顶部居中标题"小猪桌面代办助手"
- 标题与任务列表之间淡色分隔线 `rgba(0,0,0,25)`
- 任务列表与加号按钮之间淡色分隔线

## 加号按钮

- 增大：高度 40px → 52px，字号 20px → 32px（hover 36px）

## 复选框交互修复

- **Bug**: 只能用空格键打勾，鼠标点击无效
- **修复**: `CustomCheckBox` 添加 `mousePressEvent`，左键点击直接切换勾选状态
- 增加 `PointingHandCursor` 光标提示可点击

## 窗口缩放宽高

- `setFixedSize` 改为 `setMinimumSize` + `resize`
- 实现 `nativeEvent` 处理 `WM_NCHITTEST`，支持 8 个方向拖拽边框缩放
- 右下角 `QSizeGrip` 作为视觉提示
- 关闭再打开恢复默认尺寸（280×380），位置仍持久化

## 边缘隐藏行为修复

- **Bug**: 拖动到屏幕边缘松手后，如果鼠标仍在窗口区域，窗口停住不隐藏，且之后鼠标离开也永不触发隐藏
- **修复**: 重写 `EdgeHideAnimator` 为三态状态机（`animator.py`）：

| 状态 | 行为 |
|------|------|
| NORMAL | 窗口在非边缘区域，常显 |
| HIDDEN | 贴边隐藏只露 4px 把手，180ms 轮询鼠标进入把手 → 滑出显示 |
| AT_EDGE | 把手触发显示后驻留，300ms 轮询鼠标离开窗口 → 滑回隐藏 |

- 贴边后**立即**触发隐藏动画（不再等待）
- `moveEvent` 检测窗口拖离边缘（x>0 且 y>0）时调用 `cancel_at_edge()` 退出自动隐藏，保持常显

## 关闭按钮

- 尺寸增大：12×12 → 18×18
- 默认灰色 `#999999`，线条更粗更清晰
- Hover 时红色圆形底色 + 白色 X，醒目且美观

## 任务悬停提示

- 鼠标悬停任务行显示 tooltip："创建于 YYYY-MM-DD HH:MM"
- `TaskRowWidget` 接收 `created_at` 参数，截取前 16 位（含小时分钟）
- 首次只显示年月日，后续改进为显示到分钟

## 终端退出修复

- **Bug**: 点击关闭按钮关闭窗口后，终端进程不退出
- **修复**: `_close_app` 末尾添加 `QApplication.quit()` 强制退出整个应用
- **Bug**: `Ctrl+C` 无法中断终端运行的程序
- **修复**: `main.py` 添加 `signal.signal(signal.SIGINT, signal.SIG_DFL)` 恢复默认中断行为

## PyInstaller 打包

- 清理 `main.py`：移除冗余的 `sys.path.insert` 和 `os` 导入，解决 PyInstaller onefile 环境下 `ModuleNotFoundError: No module named 'window'` 报错
- 打包命令：`pyinstaller --onefile --windowed --name "小猪桌面代办助手" --paths . main.py`
- 输出：`dist/小猪桌面代办助手.exe`（约 39MB），无需安装 Python 即可运行
