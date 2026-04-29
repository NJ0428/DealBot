#!/usr/bin/env python3
"""
RSS 피드 구독 시스템
외부 RSS 피드를 구독하고 실시간으로 업데이트를 감시합니다.
"""

import logging
import feedparser
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable, Set
from pathlib import Path
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import ssl
import certifi


# 프로젝트 모듈 임포트
from feed_filter import FeedItem, FeedFilter, FilterStats


# ============================================================================
# 설정 및 로깅
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class SubscriptionConfig:
    """구독 설정"""
    url: str
    name: str = ""
    update_interval: int = 300  # 5분 (초 단위)
    enabled: bool = True
    keyword: str = ""  # 필터링용 키워드
    max_items: int = 50
    timeout: int = 30

    def __post_init__(self):
        """구독 이름 자동 생성"""
        if not self.name:
            # URL에서 도메인 추출
            parsed = urlparse(self.url)
            self.name = parsed.netloc.replace("www.", "")


@dataclass
class SubscriptionStats:
    """구독 통계"""
    subscription_name: str
    total_updates: int = 0
    successful_updates: int = 0
    failed_updates: int = 0
    last_update_time: Optional[datetime] = None
    last_error: Optional[str] = None
    total_items_collected: int = 0
    new_items_collected: int = 0

    def record_update(self, success: bool, item_count: int = 0, new_count: int = 0, error: str = None):
        """업데이트 기록"""
        self.total_updates += 1
        self.last_update_time = datetime.now()

        if success:
            self.successful_updates += 1
            self.total_items_collected += item_count
            self.new_items_collected += new_count
            self.last_error = None
        else:
            self.failed_updates += 1
            self.last_error = error


# ============================================================================
# RSS 피드 구독자
# ============================================================================

