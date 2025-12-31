# === Updated GUI + MAIN + Watched Code + Enhancements ===

# =============================
# File: Frontend/GUI.py
# =============================

import os
import sys
from dotenv import dotenv_values
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# === ENV & PATH ===
env_vars = dotenv_values(".env")
Assisistantname = env_vars.get("Assistantname", "Assistant")
current_div = os.getcwd()
old_chat_message = ""

DataDir = os.path.join(current_div, "Frontend", "Files")
GraphicsDir = os.path.join(current_div, "Frontend", "Graphics")

# === Utilities ===
def TempDirectoryPath(filename):
    os.makedirs(DataDir, exist_ok=True)
    return os.path.join(DataDir, filename)

def safe_write(path, data, retries=3):
    for _ in range(retries):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(data)
            return True
        except:
            time.sleep(0.05)
    return False

def AnswerModifier(text):
    return '\n'.join([line for line in text.split("\n") if line.strip()])

def QueryModifier(text):
    text = text.lower().strip().rstrip(".?!")
    question_words = ["how", "what", "who", "where", "when", "why"]
    if any(text.startswith(w) for w in question_words):
        return text.capitalize() + "?"
    return text.capitalize() + "."

def SetMicrophoneStatus(status):
    safe_write(TempDirectoryPath("Mic.data"), status)

def GetMicrophoneStatus():
    try:
        with open(TempDirectoryPath("Mic.data"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "False"

def SetAssistantStatus(status):
    safe_write(TempDirectoryPath("Status.data"), status)

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""

def showTextToScreen(text):
    safe_write(TempDirectoryPath("Responses.data"), text)

# === Chat Section ===
class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 40)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        self.chat_text_edit.setFont(QFont("", 13))
        layout.addWidget(self.chat_text_edit)

        self.label = QLabel()
        self.label.setStyleSheet("color: white; font-size:16px;")
        layout.addWidget(self.label, alignment=Qt.AlignRight)

        self.setStyleSheet("background-color: black;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(200)

    def loadMessages(self):
        global old_chat_message
        try:
            with open(TempDirectoryPath('Responses.data'), 'r', encoding='utf-8') as file:
                messages = file.read()
            if messages and messages != old_chat_message:
                self.addMessage(messages, 'white')
                old_chat_message = messages
        except:
            pass

    def SpeechRecogText(self):
        self.label.setText(GetAssistantStatus())

    def addMessage(self, message, color):
        cursor = self.chat_text_edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(message + "\n\n", fmt)
        self.chat_text_edit.setTextCursor(cursor)

# === GUI Entry ===
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        layout = QVBoxLayout()
        self.screen = ChatSection()
        layout.addWidget(self.screen)
        main_widget = QWidget()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        self.showFullScreen()

# === Entry ===
def GraphicalUserInterface():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


# =============================
# File: watched_code.py
# =============================

import os
import time
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
WATCHED_FILE = "watched_code.py"
LAST_CONTENT = ""

def read_file():
    with open(WATCHED_FILE, "r", encoding="utf-8") as f:
        return f.read()

def ask_chatgpt(prompt):
    print("[🤖 Asking ChatGPT...]")
    res = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Python assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content.strip()

def watch_file():
    global LAST_CONTENT
    while True:
        try:
            content = read_file()
            if content != LAST_CONTENT and len(content.strip()) > 5:
                LAST_CONTENT = content
                reply = ask_chatgpt(content)
                print("\n[✅ ChatGPT's Response:]\n", reply, "\n")
        except Exception as e:
            print("Error:", e)
        time.sleep(5)

if __name__ == "__main__":
    print(f"👀 Watching '{WATCHED_FILE}' for changes...\n")
    watch_file()


# =============================
# File: Main.py
# =============================

import os
import json
import subprocess
import threading
from time import sleep
from dotenv import dotenv_values
from Frontend.GUI import *
from Backend.Model import FirstLayerDIUM
from Backend.RealtimeSearchEngine import RealTimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech

env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
chatlog_path = os.path.join("Data", "ChatLog.json")
os.makedirs("Data", exist_ok=True)

DefaultMessage = f"""{Username}: Hello {Assistantname}, How are you?
{Assistantname}: Welcome {Username}. I am doing well. How may I help you?"""

if not os.path.exists(chatlog_path):
    with open(chatlog_path, "w", encoding="utf-8") as f:
        json.dump([], f)

def InitialExecution():
    SetMicrophoneStatus("False")
    showTextToScreen("")
    with open(chatlog_path, 'r', encoding='utf-8') as File:
        if len(File.read().strip()) < 5:
            showTextToScreen(DefaultMessage)

def MainExecution():
    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    showTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDIUM(Query)

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)
    Merged = " and ".join([" ".join(i.split()[1:]) for i in Decision])

    if R:
        SetAssistantStatus("Searching...")
        Answer = RealTimeSearchEngine(QueryModifier(Merged))
    else:
        Answer = ChatBot(QueryModifier(Merged))

    showTextToScreen(f"{Assistantname}: {Answer}")
    SetAssistantStatus("Answering ...")
    TextToSpeech(Answer)


def FirstThread():
    while True:
        if GetMicrophoneStatus() == "True":
            MainExecution()
        else:
            sleep(0.1)

def WatchCodeFile():
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class Watcher(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith("watched_code.py"):
                print("[🔁 watched_code.py modified]")

    observer = Observer()
    observer.schedule(Watcher(), path=os.getcwd(), recursive=False)
    observer.start()
    observer.join()

if __name__ == "__main__":
    InitialExecution()
    threading.Thread(target=FirstThread, daemon=True).start()
    threading.Thread(target=WatchCodeFile, daemon=True).start()
    GraphicalUserInterface()
