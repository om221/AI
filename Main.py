import os
import json
import subprocess
import threading
import keyboard
import asyncio
import requests
import webbrowser
from time import sleep
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from pywhatkit import search, playonyt
from AppOpener import close, open as appopen
from rich import print
from groq import Groq

# ==== GUI + Modules ====
from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    showTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)
from Backend.Model import FirstLayerDIUM
from Backend.RealtimeSearchEngine import RealTimeSearchEngine
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import ChatBot
from Backend.TextToSpeech import TextToSpeech

# ==== ENV ====
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0.4896.75 Safari/537.36'
messages = []
SystemChatBot = [{"role": "system", "content": f"Hello, I am {os.environ.get('Username', 'Assistant')}, You're a content writer. You have to write content like a letter"}]

functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]
DefaultMessage = f"""{Username}: Hello {Assistantname}, How are you?\n{Assistantname}: Welcome {Username}. I am doing well. How may I help you?"""
chatlog_path = os.path.join("Data", "ChatLog.json")
subprocesses = []

# === AI Content Writer ===
def ContentWriterAI(prompt):
    messages.append({"role": "user", "content": prompt})
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=SystemChatBot + messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        stream=True
    )
    answer = ""
    for chunk in completion:
        if chunk.choices[0].delta.content:
            answer += chunk.choices[0].delta.content
    answer = answer.replace("</s>", "")
    messages.append({"role": "assistant", "content": answer})
    return answer

