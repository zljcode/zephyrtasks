from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QCheckBox, QLineEdit,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QSize, QRectF, QEvent
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QFont


class CustomCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QCheckBox {
                border: none;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 0px;
                height: 0px;
            }
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self.isChecked())
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = QRectF(1.5, 1.5, 19, 19)
        radius = 5.0

        if self.isChecked():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(200, 122, 90))
            painter.drawRoundedRect(r, radius, radius)

            # Elegant checkmark path
            painter.setPen(QPen(QColor("#FAF6F0"), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            check = QPainterPath()
            check.moveTo(5.5, 11)
            check.lineTo(9, 14.5)
            check.lineTo(16.5, 7)
            painter.drawPath(check)
        else:
            painter.setPen(QPen(QColor("#C4B8AA"), 1.5))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(r, radius, radius)

        painter.end()


class DeleteButton(QLabel):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("×", parent)
        self.setFixedSize(16, 16)
        self.setAlignment(Qt.AlignCenter)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)
        self.setStyleSheet("color: #A09080; font-size: 16px; background: transparent;")
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False

    def set_visible(self, visible):
        target = 0.6 if visible else 0.0
        self._animate_opacity(target)
        self.setVisible(True)

    def _animate_opacity(self, target):
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(150)
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(target)
        self._anim.start()

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet("color: #C8553D; font-size: 16px; background: transparent;")
        self._animate_opacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet("color: #A09080; font-size: 16px; background: transparent;")
        self._animate_opacity(0.6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TaskRowWidget(QWidget):
    toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)
    edited = pyqtSignal(int, str)

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
            'background: rgba(250, 246, 240, 0.92); color: #3D3226; border: 1px solid #C87A5A; '
            'border-radius: 4px; padding: 2px 6px; '
            f'font: bold {self._BASE_FONT_SIZE}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif;'
        )
        self._edit_input.returnPressed.connect(self._on_edit_done)
        layout.addWidget(self._edit_input)
        self._edit_input.installEventFilter(self)

        self.delete_btn = DeleteButton()
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setVisible(False)
        layout.addWidget(self.delete_btn)

        self._separator_visible = True
        self._editing = False

    _BASE_FONT_SIZE = 16

    def _update_title_style(self, completed, font_size=None):
        fs = font_size or self._BASE_FONT_SIZE
        if completed:
            self.title_label.setStyleSheet(
                f'font: bold {fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #B0A090; text-decoration: line-through; background: transparent;'
            )
        else:
            self.title_label.setStyleSheet(
                f'font: bold {fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #3D3226; background: transparent;'
            )

    def set_scale(self, scale):
        fs = max(10, round(self._BASE_FONT_SIZE * scale))
        self.setFixedHeight(max(28, round(44 * scale)))
        self._update_title_style(bool(self.checkbox.isChecked()), fs)
        edit_fs = max(10, round(self._BASE_FONT_SIZE * scale))
        self._edit_input.setStyleSheet(
            'background: rgba(250, 246, 240, 0.92); color: #3D3226; border: 1px solid #C87A5A; '
            'border-radius: 4px; padding: 2px 6px; '
            f'font: bold {edit_fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif;'
        )

    def _on_toggle(self, state):
        completed = state == Qt.Checked
        self._update_title_style(completed)
        self._animate_toggle()
        self.toggled.emit(self.task_id)

    def _animate_toggle(self):
        self._opacity_effect = QGraphicsOpacityEffect(self.title_label)
        self.title_label.setGraphicsEffect(self._opacity_effect)
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(300)
        self._anim.setStartValue(0.5)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def _on_delete(self):
        self.deleted.emit(self.task_id)

    def mouseDoubleClickEvent(self, event):
        """双击任务行文字进入编辑模式"""
        if event.button() == Qt.LeftButton:
            if event.pos().x() > 30:  # 排除复选框区域
                self._enter_edit_mode()
        super().mouseDoubleClickEvent(event)

    def _enter_edit_mode(self):
        self._editing = True
        self._edit_input.setText(self.title_label.text())
        self._edit_input.setVisible(True)
        self._edit_input.setFocus()
        self._edit_input.selectAll()
        self.title_label.setVisible(False)

    def _exit_edit_mode(self, save):
        self._editing = False
        if save:
            new_title = self._edit_input.text().strip()
            if new_title and new_title != self.title_label.text():
                self.edited.emit(self.task_id, new_title)
        self._edit_input.setVisible(False)
        self.title_label.setVisible(True)

    def _on_edit_done(self):
        self._exit_edit_mode(True)

    def enterEvent(self, event):
        if not self._editing:
            self.delete_btn.set_visible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.set_visible(False)
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        if obj == self._edit_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self._exit_edit_mode(False)
                return True
        if obj == self._edit_input and event.type() == QEvent.FocusOut:
            self._exit_edit_mode(False)
            return True
        return super().eventFilter(obj, event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(61, 50, 38, 12), 0.5))
        painter.drawLine(
            12, self.height() - 1,
            self.width() - 12, self.height() - 1,
        )
        painter.end()


