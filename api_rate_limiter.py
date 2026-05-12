#!/usr/bin/env python3
"""
고급 Rate Limiting 시스템
Sliding Window 알고리즘 기반의 시간 기반 요청 제한
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from collections import deque
import os

# Redis 임포트 (선택적)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis 패키지를 찾을 수 없음. 메모리 기반이 사용됩니다.")

# 로깅 설정
logger = logging.getLogger(__name__)


@dataclass
class RateLimitPolicy:
    """Rate Limiting 정책"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_requests: int = 10  # 버스트 허용량

    def get_limit_for_window(self, window_seconds: int) -> int:
        """시간 윈도우에 따른 제한 반환"""
        if window_seconds <= 60:
            return self.requests_per_minute
        elif window_seconds <= 3600:
            return self.requests_per_hour
        else:
            return self.requests_per_day


class MemoryRateLimitStorage:
    """메모리 기반 Rate Limiting 저장소 (단일 서버용)"""

    def __init__(self):
        self.requests: Dict[str, deque] = {}
        self.locks: Dict[str, bool] = {}

    def add_request(self, key: str, timestamp: float):
        """요청 타임스탬프 추가"""
        if key not in self.requests:
            self.requests[key] = deque()
        self.requests[key].append(timestamp)

    def get_requests_in_window(self, key: str, window_start: float) -> List[float]:
        """윈도우 내 요청 타임스탬프 반환"""
        if key not in self.requests:
            return []

        # 윈도우 내 요청만 필터링
        return [ts for ts in self.requests[key] if ts >= window_start]

    def cleanup_old_requests(self, key: str, before_timestamp: float):
        """오래된 요청 제거"""
        if key in self.requests:
            self.requests[key] = deque(
                [ts for ts in self.requests[key] if ts >= before_timestamp]
            )

    def count_requests(self, key: str, window_start: float) -> int:
        """윈도우 내 요청 수 계산"""
        return len(self.get_requests_in_window(key, window_start))

    def reset(self, key: str):
        """특정 키의 요청 기록 초기화"""
        if key in self.requests:
            del self.requests[key]


