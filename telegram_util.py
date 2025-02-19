import os
from urllib.request import urlopen
import urllib.parse
import requests
from dotenv import load_dotenv
import json

# .env 파일 로드
load_dotenv()

class TelegramUtil:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.chat_test_id = os.getenv('TELEGRAM_CHAT_TEST_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message):
        """일반 메시지 전송"""
        message = urllib.parse.quote_plus(message)
        url = f"{self.base_url}/sendMessage?chat_id={self.chat_id}&parse_mode=html&disable_web_page_preview=true&text={message}"
        response = urlopen(url)
        return response.read().decode()

    def send_photo(self, photo, caption=""):
        """이미지 전송"""
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

    def send_test_message(self, message):
        """테스트용 채팅방으로 메시지 전송"""
        message = urllib.parse.quote_plus(message)
        urlopen(f"https://api.telegram.org/bot{self.bot_token}/sendMessage?chat_id={self.chat_test_id}&parse_mode=html&text={message}") 
    
    def send_multiple_photo(self, photo_paths, caption=""):
        """여러 장의 이미지 한 번에 전송"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMediaGroup"
        
        media = []
        files = {}
        
        # 각 이미지에 대한 미디어 객체 생성
        for index, photo_path in enumerate(photo_paths):
            # 첫 번째 이미지에만 캡션 추가
            media_caption = caption if index == 0 else ""
            
            media.append({
                'type': 'photo',
                'media': f'attach://photo{index}',
                'caption': media_caption,
                'parse_mode': 'html'
            })
            
            # 파일 열기
            files[f'photo{index}'] = open(photo_path, 'rb')
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'media': json.dumps(media)
            }
            
            # 요청 보내기
            response = requests.post(url, data=payload, files=files)
            
            # 파일들 닫기
            for file in files.values():
                file.close()
            
            return response.json()
            
        except Exception as e:
            # 에러 발생시에도 파일들을 확실히 닫아줌
            for file in files.values():
                file.close()
            raise e 