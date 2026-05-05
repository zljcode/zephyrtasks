import json
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect


CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ZephyrTasks", "config.json")

DEFAULT_WINDOW_WIDTH = 280
DEFAULT_WINDOW_HEIGHT = 380
MIN_WINDOW_WIDTH = 220
MIN_WINDOW_HEIGHT = 300


def get_available_geometry():
    screen = QApplication.primaryScreen()
    if screen:
        return screen.availableGeometry()
    return QRect(0, 0, 1920, 1080)


def get_default_position():
    geo = get_available_geometry()
    return geo.topRight().x() - DEFAULT_WINDOW_WIDTH - 50, geo.top() + 80


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f)


def save_window_position(x, y, hidden_edge=None):
    config = load_config()
    config["window_x"] = x
    config["window_y"] = y
    config["hidden_edge"] = hidden_edge
    save_config(config)


def load_window_position():
    config = load_config()
    x = config.get("window_x")
    y = config.get("window_y")
    hidden_edge = config.get("hidden_edge")
    if x is not None and y is not None:
        geo = get_available_geometry()
        if x < geo.left() - DEFAULT_WINDOW_WIDTH or x > geo.right():
            return None, None, None
        if y < geo.top() - DEFAULT_WINDOW_HEIGHT or y > geo.bottom():
            return None, None, None
        return x, y, hidden_edge
    return None, None, None


def is_position_on_screen(x, y):
    geo = get_available_geometry()
    return geo.left() <= x <= geo.right() and geo.top() <= y <= geo.bottom()
