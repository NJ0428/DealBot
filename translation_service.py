#!/usr/bin/env python3
"""
Google Translation API 연동 서비스
다국어 번역 기능 및 언어 감지 기능 제공
"""

import logging
from typing import List, Dict, Optional, Set
from enum import Enum
from pathlib import Path
import json
from google.cloud import translate_v2 as translate
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)


# ============================================================================
# 지원 언어
# ============================================================================

class SupportedLanguage(Enum):
    """지원하는 언어 코드"""
    KOREAN = "ko"      # 한국어
    ENGLISH = "en"     # 영어
    JAPANESE = "ja"    # 일본어
    CHINESE = "zh"     # 중국어
    SPANISH = "es"     # 스페인어
    FRENCH = "fr"      # 프랑스어
    GERMAN = "de"      # 독일어
    RUSSIAN = "ru"     # 러시아어
    ARABIC = "ar"      # 아랍어
    PORTUGUESE = "pt"  # 포르투갈어
    ITALIAN = "it"     # 이탈리아어
    VIETNAMESE = "vi"  # 베트남어
    THAI = "th"        # 태국어
    HINDI = "hi"       # 힌디어

    @classmethod
    def get_language_name(cls, code: str) -> str:
        """언어 코드로 언어 이름 반환"""
        language_names = {
            "ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese",
            "es": "Spanish", "fr": "French", "de": "German", "ru": "Russian",
            "ar": "Arabic", "pt": "Portuguese", "it": "Italian", "vi": "Vietnamese",
            "th": "Thai", "hi": "Hindi"
        }
        return language_names.get(code, code)

    @classmethod
    def get_all_languages(cls) -> Dict[str, str]:
        """모든 지원 언어 반환 {코드: 이름}"""
        return {lang.value: cls.get_language_name(lang.value) for lang in cls}


# ============================================================================
# 번역 서비스 클래스
# ============================================================================

