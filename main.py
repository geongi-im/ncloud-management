import requests
import hashlib
import hmac
import base64
import sys
import os
from datetime import datetime, date
import time
from dotenv import load_dotenv
from telegram_util import TelegramUtil
import json
import holidays

def isTodayHoliday():
    # 한국 공휴일 설정
    kr_holidays = holidays.KR()
    
    # 오늘 날짜 가져오기
    today = date.today()
    
    # 오늘이 공휴일인지 확인하고 결과 반환
    return today in kr_holidays

def	makeSignature(query):
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)
    secret_key = bytes(SECRET_KEY, 'UTF-8')

    method = "GET"
    message = method + " " + query + "\n" + timestamp + "\n" + ACCESS_KEY
    message = bytes(message, 'UTF-8')
    signingKey = base64.b64encode(hmac.new(secret_key, message, digestmod=hashlib.sha256).digest())
    return signingKey

def getNcpServerState(target, status):
    url = "https://ncloud.apigw.ntruss.com"
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    query = f"/vserver/v2/getServerInstanceDetail?responseFormatType=json&serverInstanceNo={target}"
    signature = makeSignature(query)
    headers = {
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature
    }

    response = requests.get(url + query, headers=headers)
    response_json = response.json()  # JSON 형식으로 응답을 파싱
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
        if status != this_status:
            message = f"[서버 상태 체크 필요]\n상태 : {status}\n현재상태 : {this_status}" #running booting stopped
        else:
            message = "ok"
    
    print(message)
    if message != "ok":
        telegram_util.send_message(f"[{target}]{message}")

def setNcpServerState(target, state):
    url = "https://ncloud.apigw.ntruss.com"
    timestamp = int(time.time() * 1000)
    timestamp = str(timestamp)

    if state == "on":  # 서버 실행
        query = f"/vserver/v2/startServerInstances?responseFormatType=json&serverInstanceNoList.1={target}"
        method = 'startServerInstancesResponse'
    else:  # 서버 종료
        query = f"/vserver/v2/stopServerInstances?responseFormatType=json&serverInstanceNoList.1={target}"
        method = 'stopServerInstancesResponse'
    
    signature = makeSignature(query)
    headers = {
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": ACCESS_KEY,
        "x-ncp-apigw-signature-v2": signature
    }

    response = requests.get(url + query, headers=headers)
    response_json = response.json()  # JSON 형식으로 응답을 파싱
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
        
    print(message)
    telegram_util.send_message(f"[{target}]{message}")

if __name__ == "__main__":
    load_dotenv()
    ACCESS_KEY = os.getenv("ACCESS_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    telegram_util = TelegramUtil()

    if isTodayHoliday(): #공휴일이면 종료
        print('공휴일 종료')
        sys.exit()

    if len(sys.argv) != 3:
        print("Usage: python script.py <method> <status>")
        sys.exit()

    method = sys.argv[1]
    status = sys.argv[2]

    target1 = "25741251" #1번 서버 인스턴스 번호
    target2 = "26055342" #2번 서버 인스턴스 번호

    if method == 'set':
        if status not in ["on", "off"]:
            print("Invalid state. Use 'on' or 'off'.")
        else :
            setNcpServerState(target1, status)
            setNcpServerState(target2, status)
    
    if method == 'get':
        if status not in ["running", "stopped"]:
            print("Invalid state. Use 'running' or 'stopped'.")
        else:
            getNcpServerState(target1, status)
            getNcpServerState(target2, status)