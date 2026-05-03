#!/usr/bin/env python3
"""
웹 인터페이스 예시 사용법
DealBot 웹 인터페이스의 다양한 사용 예시
"""

import requests
import json
from time import sleep

# 웹 인터페이스 기본 URL
BASE_URL = "http://localhost:5000"

def print_section(title):
    """섹션 구분자 출력"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_server_health():
    """서버 헬스체크"""
    print_section("1. 서버 헬스체크")

    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 서버 상태: {data['status']}")
            print(f"📅 시간: {data['timestamp']}")
            print(f"🔧 서비스: {data['service']}")
            return True
        else:
            print(f"❌ 서버 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        print("💡 웹 인터페이스가 실행 중인지 확인하세요")
        return False

def web_search_example(keyword, max_results=10, search_type="naver"):
    """웹 검색 예시"""
    print_section(f"2. 검색: {keyword}")

    data = {
        "keyword": keyword,
        "max_results": max_results,
        "search_type": search_type
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 검색 성공!")
            print(f"📊 결과 수: {result['count']}개")

            # 결과 표시
            print("\n📋 검색 결과 (처음 5개):")
            for i, item in enumerate(result['results'][:5], 1):
                print(f"\n{i}. {item.get('title', '제목 없음')}")
                print(f"   URL: {item.get('url', 'URL 없음')}")
                print(f"   블로그: {item.get('blog_name', '-')}")

            return result
        else:
            print(f"❌ 검색 실패: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

def batch_search_example(keywords):
    """배치 검색 예시"""
    print_section("3. 배치 검색")

    results = {}
    for keyword in keywords:
        print(f"\n🔍 검색 중: {keyword}")
        result = web_search_example(keyword, max_results=5)
        if result:
            results[keyword] = result['count']
            sleep(2)  # 요청 간격

    print("\n📊 배치 검색 요약:")
    for keyword, count in results.items():
        print(f"  - {keyword}: {count}개")

    return results

def advanced_search_example():
    """고급 검색 예시"""
    print_section("4. 고급 검색")

    # 다양한 검색 유형 테스트
    keyword = "인공지능"

    search_types = [
        ("naver", "네이버 블로그 검색"),
        ("google", "구글 검색"),
        ("multiple", "다중 검색")
    ]

    for search_type, description in search_types:
        print(f"\n🔍 {description}")
        result = web_search_example(keyword, max_results=5, search_type=search_type)
        if result:
            print(f"✅ 결과: {result['count']}개")
        sleep(2)

def comparison_search_example():
    """비교 검색 예시"""
    print_section("5. 키워드 비교 검색")

    keywords = ["파이썬", "자바스크립트", "Go언어"]
    results = batch_search_example(keywords)

    # 결과 비교
    print("\n📈 키워드별 결과 수 비교:")
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    for keyword, count in sorted_results:
        bar = "█" * (count // 2)
        print(f"  {keyword:15s}: {bar} ({count}개)")

def check_history_example():
    """검색 이력 확인 예시"""
    print_section("6. 검색 이력 확인")

    try:
        # 웹 브라우저에서 확인 권장
        print("📱 웹 브라우저에서 이력 확인:")
        print(f"   URL: {BASE_URL}/history")
        print("\n💡 이전 검색 결과 파일들을 다운로드할 수 있습니다")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def interactive_search_mode():
    """대화형 검색 모드"""
    print_section("7. 대화형 검색 모드")

    print("🔍 검색어를 입력하세요 (종료하려면 'q' 입력)")

    while True:
        keyword = input("\n검색어: ").strip()

        if keyword.lower() == 'q':
            print("👋 프로그램 종료")
            break

        if not keyword:
            continue

        # 검색 유형 선택
        print("검색 유형 선택:")
        print("  1. 네이버 블로그")
        print("  2. 구글")
        print("  3. 다중 검색")

        choice = input("선택 (1-3, 기본값: 1): ").strip() or "1"

        search_types = {"1": "naver", "2": "google", "3": "multiple"}
        search_type = search_types.get(choice, "naver")

        # 검색 실행
        result = web_search_example(keyword, max_results=10, search_type=search_type)

        if result:
            download = input("\n결과를 다운로드하시겠습니까? (y/n): ").strip().lower()
            if download == 'y':
                print("📥 웹 브라우저에서 다운로드 링크를 확인하세요:")
                print(f"   URL: {BASE_URL}/search")

def main():
    """메인 실행 함수"""
    print("🕷️ DealBot 웹 인터페이스 예시")
    print("다양한 사용 예시를 보여드립니다\n")

    # 1. 서버 헬스체크
    if not check_server_health():
        print("\n❌ 웹 인터페이스가 실행되지 않았습니다.")
        print("💡 먼저 웹 인터페이스를 시작해주세요:")
        print("   python web_interface.py")
        return

    input("\n계속하려면 Enter를 누르세요...")

    # 2. 기본 검색 예시
    web_search_example("파이썬 프로그래밍", max_results=10)
    input("\n계속하려면 Enter를 누르세요...")

    # 3. 배치 검색 예시
    batch_search_example(["머신러닝", "딥러닝", "AI"])
    input("\n계속하려면 Enter를 누르세요...")

    # 4. 고급 검색 예시
    advanced_search_example()
    input("\n계속하려면 Enter를 누르세요...")

    # 5. 비교 검색 예시
    comparison_search_example()
    input("\n계속하려면 Enter를 누르세요...")

    # 6. 이력 확인
    check_history_example()

    # 7. 대화형 모드
    print_section("완료!")
    print("모든 예시가 완료되었습니다.")
    print("\n💡 대화형 검색 모드를 시작하시겠습니까? (y/n)")

    if input().strip().lower() == 'y':
        interactive_search_mode()

    print_section("마치며")
    print("🌐 웹 인터페이스 주소: http://localhost:5000")
    print("📖 자세한 사용법: WEB_INTERFACE_GUIDE.md")
    print("\n👋 감사합니다!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 사용자가 프로그램을 종료했습니다")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")