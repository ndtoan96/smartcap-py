from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
import sys
from .app import SmartCapApp
from .icon import getIcon


if __name__ == "__main__":
    app = QApplication([])
    iconImage = getIcon()
    icon = QIcon(iconImage.toqpixmap())
    smartcap = SmartCapApp(app, icon)
    sys.exit(app.exec())
