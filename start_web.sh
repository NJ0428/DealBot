#!/bin/bash
# DealBot 웹 인터페이스 시작 스크립트

echo "=================================="
echo "🕷️ DealBot 웹 인터페이스 시작"
echo "=================================="

# Flask 설치 확인
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Flask 설치 중..."
    pip install flask werkzeug
fi

echo ""
echo "🚀 웹 서버 시작 중..."
echo "📱 접속 주소: http://localhost:5000"
echo ""
echo "⌨️  종료하려면 Ctrl+C를 누르세요"
echo "=================================="
echo ""

# 웹 인터페이스 실행
python web_interface.py