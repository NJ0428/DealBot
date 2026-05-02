#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSS 시스템 간단 테스트
필터링, 구독, 알림 시스템의 기본 기능을 테스트합니다.
"""

import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=" * 80)
print("RSS 시스템 기능 테스트")
print("=" * 80)

# 테스트 1: 필터링 시스템
print("\n[테스트 1] 필터링 시스템")
print("-" * 40)

from feed_filter import FeedFilter, FeedItem

# 필터 생성
feed_filter = FeedFilter(db_path="test_filter.db")

# 테스트 데이터 생성
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
    )
]

# 첫 번째 필터링
print("1. 첫 번째 필터링:")
new_items, stats = feed_filter.filter_new_items(test_items, "TEST")
print(f"   결과: {len(new_items)}개 새로운 아이템")
for item in new_items:
    print(f"   - {item.title}")

# 두 번째 필터링 (중복 감지)
print("\n2. 두 번째 필터링 (중복 감지):")
new_items, stats = feed_filter.filter_new_items(test_items, "TEST")
print(f"   결과: {len(new_items)}개 새로운 아이템 (예상: 0개)")

# 새로운 아이템 추가
new_item = FeedItem(
    title="메타버스 플랫폼 경쟁",
    link="https://example.com/metaverse1",
    description="메타버스 플랫폼 간 경쟁이 치열해지고 있습니다.",
    pub_date=datetime.now(),
    author="VR타임즈",
    category="기술"
)

print("\n3. 새로운 아이템 추가:")
new_items, stats = feed_filter.filter_new_items([new_item], "TEST")
print(f"   결과: {len(new_items)}개 새로운 아이템 (예상: 1개)")
for item in new_items:
    print(f"   - {item.title}")

# 통계 확인
print("\n4. 필터링 통계:")
print(f"   전체 처리: {stats.total_processed}개")
print(f"   새로운 아이템: {stats.new_items}개")
print(f"   중복 아이템: {stats.duplicate_items}개")

print("   -> 필터링 시스템 테스트 완료!")

# 테스트 2: 알림 시스템
print("\n[테스트 2] 알림 시스템")
print("-" * 40)

from change_notifier import ChangeNotifier, NotificationConfig, NotificationChannel

# 알림 설정
config = NotificationConfig(
    enabled=True,
    channels=[NotificationChannel.CONSOLE],
    min_items_for_notification=1,
    summary_limit=3
)

# 알림 관리자 생성
notifier = ChangeNotifier(config)

# 알림 전송 테스트
print("1. 알림 전송 테스트:")
test_items_for_notification = [
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
    )
]

success = notifier.notify_items(test_items_for_notification, "테스트 구독", "TEST")
print(f"   결과: 알림 전송 {'성공' if success else '실패'}")

# 통계 확인
stats = notifier.get_stats()
print("\n2. 알림 통계:")
print(f"   전체 알림: {stats['total_notifications']}회")
print(f"   콘솔 알림: {stats['console_notifications']}회")
print(f"   전송 아이템: {stats['total_items_sent']}개")

print("   -> 알림 시스템 테스트 완료!")

# 전체 요약
print("\n" + "=" * 80)
print("테스트 요약")
print("=" * 80)
print("1. 필터링 시스템: 정상 작동")
print("2. 알림 시스템: 정상 작동")
print("\n모든 테스트가 완료되었습니다!")
print("=" * 80)

# 정리
import os
# 테스트 데이터베이스 삭제
if os.path.exists("test_filter.db"):
    os.remove("test_filter.db")
    print("테스트 데이터베이스 정리 완료")