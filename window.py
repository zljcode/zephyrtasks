import ctypes
import ctypes.wintypes
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QSizeGrip, QLabel, QApplication,
)
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF
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

        # Separator line
        separator = QWidget(self)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background: rgba(61,50,38,15); margin: 0 8px;")
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
            "QScrollBar::handle:vertical { background: rgba(61,50,38,30); border-radius: 2px; min-height: 20px; }"
            "QScrollBar::handle:vertical:hover { background: rgba(61,50,38,60); }"
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

        # Separator line above add button
        sep_bottom = QWidget(self)
        sep_bottom.setFixedHeight(1)
        sep_bottom.setStyleSheet("background: rgba(0,0,0,25); margin: 0 8px;")
        main_layout.addWidget(sep_bottom)

        self.add_btn = AddButton()
        self.add_btn.clicked.connect(self._show_input)
        main_layout.addWidget(self.add_btn)

        # Size grip for visual resize indicator
        self._size_grip = QSizeGrip(self)
        self._size_grip.setFixedSize(14, 14)
        self._size_grip.setStyleSheet("background: transparent;")

        self._close_btn_rect = QRect(self.width() - 28, 8, 20, 20)

    def _load_tasks(self):
        tasks = self.db.get_all_tasks()
        for task in tasks:
            self._add_task_row(task)

    def _add_task_row(self, task):
        row = TaskRowWidget(task["id"], task["title"], task["completed"], task.get("created_at"))
        row.toggled.connect(self._on_task_toggled)
        row.deleted.connect(self._on_task_deleted)
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
        self.db.toggle_task(task_id)
        self._refresh_tasks()

    def _on_task_deleted(self, task_id):
        self.db.delete_task(task_id)
        self._refresh_tasks()

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

        # Multi-layer shadow for realistic depth
        shadow_color = QColor(61, 50, 38, 10)
        for i in range(5):
            offset = i * 1.2
            shadow_rect = full_rect.adjusted(-offset, offset * 0.8, offset, offset * 2.5)
            shadow_path = QPainterPath()
            shadow_path.addRoundedRect(shadow_rect, 12 + i, 12 + i)
            painter.fillPath(shadow_path, shadow_color)

        # Near shadow for tighter definition
        near_shadow = QPainterPath()
        near_shadow.addRoundedRect(full_rect.adjusted(0, 1, 0, 3), 10, 10)
        painter.fillPath(near_shadow, QColor(61, 50, 38, 20))

        # Card with subtle gradient
        gradient = QLinearGradient(full_rect.topLeft(), full_rect.bottomLeft())
        gradient.setColorAt(0.0, QColor(250, 248, 244, 232))
        gradient.setColorAt(0.5, QColor(250, 246, 240, 232))
        gradient.setColorAt(1.0, QColor(246, 241, 234, 232))

        content_path = QPainterPath()
        content_path.addRoundedRect(full_rect, 10, 10)
        painter.fillPath(content_path, gradient)

        # Refined border: warm tone, slightly thicker on top for light catch
        painter.setPen(QPen(QColor(61, 50, 38, 18), 0.5))
        painter.drawPath(content_path)

        # Close button — refined pill shape
        self._close_btn_rect = QRect(self.width() - 28, 8, 20, 20)
        cb = self._close_btn_rect
        cursor = self.mapFromGlobal(self.cursor().pos())
        hover = cb.contains(cursor)

        if hover:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(220, 110, 80, 200))
            painter.drawRoundedRect(QRectF(cb), 5, 5)
            painter.setPen(QPen(QColor("#FAF6F0"), 1.8, Qt.SolidLine, Qt.RoundCap))
        else:
            painter.setPen(QPen(QColor("#A09080"), 1.5, Qt.SolidLine, Qt.RoundCap))

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
            f'font: bold {fs}px "幼圆", "YouYuan", "Segoe UI", "PingFang SC", sans-serif; '
            'color: #3D3226; background: transparent; padding-top: 6px;'
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
