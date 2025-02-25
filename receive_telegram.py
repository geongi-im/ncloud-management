import telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters
import requests
import time
import os
import base64
import hmac
import hashlib
import json
from utils.logger_util import LoggerUtil
from dotenv import load_dotenv

logger = LoggerUtil().get_logger()

class TelegramBot:
    def __init__(self, access_key, secret_key, server_mapping, bot_token):
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_mapping = server_mapping
        self.bot = telegram.Bot(token=bot_token)

    def send_message(self, text, chat_id):
        self.bot.sendMessage(chat_id=chat_id, text=text, parse_mode='HTML')

    def make_signature(self, query):
        timestamp = str(int(time.time() * 1000))
        secret_key = bytes(self.secret_key, 'UTF-8')

        method = "GET"
        message = method + " " + query + "\n" + timestamp + "\n" + self.access_key
        message = bytes(message, 'UTF-8')
        signing_key = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
        return signing_key, timestamp

    def send_server_request(self, query, method, chat_id=None, server_no=None):
        url = "https://ncloud.apigw.ntruss.com"
        signature, timestamp = self.make_signature(query)

        headers = {
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signature
        }

        response = requests.get(url + query, headers=headers)
        response_json = response.json()

        if 'responseError' in response_json.keys():
            returnMessage = response_json['responseError']['returnMessage']
            message = f"[서버 오류 발생1]\nmethod : {method}\nmessage : {returnMessage}"
        elif 'error' in response_json.keys():
            returnMessage = response_json['error']['message'] + ' ' + response_json['error']['details']
            message = f"[서버 오류 발생2]\nmethod : {method}\nmessage : {returnMessage}"
        elif response_json[method]['returnCode'] != '0':
            returnMessage = response_json[method]['returnMessage']
            message = f"[서버 오류 발생3]\nmethod : {method}\nmessage : {returnMessage}"
        else:
            message = f"[성공]\nmethod : {method}"

        logger.info(message)
        if chat_id:
            self.send_message(f"[{server_no if server_no else 'all'}]{message}", chat_id)

    def set_server_state(self, action, server_no=None, chat_id=None):
        if action == "allstart":
            for server in self.server_mapping.values():
                query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
                self.send_server_request(query, 'startServerInstancesResponse', chat_id, server)
        elif action == "allstop":
            for server in self.server_mapping.values():
                query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
                self.send_server_request(query, 'stopServerInstancesResponse', chat_id, server)
        elif action == "start" and server_no:
            query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={server_no}"
            self.send_server_request(query, 'startServerInstancesResponse', chat_id, server_no)
        elif action == "stop" and server_no:
            query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={server_no}"
            self.send_server_request(query, 'stopServerInstancesResponse', chat_id, server_no)
        else:
            logger.error("Invalid action or missing server number.")

    def get_server_state(self, server_no, chat_id):
        url = "https://ncloud.apigw.ntruss.com"
        signature, timestamp = self.make_signature(f"/vserver/v2/getServerInstanceDetail?responseFormatType=json&serverInstanceNo={server_no}")

        headers = {
            "x-ncp-apigw-timestamp": timestamp,
            "x-ncp-iam-access-key": self.access_key,
            "x-ncp-apigw-signature-v2": signature
        }

        query = f"/vserver/v2/getServerInstanceDetail?responseFormatType=json&serverInstanceNo={server_no}"
        response = requests.get(url + query, headers=headers)
        response_json = response.json()

        if 'responseError' in response_json.keys():
            returnMessage = response_json['responseError']['returnMessage']
            message = f"[서버 오류 발생1]\nmessage : {returnMessage}"
        elif 'error' in response_json.keys():
            returnMessage = response_json['error']['message'] + ' ' + response_json['error']['details']
            message = f"[서버 오류 발생2]\nmessage : {returnMessage}"
        elif response_json['getServerInstanceDetailResponse']['returnCode'] != '0':
            returnMessage = response_json['getServerInstanceDetailResponse']['returnMessage']
            message = f"[서버 오류 발생3]\nmessage : {returnMessage}"
        else:
            this_status = response_json['getServerInstanceDetailResponse']['serverInstanceList'][0]['serverInstanceStatusName']
            message = f"[서버 상태]\n서버 번호: {server_no}\n현재 상태: {this_status}"

        logger.info(message)
        self.send_message(f"[{server_no}]{message}", chat_id)

    def handle_message(self, update, context):
        response_text = update.message.text
        chat_id = str(update.message.chat_id)
        user_name = str(update.message.from_user.username)
        user_full_name = str(update.message.from_user.full_name)

        logger.info(f"Received message from {user_name} ({user_full_name}): {response_text}")

        if response_text.startswith('/'):
            if response_text == '/도움말':
                message = '[도움말] 사용 가능한 명령어 목록입니다:\n\n'
                message += '/도움말 - 사용 가능한 명령어 목록을 표시합니다.\n'
                message += '/allstop - 실행 중인 모든 서버를 종료합니다.\n'
                message += '/allstart - 모든 서버를 시작합니다.\n'
                message += '/start [서버번호] - 특정 서버를 시작합니다. (예: /start 1)\n'
                message += '/stop [서버번호] - 특정 서버를 종료합니다. (예: /stop 1)\n'
                message += '/state [서버번호] - 특정 서버의 상태를 확인합니다. (예: /state 1)\n'
                self.send_message(message, chat_id)
            elif response_text == '/allstop':
                self.set_server_state('allstop', None, chat_id)
            elif response_text == '/allstart':
                self.set_server_state('allstart', None, chat_id)
            elif response_text.startswith('/start'):
                text = response_text.split()
                if len(text) != 2:
                    self.send_message('[에러] 명령어를 올바르게 입력해주세요\n\n/start 서버번호', chat_id)
                else:
                    user_input = text[1]
                    server_no = self.server_mapping.get(user_input)
                    if server_no:
                        self.set_server_state('start', server_no, chat_id)
                    else:
                        self.send_message('[에러] 유효하지 않은 서버 번호입니다.', chat_id)
            elif response_text.startswith('/stop'):
                text = response_text.split()
                if len(text) != 2:
                    self.send_message('[에러] 명령어를 올바르게 입력해주세요\n\n/stop 서버번호', chat_id)
                else:
                    user_input = text[1]
                    server_no = self.server_mapping.get(user_input)
                    if server_no:
                        self.set_server_state('stop', server_no, chat_id)
                    else:
                        self.send_message('[에러] 유효하지 않은 서버 번호입니다.', chat_id)
            elif response_text.startswith('/state'):
                text = response_text.split()
                if len(text) != 2:
                    self.send_message('[에러] 명령어를 올바르게 입력해주세요\n\n/state 서버번호', chat_id)
                else:
                    user_input = text[1]
                    server_no = self.server_mapping.get(user_input)
                    if server_no:
                        self.get_server_state(server_no, chat_id)
                    else:
                        self.send_message('[에러] 유효하지 않은 서버 번호입니다.', chat_id)
            else:
                self.send_message('[에러] 등록되지 않은 명령어입니다\n/도움말 을 확인해주세요', chat_id)

def create_server_mapping(server_list):
    return {str(idx + 1): str(server_no) for idx, server_no in enumerate(server_list)}

def main():
    load_dotenv()
    access_key = os.getenv("ACCESS_KEY")
    secret_key = os.getenv("SECRET_KEY")
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # 환경 변수에서 server_list를 가져와서 server_mapping 생성
    server_list = json.loads(os.getenv("SERVER_LIST", "[]"))
    server_mapping = create_server_mapping(server_list)

    # TelegramBot 인스턴스 생성
    telegram_bot = TelegramBot(access_key, secret_key, server_mapping, bot_token)
    
    # Telegram 업데이터 설정
    updater = Updater(token=bot_token, use_context=True)
    dispatcher = updater.dispatcher
    
    # 메시지 핸들러 등록
    dispatcher.add_handler(MessageHandler(Filters.text, telegram_bot.handle_message))
    
    # 봇 시작
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