# === Command Functions ===
def GoogleSearch(topic): search(topic); return True
def YouTubeSearch(topic): webbrowser.open(f"https://www.youtube.com/results?search_query={topic}"); return True
def PlayYoutube(query): playonyt(query); return True
def Content(topic):
    topic = topic.replace("Content", "").strip()
    result = ContentWriterAI(topic)
    os.makedirs("Data", exist_ok=True)
    with open(f"Data/{topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(result)
    return True
def OpenApp(app, sess=requests.session()):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        def extract_links(html):
            soup = BeautifulSoup(html, 'html.parser')
            return [a.get('href') for a in soup.find_all('a', {'jsname': 'UWckNb'})]
        def search_google(q):
            res = sess.get(f"https://www.google.com/search?q={q}", headers={"User-Agent": useragent})
            return res.text if res.status_code == 200 else None
        html = search_google(app)
        links = extract_links(html) if html else []
        if links: webbrowser.open(links[0])
        return True
def CloseApp(app):
    try:
        if "chrome" not in app:
            close(app, match_closest=True, output=True, throw_error=True)
        return True
    except: return False
def System(command):
    actions = {
        "mute": lambda: keyboard.press_and_release("volume mute"),
        "unmute": lambda: keyboard.press_and_release("volume mute"),
        "volume up": lambda: keyboard.press_and_release("volume up"),
        "volume down": lambda: keyboard.press_and_release("volume down")
    }
    action = actions.get(command.strip())
    if action: action()
    return True

# === Async Task Translator ===
async def TranslateAndExecute(commands: list[str]):
    tasks = []
    for command in commands:
        cmd = command.strip().lower()
        if cmd.startswith("open"): tasks.append(asyncio.to_thread(OpenApp, cmd.removeprefix("open").strip()))
        elif cmd.startswith("close"): tasks.append(asyncio.to_thread(CloseApp, cmd.removeprefix("close").strip()))
        elif cmd.startswith("play"): tasks.append(asyncio.to_thread(PlayYoutube, cmd.removeprefix("play").strip()))
        elif cmd.startswith("content"): tasks.append(asyncio.to_thread(Content, cmd.removeprefix("content").strip()))
        elif cmd.startswith("google search"): tasks.append(asyncio.to_thread(GoogleSearch, cmd.removeprefix("google search").strip()))
        elif cmd.startswith("youtube search"): tasks.append(asyncio.to_thread(YouTubeSearch, cmd.removeprefix("youtube search").strip()))
        elif cmd.startswith("system"): tasks.append(asyncio.to_thread(System, cmd.removeprefix("system").strip()))
    results = await asyncio.gather(*tasks)
    for r in results: yield r

async def Automation(commands: list[str]):
    async for _ in TranslateAndExecute(commands): pass
    return True

# === Startup Logic ===
def ShowDefaultChatIfNoChats():
    os.makedirs("Data", exist_ok=True)
    if not os.path.exists(chatlog_path): json.dump([], open(chatlog_path, "w", encoding="utf-8"))
    with open(chatlog_path, "r", encoding='utf-8') as File:
        if len(File.read().strip()) < 5:
            open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8').write("")
            open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8').write(DefaultMessage)

def ReadChatLogJson():
    with open(chatlog_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():
    data = ReadChatLogJson()
    formatted = ""
    for e in data:
        role = e.get("role")
        content = e.get("content", "")
        if role == "user": formatted += f"{Username}: {content}\n"
        if role == "assistant": formatted += f"{Assistantname}: {content}\n"
    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
        file.write(AnswerModifier(formatted))

def ShowChatOnGUI():
    data = open(TempDirectoryPath('Database.data'), 'r', encoding='utf-8').read()
    if data.strip():
        open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8').write('\n'.join(data.splitlines()))

def InitialExecution():
    SetMicrophoneStatus("False")
    showTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatOnGUI()

# === Assistant Core Execution ===
def MainExecution():
    try:
        SetAssistantStatus("Listening...")
        query = SpeechRecognition()
        showTextToScreen(f"{Username}: {query}")
        SetAssistantStatus("Thinking...")
        decision = FirstLayerDIUM(query)
        print(f"[🤖 Decision]: {decision}")
        is_task = any(d.startswith(tuple(functions)) for d in decision)
        image_task = next((d for d in decision if "generate" in d), None)
        merged_query = " and ".join(d.replace("general", "").replace("realtime", "").strip() for d in decision if d.startswith(("general", "realtime")))
        if is_task: asyncio.run(Automation(decision))
        if image_task:
            open('Frontend/Files/ImageGeneration.data', 'w', encoding='utf-8').write(f"{image_task},True")
            try:
                p1 = subprocess.Popen(['python', 'Backend/ImageGeneration.py'])
                subprocesses.append(p1)
            except Exception as e:
                print(f"[ImageGeneration Error]: {e}")
        if any(d.startswith("realtime") for d in decision):
            SetAssistantStatus("Searching...")
            ans = RealTimeSearchEngine(QueryModifier(merged_query))
            showTextToScreen(f"{Assistantname}: {ans}")
            SetAssistantStatus("Answering ...")
            TextToSpeech(ans)
        else:
            for d in decision:
                if "general" in d:
                    SetAssistantStatus("Thinking ...")
                    ans = ChatBot(QueryModifier(d.replace("general", "").strip()))
                    showTextToScreen(f"{Assistantname}: {ans}")
                    SetAssistantStatus("Answering ...")
                    TextToSpeech(ans)
                elif "exit" in d:
                    ans = ChatBot(QueryModifier("Okay, Bye!"))
                    showTextToScreen(f"{Assistantname}: {ans}")
                    SetAssistantStatus("Answering ...")
                    TextToSpeech(ans)
                    os._exit(0)
    except Exception as e:
        print(f"[❌ MainExecution Error]: {e}")

# === Threads ===
def FirstThread():
    while True:
        if GetMicrophoneStatus() == "True":
            MainExecution()
        else:
            if "Available ..." not in GetAssistantStatus():
                SetAssistantStatus("Answering ...")
            sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

def WatchCodeFile():
    try:
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
    except Exception as e:
        print("[❌ Watcher Error]:", e)

# === MAIN ===
if __name__ == "__main__":
    try:
        InitialExecution()
        threading.Thread(target=FirstThread, daemon=True).start()
        threading.Thread(target=WatchCodeFile, daemon=True).start()
        SecondThread()
    except Exception as e:
        print(f"[🔥 Assistant Failed to Start]: {e}")
