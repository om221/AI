import asyncio
import os
from random import randint
from PIL import Image
import requests
from dotenv import get_key
from time import sleep

# ==== Configuration ====
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {get_key('.env', 'HuggingFaceAPIKey')}"}
DATA_FILE_PATH = r"Frontend\Files\ImageGeneration.data"
IMAGE_FOLDER = "Data"

# Ensure image directory exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ==== Function to display images ====
def open_images(prompt):
    prompt_safe = prompt.replace(" ", "_")
    for i in range(1, 5):
        image_path = os.path.join(IMAGE_FOLDER, f"{prompt_safe}{i}.jpg")
        try:
            if os.path.exists(image_path) and os.path.getsize(image_path) > 0:
                img = Image.open(image_path)
                print(f"Opening image: {image_path}")
                img.show()
                sleep(2)
            else:
                print(f"[!] Missing or empty image: {image_path}")
        except Exception as e:
            print(f"[!] Could not open image {image_path}: {e}")

# ==== API Query Function ====
async def query(payload):
    response = await asyncio.to_thread(
        requests.post, API_URL, headers=HEADERS, json=payload
    )
    return response.content

# ==== Generate Images ====
async def generate_images(prompt: str):
    prompt_safe = prompt.replace(" ", "_")
    tasks = []

    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4k, sharpness=maximum, ultra High Details, high resolution, seed={randint(0, 999999)}"
        }
        tasks.append(asyncio.create_task(query(payload)))

    image_bytes_list = await asyncio.gather(*tasks)

    for i, image_bytes in enumerate(image_bytes_list):
        path = os.path.join(IMAGE_FOLDER, f"{prompt_safe}{i + 1}.jpg")
        with open(path, "wb") as f:
            f.write(image_bytes)

# ==== Wrapper to Run and Display ====
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))
    open_images(prompt)

# ==== Main Loop ====
while True:
    try:
        if not os.path.exists(DATA_FILE_PATH):
            sleep(1)
            continue

        with open(DATA_FILE_PATH, "r") as f:
            data = f.read().strip()

        if not data:
            sleep(1)
            continue

        Prompt, Status = data.split(",")

        if Status.strip() == "True":
            print("Generating Images ...")
            GenerateImages(prompt=Prompt.strip())

            with open(DATA_FILE_PATH, "w") as f:
                f.write("False,False")
            break
        else:
            sleep(1)

    except Exception as e:
        print(e)
