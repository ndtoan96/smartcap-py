from PySide6.QtWidgets import QApplication, QTabWidget
from PySide6.QtGui import QIcon
from PySide6 import QtCore
from PIL import ImageGrab
from .widgets import OverlayWindow, ConfigWidget, PromptWidget
from .config import ConfigValues


class SmartCapApp(object):
    def __init__(self, app: QApplication, icon: QIcon):
        self.app = app
        self.icon = icon
        self.overlayWindows = []
        self.openOverlayWindow()

    def openOverlayWindow(self):
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.CrossCursor)
        for i, screen in enumerate(self.app.screens()):
            x = screen.geometry().x()
            y = screen.geometry().y()
            w = screen.geometry().width()
            h = screen.geometry().height()
            self.overlayWindows.append(
                OverlayWindow(i, x, y, w, h, self.beginPrompt, self.closeAllWindows)
            )

    def closeAllWindows(self):
        for window in self.overlayWindows:
            window.close()

    def beginPrompt(
        self, screen_id: int, startPos: QtCore.QPointF, endPos: QtCore.QPointF
    ):
        QApplication.restoreOverrideCursor()
        self.closeAllWindows()
        screen = self.app.screens()[screen_id]
        x1 = screen.geometry().x() + startPos.x() * screen.devicePixelRatio()
        y1 = screen.geometry().y() + startPos.y() * screen.devicePixelRatio()
        x2 = screen.geometry().x() + endPos.x() * screen.devicePixelRatio()
        y2 = screen.geometry().y() + endPos.y() * screen.devicePixelRatio()
        screenshot = ImageGrab.grab(
            (int(x1), int(y1), int(x2), int(y2)), all_screens=True
        )
        self.config = ConfigValues()
        self.configWidget = ConfigWidget(self.config)
        self.promptWidget = PromptWidget(screenshot, config=self.config)
        self.appWindow = QTabWidget()
        self.appWindow.setWindowTitle("SmartCap")
        self.appWindow.setWindowIcon(self.icon)
        self.appWindow.setBaseSize(800, 640)
        self.appWindow.addTab(self.promptWidget, "Prompt")
        self.appWindow.addTab(self.configWidget, "Config")
        self.appWindow.show()
