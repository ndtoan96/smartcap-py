from PySide6.QtWidgets import QApplication, QWidget, QLabel, QTextEdit
from PySide6 import QtCore
from PySide6.QtGui import QMouseEvent, QPainter, QPixmap, QColor
import sys
from PIL import ImageGrab


class Window(QWidget):
    def __init__(self, size: QtCore.QSize):
        super().__init__()
        QApplication.setOverrideCursor(QtCore.Qt.CursorShape.CrossCursor)

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

        self.prompt = QTextEdit(self)
        self.prompt.hide()

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

            self.screenshot = ImageGrab.grab(
                all_screens=True,
                bbox=[
                    self.startPos.x(),
                    self.startPos.y(),
                    self.endPos.x(),
                    self.endPos.y(),
                ],
            ).toqpixmap()
            QApplication.restoreOverrideCursor()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    screens = app.screens()
    window = Window(app.primaryScreen().virtualSize())
    sys.exit(app.exec())
