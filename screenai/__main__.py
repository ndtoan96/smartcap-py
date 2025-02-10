from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
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
    QAction,
)
import sys
from PIL import ImageGrab
from time import sleep


class OverlayWindow(QWidget):
    def __init__(self, size: QtCore.QSize):
        super().__init__()
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.CrossCursor)

        self.setWindowTitle("ScreenAI Overlay")

        self.startPos = None
        self.endPos = None

        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        self.move(0, 0)
        self.resize(size.width(), size.height())
        quitShortcut = QShortcut(QKeySequence("Esc"), self)
        quitShortcut.activated.connect(self.close)

        self.overlay = QLabel(self)
        self.pixmap = QPixmap(size.width(), size.height())
        self.pixmap.fill(QColor(0, 0, 0, 100))
        self.overlay.setPixmap(self.pixmap)

        self.show()

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
            QApplication.restoreOverrideCursor()
            self.hide()
            self.promptWindow = PromptWindow(self.startPos, self.endPos)


class Worker(QtCore.QObject):
    finished = QtCore.Signal(str)

    def __init__(self, picture: QPixmap, prompt: str = ""):
        super().__init__()
        self.picture = picture
        self.prompt = prompt

    def run(self):
        sleep(2)
        self.finished.emit("This is a test answer")


class PromptWindow(QWidget):
    def __init__(self, startPos: QtCore.QPointF, endPos: QtCore.QPointF):
        super().__init__()
        self.setWindowTitle("ScreenAI")
        self.screenshot = ImageGrab.grab(
            all_screens=True,
            bbox=[
                min(startPos.x(), endPos.x()),
                min(startPos.y(), endPos.y()),
                max(endPos.x(), endPos.x()),
                max(endPos.y(), endPos.y()),
            ],
        ).toqpixmap()
        layout = QVBoxLayout()
        self.screenshotLabel = QLabel(self)
        self.screenshotLabel.setPixmap(self.screenshot)
        self.promptTextEdit = QTextEdit(self)
        self.promptTextEdit.setFocus()
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendPrompt)

        sendShortcut = QShortcut(QKeySequence("Ctrl+Return"), self.promptTextEdit)
        sendShortcut.activated.connect(self.sendButton.click)

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


class TrayHandler(object):
    def __init__(self, app: QApplication):
        self.app = app

    def quitApp(self):
        self.app.quit()

    def onTrayActivated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.openOverlayWindow()

    def openOverlayWindow(self):
        self.overlayWindow = OverlayWindow(app.primaryScreen().virtualSize())

    def openConfigureWindow(self):
        pass


if __name__ == "__main__":
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    tray = QSystemTrayIcon()
    tray.setIcon(QIcon("eye-icon.svg"))
    tray.setVisible(True)

    handler = TrayHandler(app)

    tray.activated.connect(handler.onTrayActivated)

    # Create the menu
    menu = QMenu()
    quitAction = QAction("Quit")
    quitAction.triggered.connect(handler.quitApp)
    captureAction = QAction("Capture")
    captureAction.triggered.connect(handler.openOverlayWindow)
    configureAction = QAction("Configure")
    configureAction.triggered.connect(handler.openConfigureWindow)
    menu.addActions([captureAction, configureAction, quitAction])

    tray.setContextMenu(menu)

    sys.exit(app.exec())
