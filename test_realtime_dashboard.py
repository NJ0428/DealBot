#!/usr/bin/env python3
"""
실시간 대시보드 테스트 스크립트
"""

import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()

        print(f"   상태: {data.get('status')}")
        print(f"   서비스: {data.get('service')}")
        print(f"   타임스탬프: {data.get('timestamp')}")

        return data.get('status') == 'healthy'
    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_start_crawling():
    """크롤링 시작 테스트"""
    print("\n🔍 크롤링 시작 테스트...")

    payload = {
        "keyword": "테스트",
        "max_results": 5,
        "search_type": "naver"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/crawl/start",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        data = response.json()

        if data.get('success'):
            print(f"   ✅ 크롤링 시작 성공")
            print(f"   작업 ID: {data.get('job_id')}")
            print(f"   메시지: {data.get('message')}")
            return data.get('job_id')
        else:
            print(f"   ❌ 크롤링 시작 실패: {data.get('error')}")
            return None

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return None

def test_get_stats():
    """통계 조회 테스트"""
    print("\n🔍 통계 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        data = response.json()

        if data.get('success'):
            stats = data.get('stats')
            print(f"   ✅ 통계 조회 성공")
            print(f"   총 크롤링: {stats.get('total_crawls')}")
            print(f"   성공률: {stats.get('success_rate', 0):.1f}%")
            print(f"   진행 중인 작업: {stats.get('active_jobs')}")
            return True
        else:
            print(f"   ❌ 통계 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_list_jobs():
    """작업 목록 조회 테스트"""
    print("\n🔍 작업 목록 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs")
        data = response.json()

        if data.get('success'):
            jobs = data.get('jobs')
            print(f"   ✅ 작업 목록 조회 성공")
            print(f"   작업 수: {data.get('count')}")

            if jobs:
                print(f"   최근 작업:")
                for job in jobs[:3]:  # 최근 3개만 표시
                    print(f"      - {job.get('keyword')}: {job.get('status')}")

            return True
        else:
            print(f"   ❌ 작업 목록 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_get_job(job_id):
    """특정 작업 조회 테스트"""
    print(f"\n🔍 작업 조회 테스트 (ID: {job_id})...")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
        data = response.json()

        if data.get('success'):
            job = data.get('job')
            print(f"   ✅ 작업 조회 성공")
            print(f"   검색어: {job.get('keyword')}")
            print(f"   상태: {job.get('status')}")
            print(f"   진행률: {job.get('progress_percentage', 0):.1f}%")
            return True
        else:
            print(f"   ❌ 작업 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 DealBot 실시간 대시보드 테스트")
    print("=" * 60)
    print(f"📡 대상 서버: {BASE_URL}")
    print("=" * 60)

    # 서버가 실행 중인지 확인
    print("\n⏳ 서버 상태 확인 중...")
    if not test_health_check():
        print("\n❌ 서버가 실행 중이지 않습니다. 먼저 서버를 시작해주세요.")
        print("   python realtime_dashboard.py")
        return

    # 기능 테스트
    test_results = []

    # 통계 조회
    test_results.append(("통계 조회", test_get_stats()))

    # 작업 목록 조회
    test_results.append(("작업 목록 조회", test_list_jobs()))

    # 크롤링 시작
    job_id = test_start_crawling()
    test_results.append(("크롤링 시작", job_id is not None))

    # 작업 조회 (크롤링 시작 성공 시)
    if job_id:
        time.sleep(2)  # 작업이 시작될 때까지 대기
        test_results.append(("작업 조회", test_get_job(job_id)))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"   {test_name}: {status}")

    print(f"\n   총: {passed}/{total} 테스트 통과")

    if passed == total:
        print("\n🎉 모든 테스트가 통과했습니다!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트가 실패했습니다.")

    print("=" * 60)

if __name__ == '__main__':
    main()