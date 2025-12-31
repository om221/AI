
import os
import sys
from dotenv import dotenv_values
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QFrame, QLabel, QSizePolicy
)
from PyQt5.QtGui import QIcon, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat
from PyQt5.QtCore import Qt, QSize, QTimer

# === ENV & PATH ===
env_vars = dotenv_values(".env")
Assisistantname = env_vars.get("Assistantname", "Assistant")
current_div = os.getcwd()
old_chat_message = ""

DataDir = os.path.join(current_div, "Frontend", "Files")
GraphicsDir = os.path.join(current_div, "Frontend", "Graphics")

# === Utility Functions ===
def TempDirectoryPath(filename):
    path = os.path.join("Frontend", "Files")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, filename)

def AnswerModifier(text):
    return '\n'.join([line for line in text.split("\n") if line.strip()])

def QueryModifier(text):
    new_query = text.lower().strip()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]
    if any(word + " " in new_query for word in question_words):
        new_query = new_query.rstrip(".!?") + "?"
    else:
        new_query = new_query.rstrip(".!?") + "."
    return new_query.capitalize()

def SetMicrophoneStatus(command):
    try:
        os.makedirs(DataDir, exist_ok=True)
        with open(os.path.join(DataDir, "Mic.data"), "w", encoding="utf-8") as file:
            file.write(command.strip())
    except Exception as e:
        print("[❌ Mic Write Error]:", e)

def GetMicrophoneStatus():
    try:
        with open(os.path.join(DataDir, "Mic.data"), "r", encoding='utf-8') as file:
            return file.read().strip()
    except:
        return "False"

def SetAssistantStatus(Status):
    try:
        with open(os.path.join(DataDir, "Status.data"), 'w', encoding='utf-8') as file:
            file.write(Status)
    except Exception as e:
        print("[❌ Status Write Error]:", e)

def GetAssistantStatus():
    try:
        with open(os.path.join(DataDir, "Status.data"), 'r', encoding='utf-8') as file:
            return file.read()
    except:
        return ""

def GraphicsPath(filename):
    return os.path.join(GraphicsDir, filename)

def DataPath(filename):
    return os.path.join(DataDir, filename)

def showTextToScreen(text):
    try:
        with open(DataPath("Responses.data"), "w", encoding="utf-8") as file:
            file.write(text)
    except Exception as e:
        print("[❌ Response Write Error]:", e)

# === Chat Section ===
class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 40)
        layout.setSpacing(10)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setFont(QFont("", 13))
        layout.addWidget(self.chat_text_edit)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsPath('Jarvis1.gif'))
        movie.setScaledSize(QSize(280,170))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        movie.start()
        layout.addWidget(self.gif_label)

        self.label = QLabel()
        self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top:-30px")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        self.setStyleSheet("background-color: black;")
        layout.setStretch(1, 1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    def loadMessages(self):
        global old_chat_message
        try:
            with open(DataPath('Responses.data'), 'r', encoding='utf-8') as file:
                messages = file.read()
            if messages and messages != old_chat_message:
                self.addMessage(messages, 'white')
                old_chat_message = messages
        except:
            pass

    def SpeechRecogText(self):
        try:
            with open(DataPath('Status.data'), 'r', encoding='utf-8') as file:
                self.label.setText(file.read())
        except:
            pass

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        block_fmt = QTextBlockFormat()
        block_fmt.setTopMargin(10)
        block_fmt.setLeftMargin(10)
        fmt.setForeground(QColor(color))
        cursor.setBlockFormat(block_fmt)
        cursor.insertText(message + "\n", fmt)
        self.chat_text_edit.setTextCursor(cursor)

# === Initial Mic Toggle Screen ===
class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 150)

        gif_label = QLabel()
        movie = QMovie(GraphicsPath('Jarvis1.gif'))
        gif_label.setMovie(movie)
        movie.setScaledSize(QSize(960, 540))
        gif_label.setAlignment(Qt.AlignCenter)
        movie.start()

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(75, 75)
        self.toggled = True
        self.load_icon(GraphicsPath('Mic_on.png'))
        self.icon_label.mousePressEvent = self.toggle_icon

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px;")

        layout.addWidget(gif_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(100)

    def SpeechRecogText(self):
        try:
            with open(DataPath('Status.data'), "r", encoding='utf-8') as file:
                self.label.setText(file.read())
        except:
            pass

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        self.icon_label.setPixmap(pixmap.scaled(width, height))

    def toggle_icon(self, event=None):
        self.toggled = not self.toggled
        if self.toggled:
            self.load_icon(GraphicsPath('Mic_on.png'))
            SetMicrophoneStatus("True")
        else:
            self.load_icon(GraphicsPath('Mic_off.png'))
            SetMicrophoneStatus("False")

# === Chat View ===
class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(ChatSection())
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")

# === Top Navigation Bar ===
class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.initUI()

    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignRight)

        home_btn = QPushButton(" Home")
        home_btn.setIcon(QIcon(GraphicsPath("Home.png")))
        home_btn.setStyleSheet("height:40px; background-color:white; color: black")
        chat_btn = QPushButton(" Chat")
        chat_btn.setIcon(QIcon(GraphicsPath("Chats.png")))

        minimize_btn = QPushButton()
        minimize_btn.setIcon(QIcon(GraphicsPath('Minimize2.png')))
        minimize_btn.setStyleSheet("background-color:white")
        minimize_btn.clicked.connect(self.parent().showMinimized)

        self.maximize_btn = QPushButton()
        self.max_icon = QIcon(GraphicsPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsPath('Minimize.png'))
        self.maximize_btn.setIcon(self.max_icon)
        self.maximize_btn.setStyleSheet("background-color:white")
        self.maximize_btn.clicked.connect(self.maximizeWindow)

        close_btn = QPushButton()
        close_btn.setIcon(QIcon(GraphicsPath('Close.png')))
        close_btn.setStyleSheet("background-color:white")
        close_btn.clicked.connect(self.parent().close)

        title = QLabel(f" {Assisistantname.capitalize()} AI  ")
        title.setStyleSheet("color: black; font-size: 18px; background-color:white")

        home_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        chat_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))

        layout.addWidget(title)
        layout.addStretch(1)
        layout.addWidget(home_btn)
        layout.addWidget(chat_btn)
        layout.addStretch(1)
        layout.addWidget(minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(close_btn)

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_btn.setIcon(self.max_icon)
        else:
            self.parent().showMaximized()
            self.maximize_btn.setIcon(self.restore_icon)

# === Main GUI Window ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        desktop = QApplication.desktop()
        screen_width = desktop.screenGeometry().width()
        screen_height = desktop.screenGeometry().height()
        stacked_widget = QStackedWidget(self)
        stacked_widget.addWidget(InitialScreen())
        stacked_widget.addWidget(MessageScreen())

        top_bar = CustomTopBar(self, stacked_widget)
        self.setMenuWidget(top_bar)
        self.setCentralWidget(stacked_widget)
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

# === Entry Point ===
def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
