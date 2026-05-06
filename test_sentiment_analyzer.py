#!/usr/bin/env python3
"""
감정 분석 시스템 테스트 스크립트
"""

from sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentConfig,
    SentimentFilter,
    SentimentResult,
    create_custom_sentiment_dict
)
import unittest
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestSentimentAnalyzer(unittest.TestCase):
    """감정 분석기 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        """긍정 감정 분석 테스트"""
        text = "이 제품은 정말 좋습니다. 매우 만족스럽고 추천합니다!"
        result = self.analyzer.analyze(text)

        self.assertEqual(result.label, 'positive')
        self.assertGreater(result.sentiment_score, 0)
        self.assertGreater(len(result.positive_words), 0)

    def test_negative_sentiment(self):
        """부정 감정 분석 테스트"""
        text = "최악입니다. 절대 사지 마세요. 완전 실망했습니다."
        result = self.analyzer.analyze(text)

        self.assertEqual(result.label, 'negative')
        self.assertLess(result.sentiment_score, 0)
        self.assertGreater(len(result.negative_words), 0)

    def test_neutral_sentiment(self):
        """중립 감정 분석 테스트"""
        text = "오늘 회사에서 회의가 있었습니다."
        result = self.analyzer.analyze(text)

        self.assertEqual(result.label, 'neutral')

    def test_empty_text(self):
        """빈 텍스트 처리 테스트"""
        result = self.analyzer.analyze("")
        self.assertEqual(result.label, 'neutral')
        self.assertEqual(result.sentiment_score, 0.0)

    def test_batch_analysis(self):
        """일괄 분석 테스트"""
        texts = [
            "좋습니다.",
            "나쁩니다.",
            "보통입니다."
        ]

        results = self.analyzer.analyze_batch(texts)
        self.assertEqual(len(results), 3)

    def test_analyze_data(self):
        """데이터 리스트 분석 테스트"""
        data = [
            {'title': '좋은 소식', 'content': '매우 긍정적입니다.'},
            {'title': '나쁜 소식', 'content': '매우 부정적입니다.'}
        ]

        analyzed = self.analyzer.analyze_data(data)

        self.assertIn('sentiment_label', analyzed[0])
        self.assertIn('sentiment_score', analyzed[0])
        self.assertEqual(analyzed[0]['sentiment_label'], 'positive')
        self.assertEqual(analyzed[1]['sentiment_label'], 'negative')


class TestSentimentFilter(unittest.TestCase):
    """감정 필터 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.test_data = [
            {'sentiment_label': 'positive', 'sentiment_score': 0.8, 'positive_score': 0.8, 'negative_score': 0.0},
            {'sentiment_label': 'negative', 'sentiment_score': -0.6, 'positive_score': 0.0, 'negative_score': 0.6},
            {'sentiment_label': 'neutral', 'sentiment_score': 0.0, 'positive_score': 0.0, 'negative_score': 0.0},
            {'sentiment_label': 'positive', 'sentiment_score': 0.4, 'positive_score': 0.4, 'negative_score': 0.0}
        ]

    def test_filter_by_sentiment(self):
        """감정 필터링 테스트"""
        positive = SentimentFilter.filter_by_sentiment(self.test_data, 'positive')
        self.assertEqual(len(positive), 2)

        negative = SentimentFilter.filter_by_sentiment(self.test_data, 'negative')
        self.assertEqual(len(negative), 1)

    def test_sort_by_sentiment(self):
        """감정 정렬 테스트"""
        sorted_data = SentimentFilter.sort_by_sentiment(self.test_data, 'positive', reverse=True)

        # 첫 번째가 가장 높은 긍정 점수
        self.assertEqual(sorted_data[0]['positive_score'], 0.8)

    def test_get_sentiment_distribution(self):
        """감정 분포 통계 테스트"""
        distribution = SentimentFilter.get_sentiment_distribution(self.test_data)

        self.assertEqual(distribution['positive'], 2)
        self.assertEqual(distribution['negative'], 1)
        self.assertEqual(distribution['neutral'], 1)

    def test_get_sentiment_summary(self):
        """감정 요약 통계 테스트"""
        summary = SentimentFilter.get_sentiment_summary(self.test_data)

        self.assertEqual(summary['total_count'], 4)
        self.assertEqual(summary['positive_count'], 2)
        self.assertEqual(summary['negative_count'], 1)
        self.assertEqual(summary['neutral_count'], 1)


