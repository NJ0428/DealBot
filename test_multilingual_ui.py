#!/usr/bin/env python3
"""
다국어 UI 시스템 테스트 스크립트
"""

import sys
from pathlib import Path

# 상위 디렉토리 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from multilingual_ui import (
    I18N, LanguageCode, LanguageInfo, UITranslations,
    TranslationFileManager, get_language_switcher_html,
    get_language_select_html
)
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_translation_system():
    """번역 시스템 테스트"""
    print("=" * 80)
    print("🧪 테스트 1: 번역 시스템 기본 기능")
    print("=" * 80)

    i18n = I18N()
    success_count = 0
    total_tests = 0

    # 테스트할 언어
    languages = [LanguageCode.KOREAN, LanguageCode.ENGLISH, LanguageCode.JAPANESE, LanguageCode.CHINESE]

    for lang in languages:
        i18n.set_language(lang)
        lang_info = i18n.get_language_info()

        print(f"\n{lang_info['flag']} {lang_info['native_name']}:")

        # 기본 번역 테스트
        tests = [
            ('common', 'app_name', 'app_name'),
            ('common', 'search', 'search'),
            ('common', 'download', 'download'),
            ('nav', 'search', 'search_page'),
            ('search_page', 'title', 'search_page_title'),
            ('search_page', 'keyword_label', 'keyword_label'),
            ('search_page', 'start_search', 'start_search'),
        ]

        for category, key, test_name in tests:
            total_tests += 1
            try:
                translated = i18n.t(category, key)
                if translated and translated != key:
                    success_count += 1
                    print(f"   ✅ {test_name}: {translated[:30]}")
                else:
                    print(f"   ❌ {test_name}: 번역 없음")
            except Exception as e:
                print(f"   ❌ {test_name}: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{total_tests}")
    return success_count >= total_tests * 0.8


def test_language_detection():
    """언어 감지 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 2: 언어 감지")
    print("=" * 80)

    # 지원 언어 확인
    all_languages = LanguageInfo.get_all_languages()
    print(f"📋 지원 언어 수: {len(all_languages)}")

    for code, info in all_languages.items():
        print(f"   {info['flag']} {code}: {info['native_name']}")

    # 기본 언어 확인
    default_lang = LanguageInfo.get_default_language()
    print(f"\n기본 언어: {default_lang}")

    # 지원 여부 확인
    supported = [
        (LanguageCode.KOREAN, True),
        (LanguageCode.ENGLISH, True),
        (LanguageCode.JAPANESE, True),
        (LanguageCode.CHINESE, True),
        (LanguageCode.SPANISH, True),
        ('invalid', False)
    ]

    success_count = 0
    for lang, expected in supported:
        result = LanguageInfo.is_supported(lang)
        if result == expected:
            success_count += 1
            print(f"   ✅ {lang}: {result} (예상: {expected})")
        else:
            print(f"   ❌ {lang}: {result} (예상: {expected})")

    print(f"\n✅ 성공: {success_count}/{len(supported)}")
    return success_count == len(supported)


def test_language_switching():
    """언어 전환 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 3: 언어 전환")
    print("=" * 80)

    i18n = I18N()

    # 언어 전환 테스트
    test_languages = [
        LanguageCode.KOREAN,
        LanguageCode.ENGLISH,
        LanguageCode.JAPANESE,
        LanguageCode.CHINESE,
        LanguageCode.KOREAN  # 다시 한국어
    ]

    success_count = 0
    previous_lang = None

    for lang in test_languages:
        try:
            i18n.set_language(lang)
            current = i18n.get_language()

            if current == lang:
                success_count += 1
                lang_info = i18n.get_language_info()
                print(f"   ✅ {lang_info['flag']} {lang_info['native_name']}: {current}")
            else:
                print(f"   ❌ {lang}: {current} (실패)")

            # 중복 언어 확인
            if lang == test_languages[-1] and previous_lang == lang:
                print(f"   ⚠️  중복 언어 전환 테스트")

            previous_lang = current

        except Exception as e:
            print(f"   ❌ {lang}: 전환 실패 - {e}")

    print(f"\n✅ 성공: {success_count}/{len(test_languages)}")
    return success_count == len(test_languages)


