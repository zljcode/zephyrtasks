# PyInstaller 打包指南

## 工具介绍

使用 **PyInstaller** 将 Python + PyQt5 项目打包成单个 `.exe` 文件，用户无需安装 Python 或任何依赖即可直接运行。

## 1. 安装 PyInstaller

```bash
pip install pyinstaller
```

## 2. 代码准备

PyInstaller onefile 模式下，`__file__` 路径指向临时解压目录，因此不能依赖 `sys.path.insert(__file__)` 来定位模块。

**打包前需确保**：

- 不要用 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 这类代码
- 入口文件（如 `main.py`）中的 import 使用项目内的相对导入即可，PyInstaller 会自动分析和打包

```python
# main.py（打包友好写法）
import sys
from PyQt5.QtWidgets import QApplication
from window import MainWindow    # 直接相对导入，PyInstaller 能正确分析

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

## 3. 打包命令

在项目根目录执行：

```bash
cd ZephyrTasks
pyinstaller --onefile --windowed --name "小猪桌面代办助手" --paths . main.py
```

参数说明：

| 参数 | 作用 |
|------|------|
| `--onefile` | 打包成单个 exe 文件 |
| `--windowed` | 不显示终端黑窗口（GUI 程序专用） |
| `--name` | 输出 exe 文件名 |
| `--paths .` | 将当前目录加入模块搜索路径，确保找到本地模块 |
| `main.py` | 程序入口 |

## 4. 构建过程说明

执行命令后 PyInstaller 会依次完成：

1. **Analysis** — 分析 `main.py` 及其所有 import 链（`window.py` → `task_widgets.py`、`database.py`、`animator.py`、`utils.py`），并自动检测 PyQt5、sqlite3 等第三方依赖
2. **PYZ** — 将所有 `.pyc` 字节码打包成一个压缩包
3. **PKG** — 将 Python 解释器、动态链接库、资源文件打包
4. **EXE** — 将启动引导程序和 PKG 合并为最终的 `.exe`

构建输出目录：

```
ZephyrTasks/
├── build/                        # 构建中间文件（可删除）
│   └── 小猪桌面代办助手/
├── dist/
│   └── 小猪桌面代办助手.exe       # ← 最终的 exe 文件
└── 小猪桌面代办助手.spec          # PyInstaller 配置文件（可删除）
```

## 5. 清理与重新打包

```bash
# 清理旧构建
rm -rf build dist *.spec

# 重新打包
pyinstaller --onefile --windowed --name "小猪桌面代办助手" --paths . main.py
```

## 6. 常见问题

### Q: 运行 exe 报 `ModuleNotFoundError: No module named 'window'`

**原因**: 入口文件中有 `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` 等代码，onefile 模式下路径指向临时目录导致找不到模块。

**解决**: 删除此类代码，使用项目内常规 import 即可。

### Q: `Hidden import "sip" not found!`

可忽略，PyQt5 在此项目下不需要 sip 模块，不影响运行。

### Q: exe 体积太大（~39MB）

PyInstaller 将整个 Python 运行时 + PyQt5 库打包在一起，这是正常的。如需减小体积可考虑使用 `--onedir` 替代 `--onefile`（分发时需要整个文件夹）。

### Q: 想自定义 exe 图标

添加 `--icon=logo.ico` 参数：

```bash
pyinstaller --onefile --windowed --icon=logo.ico --name "小猪桌面代办助手" --paths . main.py
```

图标文件需为 `.ico` 格式。
