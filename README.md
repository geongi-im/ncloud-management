# NCloud Server Management Bot

NCloud 서버 인스턴스를 텔레그램 봇을 통해 관리하는 프로젝트입니다.

## 기능

- 서버 상태 확인
- 서버 시작/중지
- 전체 서버 시작/중지
- 공휴일 자동 감지

## 설치 방법

1. 저장소 클론
```bash
git clone [repository-url]
cd ncloud-management
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
`.env` 파일을 생성하고 다음 내용을 입력하세요:
```
ACCESS_KEY=your_access_key
SECRET_KEY=your_secret_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 사용 방법

텔레그램 봇 명령어:
- `/도움말` - 사용 가능한 명령어 목록
- `/allstop` - 모든 서버 종료
- `/allstart` - 모든 서버 시작
- `/start [서버번호]` - 특정 서버 시작
- `/stop [서버번호]` - 특정 서버 종료
- `/state [서버번호]` - 특정 서버 상태 확인

## 라이선스

MIT License
