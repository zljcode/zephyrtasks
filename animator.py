from PyQt5.QtCore import QObject, QPropertyAnimation, QEasingCurve, QTimer, QRect
from PyQt5.QtGui import QCursor


class EdgeHideAnimator(QObject):
    HANDLE_SIZE = 4

    def __init__(self, window, parent=None):
        super().__init__(parent)
        self.window = window
        self._hidden_edge = None       # Hidden at this edge
        self._at_edge = None           # Visible but at edge (after hover-show)
        self._animation = None
        self._animating = False
        self._saved_geometry = None

        # Poll handle area when HIDDEN
        self._hover_timer = QTimer(self)
        self._hover_timer.setInterval(180)
        self._hover_timer.timeout.connect(self._check_handle_hover)

        # Poll mouse-leave when AT_EDGE (visible at edge)
        self._leave_timer = QTimer(self)
        self._leave_timer.setInterval(300)
        self._leave_timer.timeout.connect(self._check_mouse_leave)

    # ---- Public API ----

    def check_edge_hide(self):
        """Called on mouse release after drag. Hide immediately if at edge."""
        if self._animating or self._hidden_edge or self._at_edge:
            return

        x = self.window.x()
        y = self.window.y()

        if x <= 0:
            self._hide_to_edge("left")
        elif y <= 0:
            self._hide_to_edge("top")

    def cancel_at_edge(self):
        """Called when user drags window away from edge — keep it visible."""
        if self._at_edge:
            self._at_edge = None
            self._leave_timer.stop()

    def start_monitoring(self):
        if self._hidden_edge:
            self._hover_timer.start()

    def stop_monitoring(self):
        self._hover_timer.stop()
        self._leave_timer.stop()

    @property
    def hidden_edge(self):
        return self._hidden_edge

    @property
    def is_animating(self):
        return self._animating

    @property
    def is_hidden(self):
        return self._hidden_edge is not None

    # ---- HIDE ----

    def _hide_to_edge(self, edge):
        self._animating = True
        self._hidden_edge = edge
        geo = self.window.geometry()
        self._saved_geometry = geo

        if edge == "left":
            target = QRect(-geo.width() + self.HANDLE_SIZE, geo.y(),
                           geo.width(), geo.height())
        else:
            target = QRect(geo.x(), -geo.height() + self.HANDLE_SIZE,
                           geo.width(), geo.height())

        self._start_animation(geo, target)

    def _on_hide_finished(self):
        self._animating = False
        if self._is_cursor_in_handle():
            QTimer.singleShot(300, self._on_hide_finished)
        else:
            self._hover_timer.start()

    # ---- SHOW (from HIDDEN, mouse entered handle) ----

    def _check_handle_hover(self):
        if not self._hidden_edge or self._animating:
            return
        if self._is_cursor_in_handle():
            self._show_from_edge()

    def _show_from_edge(self):
        self._animating = True
        current_geo = self.window.geometry()
        edge = self._hidden_edge
        self._hidden_edge = None
        self._at_edge = edge
        self._hover_timer.stop()

        if edge == "left":
            target_x = max(0, self._saved_geometry.x() if self._saved_geometry else 0)
            target = QRect(target_x, current_geo.y(),
                           current_geo.width(), current_geo.height())
        else:
            target_y = max(0, self._saved_geometry.y() if self._saved_geometry else 0)
            target = QRect(current_geo.x(), target_y,
                           current_geo.width(), current_geo.height())

        self._start_animation(current_geo, target, on_finish=self._on_show_finished)

    def _on_show_finished(self):
        self._animating = False
        self._leave_timer.start()

    # ---- RE-HIDE (from AT_EDGE, mouse left window) ----

    def _check_mouse_leave(self):
        if not self._at_edge or self._animating:
            self._leave_timer.stop()
            return

        cursor = QCursor().pos()
        win_geo = self.window.geometry()

        if not win_geo.contains(cursor):
            self._leave_timer.stop()
            edge = self._at_edge
            self._at_edge = None
            self._hide_to_edge(edge)

    # ---- Helpers ----

    def _is_cursor_in_handle(self):
        cursor = QCursor().pos()
        win_geo = self.window.geometry()
        target_edge = self._hidden_edge or self._at_edge
        if target_edge == "left":
            handle_rect = QRect(0, win_geo.y(), self.HANDLE_SIZE + 10, win_geo.height())
        else:
            handle_rect = QRect(win_geo.x(), 0, win_geo.width(), self.HANDLE_SIZE + 10)
        return handle_rect.contains(cursor)

    def _start_animation(self, start_geo, end_geo, on_finish=None):
        if self._animation:
            self._animation.stop()

        self._animation = QPropertyAnimation(self.window, b"geometry")
        self._animation.setDuration(200)
        self._animation.setStartValue(start_geo)
        self._animation.setEndValue(end_geo)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

        if on_finish:
            self._animation.finished.connect(on_finish)
        else:
            self._animation.finished.connect(self._on_hide_finished)

        self._animation.start()
