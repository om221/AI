import pygame
import random
import asyncio
import edge_tts
import os
from dotenv import dotenv_values

# Load .env variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice")

# Path for saving MP3
AUDIO_PATH = os.path.join("Data", "speech.mp3")

# Async function to create speech file
async def TextToAudioFile(text):
    if os.path.exists(AUDIO_PATH):
        os.remove(AUDIO_PATH)

    communicate = edge_tts.Communicate(text, AssistantVoice, pitch='+5Hz', rate='+13%')
    await communicate.save(AUDIO_PATH)

# Plays the audio using pygame
def TTS(text, func=lambda r=None: True):
    try:
        # Generate audio
        asyncio.run(TextToAudioFile(text))

        # Play audio
        pygame.mixer.init()
        pygame.mixer.music.load(AUDIO_PATH)
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        while pygame.mixer.music.get_busy():
            if func() is False:
                break
            clock.tick(10)
        return True

    except Exception as e:
        print(f"Error in TTS: {e}")

    finally:
        try:
            func(False)
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception as e:
            print(f"Error in finally block: {e}")

# Splits long text and optionally adds chat message
def TextToSpeech(text, func=lambda r=None: True):
    sentences = str(text).split(".")
    responses = [
        "The rest of the result has been printed to the chat screen, kindly check it out sir.",
        "Sir, please look at the chat screen, the rest of the answer is there.",
        "You'll find the complete answer on the chat screen, sir.",
        "Please review the chat screen for the rest of the text, sir.",
        "Sir, the chat screen holds the continuation of the text."
    ]

    if len(sentences) > 4 and len(text) > 250:
        speak_text = ".".join(text.split(".")[:2]) + ". " + random.choice(responses)
        TTS(speak_text, func)
    else:
        TTS(text, func)

# CLI loop
if __name__ == "__main__":
    while True:
        user_input = input("Enter the text: ")
        TextToSpeech(user_input)
