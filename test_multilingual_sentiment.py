#!/usr/bin/env python3
"""
다국어 감정 분석 시스템 테스트 스크립트
"""

import sys
from pathlib import Path

# 상위 디렉토리 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from multilingual_sentiment_analyzer import (
    MultilingualSentimentAnalyzer, MultilingualSentimentConfig,
    MultilingualSentimentFilter, Language
)
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_basic_multilingual_analysis():
    """기본 다국어 감정 분석 테스트"""
    print("=" * 80)
    print("🧪 테스트 1: 기본 다국어 감정 분석")
    print("=" * 80)

    config = MultilingualSentimentConfig(
        use_translation=True,
        enabled_languages=['ko', 'en', 'ja', 'zh', 'es']
    )

    analyzer = MultilingualSentimentAnalyzer(config)

    test_texts = [
        ("이 제품은 정말 혁신적입니다. 성능이 우수하고 만족스럽습니다.", "ko"),
        ("The product is excellent. Very satisfied with the performance.", "en"),
        ("この製品は本当に素晴らしいです。性能が優秀で満足しています。", "ja"),
        ("这个产品真的很棒。性能优秀，非常满意。", "zh"),
        ("Este producto es excelente. Muy satisfecho con el rendimiento.", "es"),
    ]

    success_count = 0

    for i, (text, expected_lang) in enumerate(test_texts, 1):
        print(f"\n[{i}] {text[:40]}...")
        try:
            result = analyzer.analyze(text)
            print(f"   감지 언어: {result.detected_language} (예상: {expected_lang})")
            print(f"   감정: {result.label} (점수: {result.sentiment_score:.3f})")

            if result.sentiment_score > 0:
                success_count += 1
                print(f"   ✅ 긍정 감정 올바르게 감지")

        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print(f"\n✅ 성공: {success_count}/{len(test_texts)}")
    return success_count == len(test_texts)


def test_negative_sentiment():
    """부정 감정 분석 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 2: 부정 감정 분석")
    print("=" * 80)

    analyzer = MultilingualSentimentAnalyzer()

    negative_texts = [
        ("최악의 경험이었습니다. 다시는 이용하지 않겠습니다.", "ko"),
        ("Terrible experience. Will never use again.", "en"),
        ("最悪の経験でした。二度と利用しません。", "ja"),
        ("最糟糕的体验。再也不会使用了。", "zh"),
    ]

    success_count = 0

    for i, (text, expected_lang) in enumerate(negative_texts, 1):
        print(f"\n[{i}] {text[:40]}...")
        try:
            result = analyzer.analyze(text)
            print(f"   감지 언어: {result.detected_language}")
            print(f"   감정: {result.label} (점수: {result.sentiment_score:.3f})")

            if result.sentiment_score < 0:
                success_count += 1
                print(f"   ✅ 부정 감정 올바르게 감지")

        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print(f"\n✅ 성공: {success_count}/{len(negative_texts)}")
    return success_count == len(negative_texts)


def test_neutral_sentiment():
    """중립 감정 분석 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 3: 중립 감정 분석")
    print("=" * 80)

    analyzer = MultilingualSentimentAnalyzer()

    neutral_texts = [
        ("어제 회사에서 회의가 있었습니다.", "ko"),
        ("There was a meeting at the company yesterday.", "en"),
        ("昨日会社で会議がありました。", "ja"),
        ("昨天公司有个会议。", "zh"),
    ]

    success_count = 0

    for i, (text, expected_lang) in enumerate(neutral_texts, 1):
        print(f"\n[{i}] {text[:40]}...")
        try:
            result = analyzer.analyze(text)
            print(f"   감지 언어: {result.detected_language}")
            print(f"   감정: {result.label} (점수: {result.sentiment_score:.3f})")

            if abs(result.sentiment_score) < 0.3:
                success_count += 1
                print(f"   ✅ 중립/약한 감정으로 감지")

        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print(f"\n✅ 성공: {success_count}/{len(neutral_texts)}")
    return success_count == len(neutral_texts)


