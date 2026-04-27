#!/usr/bin/env python3
"""
RSS 피드 자동 생성 및 스케줄링 사용 예시
"""

import logging
from pathlib import Path
from web_crawler import WebCrawler
from rss_feed_generator import (
    RSSFeedGenerator,
    RSSFeedConfig,
    MultiFeedGenerator,
    WebCrawlerToRSSConverter,
    create_feed_from_crawler_data
)
from feed_scheduler import (
    RSSFeedScheduler,
    ScheduleConfig,
    FeedManager
)


# ============================================================================
# 로깅 설정
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# 예시 1: 기본 RSS 피드 생성
# ============================================================================

def example_1_basic_rss_feed():
    """기본 RSS 피드 생성 예시"""
    print("\n" + "="*60)
    print("예시 1: 기본 RSS 피드 생성")
    print("="*60)

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)

    # 데이터 크롤링
    keyword = "인공지능"
    print(f"\n1. '{keyword}' 키워드로 크롤링 시작...")
    data = crawler.search_google_news(keyword, max_results=10)
    print(f"   → {len(data)}개 아이템 수집 완료")

    # RSS 피드 생성 (유틸리티 함수 사용)
    print("\n2. RSS 피드 생성 중...")
    feed_path = create_feed_from_crawler_data(keyword, data)
    print(f"   → RSS 피드 저장 완료: {feed_path}")

    # 결과 확인
    print("\n3. 생성된 RSS 피드 미리보기:")
    with open(feed_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:15], 1):
            print(f"   {i:2d}: {line.rstrip()}")

    crawler.close()
    print("\n✅ 예시 1 완료!")


# ============================================================================
# 예시 2: 커스텀 RSS 피드 설정
# ============================================================================

def example_2_custom_rss_config():
    """커스텀 RSS 피드 설정 예시"""
    print("\n" + "="*60)
    print("예시 2: 커스텀 RSS 피드 설정")
    print("="*60)

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)

    # 데이터 크롤링
    keyword = "블록체인"
    print(f"\n1. '{keyword}' 키워드로 크롤링 시작...")
    data = crawler.search_google_news(keyword, max_results=5)
    print(f"   → {len(data)}개 아이템 수집 완료")

    # 커스텀 RSS 피드 설정
    print("\n2. 커스텀 RSS 피드 설정 생성 중...")
    config = RSSFeedConfig(
        title="내 블로그 - 블록체인 뉴스",
        description="최신 블록체인 기술 뉴스와 정보를 제공합니다",
        link="https://myblog.com/blockchain",
        language="ko",
        managing_editor="editor@myblog.com",
        web_master="webmaster@myblog.com",
        category="기술/블록체인"
    )
    print(f"   → 제목: {config.title}")
    print(f"   → 설명: {config.description}")

    # RSS 아이템 변환
    print("\n3. RSS 아이템 변환 중...")
    converter = WebCrawlerToRSSConverter()
    rss_items = converter.convert_to_rss_items(
        data,
        use_summary=True,
        max_description_length=300
    )
    print(f"   → {len(rss_items)}개 RSS 아이템 변환 완료")

    # RSS 피드 생성
    print("\n4. RSS 피드 생성 중...")
    generator = RSSFeedGenerator(config)
    output_path = "rss_feeds/blockchain_custom.xml"
    generator.save_feed(rss_items, output_path)
    print(f"   → RSS 피드 저장 완료: {output_path}")

    crawler.close()
    print("\n✅ 예시 2 완료!")


# ============================================================================
# 예시 3: 멀티피드 생성 (여러 키워드)
# ============================================================================

def example_3_multi_feed():
    """멀티피드 생성 예시"""
    print("\n" + "="*60)
    print("예시 3: 멀티피드 생성")
    print("="*60)

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)

    # 여러 키워드 크롤링
    keywords = ["AI", "메타버스", "클라우드"]
    print(f"\n1. {len(keywords)}개 키워드로 크롤링 시작...")

    data_by_keyword = {}
    for keyword in keywords:
        print(f"   → '{keyword}' 크롤링 중...")
        data = crawler.search_google_news(keyword, max_results=5)
        data_by_keyword[keyword] = data
        print(f"      {len(data)}개 아이템 수집 완료")

    # 멀티피드 생성기 초기화
    print("\n2. 멀티피드 생성기 초기화 중...")
    base_config = RSSFeedConfig(
        title="테크 뉴스 허브",
        description="최신 기술 뉴스를 다양한 주제로 제공합니다",
        link="https://technews.com"
    )
    multi_gen = MultiFeedGenerator(base_config)

    # 개별 피드 생성
    print("\n3. 개별 피드 생성 중...")
    feed_paths = multi_gen.generate_feeds(
        data_by_keyword,
        output_dir="rss_feeds/tech"
    )
    for keyword, path in feed_paths.items():
        print(f"   → {keyword}: {path}")

    # 통합 피드 생성
    print("\n4. 통합 피드 생성 중...")
    combined_path = "rss_feeds/tech/combined.xml"
    multi_gen.generate_combined_feed(
        data_by_keyword,
        combined_path
    )
    print(f"   → 통합 피드: {combined_path}")

    crawler.close()
    print("\n✅ 예시 3 완료!")


