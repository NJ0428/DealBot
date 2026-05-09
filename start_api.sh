#!/bin/bash

# DealBot REST API 서버 시작 스크립트

echo "🔌 DealBot REST API 서버 시작 중..."
echo ""

# Python 가상환경 확인
if [ -d "venv" ]; then
    echo "가상환경 활성화 중..."
    source venv/bin/activate
fi

# 필요한 패키지 확인
echo "의존성 패키지 확인 중..."
pip install -q requests beautifulsoup4 pandas openpyxl lxml aiohttp tqdm diskcache flask

# API 서버 시작
python api_server.py