@echo off
REM DealBot REST API 서버 시작 스크립트 (Windows)

echo 🔌 DealBot REST API 서버 시작 중...
echo.

REM Python 가상환경 확인
if exist venv\Scripts\activate.bat (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
)

REM 필요한 패키지 확인
echo 의존성 패키지 확인 중...
pip install -q requests beautifulsoup4 pandas openpyxl lxml aiohttp tqdm diskcache flask

REM API 서버 시작
python api_server.py

pause