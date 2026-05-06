#!/usr/bin/env python3
"""
감정 분석 시스템 사용 예시
"""

from sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentConfig,
    SentimentFilter,
    create_custom_sentiment_dict
)
from web_crawler import WebCrawler, ExcelExporter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_analysis():
    """예시 1: 기본 감정 분석"""
    print("\n" + "=" * 80)
    print("예시 1: 기본 텍스트 감정 분석")
    print("=" * 80)

    # 분석기 초기화
    analyzer = SentimentAnalyzer()

    # 테스트 텍스트
    texts = [
        "이번 분기 실적이 매우 우수합니다. 성장세가 지속되고 있습니다.",
        "실적이 부진하여 어려움을 겪고 있습니다. 우려가 큽니다.",
        "정상적인 범위 내에서 운영되고 있습니다."
    ]

    for text in texts:
        result = analyzer.analyze(text)
        print(f"\n텍스트: {text}")
        print(f"감정: {result.label} (점수: {result.sentiment_score:.3f})")
        print(f"긍정 단어: {result.positive_words}")
        print(f"부정 단어: {result.negative_words}")


def example_2_crawling_with_sentiment():
    """예시 2: 크롤링 데이터 감정 분석"""
    print("\n" + "=" * 80)
    print("예시 2: 크롤링 데이터 감정 분석")
    print("=" * 80)

    # 크롤러 및 감정 분석기 초기화
    crawler = WebCrawler()
    analyzer = SentimentAnalyzer()
    exporter = ExcelExporter()

    # 데이터 수집
    keyword = "인공지능"
    print(f"\n'{keyword}' 키워드로 뉴스 수집 중...")

    data = crawler.search_google_news(keyword, max_results=10)

    if not data:
        print("수집된 데이터가 없습니다.")
        return

    # 감정 분석 적용
    print("감정 분석 중...")
    data = analyzer.analyze_data(data)

    # 결과 요약
    summary = SentimentFilter.get_sentiment_summary(data)
    print(f"\n감정 분석 결과:")
    print(f"  총 {summary['total_count']}개 중")
    print(f"  긍정: {summary['positive_count']}개 ({summary['positive_ratio']:.1%})")
    print(f"  부정: {summary['negative_count']}개 ({summary['negative_ratio']:.1%})")
    print(f"  중립: {summary['neutral_count']}개 ({summary['neutral_ratio']:.1%})")
    print(f"  평균 감정 점수: {summary['avg_sentiment_score']:.3f}")

    # 엑셀 저장
    output_file = f"{keyword}_sentiment_analysis.xlsx"
    exporter.save_to_excel(data, output_file, sheet_name="감정분석")
    print(f"\n결과가 {output_file}에 저장되었습니다.")

    crawler.close()


def example_3_sentiment_filtering():
    """예시 3: 감정 기반 필터링 및 정렬"""
    print("\n" + "=" * 80)
    print("예시 3: 감정 기반 필터링 및 정렬")
    print("=" * 80)

    # 분석기 초기화
    analyzer = SentimentAnalyzer()

    # 테스트 데이터 생성
    test_data = [
        {'title': 'AI 기술 혁신, 시장 기대감 고조', 'content': '최신 AI 기술이 시장을 선도하고 있습니다.'},
        {'title': '경기 침체 우려, 투자심리 위축', 'content': '경제 상황이 악화되고 있습니다.'},
        {'title': '정부 정책 발표', 'content': '오늘 정부에서 새로운 정책을 발표했습니다.'},
        {'title': '신제품 대성공, 주가 급등', 'content': '투자자들의 기대감이 최고조에 달했습니다.'},
        {'title': '데이터 유출 사고 발생', 'content': '보안 시스템의 허점이 드러났습니다.'}
    ]

    # 감정 분석
    analyzed_data = analyzer.analyze_data(test_data)

    # 긍정 뉴스만 필터링
    positive_news = SentimentFilter.filter_by_sentiment(analyzed_data, 'positive', min_score=0.2)
    print(f"\n긍정적 뉴스 {len(positive_news)}개:")
    for item in positive_news:
        print(f"  - {item['title']} (점수: {item['sentiment_score']:.3f})")

    # 부정 뉴스만 필터링
    negative_news = SentimentFilter.filter_by_sentiment(analyzed_data, 'negative', min_score=0.2)
    print(f"\n부정적 뉴스 {len(negative_news)}개:")
    for item in negative_news:
        print(f"  - {item['title']} (점수: {item['sentiment_score']:.3f})")

    # 긍정 점수 높은 순으로 정렬
    sorted_by_positive = SentimentFilter.sort_by_sentiment(analyzed_data, 'positive', reverse=True)
    print("\n긍정 점수 상위 3개:")
    for item in sorted_by_positive[:3]:
        print(f"  {item['title']}: {item['positive_score']:.3f}")


