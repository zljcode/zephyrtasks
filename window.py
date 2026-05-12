import ctypes
import ctypes.wintypes
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy, QSizeGrip,
    QLabel, QApplication, QGraphicsOpacityEffect, QLineEdit,
)
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF, QTimer, QPropertyAnimation
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QPen, QFont, QLinearGradient

from database import Database
from task_widgets import TaskRowWidget, AddButton, InlineInput, CustomCheckBox, DeleteButton
from animator import EdgeHideAnimator
from utils import (
    get_default_position, load_window_position, save_window_position,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_offset = QPoint()
        self._dragging = False
        self.db = Database()
        self._last_action = None

        self._init_window()
        self._init_ui()
        self._load_tasks()

        self.edge_animator = EdgeHideAnimator(self)
        self._restore_position()

    def _init_window(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAutoFillBackground(False)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(0)

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
            'font: 15px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
            'color: #E8E0D5; background: transparent; padding-top: 6px;'
        )
        self.title_label._base_font_size = 15
        self.title_label._base_height = 36

        title_row.addStretch()
        title_row.addWidget(self.title_label)
        title_row.addStretch()

        self.counter_label = QLabel(self)
        self.counter_label.setStyleSheet(
            'font: 11px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
            'color: #8B8578; background: transparent; padding-top: 6px; padding-right: 6px;'
        )
        self.counter_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.counter_label.setFixedWidth(36)
        self.counter_label._base_font_size = 11
        title_row.addWidget(self.counter_label)

        main_layout.addWidget(title_container)

        # Separator line
        separator = QWidget(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(232,224,213,15); margin: 0 8px;")
        main_layout.addWidget(separator)

        self.input = InlineInput(self)
        self.input.submitted.connect(self._add_task)
        self.input.cancelled.connect(self._on_input_cancelled)
        self.input.setVisible(False)
        main_layout.addWidget(self.input)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollBar:vertical { width: 4px; background: transparent; }"
            "QScrollBar::handle:vertical { background: rgba(232,224,213,30); border-radius: 2px; min-height: 20px; }"
            "QScrollBar::handle:vertical:hover { background: rgba(232,224,213,51); }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
        )

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(6, 6, 6, 6)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        main_layout.addWidget(scroll, 1)

        # Separator line above bottom row
        sep_bottom = QWidget(self)
        sep_bottom.setFixedHeight(1)
        sep_bottom.setStyleSheet("background: rgba(232,224,213,20); margin: 0 8px;")
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
            'font: 12px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
            'color: #8B8578; background: transparent; padding: 4px 0;'
        )
        self.clear_btn._base_font_size = 12
        bottom_layout.addWidget(self.clear_btn)
        bottom_layout.addStretch()

        self.add_btn = AddButton()
        self.add_btn.clicked.connect(self._show_input)
        bottom_layout.addWidget(self.add_btn)

        # Toast notification for undo
        self.toast = QWidget(self)
        self.toast.setVisible(False)
        self.toast.setStyleSheet(
            "background: rgba(232, 224, 213, 242); border-radius: 6px;"
        )
        toast_layout = QHBoxLayout(self.toast)
        toast_layout.setContentsMargins(10, 6, 10, 6)
        toast_layout.setSpacing(8)

        self.toast_msg = QLabel(self)
        self.toast_msg.setStyleSheet(
            'color: #1A1D2E; font-size: 12px; background: transparent;'
        )
        toast_layout.addWidget(self.toast_msg)

        toast_layout.addStretch()

        self.toast_undo = QLabel("撤销", self)
        self.toast_undo.setCursor(Qt.PointingHandCursor)
        self.toast_undo.setStyleSheet(
            'color: #8B3A3A; font-size: 12px; font-weight: bold; background: transparent;'
        )
        toast_layout.addWidget(self.toast_undo)

        self.toast_opacity = QGraphicsOpacityEffect(self.toast)
        self.toast_opacity.setOpacity(0.0)
        self.toast.setGraphicsEffect(self.toast_opacity)

        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self._hide_toast)

        main_layout.addWidget(self.toast)

        main_layout.addWidget(bottom_row)

        # Size grip for visual resize indicator
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(14, 14)
        self._size_grip.setStyleSheet("background: transparent;")

        self._close_btn_rect = QRect(self.width() - 28, 8, 20, 20)

        self.clear_btn.mousePressEvent = self._on_clear_click
        self.toast_undo.mousePressEvent = lambda e: self._on_undo() if e.button() == Qt.LeftButton else None

    def _load_tasks(self):
        tasks = self.db.get_all_tasks()
        for task in tasks:
            self._add_task_row(task)
        self._update_counter(tasks)
        self._update_clear_btn(tasks)

    def _add_task_row(self, task):
        row = TaskRowWidget(task["id"], task["title"], task["completed"], task.get("created_at"))
        row.toggled.connect(self._on_task_toggled)
        row.deleted.connect(self._on_task_deleted)
        row.edited.connect(self._on_task_edited)
        insert_index = self.list_layout.count() - 1
        self.list_layout.insertWidget(insert_index, row)

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
        self._update_clear_btn(tasks)

    def _update_counter(self, tasks):
        total = len(tasks)
        pending = sum(1 for t in tasks if not t["completed"])
        if total > 0:
            self.counter_label.setText(f"{pending}/{total}")
        else:
            self.counter_label.setText("")

    def _update_clear_btn(self, tasks):
        completed_count = sum(1 for t in tasks if t["completed"])
        if completed_count > 0:
            self.clear_btn.setText(f"清空 {completed_count} 项已完成")
            self.clear_btn.setStyleSheet(
                f'font: 12px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
                'color: #C9A96E; background: transparent; padding: 4px 0;'
            )
            self.clear_btn.setEnabled(True)
        else:
            self.clear_btn.setText("清空已完成")
            self.clear_btn.setStyleSheet(
                f'font: 12px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
                'color: #5A564D; background: transparent; padding: 4px 0;'
            )
            self.clear_btn.setEnabled(False)

    def _on_clear_click(self, event):
        if event.button() == Qt.LeftButton and self.clear_btn.isEnabled():
            self._on_clear_completed()

    def _on_clear_completed(self):
        count = self.db.clear_completed_tasks()
        if count > 0:
            self._last_action = None
            self._refresh_tasks()
            self._show_toast(f"已清空 {count} 项已完成任务")

    def _show_toast(self, message):
        self.toast_msg.setText(message)
        self.toast.setVisible(True)
        self._animate_toast_opacity(1.0)
        self._toast_timer.start(2500)

    def _hide_toast(self):
        self._animate_toast_opacity(0.0)
        QTimer.singleShot(150, lambda: self.toast.setVisible(False))

    def _animate_toast_opacity(self, target):
        anim = QPropertyAnimation(self.toast_opacity, b"opacity")
        anim.setDuration(150)
        anim.setStartValue(self.toast_opacity.opacity())
        anim.setEndValue(target)
        anim.start()

    def _on_undo(self):
        if self._last_action is None:
            return
        action = self._last_action
        self._last_action = None
        if action["action"] == "delete":
            self.db.add_task(action["task"]["title"])
            self._refresh_tasks()
            self._show_toast("已撤销删除")
        elif action["action"] == "toggle":
            self.db.toggle_task(action["task"]["id"])
            self._refresh_tasks()
            self._show_toast("已撤销")

    def _show_input(self):
        self.input.show_input()
        self.add_btn.set_enabled(False)

    def _add_task(self, title):
        self.db.add_task(title)
        self.input.hide_input()
        self.add_btn.set_enabled(True)
        self._refresh_tasks()

    def _on_input_cancelled(self):
        self.add_btn.set_enabled(True)

    def _on_task_toggled(self, task_id):
        tasks = self.db.get_all_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task:
            self._last_action = {"action": "toggle", "task": task}
        self.db.toggle_task(task_id)
        self._refresh_tasks()
        if task:
            new_state = "已完成" if not task["completed"] else "已恢复"
            self._show_toast(f"「{task['title']}」{new_state}")

    def _on_task_deleted(self, task_id):
        tasks = self.db.get_all_tasks()
        task = next((t for t in tasks if t["id"] == task_id), None)
        if task:
            self._last_action = {"action": "delete", "task": task}
        self.db.delete_task(task_id)
        self._refresh_tasks()
        if task:
            self._show_toast(f"已删除「{task['title']}」")

    def _on_task_edited(self, task_id, new_title):
        self.db.update_task(task_id, new_title)
        self._refresh_tasks()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() == Qt.ControlModifier:
            focus_widget = QApplication.focusWidget()
            if isinstance(focus_widget, QLineEdit):
                super().keyPressEvent(event)
                return
            self._on_undo()
            return
        super().keyPressEvent(event)

    def _restore_position(self):
        x, y, hidden_edge = load_window_position()
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        if x is not None and y is not None:
            self.move(x, y)
            if hidden_edge:
                self.edge_animator._hidden_edge = hidden_edge
                geo = self.geometry()
                if hidden_edge == "left":
                    self.move(-geo.width() + self.edge_animator.HANDLE_SIZE, geo.y())
                else:
                    self.move(geo.x(), -geo.height() + self.edge_animator.HANDLE_SIZE)
                self.edge_animator.start_monitoring()
        else:
            pos = get_default_position()
            self.move(*pos)

    # ---- Painting ----

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        full_rect = QRectF(self.rect())

        # Multi-layer dark shadow
        shadow_color = QColor(0, 0, 0, 25)
        for i in range(5):
            offset = i * 1.5
            shadow_rect = full_rect.adjusted(-offset, offset * 0.6, offset, offset * 2.2)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, 12 + i, 12 + i)
            painter.fillPath(shadow_path, shadow_color)

        # Near shadow
        near_shadow = QPainterPath()
        near_shadow.addRoundedRect(full_rect.adjusted(0, 1, 0, 4), 10, 10)
        painter.fillPath(near_shadow, QColor(0, 0, 0, 40))

        # Card with deep navy gradient
        gradient = QLinearGradient(full_rect.topLeft(), full_rect.bottomLeft())
        gradient.setColorAt(0.0, QColor(26, 29, 46, 235))
        gradient.setColorAt(0.5, QColor(31, 35, 56, 235))
        gradient.setColorAt(1.0, QColor(28, 32, 64, 235))

        content_path = QPainterPath()
        content_path.addRoundedRect(full_rect, 10, 10)
        painter.fillPath(content_path, gradient)

        # Subtle gold-tinted border
        painter.setPen(QPen(QColor(201, 169, 110, 25), 0.5))
        painter.drawPath(content_path)

        # Close button
        self._close_btn_rect = QRect(self.width() - 28, 8, 20, 20)
        cb = self._close_btn_rect
        cursor = self.mapFromGlobal(self.cursor().pos())
        hover = cb.contains(cursor)

        if hover:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(160, 69, 69, 200))  # burgundy
            painter.drawRoundedRect(QRectF(cb), 5, 5)
            painter.setPen(QPen(QColor("#E8E0D5"), 1.8, Qt.SolidLine, Qt.RoundCap))
        else:
            painter.setPen(QPen(QColor("#8B8578"), 1.5, Qt.SolidLine, Qt.RoundCap))

        m = 5
        painter.drawLine(cb.left() + m, cb.top() + m, cb.right() - m, cb.bottom() - m)
        painter.drawLine(cb.right() - m, cb.top() + m, cb.left() + m, cb.bottom() - m)
        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_size_grip'):
            self._size_grip.move(self.width() - 16, self.height() - 16)
        self._update_scale()
        self.update()

    def _update_scale(self):
        scale = self.height() / DEFAULT_WINDOW_HEIGHT
        # Title
        fs = max(11, round(self.title_label._base_font_size * scale))
        h = max(28, round(self.title_label._base_height * scale))
        self.title_label.setFixedHeight(h)
        self.title_label.setStyleSheet(
            f'font: {fs}px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
            'color: #E8E0D5; background: transparent; padding-top: 6px;'
        )
        # Input
        self.input.set_scale(scale)
        # Add button
        self.add_btn.set_scale(scale)
        # Task rows
        for i in range(self.list_layout.count()):
            item = self.list_layout.itemAt(i)
            w = item.widget()
            if isinstance(w, TaskRowWidget):
                w.set_scale(scale)
        # Counter label scale
        cfs = max(9, round(self.counter_label._base_font_size * scale))
        self.counter_label.setStyleSheet(
            f'font: {cfs}px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
            'color: #8B8578; background: transparent; padding-top: 6px; padding-right: 6px;'
        )
        # Clear button scale
        cbfs = max(10, round(self.clear_btn._base_font_size * scale))
        completed_count = sum(1 for t in self.db.get_all_tasks() if t["completed"])
        if completed_count > 0:
            self.clear_btn.setStyleSheet(
                f'font: {cbfs}px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
                'color: #C9A96E; background: transparent; padding: 4px 0;'
            )
        else:
            self.clear_btn.setStyleSheet(
                f'font: {cbfs}px "幼圆", "YouYuan", "Segoe UI", sans-serif; '
                'color: #5A564D; background: transparent; padding: 4px 0;'
            )

    # ---- Drag ----

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._close_btn_rect.contains(event.pos()):
                return

            child = self.childAt(event.pos())
            if isinstance(child, (TaskRowWidget, InlineInput, AddButton, CustomCheckBox, DeleteButton)):
                return
            if child and child.parent() and isinstance(child.parent(), TaskRowWidget):
                return
            if isinstance(child, QSizeGrip):
                return

            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            self._dragging = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._close_btn_rect.contains(event.pos()):
                self._close_app()
                return
            if self._dragging:
                self._dragging = False
                self.edge_animator.check_edge_hide()
        super().mouseReleaseEvent(event)

    # ---- Native event for border resizing ----

    def nativeEvent(self, eventType, message):
        if eventType == b"windows_generic_MSG":
            try:
                msg = ctypes.wintypes.MSG.from_address(int(message))
                if msg.message == 0x84:  # WM_NCHITTEST
                    x = msg.lParam & 0xFFFF
                    y = (msg.lParam >> 16) & 0xFFFF
                    if x > 32767:
                        x -= 65536
                    if y > 32767:
                        y -= 65536
                    pos = self.mapFromGlobal(QPoint(x, y))

                    # Explicitly mark interactive areas as HTCLIENT so Windows
                    # doesn't treat them as HTTRANSPARENT on some OS versions
                    if self._close_btn_rect.contains(pos):
                        return True, 1  # HTCLIENT
                    child = self.childAt(pos)
                    if isinstance(child, (TaskRowWidget, InlineInput, AddButton,
                                         CustomCheckBox, DeleteButton, QSizeGrip)):
                        return True, 1  # HTCLIENT
                    if child and child.parent() and isinstance(child.parent(), TaskRowWidget):
                        return True, 1  # HTCLIENT

                    m = self._resize_margin
                    w, h = self.width(), self.height()

                    if pos.x() < m and pos.y() < m:
                        return True, 0xD  # HTTOPLEFT
                    elif pos.x() > w - m and pos.y() < m:
                        return True, 0xE  # HTTOPRIGHT
                    elif pos.x() < m and pos.y() > h - m:
                        return True, 0x10  # HTBOTTOMLEFT
                    elif pos.x() > w - m and pos.y() > h - m:
                        return True, 0x11  # HTBOTTOMRIGHT
                    elif pos.x() < m:
                        return True, 0xA  # HTLEFT
                    elif pos.x() > w - m:
                        return True, 0xB  # HTRIGHT
                    elif pos.y() < m:
                        return True, 0xC  # HTTOP
                    elif pos.y() > h - m:
                        return True, 0xF  # HTBOTTOM
                    else:
                        return True, 1  # HTCLIENT
            except Exception:
                pass

        return super().nativeEvent(eventType, message)

    def _close_app(self):
        self.edge_animator.stop_monitoring()
        geo = self.geometry()
        hidden_edge = self.edge_animator.hidden_edge
        if hidden_edge == "left":
            save_window_position(
                self._saved_normal_x() if hasattr(self, '_saved_nx') else 0,
                geo.y(), hidden_edge
            )
        elif hidden_edge == "top":
            save_window_position(
                geo.x(),
                self._saved_normal_y() if hasattr(self, '_saved_ny') else 0,
                hidden_edge
            )
        else:
            save_window_position(geo.x(), geo.y(), None)
        self.db.close()
        self.close()
        QApplication.quit()

    def moveEvent(self, event):
        geo = self.geometry()
        if not self.edge_animator.is_hidden and not self.edge_animator.is_animating:
            self._saved_nx = geo.x()
            self._saved_ny = geo.y()
            if geo.x() > 0 and geo.y() > 0:
                self.edge_animator.cancel_at_edge()
        self.update()
        super().moveEvent(event)

    def _saved_normal_x(self):
        return getattr(self, '_saved_nx', 0)

    def _saved_normal_y(self):
        return getattr(self, '_saved_ny', 0)
