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
`.env.sample` 파일을 `.env`로 복사하고 필요한 값들을 입력하세요:
```bash
cp .env.sample .env
```

`.env` 파일을 열어 다음 값들을 설정하세요:
```
ACCESS_KEY=your_ncp_access_key        # NCP API 액세스 키
SECRET_KEY=your_ncp_secret_key        # NCP API 시크릿 키
TELEGRAM_BOT_TOKEN=your_bot_token     # 텔레그램 봇 토큰
TELEGRAM_CHAT_ID=your_chat_id         # 텔레그램 채팅 ID
TELEGRAM_CHAT_TEST_ID=your_test_id    # (선택사항) 테스트용 채팅 ID
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