class AddButton(QLabel):
    clicked = pyqtSignal()
    _BASE_FONT_SIZE = 32
    _BASE_HEIGHT = 52

    def __init__(self, parent=None):
        super().__init__("+", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedHeight(self._BASE_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self._current_font_size = self._BASE_FONT_SIZE
        self.setStyleSheet(
            'font-size: 32px; font-weight: bold; color: #8C7B6D; background: transparent;'
        )
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.4)
        self.setGraphicsEffect(self._opacity_effect)

    def enterEvent(self, event):
        self._animate_opacity(1.0)
        self.setStyleSheet(
            f'font-size: {self._current_font_size + 4}px; font-weight: bold; color: #C87A5A; background: transparent;'
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_opacity(0.4)
        self.setStyleSheet(
            f'font-size: {self._current_font_size}px; font-weight: bold; color: #8C7B6D; background: transparent;'
        )
        super().leaveEvent(event)

    def set_scale(self, scale):
        self._current_font_size = max(16, round(self._BASE_FONT_SIZE * scale))
        self.setFixedHeight(max(36, round(self._BASE_HEIGHT * scale)))
        self.setStyleSheet(
            f'font-size: {self._current_font_size}px; font-weight: bold; color: #8C7B6D; background: transparent;'
        )

    def _animate_opacity(self, target):
        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(150)
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(target)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_enabled(self, enabled):
        self.setEnabled(enabled)
        if enabled:
            self._animate_opacity(0.4)
        else:
            self._animate_opacity(0.12)


class InlineInput(QLineEdit):
    cancelled = pyqtSignal()
    submitted = pyqtSignal(str)
    _BASE_FONT_SIZE = 16
    _BASE_HEIGHT = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self._BASE_HEIGHT)
        self._current_font_size = self._BASE_FONT_SIZE
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(
            f'background: rgba(250, 246, 240, 0.92); color: #3D3226; '
            f'border: 1px solid #C4B8AA; border-radius: 8px; '
            f'font: bold {self._current_font_size}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            f'padding: 0 12px;'
        )
        self.setPlaceholderText("")
        self.returnPressed.connect(self._on_return)
        self.setVisible(False)

    def show_input(self):
        self.setVisible(True)
        self.clear()
        self.setFocus()

    def hide_input(self):
        self.setVisible(False)
        self.clear()
        self.clearFocus()

    def _on_return(self):
        text = self.text().strip()
        if text:
            self.submitted.emit(text)
        self.hide_input()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide_input()
            self.cancelled.emit()
            return
        super().keyPressEvent(event)

    def set_scale(self, scale):
        self._current_font_size = max(10, round(self._BASE_FONT_SIZE * scale))
        self.setFixedHeight(max(24, round(self._BASE_HEIGHT * scale)))
        self._apply_style()
