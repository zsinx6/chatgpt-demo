import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")

# url = "https://api.openai.com/v1/chat/completions"
url = "https://api.openai.com/v1/images/generations"
headers = {
    "Authorization": f"Bearer {OPENAI_KEY}",
}

# json_body = {
#     "messages": [{"role": "user", "content": "Hello, how are you?"}],
#     "model": "gpt-4",
#     "temperature": 0.9,
# }
json_body = {"prompt": "A cat with wings", "n": 1, "size": "1024x1024"}

response = requests.post(url, headers=headers, json=json_body)
breakpoint()
