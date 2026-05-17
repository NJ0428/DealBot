#!/usr/bin/env python3
"""
향상된 실시간 대시보드 테스트 스크립트
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

def test_get_resources():
    """시스템 리소스 조회 테스트"""
    print("\n🔍 시스템 리소스 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/api/resources")
        data = response.json()

        if data.get('success'):
            resources = data.get('resources')
            print(f"   ✅ 리소스 조회 성공")
            print(f"   모니터링 활성: {resources.get('monitoring_active')}")
            print(f"   이력 데이터 포인트: {resources.get('history_count')}")

            if resources.get('current'):
                current = resources['current']
                print(f"   CPU 사용량: {current['cpu']['percent']:.1f}%")
                print(f"   메모리 사용량: {current['memory']['percent']:.1f}%")
                print(f"   디스크 사용량: {current['disk']['percent']:.1f}%")
                print(f"   프로세스 수: {current['process']['count']}")

            return True
        else:
            print(f"   ❌ 리소스 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_get_resource_history():
    """리소스 이력 조회 테스트"""
    print("\n🔍 리소스 이력 조회 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/api/resources/history")
        data = response.json()

        if data.get('success'):
            history = data.get('history')
            print(f"   ✅ 리소스 이력 조회 성공")
            print(f"   이력 데이터 포인트: {data.get('count')}")

            if history:
                latest = history[-1]
                print(f"   최신 데이터: {latest.get('timestamp')}")
                print(f"   CPU: {latest.get('cpu', {}).get('percent', 0):.1f}%")

            return True
        else:
            print(f"   ❌ 리소스 이력 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_start_crawling():
    """크롤링 시작 테스트"""
    print("\n🔍 크롤링 시작 테스트...")

    payload = {
        "keyword": "테스트_키워드",
        "max_results": 3,
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

            # 키워드 빈도 정보
            keyword_freq = stats.get('keyword_frequency', {})
            if keyword_freq:
                print(f"   키워드 종류: {len(keyword_freq)}개")
                print(f"   인기 키워드: {list(keyword_freq.keys())[:3]}")

            return True
        else:
            print(f"   ❌ 통계 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_keyword_trends():
    """키워드 트렌드 테스트"""
    print("\n🔍 키워드 트렌드 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        data = response.json()

        if data.get('success'):
            stats = data.get('stats')
            trends = stats.get('keyword_trends', [])

            if trends:
                print(f"   ✅ 키워드 트렌드 데이터 존재")
                print(f"   트렌드 데이터 포인트: {len(trends)}")

                # 최근 트렌드 표시
                recent_trends = trends[-3:]
                for trend in recent_trends:
                    print(f"      - {trend.get('keyword')}: {trend.get('count')}회 ({trend.get('timestamp')})")

                return True
            else:
                print(f"   ⚠️  키워드 트렌드 데이터 없음 (정상)")
                return True
        else:
            print(f"   ❌ 통계 조회 실패: {data.get('error')}")
            return False

    except Exception as e:
        print(f"   ❌ 테스트 실패: {e}")
        return False

def test_multiple_crawling():
    """다중 크롤링 테스트"""
    print("\n🔍 다중 크롤링 테스트...")

    test_keywords = ["AI", "머신러닝", "딥러닝"]
    job_ids = []

    for keyword in test_keywords:
        payload = {
            "keyword": keyword,
            "max_results": 2,
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
                job_ids.append(data.get('job_id'))
                print(f"   ✅ '{keyword}' 크롤링 시작됨: {data.get('job_id')}")
            else:
                print(f"   ❌ '{keyword}' 크롤링 실패: {data.get('error')}")

        except Exception as e:
            print(f"   ❌ '{keyword}' 요청 오류: {e}")

        time.sleep(1)  # 요청 간격

    print(f"\n   시작된 작업: {len(job_ids)}개")
    return job_ids

def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 DealBot 향상된 실시간 대시보드 테스트")
    print("=" * 60)
    print(f"📡 대상 서버: {BASE_URL}")
    print("=" * 60)

    # 서버가 실행 중인지 확인
    print("\n⏳ 서버 상태 확인 중...")
    if not test_health_check():
        print("\n❌ 서버가 실행 중이지 않습니다. 먼저 서버를 시작해주세요.")
        print("   python enhanced_realtime_dashboard.py")
        return

    # 기능 테스트
    test_results = []

    # 시스템 리소스 테스트
    test_results.append(("시스템 리소스 조회", test_get_resources()))
    test_results.append(("리소스 이력 조회", test_get_resource_history()))

    # 통계 및 키워드 테스트
    test_results.append(("통계 조회", test_get_stats()))
    test_results.append(("키워드 트렌드", test_keyword_trends()))

    # 단일 크롤링 테스트
    job_id = test_start_crawling()
    test_results.append(("크롤링 시작", job_id is not None))

    # 크롤링 후 잠시 대기하여 리소스 모니터링 테스트
    if job_id:
        print("\n⏳ 크롤링 진행 중 리소스 모니터링 테스트 (10초)...")
        for i in range(10):
            time.sleep(1)
            resource_test = test_get_resources()
            if i == 9:  # 마지막에만 결과 추가
                test_results.append(("크롤링 중 리소스 모니터링", resource_test))

    # 다중 크롤링 테스트
    print("\n🔍 다중 크롤링 시나리오 테스트...")
    multiple_jobs = test_multiple_crawling()
    test_results.append(("다중 크롤링 시작", len(multiple_jobs) > 0))

    if multiple_jobs:
        print("\n⏳ 다중 크롤링 진행 중 모니터링 (15초)...")
        for i in range(15):
            time.sleep(1)

            # 주기적으로 통계 확인
            if i % 5 == 0:
                stats_test = test_get_stats()
                resource_test = test_get_resources()
                print(f"   진행률: {(i+1)/15*100:.0f}%")

        # 최종 상태 확인
        test_results.append(("다중 크롤링 완료 후 통계", test_get_stats()))
        test_results.append(("다중 크롤링 완료 후 리소스", test_get_resources()))

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
        print("🚀 향상된 대시보드가 정상적으로 작동합니다!")
    else:
        print(f"\n⚠️  {total - passed}개 테스트가 실패했습니다.")
        print("   로그를 확인하여 문제를 진단하세요.")

    # 추가 정보
    print("\n📋 테스트 완료 후 확인사항:")
    print("   - 브라우저에서 http://localhost:5000 접속")
    print("   - 각 탭 (크롤링, 키워드 트렌드, 시스템 리소스, 로그) 확인")
    print("   - 차트가 실시간으로 업데이트되는지 확인")
    print("   - 시스템 리소스가 정확히 표시되는지 확인")

    print("=" * 60)

if __name__ == '__main__':
    main()