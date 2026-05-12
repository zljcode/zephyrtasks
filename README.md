<h1><img src="resources/logo_proper.ico" width="42" style="vertical-align: middle; margin-right: 8px">小猪桌面代办助手</h1>

极简风格悬浮桌面待办列表小组件，「月下书斋」深色主题，高保真 UI 设计。无标题栏、菜单栏、状态栏，通过悬浮窗和快捷交互完成待办管理。

<div align="center">
  <img src="resources/PixPin_2026-05-12_20-16-21.png" width="280" alt="截图" style="vertical-align: top;">
</div>

## 🚀 运行方式

### 方式一：直接运行（推荐）

前往 [Releases](https://github.com/zljcode/ZephyrTasks/releases) 页面下载最新版 `小猪桌面代办助手.exe`，双击即可运行，无需安装 Python 或任何依赖。

### 方式二：从源码运行

```bash
# 创建虚拟环境并安装依赖
python -m venv .venv
.venv/Scripts/pip install PyQt5

# 运行
python main.py
```

按 `Ctrl+C` 可在终端退出。

## 📋 功能说明

| 操作 | 行为 |
|------|------|
| 鼠标点击复选框 | 切换任务完成/未完成状态 |
| **双击任务文字** | 进入编辑模式，修改任务文本（Enter 保存 / Esc 取消） |
| 悬停任务行 | 显示创建时间（年月日 时:分） |
| 悬停任务行 + 点击 × | 删除任务 |
| 点击底部 "+" | 顶部出现输入框添加任务 |
| **标题栏右侧** | 显示待办/总数计数（如 "2/5"） |
| **点击底部「清空已完成」** | 一键清除所有已完成任务 |
| **Ctrl+Z / 点击 Toast 撤销** | 撤销上一次删除或完成操作 |
| 输入框按回车 | 确认添加 |
| 输入框按 Esc | 取消添加 |
| 拖动窗口空白处 | 移动悬浮窗 |
| 拖拽边框 | 放大缩小窗口（字体跟随缩放） |
| 拖到屏幕左/上边缘 | 贴边隐藏，仅露出 4px 把手 |
| 鼠标碰触把手 | 窗口滑入显示 |
| 鼠标离开窗口 | 自动滑回隐藏 |
| 将窗口拖离边缘 | 保持常显 |
| 右上角 × | 关闭应用 |

## 🎨 UI 特性

- 「月下书斋」深色主题：深海军蓝渐变背景（#1A1D2E → #1C2040），暖羊皮纸色文字（#E8E0D5）
- 黄铜金强调色（#C9A96E）：复选框、加号悬停、清空按钮激活态
- 勃艮第酒红危险色（#A04545）：删除按钮、关闭按钮悬停
- 字体：幼圆加粗，圆润风格，楷体标题（书卷气）
- 多层纯黑阴影，柔和金色边框
- 半透明 Toast 撤销提示（2.5 秒自动消失，点击可手动撤销）
- 加号按钮加粗放大（32px）
- 关闭按钮 hover 时酒红色圆形底色 + 暖白 X
- 窗口支持边框拖拽缩放，字体按比例自适应
- 关闭再打开恢复默认大小（280×380），位置持久化

## 💾 数据存储

- 数据目录：`C:\Users\<用户名>\.ZephyrTasks\`
  - `tasks.db` — 任务数据（SQLite，含创建/完成时间）
  - `config.json` — 窗口位置

## 📦 自行打包

```bash
# 安装打包依赖
.venv/Scripts/pip install pyinstaller

# 使用 spec 文件打包（含图标）
.venv/Scripts/pyinstaller 小猪桌面代办助手.spec
```

或手动指定参数：

```bash
.venv/Scripts/pyinstaller --onefile --windowed --name "小猪桌面代办助手" --icon=resources/logo_proper.ico --paths . main.py
```

输出：`dist/小猪桌面代办助手.exe`。更多细节详见 [PACKAGING.md](PACKAGING.md)。
