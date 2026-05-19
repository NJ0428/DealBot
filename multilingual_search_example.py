#!/usr/bin/env python3
"""
다국어 검색 예제 스크립트
Google Translation API를 활용한 다국어 키워드 검색 및 결과 번역
"""

import sys
import json
from pathlib import Path
from web_crawler import WebCrawler, Config, SupportedLanguage
from translation_service import TranslationConfig, MultiLanguageSearchHelper
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_basic_translation():
    """예제 1: 기본 번역 기능 테스트"""
    print("=" * 60)
    print("예제 1: 기본 번역 기능 테스트")
    print("=" * 60)

    from translation_service import TranslationService

    # 번역 서비스 초기화
    config = TranslationConfig()
    translation_service = TranslationService(
        credentials_path=config.get_credentials_path(),
        api_key=config.get_api_key()
    )

    if not translation_service.is_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        return

    # 키워드 번역
    keyword = "인공지능"
    print(f"\n원본 키워드: {keyword}")

    languages = ["en", "ja", "zh", "es"]
    translations = {}

    for lang in languages:
        translated = translation_service.translate(keyword, lang)
        if translated:
            translations[lang] = translated
            print(f"  {lang}: {translated}")

    # 번역 결과 저장
    result = {
        "keyword": keyword,
        "translations": translations,
        "timestamp": str(datetime.now())
    }

    output_file = Path("keyword_translations.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 번역 결과 저장 완료: {output_file}")


