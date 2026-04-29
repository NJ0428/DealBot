#!/usr/bin/env python3
"""
RSS 피드 필터링 시스템
이전에 수집한 게시물과 비교하여 새로운 게시물만 필터링합니다.
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field, asdict
import sqlite3
from contextlib import contextmanager


# ============================================================================
# 설정 및 로깅
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class FeedItem:
    """피드 아이템 데이터 모델"""
    title: str
    link: str
    description: str
    pub_date: Optional[datetime] = None
    author: str = ""
    category: str = ""
    source: str = ""
    content: str = ""

    def __post_init__(self):
        """날짜 문자열을 datetime 객체로 변환"""
        if isinstance(self.pub_date, str):
            try:
                # 다양한 날짜 형식 처리
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%a, %d %b %Y %H:%M:%S %z",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%dT%H:%M:%SZ"
                ]:
                    try:
                        self.pub_date = datetime.strptime(self.pub_date.split("+")[0].strip(), fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"날짜 변환 오류: {self.pub_date}, {e}")
                self.pub_date = None

    def get_hash(self) -> str:
        """아이템의 고유 해시 생성"""
        # 링크와 제목을 기반으로 해시 생성
        content = f"{self.link}|{self.title}"
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        data = asdict(self)
        # datetime 변환
        if self.pub_date:
            data['pub_date'] = self.pub_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'FeedItem':
        """딕셔너리로부터 인스턴스 생성"""
        return cls(**data)


@dataclass
class FilterStats:
    """필터링 통계"""
    total_processed: int = 0
    new_items: int = 0
    duplicate_items: int = 0
    filtered_items: int = 0
    last_filter_time: Optional[datetime] = None

    def add_processed(self, count: int):
        """처리된 아이템 수 추가"""
        self.total_processed += count

    def add_new(self, count: int):
        """새로운 아이템 수 추가"""
        self.new_items += count

    def add_duplicate(self, count: int):
        """중복 아이템 수 추가"""
        self.duplicate_items += count

    def add_filtered(self, count: int):
        """필터링된 아이템 수 추가"""
        self.filtered_items += count

    def update_filter_time(self):
        """필터링 시간 업데이트"""
        self.last_filter_time = datetime.now()


# ============================================================================
# 데이터베이스 관리자
# ============================================================================

class FeedDatabase:
    """피드 데이터베이스 관리자"""

    def __init__(self, db_path: str = "feed_cache.db"):
        """
        데이터베이스 관리자 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """데이터베이스 연결 컨텍스트 매니저"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self):
        """데이터베이스 테이블 초기화"""
        with self._get_connection() as conn:
            # 피드 아이템 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS feed_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hash TEXT UNIQUE NOT NULL,
                    link TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    pub_date TEXT,
                    author TEXT,
                    category TEXT,
                    source TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    keyword TEXT
                )
            """)

            # 필터링 통계 테이블
            conn.execute("""
                CREATE TABLE IF NOT EXISTS filter_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    total_processed INTEGER DEFAULT 0,
                    new_items INTEGER DEFAULT 0,
                    duplicate_items INTEGER DEFAULT 0,
                    filtered_items INTEGER DEFAULT 0,
                    last_filter_time TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 인덱스 생성
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash
                ON feed_items(hash)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_link
                ON feed_items(link)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword
                ON feed_items(keyword)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pub_date
                ON feed_items(pub_date)
            """)

            conn.commit()

    def is_item_exists(self, item_hash: str) -> bool:
        """아이템 존재 여부 확인"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM feed_items WHERE hash = ?",
                (item_hash,)
            )
            return cursor.fetchone() is not None

    def save_item(self, item: FeedItem, keyword: str = "") -> bool:
        """
        아이템 저장

        Args:
            item: 피드 아이템
            keyword: 키워드

        Returns:
            저장 성공 여부 (중복인 경우 False)
        """
        item_hash = item.get_hash()

        # 이미 존재하는지 확인
        if self.is_item_exists(item_hash):
            return False

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO feed_items
                    (hash, link, title, description, pub_date, author,
                     category, source, content, keyword)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_hash,
                    item.link,
                    item.title,
                    item.description,
                    item.pub_date.isoformat() if item.pub_date else None,
                    item.author,
                    item.category,
                    item.source,
                    item.content,
                    keyword
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            # 중복 데이터 (경쟁 조건)
            return False

    def save_items_batch(self, items: List[FeedItem], keyword: str = "") -> int:
        """
        여러 아이템 일괄 저장

        Args:
            items: 피드 아이템 리스트
            keyword: 키워드

        Returns:
            실제로 저장된 아이템 수
        """
        saved_count = 0
        for item in items:
            if self.save_item(item, keyword):
                saved_count += 1
        return saved_count

    def get_all_hashes(self) -> Set[str]:
        """모든 아이템 해시 조회"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT hash FROM feed_items")
            return {row[0] for row in cursor.fetchall()}

    def get_items_by_keyword(self, keyword: str, limit: int = 100) -> List[Dict]:
        """키워드별 아이템 조회"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM feed_items
                WHERE keyword = ?
                ORDER BY pub_date DESC
                LIMIT ?
            """, (keyword, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_items(self, hours: int = 24, limit: int = 100) -> List[Dict]:
        """최근 아이템 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM feed_items
                WHERE datetime(pub_date) >= datetime(?)
                ORDER BY pub_date DESC
                LIMIT ?
            """, (cutoff_time.isoformat(), limit))

            return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_items(self, days: int = 30) -> int:
        """오래된 아이템 정리"""
        cutoff_time = datetime.now() - timedelta(days=days)

        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM feed_items
                WHERE datetime(pub_date) < datetime(?)
            """, (cutoff_time.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            logger.info(f"오래된 아이템 {deleted_count}개 정리 완료")
            return deleted_count

    def get_stats(self) -> Dict:
        """데이터베이스 통계 조회"""
        with self._get_connection() as conn:
            # 전체 아이템 수
            cursor = conn.execute("SELECT COUNT(*) FROM feed_items")
            total_items = cursor.fetchone()[0]

            # 키워드별 아이템 수
            cursor = conn.execute("""
                SELECT keyword, COUNT(*) as count
                FROM feed_items
                GROUP BY keyword
            """)
            items_by_keyword = {row[0]: row[1] for row in cursor.fetchall()}

            # 최근 아이템 수 (24시간 이내)
            cursor = conn.execute("""
                SELECT COUNT(*) FROM feed_items
                WHERE datetime(pub_date) >= datetime('now', '-1 day')
            """)
            recent_items = cursor.fetchone()[0]

            return {
                'total_items': total_items,
                'items_by_keyword': items_by_keyword,
                'recent_items_24h': recent_items
            }


# ============================================================================
# 피드 필터링 엔진
# ============================================================================

class FeedFilter:
    """피드 필터링 엔진"""

    def __init__(self,
                 db_path: str = "feed_cache.db",
                 auto_cleanup: bool = True,
                 cleanup_days: int = 30):
        """
        피드 필터 초기화

        Args:
            db_path: 데이터베이스 경로
            auto_cleanup: 자동 정리 여부
            cleanup_days: 정리 기간 (일)
        """
        self.db = FeedDatabase(db_path)
        self.auto_cleanup = auto_cleanup
        self.cleanup_days = cleanup_days
        self.stats: Dict[str, FilterStats] = {}

    def filter_new_items(self,
                        items: List[FeedItem],
                        keyword: str = "") -> tuple[List[FeedItem], FilterStats]:
        """
        새로운 아이템 필터링

        Args:
            items: 필터링할 아이템 리스트
            keyword: 키워드

        Returns:
            (새로운 아이템 리스트, 필터링 통계)
        """
        # 통계 초기화
        stats_key = keyword or "default"
        if stats_key not in self.stats:
            self.stats[stats_key] = FilterStats()

        filter_stats = self.stats[stats_key]
        filter_stats.add_processed(len(items))

        # 새로운 아이템 필터링
        new_items = []
        duplicate_items = []

        existing_hashes = self.db.get_all_hashes()

        for item in items:
            item_hash = item.get_hash()
            if item_hash not in existing_hashes:
                new_items.append(item)
                # 데이터베이스에 저장
                self.db.save_item(item, keyword)
            else:
                duplicate_items.append(item)

        # 통계 업데이트
        filter_stats.add_new(len(new_items))
        filter_stats.add_duplicate(len(duplicate_items))
        filter_stats.update_filter_time()

        logger.info(f"필터링 완료 ({keyword}): 새로운 {len(new_items)}개, 중복 {len(duplicate_items)}개")

        # 자동 정리
        if self.auto_cleanup:
            self._cleanup_if_needed()

        return new_items, filter_stats

    def filter_new_items_from_dict(self,
                                   data_list: List[Dict],
                                   keyword: str = "") -> tuple[List[FeedItem], FilterStats]:
        """
        딕셔너리 리스트로부터 새로운 아이템 필터링

        Args:
            data_list: 데이터 딕셔너리 리스트
            keyword: 키워드

        Returns:
            (새로운 아이템 리스트, 필터링 통계)
        """
        # 딕셔너리를 FeedItem으로 변환
        items = []
        for data in data_list:
            try:
                item = FeedItem(
                    title=data.get('title', ''),
                    link=data.get('link', ''),
                    description=data.get('description', data.get('summary', '')),
                    pub_date=data.get('date'),
                    author=data.get('author', data.get('source', '')),
                    category=data.get('category', data.get('keyword', '')),
                    source=data.get('source', ''),
                    content=data.get('content', '')
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"아이템 변환 오류: {data}, {e}")

        return self.filter_new_items(items, keyword)

    def is_item_new(self, item: FeedItem) -> bool:
        """아이템이 새로운지 확인"""
        return not self.db.is_item_exists(item.get_hash())

    def get_stats(self, keyword: str = None) -> Dict:
        """필터링 통계 조회"""
        if keyword:
            if keyword in self.stats:
                stats = self.stats[keyword]
                return {
                    'keyword': keyword,
                    'total_processed': stats.total_processed,
                    'new_items': stats.new_items,
                    'duplicate_items': stats.duplicate_items,
                    'filtered_items': stats.filtered_items,
                    'last_filter_time': stats.last_filter_time.isoformat() if stats.last_filter_time else None
                }
            else:
                return {'keyword': keyword, 'message': 'No stats available'}
        else:
            # 전체 통계
            db_stats = self.db.get_stats()
            return {
                'database_stats': db_stats,
                'filter_stats': {
                    keyword: {
                        'total_processed': stats.total_processed,
                        'new_items': stats.new_items,
                        'duplicate_items': stats.duplicate_items,
                        'filtered_items': stats.filtered_items,
                        'last_filter_time': stats.last_filter_time.isoformat() if stats.last_filter_time else None
                    }
                    for keyword, stats in self.stats.items()
                }
            }

    def _cleanup_if_needed(self):
        """필요시 정리 실행"""
        try:
            self.db.cleanup_old_items(self.cleanup_days)
        except Exception as e:
            logger.warning(f"자동 정리 오류: {e}")

    def export_new_items(self,
                        items: List[FeedItem],
                        output_path: str,
                        format: str = 'json'):
        """
        새로운 아이템 내보내기

        Args:
            items: 내보낼 아이템 리스트
            output_path: 출력 경로
            format: 출력 형식 ('json' 또는 'txt')
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            data = [item.to_dict() for item in items]
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif format == 'txt':
            with open(output_file, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(f"제목: {item.title}\n")
                    f.write(f"링크: {item.link}\n")
                    f.write(f"설명: {item.description}\n")
                    if item.pub_date:
                        f.write(f"날짜: {item.pub_date.isoformat()}\n")
                    if item.author:
                        f.write(f"작성자: {item.author}\n")
                    f.write("-" * 80 + "\n\n")

        logger.info(f"아이템 내보내기 완료: {output_path} ({len(items)}개)")

    def reset_stats(self, keyword: str = None):
        """통계 리셋"""
        if keyword:
            if keyword in self.stats:
                self.stats[keyword] = FilterStats()
        else:
            self.stats = {}


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_filter_from_config(config: Dict) -> FeedFilter:
    """
    설정 딕셔너리로부터 필터 생성

    Args:
        config: 설정 딕셔너리

    Returns:
        FeedFilter 인스턴스
    """
    db_path = config.get('db_path', 'feed_cache.db')
    auto_cleanup = config.get('auto_cleanup', True)
    cleanup_days = config.get('cleanup_days', 30)

    return FeedFilter(
        db_path=db_path,
        auto_cleanup=auto_cleanup,
        cleanup_days=cleanup_days
    )


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 테스트 데이터 생성
    test_items = [
        FeedItem(
            title="AI 기술의 혁신",
            link="https://example.com/ai1",
            description="인공지능 기술이 새로운 전기를 맞이하고 있습니다.",
            pub_date="2026-04-29 10:00:00",
            author="테크미디어"
        ),
        FeedItem(
            title="블록체인의 미래",
            link="https://example.com/blockchain1",
            description="블록체인 기술이 금융 산업을 변화시키고 있습니다.",
            pub_date="2026-04-29 09:00:00",
            author="코인뉴스"
        )
    ]

    # 필터 생성 및 테스트
    filter_engine = FeedFilter(db_path="test_feed_cache.db")

    # 첫 번째 필터링 (모두 새로운 아이템)
    print("첫 번째 필터링:")
    new_items, stats = filter_engine.filter_new_items(test_items, "AI")
    print(f"새로운 아이템: {len(new_items)}개")

    # 두 번째 필터링 (모두 중복)
    print("\n두 번째 필터링:")
    new_items, stats = filter_engine.filter_new_items(test_items, "AI")
    print(f"새로운 아이템: {len(new_items)}개")

    # 통계 확인
    print("\n통계:")
    print(json.dumps(filter_engine.get_stats("AI"), indent=2))

    # 데이터베이스 통계
    print("\n데이터베이스 통계:")
    print(json.dumps(filter_engine.db.get_stats(), indent=2))