class RedisRateLimitStorage:
    """Redis 기반 Rate Limiting 저장소 (분산 환경용)"""

    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis 패키지가 설치되지 않았습니다")

        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        self._test_connection()

    def _test_connection(self):
        """Redis 연결 테스트"""
        try:
            self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise

    def add_request(self, key: str, timestamp: float):
        """요청 타임스탬프 추가 (Sorted Set 활용)"""
        try:
            # ZADD: score는 타임스탬프, member는 타임스탬프 문자열
            self.redis_client.zadd(key, {str(timestamp): timestamp})
            # TTL 설정 (24시간)
            self.redis_client.expire(key, 86400)
        except Exception as e:
            logger.error(f"Redis add_request 실패: {e}")

    def get_requests_in_window(self, key: str, window_start: float) -> List[float]:
        """윈도우 내 요청 타임스탬프 반환"""
        try:
            # ZRANGEBYSCORE: window_start 이상의 모든 항목
            results = self.redis_client.zrangebyscore(
                key,
                window_start,
                float('inf'),
                withscores=False
            )
            return [float(ts) for ts in results]
        except Exception as e:
            logger.error(f"Redis get_requests_in_window 실패: {e}")
            return []

    def cleanup_old_requests(self, key: str, before_timestamp: float):
        """오래된 요청 제거 (ZREMRANGEBYSCORE 활용)"""
        try:
            # before_timestamp 미만인 항목 제거
            self.redis_client.zremrangebyscore(key, 0, before_timestamp)
        except Exception as e:
            logger.error(f"Redis cleanup_old_requests 실패: {e}")

    def count_requests(self, key: str, window_start: float) -> int:
        """윈도우 내 요청 수 계산 (ZCOUNT 활용)"""
        try:
            count = self.redis_client.zcount(key, window_start, float('inf'))
            return int(count)
        except Exception as e:
            logger.error(f"Redis count_requests 실패: {e}")
            return 0

    def reset(self, key: str):
        """특정 키의 요청 기록 초기화"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            logger.error(f"Redis reset 실패: {e}")


class SlidingWindowRateLimiter:
    """Sliding Window Rate Limiter"""

    # 시간 윈도우 상수
    WINDOW_MINUTE = 60
    WINDOW_HOUR = 3600
    WINDOW_DAY = 86400

    def __init__(self, storage: Optional[object] = None, use_redis: bool = True):
        """
        초기화

        Args:
            storage: RateLimitStorage 인스턴스 (None인 경우 자동 생성)
            use_redis: Redis 사용 여부 (True이면 Redis, False이면 메모리)
        """
        if storage:
            self.storage = storage
        else:
            # 자동으로 저장소 선택
            if use_redis and REDIS_AVAILABLE:
                try:
                    # 환경 변수에서 Redis 설정 읽기
                    redis_host = os.getenv('REDIS_HOST', 'localhost')
                    redis_port = int(os.getenv('REDIS_PORT', 6379))
                    redis_db = int(os.getenv('REDIS_DB', 0))

                    self.storage = RedisRateLimitStorage(
                        host=redis_host,
                        port=redis_port,
                        db=redis_db
                    )
                    logger.info("Redis 기반 Rate Limiter 사용")
                except Exception as e:
                    logger.warning(f"Redis 연결 실패: {e}, 메모리 기반 전환")
                    self.storage = MemoryRateLimitStorage()
            else:
                self.storage = MemoryRateLimitStorage()
                logger.info("메모리 기반 Rate Limiter 사용")

        # 기본 정책
        self.default_policy = RateLimitPolicy()

    def _make_key(self, key_id: str, endpoint: str = 'default') -> str:
        """Redis/Storage 키 생성"""
        return f"rate_limit:{key_id}:{endpoint}"

    def _cleanup_old_entries(self, key: str, window_seconds: int):
        """오래된 엔트리 정리"""
        now = time.time()
        window_start = now - window_seconds
        self.storage.cleanup_old_requests(key, window_start)

    def record_request(
        self,
        key_id: str,
        endpoint: str = 'default',
        policy: Optional[RateLimitPolicy] = None
    ) -> Tuple[bool, Dict]:
        """
        요청 기록 및 제한 확인

        Args:
            key_id: API 키 ID
            endpoint: 엔드포인트 이름
            policy: Rate Limiting 정책 (None인 경우 기본 정책 사용)

        Returns:
            (허용_여부, 정보_딕셔너리)
        """
        policy = policy or self.default_policy
        key = self._make_key(key_id, endpoint)
        now = time.time()

        # 시간 윈도우별 체크
        windows = [
            (self.WINDOW_MINUTE, policy.requests_per_minute, "minute"),
            (self.WINDOW_HOUR, policy.requests_per_hour, "hour"),
            (self.WINDOW_DAY, policy.requests_per_day, "day")
        ]

        for window_seconds, limit, window_name in windows:
            window_start = now - window_seconds
            count = self.storage.count_requests(key, window_start)

            if count >= limit:
                # 제한 초과
                reset_time = now + window_seconds - (now - window_start)
                return False, {
                    'allowed': False,
                    'limit': limit,
                    'remaining': 0,
                    'reset': int(reset_time),
                    'window': window_name,
                    'current_count': count,
                    'retry_after': int(window_seconds - (now - window_start))
                }

        # 제한 내에 있음 - 요청 기록
        self.storage.add_request(key, now)

        # 정리 주기적으로 실행 (매 100번째 요청마다)
        count = self.storage.count_requests(key, now - self.WINDOW_DAY)
        if count % 100 == 0:
            self._cleanup_old_entries(key, self.WINDOW_DAY)

        # 남은 횟수 계산
        minute_remaining = max(0, policy.requests_per_minute -
                             self.storage.count_requests(key, now - self.WINDOW_MINUTE))
        hour_remaining = max(0, policy.requests_per_hour -
                            self.storage.count_requests(key, now - self.WINDOW_HOUR))
        day_remaining = max(0, policy.requests_per_day -
                           self.storage.count_requests(key, now - self.WINDOW_DAY))

        return True, {
            'allowed': True,
            'limits': {
                'minute': {'limit': policy.requests_per_minute, 'remaining': minute_remaining},
                'hour': {'limit': policy.requests_per_hour, 'remaining': hour_remaining},
                'day': {'limit': policy.requests_per_day, 'remaining': day_remaining}
            },
            'current_count': count + 1
        }

    def get_remaining_requests(
        self,
        key_id: str,
        endpoint: str = 'default',
        policy: Optional[RateLimitPolicy] = None
    ) -> Dict:
        """현재 남은 요청 횟수 반환"""
        policy = policy or self.default_policy
        key = self._make_key(key_id, endpoint)
        now = time.time()

        return {
            'minute': {
                'limit': policy.requests_per_minute,
                'remaining': max(0, policy.requests_per_minute -
                           self.storage.count_requests(key, now - self.WINDOW_MINUTE)),
                'reset': int(now + self.WINDOW_MINUTE)
            },
            'hour': {
                'limit': policy.requests_per_hour,
                'remaining': max(0, policy.requests_per_hour -
                           self.storage.count_requests(key, now - self.WINDOW_HOUR)),
                'reset': int(now + self.WINDOW_HOUR)
            },
            'day': {
                'limit': policy.requests_per_day,
                'remaining': max(0, policy.requests_per_day -
                           self.storage.count_requests(key, now - self.WINDOW_DAY)),
                'reset': int(now + self.WINDOW_DAY)
            }
        }

    def reset_usage(self, key_id: str, endpoint: str = 'default'):
        """사용량 초기화"""
        key = self._make_key(key_id, endpoint)
        self.storage.reset(key)
        logger.info(f"Rate limit 초기화: {key_id} / {endpoint}")

    def get_stats(self, key_id: str, endpoint: str = 'default') -> Dict:
        """Rate Limiting 통계"""
        key = self._make_key(key_id, endpoint)
        now = time.time()

        minute_count = self.storage.count_requests(key, now - self.WINDOW_MINUTE)
        hour_count = self.storage.count_requests(key, now - self.WINDOW_HOUR)
        day_count = self.storage.count_requests(key, now - self.WINDOW_DAY)

        return {
            'key_id': key_id,
            'endpoint': endpoint,
            'requests': {
                'last_minute': minute_count,
                'last_hour': hour_count,
                'last_day': day_count
            },
            'timestamp': datetime.now().isoformat()
        }


# 전역 인스턴스
_rate_limiter_instance = None

def get_rate_limiter() -> SlidingWindowRateLimiter:
    """전역 Rate Limiter 인스턴스 반환"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = SlidingWindowRateLimiter()
    return _rate_limiter_instance


