#!/usr/bin/env python3
"""
사용 예시 스크립트 (업그레이드 버전)
새로운 기능들을 보여줍니다:
1. 결과 캐싱
2. 진행률 표시
3. 비동기 요청
4. 프록시 지원
5. 로그 시스템
6. 결과 필터링
"""

from web_crawler import (
    WebCrawler, ExcelExporter, FilterCriteria,
    ResultFilter, ProxyManager
)
from datetime import datetime, timedelta


def example_1_basic_search_with_cache():
    """예시 1: 기본 검색 (캐싱 활용)"""
    print("=" * 60)
    print("예시 1: 기본 검색 (캐싱 활용)")
    print("=" * 60)

    # 캐시 활성화하여 크롤러 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "인공지능"

    # 첫 번째 검색 (실제 크롤링)
    print(f"\n🔍 '{keyword}' 첫 번째 검색 (실제 크롤링)...")
    data1 = crawler.search_google_news(keyword, max_results=5)

    # 두 번째 검색 (캐시 활용)
    print(f"\n🔍 '{keyword}' 두 번째 검색 (캐시 활용)...")
    data2 = crawler.search_google_news(keyword, max_results=5)

    # 저장
    if data1:
        exporter.save_to_excel(data1, "ai_news.xlsx", "AI_뉴스")

    crawler.close()


def example_2_with_filters():
    """예시 2: 필터링 옵션 적용 검색"""
    print("\n" + "=" * 60)
    print("예시 2: 필터링 옵션 적용 검색")
    print("=" * 60)

    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "파이썬"

    # 필터링 기준 설정
    filter_criteria = FilterCriteria(
        start_date=datetime.now() - timedelta(days=7),  # 최근 7일
        min_title_length=10,
        keywords_in_title={"파이썬", "Python"}
    )

    print(f"\n🔍 '{keyword}' 검색 (필터 적용)...")
    print(f"   - 기간: 최근 7일")
    print(f"   - 제목 키워드: 파이썬, Python")

    data = crawler.search_google_news(
        keyword,
        max_results=20,
        filter_criteria=filter_criteria
    )

    if data:
        exporter.save_to_excel(data, "python_filtered.xlsx", "파이썬_필터링")
        print(f"\n✅ 필터링된 결과 {len(data)}개 저장 완료")

    crawler.close()


def example_3_multiple_keywords_async():
    """예시 3: 다중 키워드 비동기 검색"""
    print("\n" + "=" * 60)
    print("예시 3: 다중 키워드 비동기 검색")
    print("=" * 60)

    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keywords = ["AI", "블록체인", "메타버스"]

    print(f"\n🔍 {len(keywords)}개 키워드 비동기 검색...")

    # 비동기 검색 (병렬 처리)
    results = crawler.search_multiple_keywords(
        keywords,
        max_results=5,
        use_async=False  # True 시 실제 비동기 처리
    )

    # 결과 정리
    all_data = {f"News_{k}": v for k, v in results.items()}

    # 다중 시트로 저장
    if all_data:
        exporter.save_multiple_sheets(all_data, "tech_trends.xlsx")

    crawler.close()


def example_4_source_filtering():
    """예시 4: 출처 기반 필터링"""
    print("\n" + "=" * 60)
    print("예시 4: 출처 기반 필터링")
    print("=" * 60)

    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "주식"

    # 특정 출처만 허용 또는 차단
    filter_criteria = FilterCriteria(
        # allowed_sources={"연합뉴스", "Reuters"},  # 특정 출처만 허용
        # blocked_sources={"광고"}  # 특정 출처 차단
    )

    print(f"\n🔍 '{keyword}' 검색 (출처 필터링)...")

    data = crawler.search_google_news(
        keyword,
        max_results=15,
        filter_criteria=filter_criteria
    )

    # 수동 필터링 예시
    if data:
        # 특정 출처만 필터링
        filtered_data = ResultFilter.filter_by_source(
            data,
            allowed_sources={"연합뉴스", "뉴시스"}
        )
        print(f"\n✅ 필터링 전: {len(data)}개, 필터링 후: {len(filtered_data)}개")

        exporter.save_to_excel(filtered_data, "stock_filtered.xlsx", "주식_출처필터")

    crawler.close()


def example_5_manual_filtering():
    """예시 5: 수동 필터링 체이닝"""
    print("\n" + "=" * 60)
    print("예시 5: 수동 필터링 체이닝")
    print("=" * 60)

    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "코딩"

    print(f"\n🔍 '{keyword}' 검색...")

    # 먼저 데이터 수집
    data = crawler.search_google_news(keyword, max_results=20)

    if data:
        print(f"\n🔍 단계별 필터링...")

        # 1단계: 날짜 필터링
        filtered = ResultFilter.filter_by_date(
            data,
            start_date=datetime.now() - timedelta(days=30)
        )
        print(f"   1단계 (최근 30일): {len(filtered)}개")

        # 2단계: 키워드 필터링
        filtered = ResultFilter.filter_by_keywords(
            filtered,
            keywords_in_title={"프로그래밍", "개발", "코딩"}
        )
        print(f"   2단계 (키워드): {len(filtered)}개")

        # 3단계: 길이 필터링
        filtered = ResultFilter.filter_by_length(
            filtered,
            min_length=10,
            max_length=100
        )
        print(f"   3단계 (길이): {len(filtered)}개")

        exporter.save_to_excel(filtered, "coding_filtered.xlsx", "코딩_다중필터")

    crawler.close()


