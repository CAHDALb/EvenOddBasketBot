import requests
from config import BOT_TOKEN

url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

print(requests.get(url).json())