class TranslationService:
    """Google Translation API 서비스 클래스"""

    def __init__(self, credentials_path: Optional[str] = None,
                 api_key: Optional[str] = None):
        """
        번역 서비스 초기화

        Args:
            credentials_path: Google Cloud 인증 파일 경로
            api_key: Google Cloud API 키 (대체 인증 방식)
        """
        self.translate_client = None
        self.available = False
        self.credentials_path = credentials_path
        self.api_key = api_key

        # 클라이언트 초기화 시도
        self._initialize_client()

    def _initialize_client(self) -> bool:
        """
        Translation API 클라이언트 초기화

        Returns:
            성공 여부
        """
        try:
            # 1. API 키로 초기화 시도
            if self.api_key:
                self.translate_client = translate.Client(api_key=self.api_key)
                self.available = True
                logger.info("번역 서비스 초기화 성공 (API 키 인증)")
                return True

            # 2. 자격 증명 파일로 초기화 시도
            elif self.credentials_path:
                import os
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
                self.translate_client = translate.Client()
                self.available = True
                logger.info(f"번역 서비스 초기화 성공 (자격 증명 파일: {self.credentials_path})")
                return True

            # 3. 기본 자격 증명으로 초기화 시도
            else:
                self.translate_client = translate.Client()
                self.available = True
                logger.info("번역 서비스 초기화 성공 (기본 자격 증명)")
                return True

        except DefaultCredentialsError:
            logger.warning("Google Cloud 자격 증명을 찾을 수 없습니다. 번역 기능이 비활성화됩니다.")
            return False
        except Exception as e:
            logger.error(f"번역 서비스 초기화 오류: {e}")
            return False

    def is_available(self) -> bool:
        """
        번역 서비스 사용 가능 여부 확인

        Returns:
            사용 가능 여부
        """
        return self.available

    def detect_language(self, text: str) -> Optional[str]:
        """
        텍스트 언어 감지

        Args:
            text: 언어를 감지할 텍스트

        Returns:
            언어 코드 (예: 'ko', 'en') 또는 None
        """
        if not self.available:
            logger.warning("번역 서비스가 사용 가능하지 않습니다.")
            return None

        try:
            result = self.translate_client.detect_language(text)
            language_code = result.get('language', 'unknown')
            confidence = result.get('confidence', 0.0)

            logger.debug(f"언어 감지: {language_code} (신뢰도: {confidence:.2%})")
            return language_code

        except Exception as e:
            logger.error(f"언어 감지 오류: {e}")
            return None

    def translate(self, text: str, target_language: str,
                  source_language: Optional[str] = None) -> Optional[str]:
        """
        텍스트 번역

        Args:
            text: 번역할 텍스트
            target_language: 목표 언어 코드 (예: 'en', 'ko')
            source_language: 원본 언어 코드 (None인 경우 자동 감지)

        Returns:
            번역된 텍스트 또는 None
        """
        if not self.available:
            logger.warning("번역 서비스가 사용 가능하지 않습니다.")
            return None

        if not text or not target_language:
            logger.warning("번역에 필요한 매개변수가 부족합니다.")
            return None

        try:
            result = self.translate_client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )

            translated_text = result.get('translatedText', '')
            detected_language = result.get('detectedSourceLanguage', source_language)

            logger.debug(f"번역 완료: {detected_language} -> {target_language}")
            return translated_text

        except Exception as e:
            logger.error(f"번역 오류: {e}")
            return None

    def translate_batch(self, texts: List[str], target_language: str,
                       source_language: Optional[str] = None) -> List[Optional[str]]:
        """
        여러 텍스트 일괄 번역

        Args:
            texts: 번역할 텍스트 리스트
            target_language: 목표 언어 코드
            source_language: 원본 언어 코드

        Returns:
            번역된 텍스트 리스트 (실패 시 None 포함)
        """
        if not self.available:
            logger.warning("번역 서비스가 사용 가능하지 않습니다.")
            return [None] * len(texts)

        if not texts:
            return []

        results = []
        for i, text in enumerate(texts):
            logger.debug(f"번역 중 ({i+1}/{len(texts)}): {text[:50]}...")
            translated = self.translate(text, target_language, source_language)
            results.append(translated)

        return results

    def translate_dict_values(self, data_dict: Dict, target_language: str,
                             source_language: Optional[str] = None,
                             keys_to_translate: Optional[Set[str]] = None) -> Dict:
        """
        딕셔너리의 특정 키 값들 번역

        Args:
            data_dict: 번역할 딕셔너리
            target_language: 목표 언어 코드
            source_language: 원본 언어 코드
            keys_to_translate: 번역할 키 집합 (None인 경우 모든 값 번역)

        Returns:
            번역된 딕셔너리
        """
        if not data_dict:
            return {}

        translated_dict = {}

        for key, value in data_dict.items():
            # 번역 대상 키인지 확인
            if keys_to_translate is None or key in keys_to_translate:
                # 문자열 값만 번역
                if isinstance(value, str) and value.strip():
                    translated_value = self.translate(
                        value, target_language, source_language
                    )
                    translated_dict[key] = translated_value if translated_value else value
                else:
                    translated_dict[key] = value
            else:
                translated_dict[key] = value

        return translated_dict

    def translate_keywords(self, keywords: List[str],
                          target_languages: List[str]) -> Dict[str, Dict[str, str]]:
        """
        키워드들을 여러 언어로 번역

        Args:
            keywords: 원본 키워드 리스트
            target_languages: 번역할 언어 코드 리스트

        Returns:
            {원본키워드: {언어코드: 번역된키워드}} 딕셔너리
        """
        if not keywords or not target_languages:
            return {}

        result = {}

        for keyword in keywords:
            result[keyword] = {}
            for lang in target_languages:
                translated = self.translate(keyword, lang)
                if translated:
                    result[keyword][lang] = translated

        logger.info(f"키워드 번역 완료: {len(keywords)}개 키워드를 {len(target_languages)}개 언어로")
        return result


# ============================================================================
# 다국어 검색 헬퍼
# ============================================================================

