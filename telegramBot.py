import urllib.parse
import requests
from urllib.request import urlopen
from dotenv import load_dotenv
import os

load_dotenv()

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") #mq_bot
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message):
        message = urllib.parse.quote_plus(message)
        url = f"{self.base_url}/sendMessage?chat_id={self.chat_id}&parse_mode=html&disable_web_page_preview=true&text={message}"
        response = urlopen(url)
        return response.read().decode()

    def send_photo(self, photo, caption=""):
        url = f"{self.base_url}/sendPhoto"
        payload = {
            "chat_id": self.chat_id,
            "caption": caption,
            "parse_mode": "html"
        }

        # Check if photo is a URL or a file path
        if photo.startswith('http://') or photo.startswith('https://'):
            payload["photo"] = photo
            response = requests.post(url, data=payload)
        else:
            with open(photo, 'rb') as photo_file:
                files = {
                    "photo": photo_file
                }
                response = requests.post(url, data=payload, files=files)
                
        return response.json()