def example_4_custom_configuration():
    """예시 4: 커스텀 설정"""
    print("\n" + "=" * 80)
    print("예시 4: 커스텀 설정으로 감정 분석")
    print("=" * 80)

    # 커스텀 설정
    config = SentimentConfig(
        tokenizer_type='okt',
        positive_threshold=0.2,  # 더 엄격한 긍정 기준
        negative_threshold=-0.2,  # 더 엄격한 부정 기준
        intensifier_weight=2.0,  # 강조어 가중치 증가
        negation_weight=-1.5  # 부정어 가중치 증가
    )

    analyzer = SentimentAnalyzer(config)

    text = "이 제품은 정말 최고입니다. 아주 강력하게 추천합니다!"
    result = analyzer.analyze(text)

    print(f"\n텍스트: {text}")
    print(f"감정: {result.label}")
    print(f"점수: {result.sentiment_score:.3f}")
    print(f"긍정 단어: {result.positive_words}")


def example_5_sentiment_statistics():
    """예시 5: 감정 통계 및 시각화"""
    print("\n" + "=" * 80)
    print("예시 5: 감정 분석 통계")
    print("=" * 80)

    # 분석기 초기화
    analyzer = SentimentAnalyzer()
    crawler = WebCrawler()

    # 여러 키워드 분석
    keywords = ["AI", " blockchain", "meta"]
    all_results = {}

    for keyword in keywords:
        print(f"\n'{keyword}' 분석 중...")
        data = crawler.search_google_news(keyword, max_results=5)

        if data:
            data = analyzer.analyze_data(data)
            summary = SentimentFilter.get_sentiment_summary(data)
            all_results[keyword] = summary

            print(f"  긍정: {summary['positive_ratio']:.1%}")
            print(f"  부정: {summary['negative_ratio']:.1%}")
            print(f"  평균 점수: {summary['avg_sentiment_score']:.3f}")

    # 키워드별 비교
    print("\n키워드별 감정 점수 비교:")
    for keyword, summary in all_results.items():
        print(f"  {keyword}: {summary['avg_sentiment_score']:.3f}")

    crawler.close()


def example_6_batch_analysis():
    """예시 6: 대량 텍스트 일괄 분석"""
    print("\n" + "=" * 80)
    print("예시 6: 대량 텍스트 일괄 분석")
    print("=" * 80)

    # 분석기 초기화
    analyzer = SentimentAnalyzer()

    # 테스트 텍스트 100개 생성
    texts = [
        "이 제품은 정말 좋습니다. 추천합니다!",
        "품질이 별로입니다. 실망했습니다.",
        "가격이 적당하고 성능도 괜찮습니다.",
        "완전 최악입니다. 절대 사지 마세요.",
        "기대 이상입니다. 매우 만족스럽습니다!"
    ] * 20  # 100개

    print(f"\n총 {len(texts)}개 텍스트 분석 중...")

    # 일괄 분석
    results = analyzer.analyze_batch(texts)

    # 통계
    distribution = SentimentFilter.get_sentiment_distribution(
        [{'sentiment_label': r.label, 'sentiment_score': r.sentiment_score} for r in results]
    )

    print("\n감정 분포:")
    print(f"  긍정: {distribution.get('positive', 0)}개")
    print(f"  부정: {distribution.get('negative', 0)}개")
    print(f"  중립: {distribution.get('neutral', 0)}개")


def example_7_create_custom_dict():
    """예시 7: 커스텀 감정 사전 생성"""
    print("\n" + "=" * 80)
    print("예시 7: 커스텀 감정 사전 생성")
    print("=" * 80)

    # 커스텀 사전 템플릿 생성
    dict_path = create_custom_sentiment_dict('my_custom_dict.json')
    print(f"\n커스텀 감정 사전 템플릿이 생성되었습니다: {dict_path}")
    print("이 파일을 수정하여 감정 사전을 커스터마이징할 수 있습니다.")


def main():
    """모든 예시 실행"""
    print("\n" + "=" * 80)
    print("🤖 감정 분석 시스템 예시")
    print("=" * 80)

    examples = [
        ("1. 기본 감정 분석", example_1_basic_analysis),
        ("2. 크롤링 데이터 감정 분석", example_2_crawling_with_sentiment),
        ("3. 감정 기반 필터링 및 정렬", example_3_sentiment_filtering),
        ("4. 커스텀 설정", example_4_custom_configuration),
        ("5. 감정 통계", example_5_sentiment_statistics),
        ("6. 대량 텍스트 일괄 분석", example_6_batch_analysis),
        ("7. 커스텀 감정 사전 생성", example_7_create_custom_dict)
    ]

    print("\n사용 가능한 예시:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n모든 예시를 순서대로 실행합니다...")

    for name, func in examples:
        try:
            func()
        except Exception as e:
            logger.error(f"{name} 실행 중 오류: {e}")
            continue

    print("\n" + "=" * 80)
    print("모든 예시 실행 완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()
