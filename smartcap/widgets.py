from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QComboBox,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QRadioButton,
    QHBoxLayout,
    QSizePolicy,
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
from typing import Callable
from PIL import Image
from .config import ConfigValues


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

    def __init__(self, config: ConfigValues, picture: Image.Image, prompt: str = ""):
        super().__init__()
        self.picture = picture
        self.prompt = prompt
        self.config = config

    def run(self):
        if self.config.provider == "Google":
            from google import genai
            from google.genai.types import GenerateContentConfig

            client = genai.Client(api_key=self.config.apiKey)
            response = client.models.generate_content(
                model=self.config.model,
                contents=[self.picture, self.prompt],
                config=GenerateContentConfig(
                    system_instruction=[
                        self.config.systemPrompt,
                    ],
                    temperature=0.1,
                ),
            )
        self.finished.emit(response.text)


class PromptWidget(QWidget):
    def __init__(self, screenshot: Image.Image, config: ConfigValues):
        super().__init__()
        self.config = config
        self.screenshot = screenshot
        vLayout = QVBoxLayout()
        self.screenshotLabel = QLabel(self)
        self.screenshotLabel.setMaximumWidth(500)
        self.screenshotLabel.setScaledContents(True)
        self.screenshotLabel.setPixmap(screenshot.toqpixmap())
        self.promptTextEdit = QTextEdit(self)
        self.promptTextEdit.setFocus()
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendPrompt)

        self.sendShortcut = QShortcut(QKeySequence("Ctrl+Return"), self.promptTextEdit)
        self.sendShortcut.activated.connect(self.sendButton.click)

        vLayout.addWidget(self.screenshotLabel)
        vLayout.addWidget(self.promptTextEdit)
        vLayout.addWidget(self.sendButton)

        hLayout = QHBoxLayout()
        hLayout.addLayout(vLayout)
        self.answer = QTextEdit(readOnly=True)
        self.answer.setMinimumWidth(300)
        sizePolicy = QSizePolicy()
        sizePolicy.setHorizontalPolicy(QSizePolicy.Expanding)
        sizePolicy.setVerticalPolicy(QSizePolicy.Expanding)
        self.answer.setSizePolicy(sizePolicy)
        self.answer.setAlignment(QtCore.Qt.AlignTop)
        subVLayout = QVBoxLayout()
        subVLayout.addWidget(self.answer)
        hLayout.addLayout(subVLayout)

        self.setLayout(hLayout)

    def sendPrompt(self):
        self.promptTextEdit.setDisabled(True)
        self.sendButton.setDisabled(True)

        # Use threading to prevent blocking the UI
        self.thread = QtCore.QThread()
        self.worker = Worker(
            config=self.config,
            picture=self.screenshot,
            prompt=self.promptTextEdit.toPlainText(),
        )
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.showAnswer)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def showAnswer(self, answer: str):
        self.answer.setMarkdown(answer)
        self.promptTextEdit.setEnabled(True)
        self.sendButton.setEnabled(True)


class ConfigWidget(QWidget):
    def __init__(self, config: ConfigValues):
        super().__init__()
        self.config = config

        providerLabel = QLabel("Provider:")
        providerInput = QComboBox()
        providerInput.addItem("Google")
        providerInput.setCurrentText(self.config.provider)
        providerInput.currentTextChanged.connect(lambda p: self.config.setProvider(p))
        modelLabel = QLabel("Model:")
        modelInput = QLineEdit(self.config.model)
        modelInput.textChanged.connect(lambda text: self.config.setModel(text))
        apiKeyLabel = QLabel("API Key:")
        apiKeyInput = QLineEdit(
            self.config.apiKey, echoMode=QLineEdit.EchoMode.Password
        )
        apiKeyInput.textChanged.connect(lambda text: self.config.setApiKey(text))
        apiKeyShowButton = QRadioButton("show")
        apiKeyShowButton.toggled.connect(
            lambda enabled: apiKeyInput.setEchoMode(
                QLineEdit.EchoMode.Normal if enabled else QLineEdit.EchoMode.Password
            )
        )
        apiKeyInputLayout = QHBoxLayout()
        apiKeyInputLayout.addWidget(apiKeyInput)
        apiKeyInputLayout.addWidget(apiKeyShowButton)
        grid = QGridLayout()
        grid.addWidget(providerLabel, 0, 0)
        grid.addWidget(providerInput, 0, 1)
        grid.addWidget(modelLabel, 1, 0)
        grid.addWidget(modelInput, 1, 1)
        grid.addWidget(apiKeyLabel, 2, 0)
        grid.addLayout(apiKeyInputLayout, 2, 1)

        systemPromptLabel = QLabel("System prompt:")
        systemPromptInput = QTextEdit(self.config.systemPrompt)
        systemPromptInput.textChanged.connect(
            lambda text: self.config.setSystemPrompt(text)
        )

        verticleLayout = QVBoxLayout()
        verticleLayout.addLayout(grid)
        verticleLayout.addWidget(systemPromptLabel)
        verticleLayout.addWidget(systemPromptInput)
        self.setLayout(verticleLayout)
