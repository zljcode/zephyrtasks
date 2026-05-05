import sys
import signal

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from window import MainWindow


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
