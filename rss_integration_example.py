#!/usr/bin/env python3
"""
RSS 피드 시스템 통합 예시
필터링, 구독, 알림 시스템을 통합하여 사용하는 방법을 보여줍니다.
"""

import logging
import time
from datetime import datetime
from pathlib import Path

# 프로젝트 모듈 임포트
from feed_filter import FeedFilter, FeedItem
from feed_subscriber import FeedSubscriber, SubscriptionConfig, FeedMonitor
from change_notifier import ChangeNotifier, NotificationConfig, NotificationChannel


# ============================================================================
# 로깅 설정
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# 예시 1: 기본 필터링 시스템
# ============================================================================

def example_1_basic_filtering():
    """예시 1: 기본 필터링 시스템"""
    print("\n" + "="*80)
    print("예시 1: 기본 필터링 시스템")
    print("="*80)

    # 필터 생성
    feed_filter = FeedFilter(db_path="integration_filter.db")

    # 테스트 데이터 생성
    test_data = [
        {
            'title': 'AI 기술의 혁신',
            'link': 'https://example.com/ai1',
            'description': '인공지능 기술이 새로운 전기를 맞이하고 있습니다.',
            'date': '2026-04-29 10:00:00',
            'author': '테크미디어',
            'category': 'AI'
        },
        {
            'title': '블록체인의 미래',
            'link': 'https://example.com/blockchain1',
            'description': '블록체인 기술이 금융 산업을 변화시키고 있습니다.',
            'date': '2026-04-29 09:00:00',
            'author': '코인뉴스',
            'category': '블록체인'
        }
    ]

    # 첫 번째 필터링 (모두 새로운 아이템)
    print("\n1. 첫 번째 필터링 (모두 새로운 아이템):")
    new_items, stats = feed_filter.filter_new_items_from_dict(test_data, "AI")
    print(f"   새로운 아이템: {len(new_items)}개")
    for item in new_items:
        print(f"   - {item.title}")

    # 두 번째 필터링 (모두 중복)
    print("\n2. 두 번째 필터링 (모두 중복):")
    new_items, stats = feed_filter.filter_new_items_from_dict(test_data, "AI")
    print(f"   새로운 아이템: {len(new_items)}개")

    # 새로운 데이터 추가
    new_data = [{
        'title': '메타버스 플랫폼 경쟁',
        'link': 'https://example.com/metaverse1',
        'description': '메타버스 플랫폼 간 경쟁이 치열해지고 있습니다.',
        'date': '2026-04-29 11:00:00',
        'author': 'VR타임즈',
        'category': '메타버스'
    }]

    print("\n3. 세 번째 필터링 (하나 새로운 아이템):")
    new_items, stats = feed_filter.filter_new_items_from_dict(new_data, "AI")
    print(f"   새로운 아이템: {len(new_items)}개")
    for item in new_items:
        print(f"   - {item.title}")

    # 통계 확인
    print("\n4. 필터링 통계:")
    print(f"   전체 처리: {stats.total_processed}개")
    print(f"   새로운 아이템: {stats.new_items}개")
    print(f"   중복 아이템: {stats.duplicate_items}개")

    print("\n✅ 예시 1 완료!")


# ============================================================================
# 예시 2: 구독 시스템
# ============================================================================

def example_2_subscription_system():
    """예시 2: 구독 시스템"""
    print("\n" + "="*80)
    print("예시 2: 구독 시스템")
    print("="*80)

    # 필터 생성
    feed_filter = FeedFilter(db_path="integration_subscription.db")

    # 구독자 생성
    subscriber = FeedSubscriber(feed_filter=feed_filter)

    # 테스트용 RSS 피드 구독
    test_feeds = [
        SubscriptionConfig(
            url="https://news.google.com/rss/search?q=AI&hl=ko&gl=KR&ceid=KR:ko",
            name="Google News AI",
            keyword="AI",
            update_interval=300,
            max_items=20
        ),
        SubscriptionConfig(
            url="https://news.google.com/rss/search?q=블록체인&hl=ko&gl=KR&ceid=KR:ko",
            name="Google News Blockchain",
            keyword="블록체인",
            update_interval=300,
            max_items=20
        )
    ]

    # 구독 추가
    print("\n1. 구독 추가:")
    for feed_config in test_feeds:
        subscriber.add_subscription(feed_config)
        print(f"   - {feed_config.name}: {feed_config.url}")

    # 콜백 함수 설정
    def new_items_callback(new_items, subscription):
        print(f"\n🔔 새로운 아이템 수신 ({subscription}): {len(new_items)}개")
        for item in new_items[:3]:  # 처음 3개만 표시
            print(f"   - {item.title}")
            print(f"     링크: {item.link}")
            print(f"     설명: {item.description[:100]}...")

    subscriber.add_callback(new_items_callback)

    # 수동 업데이트 테스트
    print("\n2. 구독 업데이트:")
    results = subscriber.update_all()

    # 통계 확인
    print("\n3. 구독 통계:")
    stats = subscriber.get_stats()
    print(f"   전체 구독: {stats['total_subscriptions']}개")
    print(f"   활성 구독: {stats['enabled_subscriptions']}개")

    for name, sub_stats in stats['subscriptions'].items():
        print(f"\n   구독: {name}")
        print(f"   전체 업데이트: {sub_stats['total_updates']}회")
        print(f"   성공 업데이트: {sub_stats['successful_updates']}회")
        print(f"   수집 아이템: {sub_stats['total_items_collected']}개")
        print(f"   새로운 아이템: {sub_stats['new_items_collected']}개")

    # 설정 내보내기
    print("\n4. 구독 설정 내보내기:")
    subscriber.export_config("integration_subscriptions.json")
    print("   → integration_subscriptions.json 저장 완료")

    print("\n✅ 예시 2 완료!")