class FeedSubscriber:
    """RSS 피드 구독자"""

    def __init__(self,
                 feed_filter: Optional[FeedFilter] = None,
                 user_agent: str = "DealBot RSS Subscriber/1.0"):
        """
        RSS 피드 구독자 초기화

        Args:
            feed_filter: 피드 필터 (None이면 필터링 없음)
            user_agent: 사용자 에이전트
        """
        self.feed_filter = feed_filter
        self.user_agent = user_agent
        self.subscriptions: Dict[str, SubscriptionConfig] = {}
        self.stats: Dict[str, SubscriptionStats] = {}
        self.callbacks: List[Callable] = []

        # SSL 인증서 설정
        self._ssl_context = ssl.create_default_context(cafile=certifi.where())

        logger.info("RSS 피드 구독자 초기화 완료")

    def add_subscription(self, config: SubscriptionConfig):
        """
        구독 추가

        Args:
            config: 구독 설정
        """
        self.subscriptions[config.name] = config

        # 통계 초기화
        self.stats[config.name] = SubscriptionStats(subscription_name=config.name)

        logger.info(f"구독 추가됨: {config.name} ({config.url})")

    def remove_subscription(self, name: str):
        """
        구독 제거

        Args:
            name: 구독 이름
        """
        if name in self.subscriptions:
            del self.subscriptions[name]
            del self.stats[name]
            logger.info(f"구독 제거됨: {name}")

    def add_callback(self, callback: Callable):
        """
        콜백 함수 추가

        Args:
            callback: 콜백 함수 (new_items: List[FeedItem], subscription: str) -> None
        """
        self.callbacks.append(callback)

    def fetch_feed(self, config: SubscriptionConfig) -> Optional[List[FeedItem]]:
        """
        RSS 피드 가져오기

        Args:
            config: 구독 설정

        Returns:
            피드 아이템 리스트 (실패 시 None)
        """
        try:
            logger.info(f"피드 가져오기: {config.name}")

            # feedparser 설정
            feedparser.USER_AGENT = self.user_agent

            # 피드 파싱
            feed = feedparser.parse(
                config.url,
                handlers=[]
            )

            # 에러 확인
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"피드 파싱 경고 ({config.name}): {feed.bozo_exception}")

            # 아이템 추출
            items = []
            for entry in feed.entries[:config.max_items]:
                try:
                    # 기본 필드 추출
                    title = entry.get('title', '제목 없음')
                    link = entry.get('link', '')

                    # 설명 추출 (다양한 필드 지원)
                    description = (
                        entry.get('description', '') or
                        entry.get('summary', '') or
                        entry.get('content', [{'value': ''}])[0].get('value', '')
                    )

                    # 날짜 추출 (다양한 필드 지원)
                    pub_date = None
                    for date_field in ['published_parsed', 'updated_parsed']:
                        if date_field in entry and entry[date_field]:
                            try:
                                pub_date = datetime(*entry[date_field][:6])
                                break
                            except (TypeError, ValueError):
                                continue

                    # 작성자 추출
                    author = (
                        entry.get('author', '') or
                        entry.get('dc_creator', '')
                    )

                    # 카테고리 추출
                    category = ''
                    if 'tags' in entry and entry.tags:
                        category = ', '.join([tag.get('term', '') for tag in entry.tags])

                    # 전체 내용 추출
                    content = description
                    if 'content' in entry and entry.content:
                        content = entry.content[0].get('value', description)

                    # FeedItem 생성
                    item = FeedItem(
                        title=title,
                        link=link,
                        description=description,
                        pub_date=pub_date,
                        author=author,
                        category=category,
                        source=config.name,
                        content=content
                    )

                    items.append(item)

                except Exception as e:
                    logger.warning(f"아이템 파싱 오류 ({config.name}): {e}")
                    continue

            logger.info(f"피드 가져오기 성공 ({config.name}): {len(items)}개 아이템")
            return items

        except Exception as e:
            logger.error(f"피드 가져오기 실패 ({config.name}): {e}")
            return None

    def update_subscription(self, name: str) -> Optional[List[FeedItem]]:
        """
        구독 업데이트

        Args:
            name: 구독 이름

        Returns:
            새로운 아이템 리스트 (실패 시 None)
        """
        if name not in self.subscriptions:
            logger.error(f"구독을 찾을 수 없음: {name}")
            return None

        config = self.subscriptions[name]
        stats = self.stats[name]

        if not config.enabled:
            logger.info(f"구독이 비활성화됨: {name}")
            return None

        try:
            # 피드 가져오기
            items = self.fetch_feed(config)
            if items is None:
                stats.record_update(success=False, error="피드 가져오기 실패")
                return None

            # 필터링
            new_items = []
            if self.feed_filter:
                filtered_items, filter_stats = self.feed_filter.filter_new_items(
                    items,
                    config.keyword
                )
                new_items = filtered_items
            else:
                new_items = items

            # 통계 업데이트
            stats.record_update(
                success=True,
                item_count=len(items),
                new_count=len(new_items)
            )

            # 콜백 실행
            for callback in self.callbacks:
                try:
                    callback(new_items, name)
                except Exception as e:
                    logger.error(f"콜백 실행 오류: {e}")

            logger.info(f"구독 업데이트 완료 ({name}): {len(new_items)}개 새로운 아이템")
            return new_items

        except Exception as e:
            error_msg = f"구독 업데이트 오류: {e}"
            logger.error(f"{error_msg} ({name})")
            stats.record_update(success=False, error=error_msg)
            return None

    def update_all(self) -> Dict[str, Optional[List[FeedItem]]]:
        """
        모든 구독 업데이트

        Returns:
            구독별 새로운 아이템 딕셔너리
        """
        results = {}

        for name in self.subscriptions.keys():
            results[name] = self.update_subscription(name)

        return results

    def get_stats(self, name: str = None) -> Dict:
        """
        구독 통계 조회

        Args:
            name: 구독 이름 (None이면 전체 통계)

        Returns:
            통계 딕셔너리
        """
        if name:
            if name in self.stats:
                stats = self.stats[name]
                return {
                    'subscription_name': stats.subscription_name,
                    'total_updates': stats.total_updates,
                    'successful_updates': stats.successful_updates,
                    'failed_updates': stats.failed_updates,
                    'last_update_time': stats.last_update_time.isoformat() if stats.last_update_time else None,
                    'last_error': stats.last_error,
                    'total_items_collected': stats.total_items_collected,
                    'new_items_collected': stats.new_items_collected
                }
            else:
                return {'error': 'Subscription not found'}
        else:
            # 전체 통계
            return {
                'total_subscriptions': len(self.subscriptions),
                'enabled_subscriptions': sum(
                    1 for s in self.subscriptions.values() if s.enabled
                ),
                'subscriptions': {
                    name: {
                        'total_updates': stats.total_updates,
                        'successful_updates': stats.successful_updates,
                        'failed_updates': stats.failed_updates,
                        'last_update_time': stats.last_update_time.isoformat() if stats.last_update_time else None,
                        'total_items_collected': stats.total_items_collected,
                        'new_items_collected': stats.new_items_collected
                    }
                    for name, stats in self.stats.items()
                }
            }

    def export_config(self, filepath: str = "subscriptions.json"):
        """
        구독 설정 내보내기

        Args:
            filepath: 출력 파일 경로
        """
        config_data = {
            'subscriptions': [
                {
                    'name': config.name,
                    'url': config.url,
                    'update_interval': config.update_interval,
                    'enabled': config.enabled,
                    'keyword': config.keyword,
                    'max_items': config.max_items,
                    'timeout': config.timeout
                }
                for config in self.subscriptions.values()
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"구독 설정 내보내기 완료: {filepath}")

    @classmethod
    def import_config(cls,
                     filepath: str = "subscriptions.json",
                     feed_filter: Optional[FeedFilter] = None) -> 'FeedSubscriber':
        """
        구독 설정 가져오기

        Args:
            filepath: 설정 파일 경로
            feed_filter: 피드 필터

        Returns:
            FeedSubscriber 인스턴스
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        subscriber = cls(feed_filter=feed_filter)

        for sub_config in config_data['subscriptions']:
            config = SubscriptionConfig(**sub_config)
            subscriber.add_subscription(config)

        logger.info(f"구독 설정 가져오기 완료: {filepath}")
        return subscriber


# ============================================================================
# 실시간 업데이트 모니터
# ============================================================================

class FeedMonitor:
    """RSS 피드 실시간 업데이트 모니터"""

    def __init__(self,
                 subscriber: FeedSubscriber,
                 check_interval: int = 60):
        """
        피드 모니터 초기화

        Args:
            subscriber: 피드 구독자
            check_interval: 업데이트 확인 간격 (초)
        """
        self.subscriber = subscriber
        self.check_interval = check_interval
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.update_times: Dict[str, datetime] = {}

        logger.info("RSS 피드 모니터 초기화 완료")

    def _monitor_loop(self):
        """모니터링 루프"""
        logger.info("피드 모니터링 시작")

        while self.running:
            try:
                current_time = datetime.now()

                # 각 구독 확인
                for name, config in self.subscriber.subscriptions.items():
                    if not config.enabled:
                        continue

                    # 마지막 업데이트 시간 확인
                    last_update = self.update_times.get(name)
                    if last_update:
                        time_since_update = (current_time - last_update).total_seconds()
                        if time_since_update < config.update_interval:
                            continue

                    # 업데이트 실행
                    new_items = self.subscriber.update_subscription(name)
                    self.update_times[name] = current_time

                    # 새로운 아이템이 있는 경우 로깅
                    if new_items and len(new_items) > 0:
                        logger.info(f"새로운 아이템 발견 ({name}): {len(new_items)}개")

                # 대기
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(self.check_interval)

        logger.info("피드 모니터링 종료")

    def start(self):
        """모니터링 시작"""
        if self.running:
            logger.warning("모니터가 이미 실행 중입니다")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("피드 모니터 시작됨")

    def stop(self):
        """모니터링 중지"""
        if not self.running:
            logger.warning("모니터가 실행 중이 아닙니다")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        logger.info("피드 모니터 중지됨")

    def is_running(self) -> bool:
        """실행 중 여부 확인"""
        return self.running


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_subscriber_from_feeds(feeds: List[Dict[str, str]],
                                 feed_filter: Optional[FeedFilter] = None) -> FeedSubscriber:
    """
    피드 리스트로부터 구독자 생성

    Args:
        feeds: 피드 설정 리스트 [{'url': '...', 'name': '...', 'keyword': '...'}]
        feed_filter: 피드 필터

    Returns:
        FeedSubscriber 인스턴스
    """
    subscriber = FeedSubscriber(feed_filter=feed_filter)

    for feed_config in feeds:
        url = feed_config['url']
        name = feed_config.get('name', '')
        keyword = feed_config.get('keyword', '')
        update_interval = feed_config.get('update_interval', 300)

        config = SubscriptionConfig(
            url=url,
            name=name,
            keyword=keyword,
            update_interval=update_interval
        )
        subscriber.add_subscription(config)

    return subscriber


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 필터 생성
    test_filter = FeedFilter(db_path="test_subscription_cache.db")

    # 구독자 생성
    subscriber = FeedSubscriber(feed_filter=test_filter)

    # 테스트용 RSS 피드 구독
    test_feeds = [
        SubscriptionConfig(
            url="https://news.google.com/rss/search?q=AI&hl=ko&gl=KR&ceid=KR:ko",
            name="Google News AI",
            keyword="AI",
            update_interval=300
        ),
        # 추가 테스트 피드들...
    ]

    # 구독 추가
    for feed_config in test_feeds:
        subscriber.add_subscription(feed_config)

    # 콜백 추가
    def new_items_callback(new_items: List[FeedItem], subscription: str):
        print(f"\n새로운 아이템 수신 ({subscription}):")
        for item in new_items[:3]:  # 처음 3개만 표시
            print(f"  - {item.title}")

    subscriber.add_callback(new_items_callback)

    # 수동 업데이트 테스트
    print("구독 업데이트 테스트:")
    results = subscriber.update_all()

    # 통계 확인
    print("\n구독 통계:")
    print(json.dumps(subscriber.get_stats(), indent=2))

    # 설정 내보내기
    subscriber.export_config("test_subscriptions.json")

    print("\n✅ 테스트 완료!")