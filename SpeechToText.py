import os
import time
import logging
import threading
import http.server
import socketserver
from dotenv import dotenv_values
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER
from webdriver_manager.chrome import ChromeDriverManager
import mtranslate as mt
import hashlib

# === Suppress Selenium debug logs ===
LOGGER.setLevel(logging.WARNING)

# === Load config from .env ===
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en-US")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data")
HTML_FILE = os.path.join(DATA_DIR, "voice.html")
STATUS_FILE = os.path.join(BASE_DIR, "Frontend", "Files", "Status.data")

# === HTML with continuous recognition ===
HtmlCode = f'''<!DOCTYPE html>
<html lang="en">
<head><title>Voice</title></head>
<body>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = '{InputLanguage}';
        recognition.continuous = true;

        recognition.onresult = function(event) {{
            const transcript = event.results[event.results.length - 1][0].transcript;
            output.innerText = transcript;
        }};
        recognition.onerror = function(event) {{
            output.innerText = "[Error] " + event.error;
        }};
        window.onload = () => recognition.start();
    </script>
</body>
</html>'''

# === Create HTML file ===
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(HtmlCode)

# === Quiet HTTP Server ===
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

class QuietTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
    def handle_error(self, request, client_address):
        pass

def start_http_server(directory, port=8000):
    abs_dir = os.path.abspath(directory)
    os.chdir(abs_dir)
    httpd = QuietTCPServer(("", port), QuietHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return f"http://localhost:{port}/voice.html"

# === Chrome Setup ===
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-infobars")
chrome_options.add_argument("--mute-audio")
chrome_options.add_argument("--log-level=3")
# chrome_options.add_argument("--headless=new")  # Don't use with mic

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def SetAssistantStatus(Status):
    with open(STATUS_FILE, "w", encoding="utf-8") as file:
        file.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    if any(q in new_query for q in ["what", "who", "how", "when", "why", "can you", "where"]):
        new_query = new_query.rstrip(".?!") + "?"
    else:
        new_query = new_query.rstrip(".?!") + "."
    return new_query.capitalize()

def UniversalTranslator(Text):
    try:
        translated = mt.translate(Text, "en", "auto")
        return translated.capitalize()
    except:
        return "[Translation failed]"

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# === Continuous Speech Loop ===
def ContinuousSpeechRecognition(duration=3600):  # 1 hour
    url = start_http_server(DATA_DIR)
    driver.get(url)
    print("🎙️ Listening for 1 hour...")

    start_time = time.time()
    last_hash = ""

    while time.time() - start_time < duration:
        try:
            time.sleep(1)
            text = driver.find_element(By.ID, "output").text.strip()
            current_hash = hash_text(text)

            if text and current_hash != last_hash:
                print("📝 Captured:", text)
                last_hash = current_hash
                if not InputLanguage.lower().startswith("en"):
                    SetAssistantStatus("Translating...")
                    result = QueryModifier(UniversalTranslator(text))
                else:
                    result = QueryModifier(text)

                print("✅ Final Query:", result)
                # 🔁 You can return, process, or yield result here

        except Exception as e:
            continue

    driver.quit()
    print("🕒 Session ended.")

# === Run
if __name__ == "__main__":
    ContinuousSpeechRecognition(duration=3600)  # 1 hour
import speech_recognition as sr

def SpeechRecognition():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎙️ Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, phrase_time_limit=5)
            print("🎧 Processing...")
            text = recognizer.recognize_google(audio)
            print(f"🗣️ You said: {text}")
            return text
        except sr.UnknownValueError:
            print("❌ Could not understand audio.")
            return " "
        except sr.RequestError:
            print("⚠️ Could not connect to the recognition service.")
            return "Speech recognition service is unavailable."