# ============================================================================
# 예시 3: 알림 시스템
# ============================================================================

def example_3_notification_system():
    """예시 3: 알림 시스템"""
    print("\n" + "="*80)
    print("예시 3: 알림 시스템")
    print("="*80)

    # 알림 설정
    config = NotificationConfig(
        enabled=True,
        channels=[NotificationChannel.CONSOLE],
        min_items_for_notification=1,
        summary_limit=5
    )

    # 알림 관리자 생성
    notifier = ChangeNotifier(config)

    # 테스트용 알림 요약 생성
    test_items = [
        FeedItem(
            title="AI 기술의 혁신",
            link="https://example.com/ai1",
            description="인공지능 기술이 새로운 전기를 맞이하고 있습니다.",
            pub_date=datetime.now(),
            author="테크미디어",
            category="기술"
        ),
        FeedItem(
            title="블록체인의 미래",
            link="https://example.com/blockchain1",
            description="블록체인 기술이 금융 산업을 변화시키고 있습니다.",
            pub_date=datetime.now(),
            author="코인뉴스",
            category="금융"
        ),
        FeedItem(
            title="메타버스 플랫폼 경쟁",
            link="https://example.com/metaverse1",
            description="메타버스 플랫폼 간 경쟁이 치열해지고 있습니다.",
            pub_date=datetime.now(),
            author="VR타임즈",
            category="기술"
        )
    ]

    print("\n1. 알림 전송 테스트:")
    success = notifier.notify_items(test_items, "테스트 구독", "AI")

    # 통계 확인
    print("\n2. 알림 통계:")
    stats = notifier.get_stats()
    print(f"   전체 알림: {stats['total_notifications']}회")
    print(f"   콘솔 알림: {stats['console_notifications']}회")
    print(f"   전송 아이템: {stats['total_items_sent']}개")
    print(f"   마지막 알림: {stats['last_notification_time']}")

    print(f"\n알림 전송 {'성공' if success else '실패'}")
    print("\n✅ 예시 3 완료!")


# ============================================================================
# 예시 4: 통합 시스템
# ============================================================================

