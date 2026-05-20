#!/usr/bin/env python3
"""
다국어 검색 기능 테스트 스크립트
"""

import unittest
import sys
from pathlib import Path
import json
from unittest.mock import Mock, patch

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from translation_service import (
    TranslationService,
    MultiLanguageSearchHelper,
    TranslationConfig,
    SupportedLanguage
)


class TestSupportedLanguage(unittest.TestCase):
    """지원 언어 테스트"""

    def test_language_enum_values(self):
        """언어 코드 값 테스트"""
        self.assertEqual(SupportedLanguage.KOREAN.value, "ko")
        self.assertEqual(SupportedLanguage.ENGLISH.value, "en")
        self.assertEqual(SupportedLanguage.JAPANESE.value, "ja")

    def test_get_language_name(self):
        """언어 이름 반환 테스트"""
        self.assertEqual(SupportedLanguage.get_language_name("ko"), "Korean")
        self.assertEqual(SupportedLanguage.get_language_name("en"), "English")
        self.assertEqual(SupportedLanguage.get_language_name("xx"), "xx")

    def test_get_all_languages(self):
        """모든 언어 반환 테스트"""
        all_langs = SupportedLanguage.get_all_languages()
        self.assertIn("ko", all_langs)
        self.assertIn("en", all_langs)
        self.assertIn("ja", all_langs)
        self.assertIsInstance(all_langs, dict)


class TestTranslationConfig(unittest.TestCase):
    """번역 설정 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.test_config_file = Path("test_translation_config.json")
        self.config = TranslationConfig(str(self.test_config_file))

    def tearDown(self):
        """테스트 정리"""
        if self.test_config_file.exists():
            self.test_config_file.unlink()

    def test_default_config(self):
        """기본 설정 테스트"""
        default_target = self.config.get_default_target_language()
        self.assertEqual(default_target, "en")

        supported_langs = self.config.get_supported_languages()
        self.assertIn("ko", supported_langs)
        self.assertIn("en", supported_langs)

    def test_config_file_operations(self):
        """설정 파일 작업 테스트"""
        # 설정 값 확인
        self.assertIsNotNone(self.config.get_credentials_path())
        self.assertIsNotNone(self.config.get_api_key())

        # 설정 메서드 테스트
        self.assertIsInstance(self.config.should_auto_detect_language(), bool)
        self.assertIsInstance(self.config.should_translate_search_results(), bool)


class TestTranslationService(unittest.TestCase):
    """번역 서비스 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.translation_service = TranslationService(api_key="test_key")

    def test_service_initialization(self):
        """서비스 초기화 테스트"""
        # API 키가 없는 경우 초기화 실패
        with patch('translation_service.translate.Client') as mock_client:
            mock_client.side_effect = Exception("API key required")

            service = TranslationService(api_key="test_key")
            self.assertFalse(service.is_available())

    def test_is_available(self):
        """서비스 사용 가능 여부 테스트"""
        # 초기 상태에서는 API 연결 실패
        self.assertFalse(self.translation_service.is_available())


class TestMultiLanguageSearchHelper(unittest.TestCase):
    """다국어 검색 헬퍼 테스트"""

    def setUp(self):
        """테스트 설정"""
        # 모의 번역 서비스 생성
        self.mock_translation_service = Mock(spec=TranslationService)
        self.mock_translation_service.is_available.return_value = False
        self.helper = MultiLanguageSearchHelper(self.mock_translation_service)

    def test_prepare_multilingual_keywords_no_service(self):
        """번역 서비스 없는 경우 키워드 준비 테스트"""
        result = self.helper.prepare_multilingual_keywords("테스트", ["en", "ja"])
        self.assertIn("ko", result)
        self.assertEqual(result["ko"], ["테스트"])

    def test_prepare_multilingual_keywords_with_service(self):
        """번역 서비스 있는 경우 키워드 준비 테스트"""
        # 모의 번역 서비스 설정
        self.mock_translation_service.is_available.return_value = True
        self.mock_translation_service.translate.return_value = "Test"

        helper = MultiLanguageSearchHelper(self.mock_translation_service)
        result = helper.prepare_multilingual_keywords("테스트", ["en"])

        self.assertIn("en", result)
        self.assertIn("Test", result["en"])

    def test_translate_search_results_no_service(self):
        """번역 서비스 없는 경우 결과 번역 테스트"""
        test_results = [
            {"제목": "테스트 제목", "요약": "테스트 요약"},
            {"제목": "또 다른 제목", "요약": "또 다른 요약"}
        ]

        translated = self.helper.translate_search_results(test_results, "en")

        # 서비스가 없으면 원본 반환
        self.assertEqual(len(translated), 2)
        self.assertEqual(translated[0]["제목"], "테스트 제목")


def run_tests():
    """테스트 실행"""
    print("=" * 60)
    print("🧪 다국어 검색 기능 테스트")
    print("=" * 60)

    # 테스트 스위트 생성
    test_classes = [
        TestSupportedLanguage,
        TestTranslationConfig,
        TestTranslationService,
        TestMultiLanguageSearchHelper
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"실행한 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ 모든 테스트가 성공했습니다!")
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")

    return result.wasSuccessful()


def integration_test():
    """통합 테스트 (Google Cloud 자격 증명 필요)"""
    print("\n" + "=" * 60)
    print("🔗 통합 테스트")
    print("=" * 60)

    try:
        # 실제 서비스 초기화
        config = TranslationConfig()
        translation_service = TranslationService(
            credentials_path=config.get_credentials_path(),
            api_key=config.get_api_key()
        )

        if not translation_service.is_available():
            print("⚠️ Google Cloud 자격 증명이 설정되지 않았습니다.")
            print("통합 테스트를 건너뜁니다.")
            return

        print("✅ 번역 서비스 초기화 성공")

        # 언어 감지 테스트
        test_text = "안녕하세요, 반갑습니다."
        detected = translation_service.detect_language(test_text)
        print(f"언어 감지: '{test_text}' -> {detected}")

        # 번역 테스트
        translated = translation_service.translate(test_text, "en")
        if translated:
            print(f"번역 결과: '{test_text}' -> '{translated}'")

        # 다국어 검색 헬퍼 테스트
        helper = MultiLanguageSearchHelper(translation_service)

        multilingual_keywords = helper.prepare_multilingual_keywords("테스트", ["en", "ja"])
        print(f"\n다국어 키워드 준비: {multilingual_keywords}")

        print("\n✅ 통합 테스트 성공!")

    except Exception as e:
        print(f"❌ 통합 테스트 오류: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("🌐 다국어 검색 기능 테스트 스크립트")
    print("=" * 60)

    try:
        # 단위 테스트 실행
        print("\n[1/2] 단위 테스트 실행")
        unit_success = run_tests()

        # 통합 테스트 실행 (선택)
        print("\n[2/2] 통합 테스트 실행")
        integration_test()

        print("\n✨ 모든 테스트 완료!")

        return 0 if unit_success else 1

    except KeyboardInterrupt:
        print("\n\n사용자가 테스트를 중단했습니다.")
        return 1
    except Exception as e:
        print(f"\n❌ 테스트 실행 오류: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())