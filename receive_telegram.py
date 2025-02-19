from typing import Dict, Optional
import telegram
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import requests
import time
import os
import base64
import hmac
import hashlib
from dotenv import load_dotenv
from utils.logger_util import LoggerUtil

# Constants
SERVER_MAPPING: Dict[str, str] = {
    "1": "25741251",
    "2": "26055342"
}

HELP_MESSAGE = '''[도움말] 사용 가능한 명령어 목록입니다:

/도움말 - 사용 가능한 명령어 목록을 표시합니다.
/allstop - 실행 중인 모든 서버를 종료합니다.
/allstart - 모든 서버를 시작합니다.
/start [서버번호] - 특정 서버를 시작합니다. (예: /start 1)
/stop [서버번호] - 특정 서버를 종료합니다. (예: /stop 1)
/state [서버번호] - 특정 서버의 상태를 확인합니다. (예: /state 1)'''

class NCPServerManager:
    def __init__(self):
        load_dotenv()
        self.access_key = os.getenv("ACCESS_KEY")
        self.secret_key = os.getenv("SECRET_KEY")
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.logger = LoggerUtil().get_logger()
        
        if not all([self.access_key, self.secret_key, self.telegram_token]):
            raise ValueError("필수 환경 변수가 설정되지 않았습니다.")
        
        self.base_url = "https://ncloud.apigw.ntruss.com"
        self.bot = telegram.Bot(token=self.telegram_token)

    def make_signature(self, query: str):
        timestamp = str(int(time.time() * 1000))
        secret_key = bytes(self.secret_key, 'UTF-8')
        method = "GET"
        
        message = f"{method} {query}\n{timestamp}\n{self.access_key}"
        message = bytes(message, 'UTF-8')
        signing_key = base64.b64encode(
            hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()
        )
        return signing_key

    def send_server_request(self, query: str, method: str, chat_id: str, server_no: Optional[str] = None):
        try:
            timestamp = str(int(time.time() * 1000))
            signature = self.make_signature(query)
            
            headers = {
                "x-ncp-apigw-timestamp": timestamp,
                "x-ncp-iam-access-key": self.access_key,
                "x-ncp-apigw-signature-v2": signature
            }

            response = requests.get(self.base_url + query, headers=headers)
            response.raise_for_status()
            response_json = response.json()

            message = self._process_response(response_json, method)
            server_prefix = f"[{server_no if server_no else 'all'}]"
            self.send_message(f"{server_prefix}{message}", chat_id)
            
        except requests.RequestException as e:
            error_msg = f"[네트워크 오류]\n{str(e)}"
            self.logger.error(error_msg)
            self.send_message(error_msg, chat_id)
        except Exception as e:
            error_msg = f"[시스템 오류]\n{str(e)}"
            self.logger.error(error_msg)
            self.send_message(error_msg, chat_id)

    def _process_response(self, response_json: dict, method: str):
        if 'responseError' in response_json:
            return f"[서버 오류]\nmethod: {method}\nmessage: {response_json['responseError']['returnMessage']}"
        elif 'error' in response_json:
            return f"[서버 오류]\nmethod: {method}\nmessage: {response_json['error']['message']}"
        elif response_json[method]['returnCode'] != '0':
            return f"[서버 오류]\nmethod: {method}\nmessage: {response_json[method]['returnMessage']}"
        return f"[성공]\nmethod: {method}"

    def send_message(self, text: str, chat_id: str):
        try:
            self.bot.send_message(chat_id=chat_id, text=text, parse_mode='HTML')
        except telegram.error.TelegramError as e:
            self.logger.error(f"텔레그램 메시지 전송 실패: {str(e)}")

    def set_server_state(self, action: str, server_no: Optional[str] = None, chat_id: Optional[str] = None):
        if action == "allstart":
            for server in SERVER_MAPPING.values():
                query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
                self.send_server_request(query, 'startServerInstancesResponse', chat_id, server)
        elif action == "allstop":
            for server in SERVER_MAPPING.values():
                query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
                self.send_server_request(query, 'stopServerInstancesResponse', chat_id, server)
        elif action in ["start", "stop"] and server_no:
            action_type = "start" if action == "start" else "stop"
            query = f"/vserver/v2/{action_type}ServerInstances?responseFormatType=json&serverInstanceNoList.1={server_no}"
            self.send_server_request(query, f'{action_type}ServerInstancesResponse', chat_id, server_no)
        else:
            self.logger.error(f"Invalid action: {action} or missing server number")

    def get_server_state(self, server_no: str, chat_id: str):
        query = f"/vserver/v2/getServerInstanceDetail?responseFormatType=json&serverInstanceNo={server_no}"
        try:
            timestamp = str(int(time.time() * 1000))
            signature = self.make_signature(query)
            
            headers = {
                "x-ncp-apigw-timestamp": timestamp,
                "x-ncp-iam-access-key": self.access_key,
                "x-ncp-apigw-signature-v2": signature
            }

            response = requests.get(self.base_url + query, headers=headers)
            response.raise_for_status()
            response_json = response.json()

            if 'getServerInstanceDetailResponse' in response_json:
                status = response_json['getServerInstanceDetailResponse']['serverInstanceList'][0]['serverInstanceStatusName']
                message = f"[서버 상태]\n서버 번호: {server_no}\n현재 상태: {status}"
            else:
                message = "[오류] 서버 상태를 가져올 수 없습니다."

            self.send_message(f"[{server_no}]{message}", chat_id)
            
        except Exception as e:
            error_msg = f"[서버 상태 조회 오류]\n{str(e)}"
            self.logger.error(error_msg)
            self.send_message(error_msg, chat_id)

