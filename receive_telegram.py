import telegram
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters
import requests
import time
import os
import base64
import hmac
import hashlib
from utils.logger_util import LoggerUtil
from dotenv import load_dotenv

logger = LoggerUtil().get_logger()

def sendMessage(text, chatId) :
    bot.sendMessage(chat_id = chatId, text = text, parse_mode='HTML')

def callbackContext(update, context):
    responseText = update.message.text
    chatId = str(update.message.chat_id)
    userId = str(update.message.from_user.id)
    userName = str(update.message.from_user.username)
    userFullName = str(update.message.from_user.full_name)

    logger.info(f"Received message from {userName} ({userFullName}): {responseText}")

    # 서버 번호 매핑
    server_mapping = {
        "1": "25741251",
        "2": "26055342"
    }

    if responseText.startswith('/'): # /로 시작해야지만 인식
        if responseText == '/도움말':
            message = '[도움말] 사용 가능한 명령어 목록입니다:\n\n'
            message += '/도움말 - 사용 가능한 명령어 목록을 표시합니다.\n'
            message += '/allstop - 실행 중인 모든 서버를 종료합니다.\n'
            message += '/allstart - 모든 서버를 시작합니다.\n'
            message += '/start [서버번호] - 특정 서버를 시작합니다. (예: /start 1)\n'
            message += '/stop [서버번호] - 특정 서버를 종료합니다. (예: /stop 1)\n'
            message += '/state [서버번호] - 특정 서버의 상태를 확인합니다. (예: /state 1)\n'
            sendMessage(message, chatId)
        elif responseText == '/allstop': #실행중인 모든 서버 종료
            setNcpServerState('allstop', None, chatId)  # chatId를 세 번째 인자로 전달
        elif responseText == '/allstart': #실행중인 모든 서버 시작
            setNcpServerState('allstart', None, chatId)  # chatId를 세 번째 인자로 전달
        elif responseText.startswith('/start'): #실행중인 특정 서버 시작
            text = responseText.split()
            if len(text) != 2:
                sendMessage('[에러] 명령어를 올바르게 입력해주세요\n\n/start 서버번호', chatId)
            else:
                user_input = text[1]
                server_no = server_mapping.get(user_input)
                if server_no:
                    setNcpServerState('start', server_no, chatId)
                else:
                    sendMessage('[에러] 유효하지 않은 서버 번호입니다.', chatId)
        elif responseText.startswith('/stop'): #실행중인 특정 서버 종료
            text = responseText.split()
            if len(text) != 2:
                sendMessage('[에러] 명령어를 올바르게 입력해주세요\n\n/stop 서버번호', chatId)
            else:
                user_input = text[1]
                server_no = server_mapping.get(user_input)
                if server_no:
                    setNcpServerState('stop', server_no, chatId)
                else:
                    sendMessage('[에러] 유효하지 않은 서버 번호입니다.', chatId)
        elif responseText.startswith('/state'): # 특정 서버 상태 확인
            text = responseText.split()
            if len(text) != 2:
                sendMessage('[에러] 명령어를 올바르게 입력해주세요\n\n/state 서버번호', chatId)
            else:
                user_input = text[1]
                server_no = server_mapping.get(user_input)
                if server_no:
                    getNcpServerState(server_no, chatId)
                else:
                    sendMessage('[에러] 유효하지 않은 서버 번호입니다.', chatId)
        else:
            sendMessage('[에러] 등록되지 않은 명령어입니다\n/도움말 을 확인해주세요', chatId)

def makeSignature(query):
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)
    secret_key = bytes(SECRET_KEY, 'UTF-8')

    method = "GET"
    message = method + " " + query + "\n" + timestamp + "\n" + ACCESS_KEY
    message = bytes(message, 'UTF-8')
    signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
    return signingKey

def sendServerRequest(query, method, chatId=None, server_no=None):
    url = "https://ncloud.apigw.ntruss.com"
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    signature = makeSignature(query)
    headers = {
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": ACCESS_KEY,
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
    if chatId:
        sendMessage(f"[{server_no if server_no else 'all'}]{message}", chatId)

def setNcpServerState(action, server_no=None, chatId=None):
    server_mapping = {
        "1": "25741251",
        "2": "26055342"
    }

    if action == "allstart":
        for server in server_mapping.values():
            query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
            sendServerRequest(query, 'startServerInstancesResponse', chatId, server)
    elif action == "allstop":
        for server in server_mapping.values():
            query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={server}"
            sendServerRequest(query, 'stopServerInstancesResponse', chatId, server)
    elif action == "start" and server_no:
        query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={server_no}"
        sendServerRequest(query, 'startServerInstancesResponse', chatId, server_no)
    elif action == "stop" and server_no:
        query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={server_no}"
        sendServerRequest(query, 'stopServerInstancesResponse', chatId, server_no)
    else:
        logger.error("Invalid action or missing server number.")
        return

def getNcpServerState(server_no, chatId):
    url = "https://ncloud.apigw.ntruss.com"
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    query = f"/vserver/v2/getServerInstanceDetail?responseFormatType=json&serverInstanceNo={server_no}"
    signature = makeSignature(query)
    headers = {
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature
    }

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
    sendMessage(f"[{server_no}]{message}", chatId)

load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

bot = telegram.Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
updater = Updater(token=os.getenv("TELEGRAM_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher
updater.start_polling()
dispatcher.add_handler(MessageHandler(Filters.text, callbackContext))