class MultiLanguageSearchHelper:
    """다국어 검색 헬퍼 클래스"""

    def __init__(self, translation_service: TranslationService):
        """
        다국어 검색 헬퍼 초기화

        Args:
            translation_service: 번역 서비스 인스턴스
        """
        self.translation_service = translation_service
        self.search_history: List[Dict] = []

    def prepare_multilingual_keywords(self, base_keyword: str,
                                      languages: List[str]) -> Dict[str, List[str]]:
        """
        기본 키워드를 여러 언어로 번역하여 검색 준비

        Args:
            base_keyword: 기본 키워드
            languages: 번역할 언어 코드 리스트

        Returns:
            {언어코드: [번역된키워드, 기본키워드]} 딕셔너리
        """
        if not self.translation_service.is_available():
            # 번역 서비스가 없으면 원본 키워드만 사용
            logger.warning("번역 서비스를 사용할 수 없어 원본 키워드만 사용합니다.")
            return {"ko": [base_keyword]}

        result = {}
        result["ko"] = [base_keyword]  # 원본 언어 포함

        for lang in languages:
            if lang == "ko":  # 한국어는 이미 포함
                continue

            translated = self.translation_service.translate(base_keyword, lang)
            if translated:
                if lang not in result:
                    result[lang] = []
                result[lang].append(translated)
                result[lang].append(base_keyword)  # 원본 키워드도 포함

        # 기록 저장
        self.search_history.append({
            'keyword': base_keyword,
            'languages': languages,
            'result': result,
            'timestamp': datetime.now().isoformat()
        })

        logger.info(f"다국어 키워드 준비 완료: {len(result)}개 언어")
        return result

    def translate_search_results(self, results: List[Dict],
                                target_language: str = "en",
                                keys_to_translate: Optional[Set[str]] = None) -> List[Dict]:
        """
        검색 결과 번역

        Args:
            results: 검색 결과 딕셔너리 리스트
            target_language: 목표 언어 코드
            keys_to_translate: 번역할 키 집합 (예: {'제목', '요약'})

        Returns:
            번역된 검색 결과 리스트
        """
        if not results:
            return []

        if not self.translation_service.is_available():
            logger.warning("번역 서비스를 사용할 수 없어 원본 결과를 반환합니다.")
            return results

        # 번역할 키가 지정되지 않으면 기본 키 사용
        if keys_to_translate is None:
            keys_to_translate = {'제목', '요약', 'title', 'summary', 'description'}

        translated_results = []

        for result in results:
            translated_result = self.translation_service.translate_dict_values(
                result, target_language, keys_to_translate=keys_to_translate
            )
            translated_results.append(translated_result)

        logger.info(f"검색 결과 번역 완료: {len(results)}개 항목")
        return translated_results

    def get_search_history(self) -> List[Dict]:
        """
        검색 기록 반환

        Returns:
            검색 기록 리스트
        """
        return self.search_history


# ============================================================================
# 설정 관리
# ============================================================================

class TranslationConfig:
    """번역 서비스 설정 클래스"""

    def __init__(self, config_file: str = "translation_config.json"):
        """
        설정 로드

        Args:
            config_file: 설정 파일 경로
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"번역 설정 로드 완료: {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"설정 파일 로드 오류: {e}")
                return self._get_default_config()
        else:
            # 기본 설정 파일 생성
            default_config = self._get_default_config()
            self._save_config(default_config)
            return default_config

    def _get_default_config(self) -> Dict:
        """기본 설정 반환"""
        return {
            "credentials_path": "",
            "api_key": "",
            "default_target_language": "en",
            "supported_languages": ["ko", "en", "ja", "zh", "es"],
            "auto_detect_language": True,
            "translate_search_results": True,
            "translate_keywords": True,
            "cache_translations": True,
            "max_cache_size": 1000
        }

    def _save_config(self, config: Dict) -> None:
        """설정 파일 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"설정 파일 저장 완료: {self.config_file}")
        except Exception as e:
            logger.error(f"설정 파일 저장 오류: {e}")

    def get_credentials_path(self) -> Optional[str]:
        """자격 증명 파일 경로 반환"""
        return self.config.get("credentials_path") or None

    def get_api_key(self) -> Optional[str]:
        """API 키 반환"""
        return self.config.get("api_key") or None

    def get_default_target_language(self) -> str:
        """기본 목표 언어 반환"""
        return self.config.get("default_target_language", "en")

    def get_supported_languages(self) -> List[str]:
        """지원 언어 리스트 반환"""
        return self.config.get("supported_languages", ["ko", "en", "ja", "zh", "es"])

    def should_auto_detect_language(self) -> bool:
        """언어 자동 감지 여부"""
        return self.config.get("auto_detect_language", True)

    def should_translate_search_results(self) -> bool:
        """검색 결과 자동 번역 여부"""
        return self.config.get("translate_search_results", True)

    def should_translate_keywords(self) -> bool:
        """키워드 자동 번역 여부"""
        return self.config.get("translate_keywords", True)

    def should_cache_translations(self) -> bool:
        """번역 캐싱 여부"""
        return self.config.get("cache_translations", True)