def handle_message(update: Update, context: CallbackContext):
    ncp_manager = NCPServerManager()
    logger = LoggerUtil().get_logger()
    
    response_text = update.message.text
    chat_id = str(update.message.chat_id)
    
    logger.info(f"Received message: {response_text} from chat_id: {chat_id}")

    if not response_text.startswith('/'):
        return

    command_parts = response_text.split()
    command = command_parts[0].lower()

    try:
        if command == '/도움말':
            ncp_manager.send_message(HELP_MESSAGE, chat_id)
        elif command == '/allstop':
            ncp_manager.set_server_state('allstop', None, chat_id)
        elif command == '/allstart':
            ncp_manager.set_server_state('allstart', None, chat_id)
        elif command in ['/start', '/stop', '/state']:
            if len(command_parts) != 2:
                ncp_manager.send_message(f"[에러] 명령어를 올바르게 입력해주세요\n\n{command} 서버번호", chat_id)
                return

            server_no = SERVER_MAPPING.get(command_parts[1])
            if not server_no:
                ncp_manager.send_message("[에러] 유효하지 않은 서버 번호입니다.", chat_id)
                return

            if command == '/start':
                ncp_manager.set_server_state('start', server_no, chat_id)
            elif command == '/stop':
                ncp_manager.set_server_state('stop', server_no, chat_id)
            else:  # /state
                ncp_manager.get_server_state(server_no, chat_id)
        else:
            ncp_manager.send_message("[에러] 등록되지 않은 명령어입니다\n/도움말 을 확인해주세요", chat_id)
            
    except Exception as e:
        error_msg = f"[시스템 오류]\n{str(e)}"
        logger.error(error_msg)
        ncp_manager.send_message(error_msg, chat_id)

def main():
    try:
        logger = LoggerUtil().get_logger()
        ncp_manager = NCPServerManager()
        updater = Updater(token=ncp_manager.telegram_token, use_context=True)
        dispatcher = updater.dispatcher
        
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        logger.info("Bot started successfully")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger = LoggerUtil().get_logger()
        logger.error(f"Bot startup failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
