#!/usr/bin/env python3
"""
사용 예시 스크립트
다양한 크롤링 방법을 보여줍니다.
"""

from web_crawler import WebCrawler, ExcelExporter


def example_1_google_news():
    """예시 1: Google News 검색"""
    print("=" * 60)
    print("예시 1: Google News에서 '인공지능' 검색")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    # 검색
    data = crawler.search_google_news("인공지능", max_results=5)

    # 저장
    if data:
        exporter.save_to_excel(data, "ai_news.xlsx", "AI_뉴스")


def example_2_multiple_keywords():
    """예시 2: 여러 키워드 검색"""
    print("\n" + "=" * 60)
    print("예시 2: 여러 주제 동시 검색")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    keywords = ["AI", "블록체인", "메타버스"]
    all_data = {}

    for keyword in keywords:
        print(f"\n🔍 '{keyword}' 검색 중...")
        data = crawler.search_google_news(keyword, max_results=3)

        if data:
            all_data[f"News_{keyword}"] = data

    # 다중 시트로 저장
    if all_data:
        exporter.save_multiple_sheets(all_data, "tech_trends.xlsx")


def example_3_naver_blog():
    """예시 3: 네이버 블로그 검색"""
    print("\n" + "=" * 60)
    print("예시 3: 네이버 블로그 검색")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    data = crawler.search_naver_blog("파이썬 강의")

    if data:
        exporter.save_to_excel(data, "python_blog.xlsx", "파이썬_블로그")


def example_4_custom_url():
    """예시 4: 사용자 정의 URL 크롤링"""
    print("\n" + "=" * 60)
    print("예시 4: 특정 URL 크롤링")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    # 예시 URL (실제 사용 시 원하는 URL로 변경)
    url = "https://news.google.com"

    data = crawler.crawl_custom_url(url)

    if data:
        exporter.save_to_excel(data, "custom_crawl.xlsx", "크롤링_결과")


def example_5_comprehensive():
    """예시 5: 종합 검색 (뉴스 + 블로그)"""
    print("\n" + "=" * 60)
    print("예시 5: 종합 검색 (뉴스 + 블로그)")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    keyword = "주식 투자"
    all_data = {}

    # Google News
    print(f"\n🔍 Google News에서 '{keyword}' 검색...")
    news_data = crawler.search_google_news(keyword, max_results=5)
    if news_data:
        all_data["뉴스"] = news_data

    # 네이버 블로그
    print(f"\n🔍 네이버 블로그에서 '{keyword}' 검색...")
    blog_data = crawler.search_naver_blog(keyword)
    if blog_data:
        all_data["블로그"] = blog_data[:5]  # 상위 5개만

    # 통합 저장
    if all_data:
        exporter.save_multiple_sheets(all_data, f"{keyword}_종합.xlsx")


if __name__ == "__main__":
    import time

    # 모든 예시 실행
    example_1_google_news()
    time.sleep(2)

    example_2_multiple_keywords()
    time.sleep(2)

    example_3_naver_blog()
    time.sleep(2)

    example_4_custom_url()
    time.sleep(2)

    example_5_comprehensive()

    print("\n" + "=" * 60)
    print("✅ 모든 예시 실행 완료!")
    print("=" * 60)
