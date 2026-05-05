from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QCheckBox, QLineEdit,
    QGraphicsOpacityEffect, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QSize, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont


class CustomCheckBox(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
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
        rect = QRectF(0.5, 0.5, 19, 19)
        if self.isChecked():
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(100, 100, 100, 60))
            painter.drawRoundedRect(rect, 4, 4)
            painter.setPen(QPen(QColor("#333333"), 2))
            font = QFont()
            font.setPixelSize(14)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, "✓")
        else:
            painter.setPen(QPen(QColor("#BBBBBB"), 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, 4, 4)
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
        self.setStyleSheet("color: #999999; font-size: 16px; background: transparent;")
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
        self.setStyleSheet("color: #FF5555; font-size: 16px; background: transparent;")
        self._animate_opacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet("color: #999999; font-size: 16px; background: transparent;")
        self._animate_opacity(0.6)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TaskRowWidget(QWidget):
    toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)

    def __init__(self, task_id, title, completed, created_at=None, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.setFixedHeight(40)
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

        self.delete_btn = DeleteButton()
        self.delete_btn.clicked.connect(self._on_delete)
        self.delete_btn.setVisible(False)
        layout.addWidget(self.delete_btn)

        self._separator_visible = True

    _BASE_FONT_SIZE = 16

    def _update_title_style(self, completed, font_size=None):
        fs = font_size or self._BASE_FONT_SIZE
        if completed:
            self.title_label.setStyleSheet(
                f'font: bold {fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #AAAAAA; text-decoration: line-through; background: transparent;'
            )
        else:
            self.title_label.setStyleSheet(
                f'font: bold {fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
                'color: #333333; background: transparent;'
            )

    def set_scale(self, scale):
        fs = max(10, round(self._BASE_FONT_SIZE * scale))
        self.setFixedHeight(max(28, round(40 * scale)))
        self._update_title_style(bool(self.checkbox.isChecked()), fs)

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

    def enterEvent(self, event):
        self.delete_btn.set_visible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.delete_btn.set_visible(False)
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 0, 0, 20), 0.5))
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
            'font-size: 32px; font-weight: bold; color: #666666; background: transparent;'
        )
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.5)
        self.setGraphicsEffect(self._opacity_effect)

    def enterEvent(self, event):
        self._animate_opacity(1.0)
        self.setStyleSheet(
            f'font-size: {self._current_font_size + 4}px; font-weight: bold; color: #444444; background: transparent;'
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_opacity(0.5)
        self.setStyleSheet(
            f'font-size: {self._current_font_size}px; font-weight: bold; color: #666666; background: transparent;'
        )
        super().leaveEvent(event)

    def set_scale(self, scale):
        self._current_font_size = max(16, round(self._BASE_FONT_SIZE * scale))
        self.setFixedHeight(max(36, round(self._BASE_HEIGHT * scale)))
        self.setStyleSheet(
            f'font-size: {self._current_font_size}px; font-weight: bold; color: #666666; background: transparent;'
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
            self._animate_opacity(0.5)
        else:
            self._animate_opacity(0.15)


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
            f'background: rgba(248, 245, 241, 0.9); color: #333333; '
            f'border: 1px solid #CCCCCC; border-radius: 6px; '
            f'font: bold {self._current_font_size}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            f'padding: 0 10px;'
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
