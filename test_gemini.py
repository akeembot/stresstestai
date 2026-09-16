import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Key found: {key[:10]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"

body = {
    "contents": [{"parts": [{"text": "say hello in one word"}]}]
}

r = requests.post(url, json=body, timeout=15)
print(f"Status: {r.status_code}")
print(r.text[:300])
