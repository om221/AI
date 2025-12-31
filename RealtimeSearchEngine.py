from googlesearch import search
from groq import Groq
from json import load, dump
import datetime
from dotenv import dotenv_values
import os

# Load environment variables
env_vars = dotenv_values(".env")
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize Groq client
client = Groq(api_key=GroqAPIKey)

# Initial system message
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar. ***
*** Just answer the question from the provided data in a professional way. ***"""

SystemChatBot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "hi"},
    {"role": "assistant", "content": "Hello, how can I help you?"}
]

# Ensure log directory exists
if not os.path.exists("Data"):
    os.makedirs("Data")

# Load chat log or create new
if not os.path.exists("Data/ChatLog.json"):
    with open("Data/ChatLog.json", "w") as f:
        dump([], f)

def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    answer = f"The search results for '{query}' are:\n[start]\n"
    for res in results:
        answer += f"Title: {res.title}\nDescription: {res.description}\n\n"
    answer += "[end]"
    return answer

def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def Information():
    now = datetime.datetime.now()
    info = (
        "Use this real-time information if needed:\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours: {now.strftime('%M')} minutes: {now.strftime('%S')} seconds.\n"
    )
    return info

def RealTimeSearchEngine(prompt):
    global SystemChatBot

    # Load previous messages
    with open("Data/ChatLog.json", 'r') as f:
        messages = load(f)

    # Add user message
    messages.append({"role": "user", "content": prompt})

    # Add search results as system message
    SystemChatBot.append({"role": "system", "content": GoogleSearch(prompt)})

    # Add date/time info
    full_messages = SystemChatBot + [{"role": "system", "content": Information()}] + messages

    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=full_messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        stream=True
    )

    answer = ""
    for chunk in completion:
        delta = chunk.choices[0].delta
        if hasattr(delta, "content") and delta.content:
            answer += delta.content

    answer = answer.strip().replace("</s>", "")

    messages.append({"role": "assistant", "content": answer})

    # Save conversation
    with open("Data/ChatLog.json", "w") as f:
        dump(messages, f, indent=4)

    # Clean system prompt stack
    SystemChatBot.pop()

    return AnswerModifier(answer)

# Run loop
if __name__ == "__main__":
    while True:
        prompt = input("Enter your query: ")
        print(RealTimeSearchEngine(prompt))