def example_4_integrated_system():
    """예시 4: 통합 시스템"""
    print("\n" + "="*80)
    print("예시 4: 필터링 + 구독 + 알림 통합 시스템")
    print("="*80)

    # 1. 필터 생성
    print("\n1. 필터 시스템 초기화:")
    feed_filter = FeedFilter(db_path="integrated_filter.db")
    print("   → 필터 시스템 초기화 완료")

    # 2. 구독자 생성
    print("\n2. 구독 시스템 초기화:")
    subscriber = FeedSubscriber(feed_filter=feed_filter)
    print("   → 구독 시스템 초기화 완료")

    # 3. 알림 관리자 생성
    print("\n3. 알림 시스템 초기화:")
    notification_config = NotificationConfig(
        enabled=True,
        channels=[NotificationChannel.CONSOLE],
        min_items_for_notification=1,
        summary_limit=5
    )
    notifier = ChangeNotifier(notification_config)
    print("   → 알림 시스템 초기화 완료")

    # 4. 구독 설정
    print("\n4. 구독 설정:")
    test_feeds = [
        SubscriptionConfig(
            url="https://news.google.com/rss/search?q=AI&hl=ko&gl=KR&ceid=KR:ko",
            name="Google News AI",
            keyword="AI",
            update_interval=300,
            max_items=20
        )
    ]

    for feed_config in test_feeds:
        subscriber.add_subscription(feed_config)
        print(f"   - {feed_config.name} 추가 완료")

    # 5. 콜백 설정 (필터링 + 알림)
    print("\n5. 콜백 시스템 설정:")

    def integrated_callback(new_items, subscription):
        """통합 콜백 함수"""
        if not new_items:
            return

        print(f"\n📊 새로운 아이템 {len(new_items)}개 발견 ({subscription})")

        # 알림 전송
        notifier.notify_items(new_items, subscription)

    subscriber.add_callback(integrated_callback)
    print("   → 통합 콜백 설정 완료")

    # 6. 업데이트 실행
    print("\n6. 구독 업데이트 실행:")
    results = subscriber.update_all()

    # 7. 전체 통계 확인
    print("\n7. 전체 시스템 통계:")

    # 필터 통계
    filter_stats = feed_filter.get_stats()
    print(f"\n   [필터 시스템]")
    if 'database_stats' in filter_stats:
        db_stats = filter_stats['database_stats']
        print(f"   전체 아이템: {db_stats['total_items']}개")
        print(f"   최근 24시간 아이템: {db_stats['recent_items_24h']}개")

    # 구독 통계
    sub_stats = subscriber.get_stats()
    print(f"\n   [구독 시스템]")
    print(f"   전체 구독: {sub_stats['total_subscriptions']}개")
    for name, stats in sub_stats['subscriptions'].items():
        print(f"   {name}:")
        print(f"     업데이트: {stats['total_updates']}회")
        print(f"     새로운 아이템: {stats['new_items_collected']}개")

    # 알림 통계
    notif_stats = notifier.get_stats()
    print(f"\n   [알림 시스템]")
    print(f"   전체 알림: {notif_stats['total_notifications']}회")
    print(f"   전송 아이템: {notif_stats['total_items_sent']}개")

    print("\n✅ 예시 4 완료!")


# ============================================================================
# 예시 5: 실시간 모니터링
# ============================================================================

def example_5_realtime_monitoring():
    """예시 5: 실시간 모니터링 시스템"""
    print("\n" + "="*80)
    print("예시 5: 실시간 모니터링 시스템")
    print("="*80)

    # 시스템 초기화
    print("\n1. 시스템 초기화:")

    feed_filter = FeedFilter(db_path="monitoring_filter.db")
    subscriber = FeedSubscriber(feed_filter=feed_filter)

    notification_config = NotificationConfig(
        enabled=True,
        channels=[NotificationChannel.CONSOLE],
        min_items_for_notification=1,
        summary_limit=3
    )
    notifier = ChangeNotifier(notification_config)

    # 구독 설정
    test_feeds = [
        SubscriptionConfig(
            url="https://news.google.com/rss/search?q=AI&hl=ko&gl=KR&ceid=KR:ko",
            name="Google News AI",
            keyword="AI",
            update_interval=180,  # 3분
            max_items=15
        )
    ]

    for feed_config in test_feeds:
        subscriber.add_subscription(feed_config)

    # 콜백 설정
    def monitoring_callback(new_items, subscription):
        if new_items:
            print(f"\n🚨 새로운 아이템 감지 ({subscription}): {len(new_items)}개")
            notifier.notify_items(new_items, subscription)

    subscriber.add_callback(monitoring_callback)
    print("   → 모니터링 시스템 초기화 완료")

    # 모니터 시작
    print("\n2. 실시간 모니터링 시작:")
    print("   → 3분마다 자동 업데이트")
    print("   → 중지하려면 Ctrl+C를 누르세요")

    monitor = FeedMonitor(subscriber, check_interval=60)
    monitor.start()

    # 테스트를 위해 2분만 실행
    print("\n3. 2분간 테스트 실행 중...")
    try:
        time.sleep(120)  # 2分钟
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자 중단")

    monitor.stop()
    print("\n✅ 예시 5 완료!")


# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    print("\n" + "="*80)
    print("RSS 피드 시스템 통합 예시")
    print("="*80)

    examples = [
        ("1", "기본 필터링 시스템", example_1_basic_filtering),
        ("2", "구독 시스템", example_2_subscription_system),
        ("3", "알림 시스템", example_3_notification_system),
        ("4", "통합 시스템", example_4_integrated_system),
        ("5", "실시간 모니터링", example_5_realtime_monitoring),
        ("0", "모든 예시 실행", None),
    ]

    print("\n사용 가능한 예시:")
    for key, desc, _ in examples:
        print(f"  {key}. {desc}")

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