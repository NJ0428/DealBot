#!/usr/bin/env python3
"""
REST API 서버 사용 예시
"""

import requests
import json
from datetime import datetime

# API 서버 주소
BASE_URL = "http://localhost:5000/api/v1"

# 샘플 API 키 (실제 사용 시 생성된 키로 교체)
API_KEY_ID = "your_key_id_here"
API_KEY_SECRET = "your_key_secret_here"

class DealBotClient:
    """DealBot API 클라이언트"""

    def __init__(self, base_url: str = BASE_URL, key_id: str = None, key_secret: str = None):
        self.base_url = base_url
        self.key_id = key_id or API_KEY_ID
        self.key_secret = key_secret or API_KEY_SECRET

        # 헤더 설정
        self.headers = {
            'X-API-Key-ID': self.key_id,
            'X-API-Key-Secret': self.key_secret,
            'Content-Type': 'application/json'
        }

    def _request(self, method: str, endpoint: str, data: dict = None):
        """API 요청"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"API 요청 오류: {e}")
            if hasattr(e.response, 'json'):
                print(f"오류 상세: {e.response.json()}")
            return None

    def health_check(self):
        """헬스체크"""
        return self._request('GET', '/health')

    def get_stats(self):
        """서버 통계 조회"""
        return self._request('GET', '/stats')

    def create_api_key(self, name: str, rate_limit: int = 1000,
                      expires_in_days: int = None, permissions: list = None):
        """API 키 생성"""
        data = {
            'name': name,
            'rate_limit': rate_limit
        }
        if expires_in_days:
            data['expires_in_days'] = expires_in_days
        if permissions:
            data['permissions'] = permissions

        return self._request('POST', '/keys', data)

    def list_api_keys(self):
        """모든 API 키 목록"""
        return self._request('GET', '/keys')

    def get_api_key(self, key_id: str):
        """특정 API 키 조회"""
        return self._request('GET', f'/keys/{key_id}')

    def get_api_key_stats(self, key_id: str):
        """API 키 통계 조회"""
        return self._request('GET', f'/keys/{key_id}/stats')

    def activate_api_key(self, key_id: str):
        """API 키 활성화"""
        return self._request('POST', f'/keys/{key_id}/activate')

    def deactivate_api_key(self, key_id: str):
        """API 키 비활성화"""
        return self._request('POST', f'/keys/{key_id}/deactivate')

    def delete_api_key(self, key_id: str):
        """API 키 삭제"""
        return self._request('DELETE', f'/keys/{key_id}')

    def crawl_news(self, keyword: str, max_results: int = 20,
                   search_type: str = 'naver', enable_sentiment: bool = False):
        """뉴스 크롤링"""
        data = {
            'keyword': keyword,
            'max_results': max_results,
            'search_type': search_type,
            'enable_sentiment': enable_sentiment
        }
        return self._request('POST', '/crawl/news', data)

    def crawl_multiple(self, keywords: list, max_results: int = 20,
                      use_async: bool = True):
        """다중 키워드 크롤링"""
        data = {
            'keywords': keywords,
            'max_results': max_results,
            'use_async': use_async
        }
        return self._request('POST', '/crawl/multiple', data)

    def analyze_sentiment(self, text: str):
        """텍스트 감정 분석"""
        data = {'text': text}
        return self._request('POST', '/sentiment/analyze', data)

    def analyze_sentiment_batch(self, texts: list):
        """배치 감정 분석"""
        data = {'texts': texts}
        return self._request('POST', '/sentiment/batch', data)

    def filter_sentiment(self, results: list, sentiment: str = 'positive', min_score: float = 0.0):
        """감정 필터링"""
        data = {
            'results': results,
            'sentiment': sentiment,
            'min_score': min_score
        }
        return self._request('POST', '/sentiment/filter', data)

    def get_sentiment_stats(self, results: list):
        """감정 통계"""
        data = {'results': results}
        return self._request('POST', '/sentiment/stats', data)

def main():
    """사용 예시"""
    print("=" * 60)
    print("🔌 DealBot REST API 사용 예시")
    print("=" * 60)

    # 클라이언트 초기화
    client = DealBotClient()

    # 1. 헬스체크
    print("\n1. 헬스체크")
    health = client.health_check()
    print(f"   서버 상태: {health['status']}")
    print(f"   서비스: {health['service']}")
    print(f"   버전: {health['version']}")

    # 2. 서버 통계
    print("\n2. 서버 통계")
    stats = client.get_stats()
    print(f"   API 키 수: {stats['api_keys_count']}")
    print(f"   총 요청 수: {stats['total_requests']}")
    print(f"   활성 키 수: {stats['active_keys']}")

    # 3. 뉴스 크롤링
    print("\n3. 뉴스 크롤링")
    result = client.crawl_news("인공지능", max_results=5, search_type='naver')
    if result:
        print(f"   검색어: {result['keyword']}")
        print(f"   결과 수: {result['count']}")
        print(f"   검색 시간: {result['timestamp']}")
        if result['results']:
            print(f"   첫 번째 결과: {result['results'][0]['title'][:50]}...")

    # 4. 감정 분석
    print("\n4. 감정 분석")
    sentiment_result = client.analyze_sentiment("이 제품은 정말 좋습니다. 강력 추천합니다!")
    if sentiment_result:
        result = sentiment_result['result']
        print(f"   감정: {result['label']}")
        print(f"   점수: {result['sentiment_score']:.3f}")
        print(f"   신뢰도: {result['confidence']:.3f}")

    # 5. 다중 키워드 크롤링
    print("\n5. 다중 키워드 크롤링")
    multi_result = client.crawl_multiple(["AI", "블록체인"], max_results=3)
    if multi_result:
        print(f"   검색어: {multi_result['keywords']}")
        print(f"   총 결과 수: {multi_result['total_count']}")
        for keyword, data in multi_result['results'].items():
            print(f"   {keyword}: {data['count']}개")

    # 6. 배치 감정 분석
    print("\n6. 배치 감정 분석")
    texts = [
        "이 제품은 정말 좋아요!",
        "별로입니다. 다시는 안 사요.",
        "그냥 그렇네요."
    ]
    batch_result = client.analyze_sentiment_batch(texts)
    if batch_result:
        print(f"   분석된 텍스트 수: {batch_result['count']}")
        for item in batch_result['results']:
            print(f"   {item['text'][:30]}... -> {item['label']}")

    print("\n" + "=" * 60)
    print("✅ 사용 예시 완료")
    print("=" * 60)

if __name__ == '__main__':
    main()