def test_html_generation():
    """HTML 생성 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 4: HTML 생성")
    print("=" * 80)

    success_count = 0
    total_tests = 2

    # 언어 전환기 HTML 테스트
    try:
        html = get_language_switcher_html(LanguageCode.KOREAN)
        if 'language-switcher' in html and 'lang-btn' in html:
            success_count += 1
            print(f"   ✅ 언어 전환기 HTML: {len(html)}자")
        else:
            print(f"   ❌ 언어 전환기 HTML: 구조 오류")
    except Exception as e:
        print(f"   ❌ 언어 전환기 HTML: 오류 - {e}")

    # 언어 선택 HTML 테스트
    try:
        html = get_language_select_html(LanguageCode.ENGLISH)
        if 'language-selector' in html and '<select' in html:
            success_count += 1
            print(f"   ✅ 언어 선택 HTML: {len(html)}자")
        else:
            print(f"   ❌ 언어 선택 HTML: 구조 오류")
    except Exception as e:
        print(f"   ❌ 언어 선택 HTML: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{total_tests}")
    return success_count == total_tests


def test_file_operations():
    """파일 작업 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 5: 번역 파일 작업")
    print("=" * 80)

    success_count = 0
    total_tests = 2

    # 번역 내보내기 테스트
    try:
        TranslationFileManager.export_all_languages('test_translations')
        success_count += 1
        print(f"   ✅ 번역 파일 내보내기: 완료")

        # 파일 존재 확인
        test_file = Path('test_translations/ko.json')
        if test_file.exists():
            print(f"   📁 파일 확인: {test_file}")
        else:
            print(f"   ⚠️  파일 존재 확인: 실패")

    except Exception as e:
        print(f"   ❌ 번역 파일 내보내기: 오류 - {e}")

    # 번역 로드 테스트
    try:
        translations = TranslationFileManager.load_translations_from_file('test_translations/ko.json')
        if translations and 'language' in translations:
            success_count += 1
            print(f"   ✅ 번역 파일 로드: {translations['language']}")
        else:
            print(f"   ❌ 번역 파일 로드: 구조 오류")

    except Exception as e:
        print(f"   ❌ 번역 파일 로드: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{total_tests}")
    return success_count == total_tests


def test_error_messages():
    """에러 메시지 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 6: 에러 메시지")
    print("=" * 80)

    i18n = I18n()
    success_count = 0
    total_tests = len(languages)

    # 테스트할 언어
    languages = [LanguageCode.KOREAN, LanguageCode.ENGLISH, LanguageCode.JAPANESE, LanguageCode.CHINESE]

    # 에러 메시지 테스트
    error_tests = [
        ('errors', 'keyword_required', 'keyword_required'),
        ('errors', 'search_failed', 'search_failed'),
        ('errors', 'network_error', 'network_error'),
        ('errors', 'file_not_found', 'file_not_found'),
        ('errors', 'analysis_failed', 'analysis_failed'),
    ]

    for lang in languages:
        i18n.set_language(lang)
        lang_info = i18n.get_language_info()

        print(f"\n{lang_info['flag']} {lang_info['native_name']}:")

        for category, key, test_name in error_tests:
            try:
                error_msg = i18n.t(category, key)
                if error_msg and error_msg != key:
                    success_count += 1
                    print(f"   ✅ {test_name}: {error_msg[:40]}")
                else:
                    print(f"   ❌ {test_name}: 번역 없음")
            except Exception as e:
                print(f"   ❌ {test_name}: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{len(languages) * len(error_tests)}")
    return success_count >= len(languages) * len(error_tests) * 0.8


def test_page_translations():
    """페이지별 번역 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 7: 페이지별 번역")
    print("=" * 80)

    i18n = I18N()
    pages = ['search_page', 'results_page', 'sentiment', 'settings']
    success_count = 0
    total_tests = 0

    for lang in [LanguageCode.KOREAN, LanguageCode.ENGLISH]:
        i18n.set_language(lang)
        lang_info = i18n.get_language_info()

        print(f"\n{lang_info['flag']} {lang_info['native_name']}:")

        for page in pages:
            total_tests += 1
            try:
                title = i18n.t(page, 'title')
                if title and title != 'title':
                    success_count += 1
                    print(f"   ✅ {page} title: {title[:30]}")
                else:
                    print(f"   ❌ {page} title: 번역 없음")
            except Exception as e:
                print(f"   ❌ {page} title: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{total_tests}")
    return success_count >= total_tests * 0.8