# ============================================================================
# 예시 4: 간격 기반 스케줄링
# ============================================================================

def example_4_interval_schedule():
    """간격 기반 스케줄링 예시"""
    print("\n" + "="*60)
    print("예시 4: 간격 기반 스케줄링 (매 1분)")
    print("="*60)

    # FeedManager 사용
    manager = FeedManager()

    # 1분마다 실행되는 스케줄러 생성
    print("\n1. 스케줄러 생성 중...")
    scheduler = manager.create_scheduler(
        keywords=["AI"],
        schedule_type='interval',
        interval_minutes=1,  # 1분마다
        use_background=False  # BlockingScheduler 사용
    )
    print("   → 스케줄러 생성 완료")

    # 스케줄러 상태 확인
    print("\n2. 스케줄러 상태:")
    status = scheduler.get_status()
    print(f"   → 실행 중: {status['scheduler_running']}")
    print(f"   → 총 키워드: {status['total_keywords']}")
    print(f"   → 등록된 작업: {status['jobs_count']}개")

    # 설정 저장
    print("\n3. 설정 저장 중...")
    scheduler.save_config("scheduler_config_example.json")
    print("   → 설정 저장 완료: scheduler_config_example.json")

    print("\n4. 스케줄러 시작 (Ctrl+C로 종료)...")
    print("   → 'AI' 키워드를 매 1분마다 크롤링합니다")

    # 스케줄러 시작 (실제로는 주석 처리)
    # scheduler.start(run_immediately=True)

    print("\n⚠️  실제 실행을 위해서는 아래 주석을 해제하세요:")
    print("   scheduler.start(run_immediately=True)")

    # 정리
    scheduler.shutdown()
    print("\n✅ 예시 4 완료!")


# ============================================================================
# 예시 5: 크론 기반 스케줄링
# ============================================================================

def example_5_cron_schedule():
    """크론 기반 스케줄링 예시"""
    print("\n" + "="*60)
    print("예시 5: 크론 기반 스케줄링 (매일 특정 시간)")
    print("="*60)

    # 스케줄러 생성
    print("\n1. 스케줄러 생성 중...")
    config = ScheduleConfig(
        schedule_type='cron',
        cron_hour=9,  # 매일 9시
        cron_minute=0,
        rss_output_dir="rss_feeds/scheduled"
    )

    scheduler = RSSFeedScheduler(default_config=config)

    # 여러 키워드 추가
    keywords = ["인공지능", "블록체인", "빅데이터"]
    print(f"\n2. {len(keywords)}개 키워드 추가 중...")
    for keyword in keywords:
        scheduler.add_keyword(keyword)
        print(f"   → 추가됨: {keyword}")

    # 스케줄링 등록
    print("\n3. 스케줄링 등록 중...")
    scheduler.schedule_all()
    print("   → 모든 키워드에 대한 스케줄링 완료")

    # 상태 확인
    print("\n4. 스케줄러 상태:")
    status = scheduler.get_status()
    print(f"   → 실행 중: {status['scheduler_running']}")
    print(f"   → 총 키워드: {status['total_keywords']}")

    # 스케줄러 시작 (실제로는 주석 처리)
    print("\n5. 스케줄러 시작 예정:")
    print("   → 매일 9시 0분에 크롤링 실행")
    print("   → 키워드: " + ", ".join(keywords))

    # 정리
    scheduler.shutdown()
    print("\n⚠️  실제 실행을 위해서는 아래 주석을 해제하세요:")
    print("   scheduler.start(run_immediately=True)")

    print("\n✅ 예시 5 완료!")


# ============================================================================
# 예시 6: 커스텀 혼합 스케줄링
# ============================================================================

