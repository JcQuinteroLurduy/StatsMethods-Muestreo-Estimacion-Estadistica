import sys
import os

# Asegura que los imports relativos del proyecto funcionen
sys.path.insert(0, os.path.dirname(__file__))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from ui.main_window import MainWindow


def main() -> None:
    # Hi-DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps,   True)

    app = QApplication(sys.argv)
    app.setApplicationName("StatSampler Pro")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("StatSampler")

    # Fuente base
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