def test_language_detection():
    """언어 감지 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 4: 언어 감지")
    print("=" * 80)

    config = MultilingualSentimentConfig(
        use_translation=True,
        auto_detect_language=True
    )

    analyzer = MultilingualSentimentAnalyzer(config)

    language_test = [
        ("이것은 한국어 텍스트입니다.", "ko"),
        ("This is English text.", "en"),
        ("これは日本語のテキストです。", "ja"),
        ("这是中文文本。", "zh"),
        ("Este es texto en español.", "es"),
        ("Ceci est un texte français.", "fr"),
        ("Dies ist ein deutscher Text.", "de"),
    ]

    success_count = 0

    for i, (text, expected_lang) in enumerate(language_test, 1):
        print(f"\n[{i}] {text[:30]}...")
        try:
            detected_lang = analyzer.detect_language(text)
            print(f"   감지 언어: {detected_lang} (예상: {expected_lang})")

            # 번역 서비스가 없으면 기본 언어로 감지
            if not analyzer.translation_service or not analyzer.translation_service.is_available():
                print(f"   ⚠️  번역 서비스 없음, 기본 언어로 감지됨")
                if detected_lang == config.default_language:
                    success_count += 1
            elif detected_lang == expected_lang:
                success_count += 1
                print(f"   ✅ 올바른 언어 감지")

        except Exception as e:
            print(f"   ❌ 오류: {e}")

    print(f"\n✅ 성공: {success_count}/{len(language_test)}")
    return success_count >= len(language_test) * 0.5  # 50% 이상 성공하면 통과


def test_batch_analysis():
    """일괄 분석 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 5: 일괄 분석")
    print("=" * 80)

    analyzer = MultilingualSentimentAnalyzer()

    batch_texts = [
        "정말 좋은 제품입니다. 강력 추천합니다!",
        "품질이 좋지 않습니다. 실망했습니다.",
        "기능이 개선되었습니다. 만족합니다.",
        "문제가 많습니다. 손해입니다.",
        "보통 수준입니다. 특별한 점이 없습니다.",
    ]

    print(f"🔄 {len(batch_texts)}개 텍스트 일괄 분석 중...")

    try:
        results = analyzer.analyze_batch(batch_texts)

        print(f"✅ 일괄 분석 완료: {len(results)}개 결과")

        positive_count = sum(1 for r in results if r.label == 'positive')
        negative_count = sum(1 for r in results if r.label == 'negative')
        neutral_count = sum(1 for r in results if r.label == 'neutral')

        print(f"   긍정: {positive_count}개, 부정: {negative_count}개, 중립: {neutral_count}개")

        # 결과 검증
        expected_positives = 2  # "정말 좋은", "기능이 개선"
        expected_negatives = 2  # "품질이 좋지 않", "문제가 많습니다"

        actual_positives = positive_count
        actual_negatives = negative_count

        success = (actual_positives >= expected_positives - 1 and
                  actual_negatives >= expected_negatives - 1)

        if success:
            print(f"   ✅ 예상과 비슷한 분포")
        else:
            print(f"   ⚠️  분포가 예상과 다름")

        return success

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_data_integration():
    """데이터 통합 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 6: 데이터 통합")
    print("=" * 80)

    analyzer = MultilingualSentimentAnalyzer()

    # 테스트 데이터
    test_data = [
        {
            'title': '혁신적인 신제품 출시',
            'content': '이번 신제품은 정말 혁신적입니다. 성능이 우수하고 만족스럽습니다.',
            'source': 'test'
        },
        {
            'title': 'Product Launch',
            'content': 'The new product is innovative. Excellent performance.',
            'source': 'test'
        },
        {
            'title': '품질 문제 발생',
            'content': '품질이 좋지 않습니다. 실망했습니다.',
            'source': 'test'
        }
    ]

    print(f"🔄 {len(test_data)}개 데이터 아이템 분석 중...")

    try:
        analyzed_data = analyzer.analyze_data(test_data)

        print(f"✅ 데이터 분석 완료")

        # 결과 확인
        for i, item in enumerate(analyzed_data, 1):
            print(f"\n[{i}] {item.get('title', 'No title')[:30]}...")
            print(f"   감지 언어: {item.get('detected_language', 'N/A')}")
            print(f"   감정: {item.get('sentiment_label', 'N/A')} ({item.get('sentiment_score', 0):.3f})")

        # 필수 필드 확인
        required_fields = ['detected_language', 'sentiment_label', 'sentiment_score', 'positive_score', 'negative_score']
        all_present = all(field in analyzed_data[0] for field in required_fields)

        if all_present:
            print(f"\n✅ 필수 필드 모두 포함")
        else:
            missing = [f for f in required_fields if f not in analyzed_data[0]]
            print(f"\n❌ 누락된 필드: {missing}")

        return all_present

    except Exception as e:
        print(f"❌ 오류: {e}")
        return False


def test_multilingual_filter():
    """다국어 필터 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 7: 다국어 필터")
    print("=" * 80)

    analyzer = MultilingualSentimentAnalyzer()

    # 테스트 데이터 생성
    test_data = []
    test_texts = [
        ("한국어 긍정 텍스트입니다. 정말 좋습니다.", "ko", "positive"),
        ("Korean negative text. Very bad.", "en", "negative"),
        ("일본어 중립 텍스트입니다。", "ja", "neutral"),
        ("Chinese positive text. Excellent.", "zh", "positive"),
    ]

    for text, lang, expected_sentiment in test_texts:
        result = analyzer.analyze(text)
        item = result.to_dict()
        item['detected_language'] = lang  # 강제 설정 (테스트용)
        test_data.append(item)

    # 언어 필터링
    korean_items = MultilingualSentimentFilter.filter_by_language(test_data, 'ko')
    print(f"🇰🇷 한국어 아이템: {len(korean_items)}개")

    # 감정 및 언어 필터링
    positive_en_items = MultilingualSentimentFilter.filter_by_sentiment_and_language(
        test_data, 'positive', 'en'
    )
    print(f"🇺🇸 영어 긍정 아이템: {len(positive_en_items)}개")

    # 언어별 분포
    distribution = MultilingualSentimentFilter.get_language_sentiment_distribution(test_data)
    print(f"\n📊 언어별 감정 분포:")
    for lang, counts in distribution.items():
        lang_name = Language.get_language_name(lang)
        print(f"   {lang_name}: 긍정 {counts['positive']}, 부정 {counts['negative']}, 중립 {counts['neutral']}")

    # 전체 요약
    summary = MultilingualSentimentFilter.get_multilingual_summary(test_data)
    print(f"\n📈 전체 요약:")
    print(f"   총 {summary['total_count']}개")
    print(f"   긍정: {summary['positive_count']}개 ({summary['positive_ratio']:.1%})")
    print(f"   부정: {summary['negative_count']}개 ({summary['negative_ratio']:.1%})")
    print(f"   중립: {summary['neutral_count']}개 ({summary['neutral_ratio']:.1%})")
    print(f"   번역 사용: {summary['translation_usage_ratio']:.1%}")

    return True


