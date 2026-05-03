@echo off
REM DealBot 웹 인터페이스 시작 스크립트 (Windows)

echo ==================================
echo 🕷️ DealBot 웹 인터페이스 시작
echo ==================================

REM Flask 설치 확인
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 📦 Flask 설치 중...
    pip install flask werkzeug
)

echo.
echo 🚀 웹 서버 시작 중...
echo 📱 접속 주소: http://localhost:5000
echo.
echo ⌨️  종료하려면 Ctrl+C를 누르세요
echo ==================================
echo.

REM 웹 인터페이스 실행
python web_interface.py

pause