def example_6_custom_mixed_schedule():
    """커스텀 혼합 스케줄링 예시"""
    print("\n" + "="*60)
    print("예시 6: 커스텀 혼합 스�테일링")
    print("="*60)

    # 스케줄러 생성
    print("\n1. 스케줄러 생성 중...")
    scheduler = RSSFeedScheduler()

    # 각 키워드별로 다른 스케줄 설정
    print("\n2. 키워드별 스케줄 설정 중...")

    # AI: 1시간마다
    print("   → AI: 1시간마다 (interval)")
    scheduler.add_keyword("AI")

    # 블록체인: 2시간마다
    print("   → 블록체인: 2시간마다 (interval)")
    blockchain_config = ScheduleConfig(
        schedule_type='interval',
        interval_hours=2
    )
    scheduler.add_keyword("블록체인", blockchain_config)

    # 메타버스: 매일 10시
    print("   → 메타버스: 매일 10시 (cron)")
    metaverse_config = ScheduleConfig(
        schedule_type='cron',
        cron_hour=10,
        cron_minute=0
    )
    scheduler.add_keyword("메타버스", metaverse_config)

    # 스케줄링 등록
    print("\n3. 스케줄링 등록 중...")
    scheduler.schedule_all()

    # 상태 확인
    print("\n4. 스케줄러 상태:")
    status = scheduler.get_status()
    for kw_status in status['keywords']:
        print(f"   → {kw_status['keyword']}: ")
        print(f"      활성화: {kw_status['enabled']}")
        print(f"      총 크롤링: {kw_status['total_crawled']}회")
        print(f"      에러 수: {kw_status['error_count']}회")

    # 설정 저장
    print("\n5. 설정 저장 중...")
    scheduler.save_config("mixed_schedule_config.json")
    print("   → 설정 저장 완료: mixed_schedule_config.json")

    # 정리
    scheduler.shutdown()

    print("\n⚠️  실제 실행을 위해서는 아래 주석을 해제하세요:")
    print("   scheduler.start(run_immediately=True)")

    print("\n✅ 예시 6 완료!")


# ============================================================================
# 예시 7: 설정 로드 및 실행
# ============================================================================

def example_7_load_and_run():
    """설정 로드 및 실행 예시"""
    print("\n" + "="*60)
    print("예시 7: 설정 로드 및 실행")
    print("="*60)

    # 먼저 설정 파일이 있는지 확인
    config_file = "scheduler_config_example.json"

    if Path(config_file).exists():
        print(f"\n1. 설정 파일 로드 중: {config_file}")
        scheduler = RSSFeedScheduler.load_config(config_file)
        print("   → 설정 로드 완료")

        # 상태 확인
        print("\n2. 스케줄러 상태:")
        status = scheduler.get_status()
        print(f"   → 총 키워드: {status['total_keywords']}")

        for kw_status in status['keywords']:
            print(f"   → {kw_status['keyword']}: ")
            print(f"      마지막 크롤링: {kw_status['last_crawled']}")
            print(f"      총 크롤링 횟수: {kw_status['total_crawled']}회")

        # 정리
        scheduler.shutdown()
        print("\n✅ 예시 7 완료!")
    else:
        print(f"\n⚠️  설정 파일을 찾을 수 없음: {config_file}")
        print("   → 먼저 예시 4를 실행하여 설정 파일을 생성하세요")


# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("RSS 피드 자동 생성 및 스케줄링 사용 예시")
    print("="*60)

    examples = [
        ("1", "기본 RSS 피드 생성", example_1_basic_rss_feed),
        ("2", "커스텀 RSS 피드 설정", example_2_custom_rss_config),
        ("3", "멀티피드 생성", example_3_multi_feed),
        ("4", "간격 기반 스케줄링", example_4_interval_schedule),
        ("5", "크론 기반 스케줄링", example_5_cron_schedule),
        ("6", "커스텀 혼합 스케줄링", example_6_custom_mixed_schedule),
        ("7", "설정 로드 및 실행", example_7_load_and_run),
        ("0", "모든 예시 실행", None),
    ]

    print("\n사용 가능한 예시:")
    for key, desc, _ in examples:
        print(f"  {key}. {desc}")

    # 사용자 입력 (실제 실행 시에는 주석 처리)
    # choice = input("\n실행할 예시 번호를 입력하세요 (0-7): ").strip()

    # 테스트를 위해 예시 1 자동 실행
    choice = "1"

    if choice == "0":
        # 모든 예시 실행
        for key, desc, func in examples[:-1]:
            if func:
                try:
                    func()
                except Exception as e:
                    print(f"\n❌ 예시 {key} 실행 중 오류: {e}")
                    import traceback
                    traceback.print_exc()
    else:
        # 선택된 예시 실행
        for key, desc, func in examples:
            if key == choice:
                if func:
                    try:
                        func()
                    except Exception as e:
                        print(f"\n❌ 실행 중 오류: {e}")
                        import traceback
                        traceback.print_exc()
                break
        else:
            print(f"\n⚠️  잘못된 선택: {choice}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자 중단")
    except Exception as e:
        print(f"\n\n❌ 치명적 오류: {e}")
        import traceback
        traceback.print_exc()
