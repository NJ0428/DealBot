#!/usr/bin/env python3
"""
REST API 서버 테스트 스크립트
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000/api/v1"

def print_section(title):
    """섹션 구분선 출력"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def print_response(response):
    """API 응답 출력"""
    if response.status_code == 200:
        print(f"✅ 성공 ({response.status_code})")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ 실패 ({response.status_code})")
        print(response.text)

def test_health_check():
    """헬스체크 테스트"""
    print_section("1. 헬스체크 테스트")

    try:
        response = requests.get(f"{BASE_URL}/health")
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return False

def test_create_api_key(admin_key_id, admin_key_secret):
    """API 키 생성 테스트"""
    print_section("2. API 키 생성 테스트")

    headers = {
        'X-API-Key-ID': admin_key_id,
        'X-API-Key-Secret': admin_key_secret,
        'Content-Type': 'application/json'
    }

    data = {
        'name': 'Test API Key',
        'rate_limit': 100,
        'expires_in_days': 30,
        'permissions': ['read', 'write']
    }

    try:
        response = requests.post(f"{BASE_URL}/keys", headers=headers, json=data)
        print_response(response)

        if response.status_code == 201:
            return response.json()['key']
        return None
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return None

def test_list_api_keys(admin_key_id, admin_key_secret):
    """API 키 목록 조회 테스트"""
    print_section("3. API 키 목록 조회 테스트")

    headers = {
        'X-API-Key-ID': admin_key_id,
        'X-API-Key-Secret': admin_key_secret,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{BASE_URL}/keys", headers=headers)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def test_get_api_key_stats(admin_key_id, admin_key_secret, key_id):
    """API 키 통계 조회 테스트"""
    print_section("4. API 키 통계 조회 테스트")

    headers = {
        'X-API-Key-ID': admin_key_id,
        'X-API-Key-Secret': admin_key_secret,
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{BASE_URL}/keys/{key_id}/stats", headers=headers)
        print_response(response)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def test_crawl_news(api_key_id, api_key_secret):
    """뉴스 크롤링 테스트"""
    print_section("5. 뉴스 크롤링 테스트")

    headers = {
        'X-API-Key-ID': api_key_id,
        'X-API-Key-Secret': api_key_secret,
        'Content-Type': 'application/json'
    }

    data = {
        'keyword': '인공지능',
        'max_results': 5,
        'search_type': 'naver',
        'enable_sentiment': True
    }

    try:
        print("크롤링 시작...")
        response = requests.post(f"{BASE_URL}/crawl/news", headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공 ({response.status_code})")
            print(f"검색어: {result['keyword']}")
            print(f"결과 수: {result['count']}")
            print(f"검색 시간: {result['timestamp']}")

            if result.get('sentiment_stats'):
                stats = result['sentiment_stats']
                print(f"\n감정 통계:")
                print(f"  긍정: {stats['positive_count']} ({stats['positive_ratio']:.1%})")
                print(f"  부정: {stats['negative_count']} ({stats['negative_ratio']:.1%})")
                print(f"  중립: {stats['neutral_count']}")

            return True
        else:
            print(f"❌ 실패 ({response.status_code})")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def test_sentiment_analysis(api_key_id, api_key_secret):
    """감정 분석 테스트"""
    print_section("6. 감정 분석 테스트")

    headers = {
        'X-API-Key-ID': api_key_id,
        'X-API-Key-Secret': api_key_secret,
        'Content-Type': 'application/json'
    }

    # 단일 텍스트 분석
    data = {
        'text': '이 제품은 정말 좋습니다. 강력 추천합니다!'
    }

    try:
        response = requests.post(f"{BASE_URL}/sentiment/analyze", headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공 ({response.status_code})")
            print(f"텍스트: {data['text']}")
            print(f"감정: {result['result']['label']}")
            print(f"점수: {result['result']['sentiment_score']:.3f}")
            print(f"신뢰도: {result['result']['confidence']:.3f}")
            return True
        else:
            print(f"❌ 실패 ({response.status_code})")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def test_batch_sentiment(api_key_id, api_key_secret):
    """배치 감정 분석 테스트"""
    print_section("7. 배치 감정 분석 테스트")

    headers = {
        'X-API-Key-ID': api_key_id,
        'X-API-Key-Secret': api_key_secret,
        'Content-Type': 'application/json'
    }

    data = {
        'texts': [
            '이 제품은 정말 좋아요!',
            '별로입니다. 다시는 안 사요.',
            '그냥 그렇네요.'
        ]
    }

    try:
        response = requests.post(f"{BASE_URL}/sentiment/batch", headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 성공 ({response.status_code})")
            print(f"분석된 텍스트 수: {result['count']}")
            print("\n결과:")
            for item in result['results']:
                print(f"  {item['text'][:30]}... -> {item['label']} ({item['sentiment_score']:.2f})")
            return True
        else:
            print(f"❌ 실패 ({response.status_code})")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def test_error_handling():
    """에러 처리 테스트"""
    print_section("8. 에러 처리 테스트")

    # 잘못된 API 키로 인증 테스트
    print("1. 잘못된 API 키로 인증 시도:")
    headers = {
        'X-API-Key-ID': 'invalid_key',
        'X-API-Key-Secret': 'invalid_secret',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{BASE_URL}/stats", headers=headers)
        if response.status_code == 401:
            print("  ✅ 401 Unauthorized (올바른 에러 응답)")
        else:
            print(f"  ❌ 잘못된 상태 코드: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")

    # 필수 파라미터 누락 테스트
    print("\n2. 필수 파라미터 누락 테스트:")

    # 먼저 테스트 API 키 생성 필요
    # 생략 (복잡성을 줄이기 위해)

def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("  🧪 DealBot REST API 서버 테스트")
    print("=" * 60)

    # 1. 헬스체크
    if not test_health_check():
        print("\n❌ 서버가 실행 중이지 않습니다. 먼저 서버를 시작해주세요.")
        print("시작 명령: python api_server.py")
        return

    # 기본 Admin API 키 입력 받기
    print("\n" + "=" * 60)
    print("  🔑 Admin API 키 정보 입력")
    print("=" * 60)
    print("\n최초 실행 시 생성된 기본 Admin API 키 정보를 입력하세요.")

    admin_key_id = input("\nAdmin Key ID: ").strip()
    admin_key_secret = input("Admin Key Secret: ").strip()

    if not admin_key_id or not admin_key_secret:
        print("\n❌ API 키 정보가 입력되지 않았습니다.")
        return

    # 2. API 키 생성 테스트
    new_api_key = test_create_api_key(admin_key_id, admin_key_secret)

    # 3. API 키 목록 조회 테스트
    test_list_api_keys(admin_key_id, admin_key_secret)

    # 4. API 키 통계 조회 테스트
    if new_api_key:
        test_get_api_key_stats(admin_key_id, admin_key_secret, new_api_key['key_id'])

        # 5. 뉴스 크롤링 테스트
        test_crawl_news(new_api_key['key_id'], new_api_key['key_secret'])

        # 6. 감정 분석 테스트
        test_sentiment_analysis(new_api_key['key_id'], new_api_key['key_secret'])

        # 7. 배치 감정 분석 테스트
        test_batch_sentiment(new_api_key['key_id'], new_api_key['key_secret'])

    # 8. 에러 처리 테스트
    test_error_handling()

    # 테스트 완료
    print_section("테스트 완료")
    print("✅ 모든 테스트가 완료되었습니다.")
    print("\n참고:")
    print("- 생성된 테스트 API 키는 수동으로 삭제해야 합니다")
    print("- API 키 관리: Admin API 사용")
    print("- 상세 가이드: API_GUIDE.md")

if __name__ == '__main__':
    main()