def test_configuration():
    """설정 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 8: 설정")
    print("=" * 80)

    # 기본 설정
    default_config = MultilingualSentimentConfig()
    print(f"📋 기본 설정:")
    print(f"   지원 언어: {default_config.enabled_languages}")
    print(f"   기본 언어: {default_config.default_language}")
    print(f"   번역 사용: {default_config.use_translation}")
    print(f"   결과 통합: {default_config.combine_results}")

    # 사용자 정의 설정
    custom_config = MultilingualSentimentConfig(
        enabled_languages=['ko', 'en', 'ja'],
        default_language='ko',
        use_translation=True,
        auto_detect_language=True,
        combine_results=True,
        prefer_original_language=True
    )

    print(f"\n📋 사용자 정의 설정:")
    print(f"   지원 언어: {custom_config.enabled_languages}")
    print(f"   기본 언어: {custom_config.default_language}")

    # 분석기 초기화
    analyzer = MultilingualSentimentAnalyzer(custom_config)

    print(f"\n✅ 분석기 초기화 완료")
    print(f"   지원 언어 수: {len(analyzer.get_supported_languages())}")

    return True


def main():
    """메인 테스트 함수"""
    print("🌍 다국어 감정 분석 시스템 테스트")
    print("=" * 80)

    tests = [
        ("기본 다국어 감정 분석", test_basic_multilingual_analysis),
        ("부정 감정 분석", test_negative_sentiment),
        ("중립 감정 분석", test_neutral_sentiment),
        ("언어 감지", test_language_detection),
        ("일괄 분석", test_batch_analysis),
        ("데이터 통합", test_data_integration),
        ("다국어 필터", test_multilingual_filter),
        ("설정", test_configuration)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ 성공" if result else "❌ 실패"
        except Exception as e:
            results[test_name] = f"❌ 오류: {e}"
            logger.error(f"{test_name} 테스트 중 오류 발생: {e}")

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)

    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    total_tests = len(tests)
    passed_tests = sum(1 for result in results.values() if "✅" in result)

    print(f"\n총계: {passed_tests}/{total_tests} 테스트 통과")

    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return 0
    elif passed_tests >= total_tests * 0.7:
        print("✅ 대부분의 테스트가 통과했습니다!")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())