class RateLimitMiddleware:
    """Rate Limiting 미들웨어"""

    def __init__(self, rate_limiter: SlidingWindowRateLimiter):
        self.rate_limiter = rate_limiter

    def check_rate_limit(
        self,
        key_id: str,
        endpoint: str = 'default',
        policy: Optional[RateLimitPolicy] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Rate Limiting 체크

        Returns:
            (허용_여부, 응답_정보)
        """
        allowed, info = self.rate_limiter.record_request(
            key_id=key_id,
            endpoint=endpoint,
            policy=policy
        )

        if not allowed:
            error_response = {
                'error': 'Rate limit exceeded',
                'message': f'Rate limit of {info["limit"]} requests per {info["window"]} exceeded',
                'retry_after': info['retry_after'],
                'reset_at': info['reset']
            }
            return False, error_response

        return True, {
            'X-RateLimit-Limit-Minute': info['limits']['minute']['limit'],
            'X-RateLimit-Remaining-Minute': info['limits']['minute']['remaining'],
            'X-RateLimit-Limit-Hour': info['limits']['hour']['limit'],
            'X-RateLimit-Remaining-Hour': info['limits']['hour']['remaining'],
            'X-RateLimit-Limit-Day': info['limits']['day']['limit'],
            'X-RateLimit-Remaining-Day': info['limits']['day']['remaining'],
        }

    def get_rate_limit_info(self, key_id: str, endpoint: str = 'default') -> Dict:
        """현재 Rate Limiting 정보 반환"""
        return self.rate_limiter.get_remaining_requests(key_id, endpoint)

    def reset_user_limit(self, key_id: str, endpoint: str = 'default'):
        """사용자 제한 초기화"""
        self.rate_limiter.reset_usage(key_id, endpoint)


# 티어별 정책 프리셋
RATE_LIMIT_POLICIES = {
    'free': RateLimitPolicy(
        requests_per_minute=10,
        requests_per_hour=100,
        requests_per_day=1000
    ),
    'basic': RateLimitPolicy(
        requests_per_minute=30,
        requests_per_hour=500,
        requests_per_day=5000
    ),
    'pro': RateLimitPolicy(
        requests_per_minute=60,
        requests_per_hour=1000,
        requests_per_day=10000
    ),
    'enterprise': RateLimitPolicy(
        requests_per_minute=120,
        requests_per_hour=5000,
        requests_per_day=50000
    )
}


def get_policy_for_tier(tier: str) -> RateLimitPolicy:
    """티어에 따른 정책 반환"""
    return RATE_LIMIT_POLICIES.get(tier.lower(), RATE_LIMIT_POLICIES['basic'])