# ============================================================================
# 메인 함수
# ============================================================================

from datetime import datetime

def main():
    """메인 함수 - 테스트용"""

    print("=" * 60)
    print("🌐 Google Translation API 서비스 테스트")
    print("=" * 60)

    # 설정 로드
    config = TranslationConfig()

    print("\n[설정]")
    print(f"기본 목표 언어: {config.get_default_target_language()}")
    print(f"지원 언어: {', '.join(config.get_supported_languages())}")

    # 번역 서비스 초기화
    print("\n[번역 서비스 초기화]")
    translation_service = TranslationService(
        credentials_path=config.get_credentials_path(),
        api_key=config.get_api_key()
    )

    if not translation_service.is_available():
        print("⚠️ 번역 서비스를 사용할 수 없습니다.")
        print("Google Cloud 자격 증명을 설정해주세요:")
        print("1. Google Cloud Console에서 프로젝트 생성")
        print("2. Translation API 활성화")
        print("3. 서비스 계정 키 다운로드")
        print("4. translation_config.json 파일에 경로 설정")
        return

    print("✅ 번역 서비스가 사용 가능합니다.")

    # 테스트 1: 언어 감지
    print("\n[테스트 1: 언어 감지]")
    test_texts = [
        "안녕하세요, 반갑습니다.",
        "Hello, nice to meet you.",
        "こんにちは、はじめまして。",
        "你好，很高兴见到你。"
    ]

    for text in test_texts:
        detected = translation_service.detect_language(text)
        print(f"  '{text}' -> {detected}")

    # 테스트 2: 텍스트 번역
    print("\n[테스트 2: 텍스트 번역]")
    source_text = "안녕하세요, 오늘 날씨가 좋습니다."
    target_lang = input(f"번역할 언어 코드를 입력하세요 (예: en, ja, zh, es, fr): ").strip()

    if target_lang:
        translated = translation_service.translate(source_text, target_lang)
        if translated:
            print(f"  원본: {source_text}")
            print(f"  번역: {translated}")
        else:
            print("  ❌ 번역 실패")

    # 테스트 3: 다국어 키워드 준비
    print("\n[테스트 3: 다국어 키워드 준비]")
    keyword = input("기본 키워드를 입력하세요: ").strip()

    if keyword:
        helper = MultiLanguageSearchHelper(translation_service)
        languages = config.get_supported_languages()

        multilingual_keywords = helper.prepare_multilingual_keywords(keyword, languages)
        print(f"\n다국어 키워드 준비 결과:")
        for lang, keywords in multilingual_keywords.items():
            print(f"  {lang}: {', '.join(keywords)}")

    # 테스트 4: 다국어 지원 정보
    print("\n[다국어 지원 정보]")
    all_languages = SupportedLanguage.get_all_languages()
    print(f"지원하는 언어 ({len(all_languages)}개):")
    for code, name in all_languages.items():
        print(f"  {code}: {name}")

    print("\n✨ 테스트 완료!")


if __name__ == "__main__":
    main()