def example_2_multilingual_search():
    """예제 2: 다국어 검색"""
    print("\n" + "=" * 60)
    print("예제 2: 다국어 검색")
    print("=" * 60)

    # 크롤러 초기화 (번역 기능 활성화)
    crawler = WebCrawler(enable_translation=True)

    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        crawler.close()
        return

    # 다국어 검색
    keyword = "기후변화"
    languages = ["ko", "en", "ja", "zh"]

    print(f"\n🔍 다국어 검색: '{keyword}'")
    print(f"검색 언어: {', '.join(languages)}")

    results = crawler.search_multilingual(
        keyword=keyword,
        languages=languages,
        max_results=5,
        translate_results=False  # 원본 결과 유지
    )

    # 결과 요약
    print("\n📊 검색 결과 요약:")
    for lang, articles in results.items():
        lang_name = SupportedLanguage.get_language_name(lang)
        print(f"  {lang_name} ({lang}): {len(articles)}개 항목")

    # 결과 저장
    output_file = Path("multilingual_search_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        # 딕셔너리를 JSON 직렬화 가능한 형태로 변환
        serializable_results = {}
        for lang, articles in results.items():
            serializable_results[lang] = [
                {k: str(v) if v else "" for k, v in article.items()}
                for article in articles
            ]

        json.dump(serializable_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 다국어 검색 결과 저장 완료: {output_file}")

    crawler.close()


def example_3_translated_search_results():
    """예제 3: 번역된 검색 결과"""
    print("\n" + "=" * 60)
    print("예제 3: 번역된 검색 결과")
    print("=" * 60)

    # 크롤러 초기화
    crawler = WebCrawler(enable_translation=True)

    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        crawler.close()
        return

    # 다국어 검색 및 결과 번역
    keyword = "신재생에너지"
    languages = ["ko", "en", "ja"]

    print(f"\n🔍 다국어 검색 및 번역: '{keyword}'")
    print(f"검색 언어: {', '.join(languages)}")
    print(f"번역 언어: English")

    results = crawler.search_multilingual(
        keyword=keyword,
        languages=languages,
        max_results=3,
        translate_results=True,
        target_language="en"
    )

    # 번역된 결과 표시
    print("\n📊 번역된 검색 결과:")
    for lang, articles in results.items():
        lang_name = SupportedLanguage.get_language_name(lang)
        print(f"\n{lang_name} ({lang}):")
        for i, article in enumerate(articles[:2], 1):  # 각 언어당 2개만 표시
            title = article.get('제목', 'N/A')
            print(f"  {i}. {title}")

    crawler.close()


def example_4_keyword_translation_batch():
    """예제 4: 여러 키워드 일괄 번역"""
    print("\n" + "=" * 60)
    print("예제 4: 여러 키워드 일괄 번역")
    print("=" * 60)

    from translation_service import TranslationService

    # 번역 서비스 초기화
    config = TranslationConfig()
    translation_service = TranslationService(
        credentials_path=config.get_credentials_path(),
        api_key=config.get_api_key()
    )

    if not translation_service.is_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        return

    # 여러 키워드 번역
    keywords = ["기후변화", "인공지능", "신재생에너지", "디지털전환"]
    target_languages = ["en", "ja", "zh"]

    print(f"\n원본 키워드: {', '.join(keywords)}")
    print(f"번역 언어: {', '.join(target_languages)}")

    translated_keywords = translation_service.translate_keywords(
        keywords, target_languages
    )

    # 번역 결과 표시
    print("\n📊 번역 결과:")
    for original, translations in translated_keywords.items():
        print(f"\n{original}:")
        for lang, translated in translations.items():
            print(f"  {lang}: {translated}")

    # 결과 저장
    output_file = Path("batch_keyword_translations.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(translated_keywords, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 일괄 번역 결과 저장 완료: {output_file}")


def example_5_language_detection():
    """예제 5: 언어 감지"""
    print("\n" + "=" * 60)
    print("예제 5: 언어 감지")
    print("=" * 60)

    from translation_service import TranslationService

    # 번역 서비스 초기화
    config = TranslationConfig()
    translation_service = TranslationService(
        credentials_path=config.get_credentials_path(),
        api_key=config.get_api_key()
    )

    if not translation_service.is_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        return

    # 다양한 언어 텍스트 감지
    test_texts = [
        ("한국어", "안녕하세요, 오늘 날씨가 좋습니다."),
        ("English", "Hello, the weather is nice today."),
        ("日本語", "こんにちは、今日の天気は良いです。"),
        ("中文", "你好，今天天气很好。"),
        ("Español", "Hola, el clima es bueno hoy."),
        ("Français", "Bonjour, le temps est bon aujourd'hui.")
    ]

    print("\n📊 언어 감지 결과:")
    for expected, text in test_texts:
        detected = translation_service.detect_language(text)
        lang_name = SupportedLanguage.get_language_name(detected) if detected else "Unknown"
        status = "✅" if detected in ["ko", "en", "ja", "zh", "es", "fr"] else "⚠️"
        print(f"{status} '{text}' -> {detected} ({lang_name}) [기대: {expected}]")


def example_6_custom_multilingual_search():
    """예제 6: 사용자 정의 다국어 검색"""
    print("\n" + "=" * 60)
    print("예제 6: 사용자 정의 다국어 검색")
    print("=" * 60)

    # 사용자 입력 받기
    print("\n사용자 정의 다국어 검색 설정")

    try:
        keyword = input("검색 키워드 (기본값: 기술): ").strip() or "기술"

        print("\n사용 가능한 언어:")
        all_langs = SupportedLanguage.get_all_languages()
        for code, name in all_langs.items():
            print(f"  {code}: {name}")

        langs_input = input("\n검색할 언어 코드 (쉼표로 구분, 예: ko,en,ja): ").strip()
        languages = [l.strip() for l in langs_input.split(',')] if langs_input else Config.SUPPORTED_LANGUAGES

        max_results = int(input(f"각 언어당 최대 결과 수 (기본값: 3): ").strip() or "3")

        translate = input("결과를 번역하시겠습니까? (y/n, 기본값: n): ").strip().lower() == 'y'
        target_lang = input("번역 언어 (기본값: en): ").strip() or "en"

        # 크롤러 초기화
        crawler = WebCrawler(enable_translation=True)

        if not crawler.is_translation_available():
            print("❌ 번역 서비스를 사용할 수 없습니다.")
            crawler.close()
            return

        # 다국어 검색 수행
        print(f"\n🔍 다국어 검색 시작: '{keyword}'")
        results = crawler.search_multilingual(
            keyword=keyword,
            languages=languages,
            max_results=max_results,
            translate_results=translate,
            target_language=target_lang
        )

        # 결과 요약
        print("\n📊 검색 결과 요약:")
        for lang, articles in results.items():
            lang_name = SupportedLanguage.get_language_name(lang)
            print(f"  {lang_name} ({lang}): {len(articles)}개 항목")

        # 결과 저장
        timestamp = str(datetime.now().strftime('%Y%m%d_%H%M%S'))
        output_file = Path(f"custom_multilingual_search_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            serializable_results = {}
            for lang, articles in results.items():
                serializable_results[lang] = [
                    {k: str(v) if v else "" for k, v in article.items()}
                    for article in articles
                ]

            json.dump(serializable_results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 사용자 정의 검색 결과 저장 완료: {output_file}")

        crawler.close()

    except KeyboardInterrupt:
        print("\n\n사용자가 검색을 취소했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


def main():
    """메인 함수"""
    from datetime import datetime

    print("=" * 60)
    print("🌐 다국어 검색 예제 스크립트")
    print("=" * 60)
    print("\nGoogle Translation API를 활용한 다국어 검색 및 번역 기능")
    print("Google Cloud 자격 증명이 필요합니다.")

    try:
        print("\n[예제 메뉴]")
        print("1. 기본 번역 기능 테스트")
        print("2. 다국어 검색")
        print("3. 번역된 검색 결과")
        print("4. 여러 키워드 일괄 번역")
        print("5. 언어 감지")
        print("6. 사용자 정의 다국어 검색")
        print("0. 종료")

        choice = input("\n실행할 예제를 선택하세요 (0-6): ").strip()

        if choice == "1":
            example_1_basic_translation()
        elif choice == "2":
            example_2_multilingual_search()
        elif choice == "3":
            example_3_translated_search_results()
        elif choice == "4":
            example_4_keyword_translation_batch()
        elif choice == "5":
            example_5_language_detection()
        elif choice == "6":
            example_6_custom_multilingual_search()
        elif choice == "0":
            print("\n프로그램을 종료합니다.")
        else:
            print("❌ 잘못된 선택입니다.")

    except KeyboardInterrupt:
        print("\n\n사용자가 프로그램을 종료했습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        logger.error(f"메인 함수 오류: {e}", exc_info=True)

    print("\n✨ 예제 실행 완료!")


if __name__ == "__main__":
    main()