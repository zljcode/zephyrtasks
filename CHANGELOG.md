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

## PyInstaller 打包分发修复（别人电脑无法运行）

- **Bug**: 打包的 exe 在自己电脑可运行，发给别人无法运行（双击无反应/闪退）
- **根因 1**: Qt 平台插件 `qwindows.dll` 未被打包，或者目标路径错误。PyInstaller 运行时 hook 将 `QT_PLUGIN_PATH` 设为 `PyQt5/Qt5/plugins`，但 spec 中 `datas` 需要将 platforms 目录显式映射到正确目标路径 `PyQt5\Qt5\plugins\platforms`
- **根因 2**: 目标机器缺少 MSVC 运行时 DLL（`msvcp140.dll`、`vcruntime140.dll`、`vcruntime140_1.dll` 等）和 OpenGL 依赖 DLL（`libEGL.dll`、`libGLESv2.dll`、`d3dcompiler_47.dll`），这些在开发机上有（随 Python/VS 安装），但在干净 Windows 上不存在
- **修复**: 
  - `datas` 中显式将 Qt platforms 插件目录映射到 `PyQt5\Qt5\plugins\platforms`
  - `binaries` 中显式打包 9 个关键运行时 DLL：msvcp140/msvcp140_1/msvcp140_2、vcruntime140/vcruntime140_1、concrt140、libEGL、libGLESv2、d3dcompiler_47
  - `hiddenimports` 显式声明 PyQt5.QtCore/QtGui/QtWidgets/Qt5.sip
  - spec 文件通过 `SPECPATH` 自动定位 `.venv` 中的 PyQt5 路径，无需硬编码
- exe 体积由 39MB 增至 41MB（DLL 补充约 2MB）

## 跨电脑点击交互失效修复（别人电脑无法点击）

- **Bug**: exe 在别人电脑上窗口可渲染、可拖拽，但所有内部交互全部失灵（添加任务、完成任务、删除任务、关闭按钮均无法点击）
- **根因**: `nativeEvent` 处理 `WM_NCHITTEST` 时，对子控件区域（按钮、复选框、关闭按钮等）返回 `(False, 0)`，让 Windows 做默认判定。在无边框 + `WA_TranslucentBackground` 窗口下，某些 Windows 版本/更新的 `DefWindowProc` 会将未处理的 hit-test 区域判定为 `HTTRANSPARENT`（鼠标穿透），导致所有点击事件直接透传到背后窗口，子控件永远收不到事件
- **修复**: 将所有交互区域的 `WM_NCHITTEST` 返回值从 `(False, 0)` 改为 `(True, 1)`（`HTCLIENT`），显式告知 Windows 这些区域是正常客户区，不应穿透。同时新增 `else` 分支覆盖窗口内部非边缘区域，统一返回 `HTCLIENT`

## 虚拟环境配置

- 项目根目录创建 `.venv` 虚拟环境，仅安装 PyQt5 + PyInstaller 两个依赖
- `.gitignore` 添加 `.venv/` 排除项
- 打包命令改为使用虚拟环境：`.venv/Scripts/pyinstaller 小猪桌面代办助手.spec`
- 复现打包只需：`python -m venv .venv && .venv/Scripts/pip install pyqt5 pyinstaller`