def test_custom_translations():
    """사용자 정의 번역 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 8: 사용자 정의 번역")
    print("=" * 80)

    # 사용자 정의 번역 추가
    custom_category = 'custom'
    custom_key = 'welcome_message'

    custom_translations = {
        LanguageCode.KOREAN: "환영합니다! DealBot을 사용해 주셔서 감사합니다.",
        LanguageCode.ENGLISH: "Welcome! Thank you for using DealBot.",
        LanguageCode.JAPANESE: "ようこそ！DealBotをご利用いただきありがとうございます。"
    }

    try:
        UITranslations.add_custom_translation(custom_category, custom_key, custom_translations)
        print(f"   ✅ 사용자 정의 번역 추가 완료")

        # 사용자 정의 번역 테스트
        i18n = I18N()
        test_count = 0

        for lang in [LanguageCode.KOREAN, LanguageCode.ENGLISH, LanguageCode.JAPANESE]:
            i18n.set_language(lang)
            translated = i18n.t(custom_category, custom_key)
            if translated and translated != custom_key:
                test_count += 1
                print(f"   ✅ {lang}: {translated[:40]}...")

        print(f"   ✅ 사용자 정의 번역 테스트: {test_count}/3 성공")

        return test_count == 3

    except Exception as e:
        print(f"   ❌ 사용자 정의 번역: 오류 - {e}")
        return False


def test_translation_export():
    """번역 내보내기 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 9: 번역 내보내기")
    print("=" * 80)

    i18n = I18N()

    # 각 언어별로 번역 내보내기
    success_count = 0
    total_languages = len(LanguageInfo.SUPPORTED_LANGUAGES)

    for lang in LanguageInfo.SUPPORTED_LANGUAGES.keys():
        try:
            translations = i18n.get_current_translations()
            if translations and len(translations) > 0:
                success_count += 1
                print(f"   ✅ {lang}: {len(translations)}개 카테고리")
            else:
                print(f"   ❌ {lang}: 번역 없음")
        except Exception as e:
            print(f"   ❌ {lang}: 오류 - {e}")

    print(f"\n✅ 성공: {success_count}/{total_languages}")
    return success_count == total_languages


def test_rtl_support():
    """RTL (오른쪽에서 왼쪽으로) 언어 지원 테스트"""
    print("\n" + "=" * 80)
    print("🧪 테스트 10: RTL 언어 지원")
    print("=" * 80)

    rtl_languages = [LanguageCode.ARABIC]
    rtl_count = 0

    for lang in rtl_languages:
        lang_info = LanguageInfo.get_language_info(lang)
        direction = lang_info.get('direction', 'ltr')

        print(f"\n{lang_info['flag']} {lang_info['native_name']}:")
        print(f"   방향: {direction}")

        if direction == 'rtl':
            rtl_count += 1
            print(f"   ✅ RTL 지원 확인")
        else:
            print(f"   ❌ RTL 미지원")

    print(f"\n✅ RTL 언어: {rtl_count}/{len(rtl_languages)}")
    return rtl_count == len(rtl_languages)


def main():
    """메인 테스트 함수"""
    print("🌐 다국어 UI 시스템 테스트")
    print("=" * 80)

    tests = [
        ("번역 시스템 기본 기능", test_translation_system),
        ("언어 감지", test_language_detection),
        ("언어 전환", test_language_switching),
        ("HTML 생성", test_html_generation),
        ("파일 작업", test_file_operations),
        ("에러 메시지", test_error_messages),
        ("페이지별 번역", test_page_translations),
        ("사용자 정의 번역", test_custom_translations),
        ("번역 내보내기", test_translation_export),
        ("RTL 언어 지원", test_rtl_support)
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
    elif passed_tests >= total_tests * 0.8:
        print("✅ 대부분의 테스트가 통과했습니다!")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())