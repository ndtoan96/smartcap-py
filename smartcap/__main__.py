from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
)
from PySide6 import QtCore
from PySide6.QtGui import (
    QMouseEvent,
    QPainter,
    QPixmap,
    QColor,
    QShortcut,
    QKeySequence,
    QIcon,
)
import sys
from time import sleep
from typing import Callable
from PIL import Image, ImageGrab
from pathlib import Path


class OverlayWindow(QWidget):
    def __init__(
        self,
        screen_id: int,
        x: int,
        y: int,
        width: int,
        height: int,
        finishedCallback: Callable,
        cancelCallback: Callable,
    ):
        super().__init__()
        self.screen_id = screen_id
        self.finishedCallback = finishedCallback
        self.cancelCallback = cancelCallback
        self.startPos = None
        self.endPos = None

        self.setWindowTitle("SmartCap")
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.move(x, y)
        self.resize(width, height)
        self.quitShortcut = QShortcut(QKeySequence("Esc"), self)
        self.quitShortcut.activated.connect(self.cancelCallback)

        self.overlay = QLabel(self)
        self.pixmap = QPixmap(width, height)
        self.pixmap.fill(QColor(0, 0, 0, 100))
        self.overlay.setPixmap(self.pixmap)

        self.show()
        self.activateWindow()

    def mousePressEvent(self, event: QMouseEvent):
        if self.startPos is None:
            self.startPos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.startPos is not None and self.endPos is None:
            pixmap = self.pixmap.copy(0, 0, self.pixmap.width(), self.pixmap.height())
            painter = QPainter(pixmap)
            painter.setPen("white")
            x1 = self.startPos.x()
            y1 = self.startPos.y()
            x2 = event.position().x()
            y2 = event.position().y()
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            painter.end()
            self.overlay.setPixmap(pixmap)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self.endPos is None:
            self.endPos = event.position()
            self.hide()
            self.finishedCallback(self.screen_id, self.startPos, self.endPos)


class Worker(QtCore.QObject):
    finished = QtCore.Signal(str)

    def __init__(self, picture: Image.Image, prompt: str = ""):
        super().__init__()
        self.picture = picture
        self.prompt = prompt

    def run(self):
        sleep(2)
        self.finished.emit("This is a test answer")


class PromptWindow(QWidget):
    def __init__(self, iconPath: str, screenshot: Image.Image):
        super().__init__()
        self.screenshot = screenshot
        self.setWindowTitle("SmartCap")
        icon = QIcon(QPixmap(iconPath))
        self.setWindowIcon(icon)
        layout = QVBoxLayout()
        self.screenshotLabel = QLabel(self)
        self.screenshotLabel.setMaximumSize(800, 640)
        self.screenshotLabel.setScaledContents(True)
        self.screenshotLabel.setPixmap(screenshot.toqpixmap())
        self.promptTextEdit = QTextEdit(self)
        self.promptTextEdit.setFocus()
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendPrompt)

        self.sendShortcut = QShortcut(QKeySequence("Ctrl+Return"), self.promptTextEdit)
        self.sendShortcut.activated.connect(self.sendButton.click)

        layout.addWidget(self.screenshotLabel)
        layout.addWidget(self.promptTextEdit)
        layout.addWidget(self.sendButton)
        self.setLayout(layout)
        self.show()

    def sendPrompt(self):
        self.promptTextEdit.setDisabled(True)
        self.sendButton.hide()

        # Use threading to prevent blocking the UI
        self.thread = QtCore.QThread()
        self.worker = Worker(
            picture=self.screenshot, prompt=self.promptTextEdit.toPlainText()
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.showAnswer)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def showAnswer(self, answer: str):
        self.answer = QLabel(answer, self)
        self.answer.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.layout().addWidget(self.answer)


class SmartCapApp(object):
    def __init__(self, app: QApplication, iconPath: str):
        self.app = app
        self.iconPath = iconPath
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
        self.promptWindow = PromptWindow(iconPath, screenshot)


if __name__ == "__main__":
    app = QApplication([])
    iconPath = Path(__file__).parent.parent.joinpath("smartcap_icon.png")
    smartcap = SmartCapApp(app, iconPath)
    sys.exit(app.exec())