class TestSentimentConfig(unittest.TestCase):
    """감정 분석 설정 테스트"""

    def test_custom_config(self):
        """커스텀 설정 테스트"""
        config = SentimentConfig(
            positive_threshold=0.3,
            negative_threshold=-0.3
        )

        analyzer = SentimentAnalyzer(config)

        # 낮은 긍정 점수 (임계값 미달)
        text = "괜찮습니다."
        result = analyzer.analyze(text)

        # 임계값이 높아서 중립으로 분류될 수 있음
        self.assertIn(result.label, ['neutral', 'positive'])


def test_integration_with_crawler():
    """크롤러 통합 테스트"""
    print("\n" + "=" * 80)
    print("크롤러 통합 테스트")
    print("=" * 80)

    try:
        from web_crawler import WebCrawler, ExcelExporter

        # 초기화
        crawler = WebCrawler(use_cache=True)
        analyzer = SentimentAnalyzer()
        exporter = ExcelExporter()

        # 데이터 수집
        print("\nAI 뉴스 수집 중...")
        data = crawler.search_google_news("AI", max_results=5)

        if not data:
            print("수집된 데이터가 없습니다.")
            return

        # 감정 분석
        print("감정 분석 중...")
        data = analyzer.analyze_data(data)

        # 결과 출력
        print("\n분석 결과:")
        for item in data[:3]:
            print(f"  {item.get('title', 'N/A')[:50]}...")
            print(f"    감정: {item.get('sentiment_label', 'N/A')}, 점수: {item.get('sentiment_score', 0):.3f}")

        # 통계
        summary = SentimentFilter.get_sentiment_summary(data)
        print(f"\n통계:")
        print(f"  긍정: {summary['positive_count']}개")
        print(f"  부정: {summary['negative_count']}개")
        print(f"  중립: {summary['neutral_count']}개")

        # 저장
        output_file = "sentiment_test_results.xlsx"
        exporter.save_to_excel(data, output_file)
        print(f"\n결과가 {output_file}에 저장되었습니다.")

        crawler.close()

    except Exception as e:
        print(f"테스트 중 오류: {e}")


def run_manual_tests():
    """수동 테스트 실행"""
    print("\n" + "=" * 80)
    print("수동 감정 분석 테스트")
    print("=" * 80)

    analyzer = SentimentAnalyzer()

    test_cases = [
        ("긍정 테스트 1", "이 제품은 정말 최고입니다! 강력 추천합니다.", 'positive'),
        ("긍정 테스트 2", "성과가 매우 우수하고 성장세가 뚜렷합니다.", 'positive'),
        ("부정 테스트 1", "최악의 경험이었습니다. 절대 다시는 이용하지 않겠습니다.", 'negative'),
        ("부정 테스트 2", "실적이 급락하고 위기 상황입니다.", 'negative'),
        ("중립 테스트", "오늘 회의에서 일정이 논의되었습니다.", 'neutral')
    ]

    print("\n테스트 케이스:")
    all_passed = True

    for name, text, expected in test_cases:
        result = analyzer.analyze(text)
        passed = result.label == expected
        status = "✓" if passed else "✗"

        print(f"\n{status} {name}")
        print(f"  텍스트: {text}")
        print(f"  예상: {expected}, 실제: {result.label}")
        print(f"  점수: {result.sentiment_score:.3f}")

        if not passed:
            all_passed = False

    print("\n" + "=" * 80)
    if all_passed:
        print("모든 테스트 통과!")
    else:
        print("일부 테스트 실패")
    print("=" * 80)


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 80)
    print("🧪 감정 분석 시스템 테스트")
    print("=" * 80)

    # 유닛 테스트
    print("\n1. 유닛 테스트 실행...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # 수동 테스트
    print("\n2. 수동 테스트 실행...")
    run_manual_tests()

    # 통합 테스트
    print("\n3. 통합 테스트 실행...")
    test_integration_with_crawler()

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()
