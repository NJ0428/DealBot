#!/usr/bin/env python3
"""
자동 번역 기능 테스트 스크립트
수집된 데이터의 자동 번역 기능을 테스트합니다.
"""

import sys
from pathlib import Path

# 상위 디렉토리 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from web_crawler import WebCrawler, Config, SupportedLanguage
import logging

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_auto_translation_basic():
    """기본 자동 번역 테스트"""
    print("=" * 60)
    print("🧪 테스트 1: 기본 자동 번역 기능")
    print("=" * 60)

    # 크롤러 초기화 (자동 번역 활성화)
    crawler = WebCrawler(
        use_cache=True,
        enable_translation=True,
        auto_translate_collected=True
    )

    # 번역 서비스 상태 확인
    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        print("Google Cloud 자격 증명을 설정해주세요.")
        crawler.close()
        return False

    print(f"✅ 번역 서비스 사용 가능")
    print(f"📋 자동 번역 상태: {crawler.get_auto_translation_status()}")

    # 키워드 검색 (자동 번역 적용)
    keyword = "인공지능"
    print(f"\n🔍 '{keyword}' 검색 및 자동 번역 시작...")

    try:
        results = crawler.search_google_news(keyword, max_results=3)

        if results:
            print(f"✅ 검색 완료: {len(results)}개 항목")

            # 번역 결과 확인
            print(f"\n📋 번역 결과 샘플:")
            for i, item in enumerate(results, 1):
                print(f"\n[{i}] 원본 제목: {item.get('제목', 'N/A')}")
                if '제목_translated' in item:
                    print(f"    번역 제목: {item['제목_translated']}")
                    print(f"    번역 언어: {item.get('제목_lang', 'N/A')}")

                print(f"    원본 요약: {item.get('요약', 'N/A')[:50]}...")
                if '요약_translated' in item:
                    print(f"    번역 요약: {item['요약_translated'][:50]}...")

            crawler.close()
            return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        crawler.close()
        return False

    crawler.close()
    return False


def test_auto_translation_custom_fields():
    """사용자 정의 필드 자동 번역 테스트"""
    print("\n" + "=" * 60)
    print("🧪 테스트 2: 사용자 정의 필드 자동 번역")
    print("=" * 60)

    # 크롤러 초기화
    crawler = WebCrawler(
        use_cache=True,
        enable_translation=True,
        auto_translate_collected=False
    )

    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        crawler.close()
        return False

    # 사용자 정의 필드 설정
    custom_fields = {'제목'}  # 제목만 번역
    crawler.enable_auto_translation(True, custom_fields)

    print(f"✅ 사용자 정의 번역 필드 설정: {custom_fields}")
    print(f"📋 자동 번역 상태: {crawler.get_auto_translation_status()}")

    # 검색
    keyword = "기후변화"
    print(f"\n🔍 '{keyword}' 검색 (제목만 번역)...")

    try:
        results = crawler.search_google_news(keyword, max_results=2)

        if results:
            print(f"✅ 검색 완료: {len(results)}개 항목")

            # 번역 결과 확인
            print(f"\n📋 번역 결과 (제목만 번역):")
            for i, item in enumerate(results, 1):
                print(f"\n[{i}] 원본 제목: {item.get('제목', 'N/A')}")
                if '제목_translated' in item:
                    print(f"    ✅ 번역 제목: {item['제목_translated']}")
                else:
                    print(f"    ❌ 번역 안됨")

                print(f"    요약: {item.get('요약', 'N/A')[:50]}...")
                if '요약_translated' in item:
                    print(f"    ⚠️  번역 요약: {item['요약_translated'][:50]}...")
                else:
                    print(f"    ✅ 번역 안됨 (의도적)")

        crawler.close()
        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        crawler.close()
        return False


def test_manual_translation():
    """수동 번역 테스트"""
    print("\n" + "=" * 60)
    print("🧪 테스트 3: 수동 번역 기능")
    print("=" * 60)

    # 크롤러 초기화
    crawler = WebCrawler(
        use_cache=True,
        enable_translation=True,
        auto_translate_collected=False
    )

    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        crawler.close()
        return False

    # 먼저 검색 (자동 번역 없이)
    keyword = "블록체인"
    print(f"\n🔍 '{keyword}' 검색 (자동 번역 없이)...")

    try:
        results = crawler.search_google_news(keyword, max_results=2)

        if not results:
            print("❌ 검색 결과 없음")
            crawler.close()
            return False

        print(f"✅ 검색 완료: {len(results)}개 항목")

        # 수동으로 번역
        print(f"\n🔄 수동 번역 시작...")
        target_language = crawler.translation_config.get_default_target_language() if crawler.translation_config else "en"
        translated_results = crawler.auto_translate_batch(results, target_language)

        print(f"✅ 수동 번역 완료")

        # 번역 결과 확인
        print(f"\n📋 수동 번역 결과:")
        for i, item in enumerate(translated_results, 1):
            print(f"\n[{i}] 원본 제목: {item.get('제목', 'N/A')}")
            if '제목_translated' in item:
                print(f"    ✅ 번역 제목: {item['제목_translated']}")

        crawler.close()
        return True

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        crawler.close()
        return False


def test_status_management():
    """상태 관리 테스트"""
    print("\n" + "=" * 60)
    print("🧪 테스트 4: 자동 번역 상태 관리")
    print("=" * 60)

    # 크롤러 초기화
    crawler = WebCrawler(
        use_cache=True,
        enable_translation=True
    )

    if not crawler.is_translation_available():
        print("❌ 번역 서비스를 사용할 수 없습니다.")
        crawler.close()
        return False

    # 초기 상태 확인
    initial_status = crawler.get_auto_translation_status()
    print(f"📋 초기 상태: {initial_status}")

    # 활성화
    print(f"\n🔄 자동 번역 활성화...")
    crawler.enable_auto_translation(True)
    active_status = crawler.get_auto_translation_status()
    print(f"📋 활성화 상태: {active_status}")

    # 필드 변경
    print(f"\n🔄 번역 필드 변경...")
    new_fields = {'제목', '요약', '설명'}
    crawler.enable_auto_translation(True, new_fields)
    updated_status = crawler.get_auto_translation_status()
    print(f"📋 업데이트 상태: {updated_status}")

    # 비활성화
    print(f"\n🔄 자동 번역 비활성화...")
    crawler.enable_auto_translation(False)
    disabled_status = crawler.get_auto_translation_status()
    print(f"📋 비활성화 상태: {disabled_status}")

    crawler.close()
    return True


def main():
    """메인 테스트 함수"""
    print("🌐 수집 데이터 자동 번역 기능 테스트")
    print("=" * 60)

    tests = [
        ("기본 자동 번역 기능", test_auto_translation_basic),
        ("사용자 정의 필드 자동 번역", test_auto_translation_custom_fields),
        ("수동 번역 기능", test_manual_translation),
        ("상태 관리", test_status_management)
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
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)

    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    total_tests = len(tests)
    passed_tests = sum(1 for result in results.values() if "✅" in result)

    print(f"\n총계: {passed_tests}/{total_tests} 테스트 통과")

    if passed_tests == total_tests:
        print("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())