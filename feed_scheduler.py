#!/usr/bin/env python3
"""
RSS 피드 스케줄러 모듈
APScheduler를 사용하여 정기적인 자동 크롤링 및 RSS 피드 업데이트를 수행합니다.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Callable
from pathlib import Path
import json
from dataclasses import dataclass, field, asdict
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import signal
import sys

# 프로젝트 모듈 임포트
from web_crawler import WebCrawler
from rss_feed_generator import (
    RSSFeedGenerator,
    RSSFeedConfig,
    MultiFeedGenerator,
    WebCrawlerToRSSConverter
)


# ============================================================================
# 설정 및 로깅
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 스케줄링 설정
# ============================================================================

@dataclass
class ScheduleConfig:
    """스케줄링 설정"""
    # 스케줄 유형: 'interval' (간격) 또는 'cron' (크론)
    schedule_type: str = 'interval'

    # 간격 기반 설정
    interval_minutes: int = 60
    interval_hours: int = 0

    # 크론 기반 설정
    cron_hour: int = 9
    cron_minute: int = 0
    cron_day_of_week: str = '*'  # 0-6 또는 MON-FRI
    cron_day: str = '*'
    cron_month: str = '*'

    # RSS 피드 설정
    rss_output_dir: str = "rss_feeds"
    rss_base_title: str = "DealBot"
    rss_base_link: str = "https://github.com/yourusername/DealBot"

    # 크롤러 설정
    max_results_per_keyword: int = 20
    use_cache: bool = True

    # 이메일 알림 설정 (선택사항)
    enable_email_notification: bool = False
    email_recipients: List[str] = field(default_factory=list)

    # 통합 피드 생성 여부
    create_combined_feed: bool = True


@dataclass
class KeywordSchedule:
    """키워드별 스케줄 정보"""
    keyword: str
    enabled: bool = True
    schedule_config: Optional[ScheduleConfig] = None  # None이면 기본 설정 사용
    last_crawled: Optional[datetime] = None
    total_crawled: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


# ============================================================================
# RSS 피드 스케줄러
# ============================================================================

class RSSFeedScheduler:
    """RSS 피드 자동 업데이트 스케줄러"""

    def __init__(self,
                 default_config: ScheduleConfig = None,
                 use_background: bool = False):
        """
        RSS 피드 스케줄러 초기화

        Args:
            default_config: 기본 스케줄링 설정
            use_background: 백그라운드 스케줄러 사용 여부
                           (False면 BlockingScheduler 사용)
        """
        self.default_config = default_config or ScheduleConfig()
        self.keyword_schedules: Dict[str, KeywordSchedule] = {}
        self.crawlers: Dict[str, WebCrawler] = {}

        # 스케줄러 타입 선택
        if use_background:
            self.scheduler = BackgroundScheduler()
        else:
            self.scheduler = BlockingScheduler()

        # 이벤트 리스너 등록
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

        # 시그널 핸들러 등록 (Graceful Shutdown)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("RSS 피드 스케줄러 초기화 완료")

    def add_keyword(self,
                   keyword: str,
                   schedule_config: Optional[ScheduleConfig] = None):
        """
        키워드 추가

        Args:
            keyword: 크롤링할 키워드
            schedule_config: 스케줄링 설정 (None이면 기본 설정 사용)
        """
        # 키워드 스케줄 생성
        keyword_schedule = KeywordSchedule(
            keyword=keyword,
            enabled=True,
            schedule_config=schedule_config
        )

        self.keyword_schedules[keyword] = keyword_schedule

        # 크롤러 초기화
        crawler = WebCrawler(
            use_cache=self.default_config.use_cache
        )
        self.crawlers[keyword] = crawler

        logger.info(f"키워드 추가됨: {keyword}")

    def add_keywords(self,
                    keywords: List[str],
                    schedule_config: Optional[ScheduleConfig] = None):
        """
        여러 키워드 한번에 추가

        Args:
            keywords: 키워드 리스트
            schedule_config: 스케줄링 설정
        """
        for keyword in keywords:
            self.add_keyword(keyword, schedule_config)

    def remove_keyword(self, keyword: str):
        """
        키워드 제거

        Args:
            keyword: 제거할 키워드
        """
        if keyword in self.keyword_schedules:
            del self.keyword_schedules[keyword]

            # 크롤러 정리
            if keyword in self.crawlers:
                self.crawlers[keyword].close()
                del self.crawlers[keyword]

            # 등록된 작업 제거
            job_id = f"crawl_{keyword}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)

            logger.info(f"키워드 제거됨: {keyword}")

    def schedule_all(self):
        """모든 키워드에 대한 스케줄링 등록"""
        for keyword, schedule_info in self.keyword_schedules.items():
            if not schedule_info.enabled:
                continue

            self._schedule_keyword(keyword, schedule_info)

        logger.info(f"총 {len(self.keyword_schedules)}개 키워드 스케줄링 완료")

    def _schedule_keyword(self, keyword: str, schedule_info: KeywordSchedule):
        """
        개별 키워드 스케줄링

        Args:
            keyword: 키워드
            schedule_info: 키워드 스케줄 정보
        """
        # 설정 가져오기
        config = schedule_info.schedule_config or self.default_config

        # 작업 ID
        job_id = f"crawl_{keyword}"

        # 트리거 생성
        if config.schedule_type == 'cron':
            trigger = CronTrigger(
                hour=config.cron_hour,
                minute=config.cron_minute,
                day_of_week=config.cron_day_of_week,
                day=config.cron_day,
                month=config.cron_month
            )
            logger.info(f"{keyword}: Cron 스케줄 등록 ({config.cron_hour}:{config.cron_minute})")
        else:  # interval
            # 시간과 분을 총 분으로 변환
            total_minutes = config.interval_hours * 60 + config.interval_minutes
            trigger = IntervalTrigger(minutes=total_minutes)
            logger.info(f"{keyword}: Interval 스케줄 등록 ({total_minutes}분)")

        # 작업 등록
        self.scheduler.add_job(
            self._crawl_and_generate_feed,
            trigger=trigger,
            id=job_id,
            args=[keyword],
            name=f"Crawl and generate RSS feed for {keyword}",
            replace_existing=True
        )

    def _crawl_and_generate_feed(self, keyword: str):
        """
        크롤링 및 RSS 피드 생성 작업

        Args:
            keyword: 키워드
        """
        schedule_info = self.keyword_schedules.get(keyword)
        if not schedule_info:
            logger.warning(f"키워드 스케줄 정보를 찾을 수 없음: {keyword}")
            return

        logger.info(f"크롤링 시작: {keyword} ({datetime.now()})")

        try:
            # 크롤러 가져오기
            crawler = self.crawlers.get(keyword)
            if not crawler:
                logger.error(f"크롤러를 찾을 수 없음: {keyword}")
                return

            # 설정 가져오기
            config = schedule_info.schedule_config or self.default_config

            # 크롤링 수행
            data = crawler.search_google_news(
                keyword,
                max_results=config.max_results_per_keyword
            )

            if not data:
                logger.warning(f"크롤링 결과 없음: {keyword}")
                return

            # RSS 피드 생성
            feed_config = RSSFeedConfig(
                title=f"{config.rss_base_title} - {keyword}",
                description=f"{keyword} 관련 뉴스/블로그 피드",
                link=config.rss_base_link,
                language="ko"
            )

            converter = WebCrawlerToRSSConverter()
            rss_items = converter.convert_to_rss_items(data)

            generator = RSSFeedGenerator(feed_config)
            output_path = str(
                Path(config.rss_output_dir) / f"{keyword}.xml"
            )
            generator.save_feed(rss_items, output_path)

            # 스케줄 정보 업데이트
            schedule_info.last_crawled = datetime.now()
            schedule_info.total_crawled += 1
            schedule_info.error_count = 0
            schedule_info.last_error = None

            logger.info(f"크롤링 완료: {keyword}, {len(data)}개 아이템 수집")

        except Exception as e:
            logger.error(f"크롤링 오류 ({keyword}): {e}")
            schedule_info.error_count += 1
            schedule_info.last_error = str(e)

    def generate_combined_feed(self):
        """통합 RSS 피드 생성"""
        # 설정
        config = self.default_config

        # 모든 크롤러에서 데이터 수집
        all_data_by_keyword = {}

        for keyword in self.keyword_schedules.keys():
            crawler = self.crawlers.get(keyword)
            if not crawler:
                continue

            try:
                # 캐시에서 최신 데이터 가져오기
                data = crawler.search_google_news(
                    keyword,
                    max_results=config.max_results_per_keyword
                )
                all_data_by_keyword[keyword] = data
            except Exception as e:
                logger.error(f"통합 피드 생성 오류 ({keyword}): {e}")

        # 통합 피드 생성
        if all_data_by_keyword:
            base_config = RSSFeedConfig(
                title=config.rss_base_title,
                description=f"{config.rss_base_title} 통합 뉴스/블로그 피드",
                link=config.rss_base_link,
                language="ko"
            )

            multi_gen = MultiFeedGenerator(base_config)
            combined_path = str(
                Path(config.rss_output_dir) / "combined.xml"
            )
            multi_gen.generate_combined_feed(
                all_data_by_keyword,
                combined_path
            )

            logger.info(f"통합 피드 생성 완료: {combined_path}")

    def _job_executed_listener(self, event):
        """작업 실행 이벤트 리스너"""
        if event.exception:
            logger.error(f"작업 실패: {event.job_id}, 예외: {event.exception}")
        else:
            logger.info(f"작업 성공: {event.job_id}")

    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Graceful Shutdown)"""
        logger.info(f"시그널 수신 ({signum}), 스케줄러 종료 중...")
        self.shutdown()
        sys.exit(0)

    def start(self, run_immediately: bool = False):
        """
        스케줄러 시작

        Args:
            run_immediately: 즉시 실행 후 스케줄링 시작 여부
        """
        logger.info("RSS 피드 스케줄러 시작")

        # 즉시 실행 옵션
        if run_immediately:
            logger.info("즉시 실행 모드: 모든 키워드 크롤링 시작")
            for keyword in self.keyword_schedules.keys():
                self._crawl_and_generate_feed(keyword)

            # 통합 피드 생성
            if self.default_config.create_combined_feed:
                self.generate_combined_feed()

        # 스케줄러 시작
        try:
            self.scheduler.start()
            logger.info("스케줄러가 시작되었습니다. Ctrl+C로 종료하세요.")

            # BlockingScheduler인 경우 대기
            if isinstance(self.scheduler, BlockingScheduler):
                try:
                    # 무한 대기 (SIGINT 핸들러가 종료 처리)
                    while True:
                        import time
                        time.sleep(1)
                except (KeyboardInterrupt, SystemExit):
                    pass

        except (KeyboardInterrupt, SystemExit):
            logger.info("스케줄러 종료")
            self.shutdown()

    def shutdown(self):
        """스케줄러 종료"""
        logger.info("스케줄러 종료 중...")

        # 스케줄러 종료
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        # 모든 크롤러 정리
        for crawler in self.crawlers.values():
            crawler.close()

        logger.info("스케줄러 종료 완료")

    def get_status(self) -> Dict:
        """
        스케줄러 상태 정보 반환

        Returns:
            상태 정보 딕셔너리
        """
        status = {
            "scheduler_running": self.scheduler.running,
            "total_keywords": len(self.keyword_schedules),
            "enabled_keywords": sum(
                1 for s in self.keyword_schedules.values() if s.enabled
            ),
            "jobs_count": len(self.scheduler.get_jobs()),
            "keywords": []
        }

        for keyword, schedule_info in self.keyword_schedules.items():
            keyword_status = {
                "keyword": keyword,
                "enabled": schedule_info.enabled,
                "last_crawled": schedule_info.last_crawled.isoformat() if schedule_info.last_crawled else None,
                "total_crawled": schedule_info.total_crawled,
                "error_count": schedule_info.error_count,
                "last_error": schedule_info.last_error
            }
            status["keywords"].append(keyword_status)

        return status

    def save_config(self, filepath: str = "scheduler_config.json"):
        """
        스케줄러 설정 저장

        Args:
            filepath: 저장 파일 경로
        """
        config_data = {
            "default_config": asdict(self.default_config),
            "keyword_schedules": {}
        }

        for keyword, schedule_info in self.keyword_schedules.items():
            keyword_data = asdict(schedule_info)
            # datetime 변환
            if keyword_data["last_crawled"]:
                keyword_data["last_crawled"] = keyword_data["last_crawled"].isoformat()
            config_data["keyword_schedules"][keyword] = keyword_data

        # JSON 저장
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"설정 저장 완료: {filepath}")

    @classmethod
    def load_config(cls, filepath: str = "scheduler_config.json"):
        """
        스케줄러 설정 로드

        Args:
            filepath: 설정 파일 경로

        Returns:
            RSSFeedScheduler 인스턴스
        """
        # JSON 로드
        with open(filepath, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # 기본 설정 복원
        default_config = ScheduleConfig(**config_data["default_config"])

        # 스케줄러 생성
        scheduler = cls(default_config=default_config)

        # 키워드 스케줄 복원
        for keyword, keyword_data in config_data["keyword_schedules"].items():
            schedule_info = KeywordSchedule(**keyword_data)
            # datetime 변환
            if schedule_info.last_crawled:
                schedule_info.last_crawled = datetime.fromisoformat(
                    schedule_info.last_crawled
                )

            scheduler.keyword_schedules[keyword] = schedule_info

            # 크롤러 초기화
            crawler = WebCrawler(
                use_cache=default_config.use_cache
            )
            scheduler.crawlers[keyword] = crawler

        logger.info(f"설정 로드 완료: {filepath}")
        return scheduler


# ============================================================================
# 통합 관리자
# ============================================================================

class FeedManager:
    """RSS 피드 및 스케줄링 통합 관리자"""

    def __init__(self):
        """피드 관리자 초기화"""
        self.scheduler: Optional[RSSFeedScheduler] = None

    def create_scheduler(self,
                        keywords: List[str],
                        schedule_type: str = 'interval',
                        interval_minutes: int = 60,
                        cron_hour: int = 9,
                        cron_minute: int = 0,
                        use_background: bool = False) -> RSSFeedScheduler:
        """
        스케줄러 생성

        Args:
            keywords: 키워드 리스트
            schedule_type: 스케줄 유형 ('interval' 또는 'cron')
            interval_minutes: 간격 기반 시간 (분)
            cron_hour: 크론 시간
            cron_minute: 크론 분
            use_background: 백그라운드 스케줄러 사용 여부

        Returns:
            RSSFeedScheduler 인스턴스
        """
        # 설정 생성
        config = ScheduleConfig(
            schedule_type=schedule_type,
            interval_minutes=interval_minutes,
            cron_hour=cron_hour,
            cron_minute=cron_minute
        )

        # 스케줄러 생성
        self.scheduler = RSSFeedScheduler(
            default_config=config,
            use_background=use_background
        )

        # 키워드 추가
        self.scheduler.add_keywords(keywords)

        # 스케줄링 등록
        self.scheduler.schedule_all()

        return self.scheduler

    def quick_start(self,
                   keywords: List[str],
                   schedule_type: str = 'interval',
                   interval_minutes: int = 60,
                   run_immediately: bool = True):
        """
        빠른 시작

        Args:
            keywords: 키워드 리스트
            schedule_type: 스케줄 유형
            interval_minutes: 간격 (분)
            run_immediately: 즉시 실행 여부
        """
        # 스케줄러 생성
        self.create_scheduler(
            keywords=keywords,
            schedule_type=schedule_type,
            interval_minutes=interval_minutes
        )

        # 시작
        self.scheduler.start(run_immediately=run_immediately)


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 사용 예시
    def example_interval_schedule():
        """간격 기반 스케줄링 예시"""
        manager = FeedManager()

        # 30분마다 크롤링
        manager.quick_start(
            keywords=["AI", "블록체인", "메타버스"],
            schedule_type='interval',
            interval_minutes=30,
            run_immediately=True
        )

    def example_cron_schedule():
        """크론 기반 스케줄링 예시"""
        manager = FeedManager()

        # 매일 9시 0분에 크롤링
        manager.create_scheduler(
            keywords=["AI", "블록체인"],
            schedule_type='cron',
            cron_hour=9,
            cron_minute=0
        )

        # 시작
        manager.scheduler.start(run_immediately=True)

    def example_custom_schedule():
        """커스텀 스케줄링 예시"""
        # 각 키워드별로 다른 스케줄 설정
        scheduler = RSSFeedScheduler()

        # AI: 1시간마다
        scheduler.add_keyword("AI")

        # 블록체인: 2시간마다
        blockchain_config = ScheduleConfig(
            schedule_type='interval',
            interval_hours=2
        )
        scheduler.add_keyword("블록체인", blockchain_config)

        # 메타버스: 매일 10시
        metaverse_config = ScheduleConfig(
            schedule_type='cron',
            cron_hour=10,
            cron_minute=0
        )
        scheduler.add_keyword("메타버스", metaverse_config)

        # 스케줄링 등록
        scheduler.schedule_all()

        # 설정 저장
        scheduler.save_config("my_scheduler_config.json")

        # 시작
        scheduler.start(run_immediately=True)

    # 실행 (원하는 예시 선택)
    # example_interval_schedule()
    # example_cron_schedule()
    # example_custom_schedule()