def example_6_with_logging():
    """예시 6: 로그 시스템 확인"""
    print("\n" + "=" * 60)
    print("예시 6: 로그 시스템 확인")
    print("=" * 60)

    from web_crawler import logger

    print("\n📝 로그가 'logs/' 디렉토리에 저장됩니다.")

    crawler = WebCrawler(use_cache=True)

    # 로그 메시지
    logger.info("사용자 정의 로그 메시지")
    logger.warning("경고 메시지 테스트")

    keyword = "데이터 사이언스"
    print(f"\n🔍 '{keyword}' 검색 (로그 기록 중)...")

    data = crawler.search_google_news(keyword, max_results=5)

    print(f"\n✅ 로그 파일 확인: logs/crawler_{datetime.now().strftime('%Y%m%d')}.log")

    crawler.close()


def example_7_cache_management():
    """예시 7: 캐시 관리"""
    print("\n" + "=" * 60)
    print("예시 7: 캐시 관리")
    print("=" * 60)

    crawler = WebCrawler(use_cache=True)

    keyword = "머신러닝"

    # 첫 번째 검색
    print(f"\n🔍 '{keyword}' 검색 #1...")
    data1 = crawler.search_google_news(keyword, max_results=3)

    # 캐시 상태 확인
    print(f"\n📦 캐시 상태: '.cache/' 디렉토리 확인")

    # 두 번째 검색 (캐시 활용)
    print(f"\n🔍 '{keyword}' 검색 #2 (캐시 활용)...")
    data2 = crawler.search_google_news(keyword, max_results=3)

    # 캐시 비우기
    print(f"\n🗑️  캐시 비우기...")
    crawler.clear_cache()

    # 세 번째 검색 (캐시 비워짐)
    print(f"\n🔍 '{keyword}' 검색 #3 (캐시 비워짐)...")
    data3 = crawler.search_google_news(keyword, max_results=3)

    crawler.close()


def example_8_comprehensive():
    """예시 8: 종합 검색 (모든 기능 활용)"""
    print("\n" + "=" * 60)
    print("예시 8: 종합 검색 (모든 기능 활용)")
    print("=" * 60)

    # 캐시 활성화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    keyword = "클라우드 컴퓨팅"

    # 종합 필터링 기준
    filter_criteria = FilterCriteria(
        start_date=datetime.now() - timedelta(days=14),  # 최근 2주
        keywords_in_title={"클라우드", "Cloud"},
        min_title_length=15
    )

    print(f"\n🔍 '{keyword}' 종합 검색...")
    print(f"   기간: 최근 2주")
    print(f"   캐시: 활성화")
    print(f"   필터: 제목 키워드 + 길이")

    # Google News
    news_data = crawler.search_google_news(
        keyword,
        max_results=15,
        filter_criteria=filter_criteria
    )

    # 네이버 블로그
    print(f"\n🔍 네이버 블로그 '{keyword}' 검색...")
    blog_data = crawler.search_naver_blog(keyword, max_results=10)

    # 결과 정리
    all_data = {}
    if news_data:
        all_data["뉴스"] = news_data
    if blog_data:
        all_data["블로그"] = blog_data[:5]

    # 통합 저장
    if all_data:
        exporter.save_multiple_sheets(all_data, f"{keyword}_종합.xlsx")
        print(f"\n✅ 종합 검색 완료!")

    crawler.close()


def example_9_proxy_setup():
    """예시 9: 프록시 설정"""
    print("\n" + "=" * 60)
    print("예시 9: 프록시 설정")
    print("=" * 60)

    # 프록시 매니저 생성
    proxy_manager = ProxyManager()

    print(f"\n📋 프록시 설정:")
    print(f"   - 프록시 파일: {proxy_manager.proxy_file}")
    print(f"   - 등록된 프록시: {len(proxy_manager.proxies)}개")

    if proxy_manager.proxies:
        print(f"\n   프록시 리스트:")
        for i, proxy in enumerate(proxy_manager.proxies[:5], 1):
            print(f"   {i}. {proxy}")

    # 프록시 활성화 크롤러
    print(f"\n🔍 프록시 활성화 크롤러 테스트...")
    crawler_with_proxy = WebCrawler(use_proxy=True)

    keyword = "사이버 보안"
    data = crawler_with_proxy.search_google_news(keyword, max_results=3)

    if data:
        print(f"\n✅ 프록시를 통한 검색 완료: {len(data)}개 항목")

    crawler_with_proxy.close()


if __name__ == "__main__":
    import time

    print("\n🚀 웹 크롤러 업그레이드 기능 예시")
    print("=" * 60)

    examples = [
        ("기본 검색 (캐싱)", example_1_basic_search_with_cache),
        ("필터링 옵션", example_2_with_filters),
        ("다중 키워드 비동기 검색", example_3_multiple_keywords_async),
        ("출처 기반 필터링", example_4_source_filtering),
        ("수동 필터링 체이닝", example_5_manual_filtering),
        ("로그 시스템", example_6_with_logging),
        ("캐시 관리", example_7_cache_management),
        ("종합 검색", example_8_comprehensive),
        ("프록시 설정", example_9_proxy_setup),
    ]

    print("\n실행할 예시를 선택하세요:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print(f"{len(examples) + 1}. 모든 예시 실행")
    print("0. 종료")

    try:
        choice = input("\n선택 (0-{}): ".format(len(examples) + 1)).strip()

        if choice == "0":
            print("종료합니다.")
        elif choice == str(len(examples) + 1):
            # 모든 예시 실행
            for name, func in examples:
                print(f"\n{'=' * 60}")
                print(f"실행: {name}")
                print('=' * 60)
                try:
                    func()
                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                time.sleep(1)
        else:
            # 선택된 예시 실행
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                try:
                    func()
                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
            else:
                print("잘못된 선택입니다.")

    except ValueError:
        print("잘못된 입력입니다.")
    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다.")

    print("\n" + "=" * 60)
    print("✅ 예시 실행 완료!")
    print("=" * 60)
