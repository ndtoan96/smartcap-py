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
)
import sys
from PIL import ImageGrab


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
        self.sendButton.setDisabled(True)
        print(self.promptTextEdit.toPlainText())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screens = app.screens()
    window = OverlayWindow(app.primaryScreen().virtualSize())
    sys.exit(app.exec())
