#!/usr/bin/env python3
"""
재시도 메커니즘
다양한 재시도 전략 및 데코레이터 제공
"""

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Callable, Any, Type, Tuple
from functools import wraps
from enum import Enum


# 로깅 설정
logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """재시도 전략 열거형"""
    FIXED_DELAY = "fixed_delay"          # 고정 지연
    EXPONENTIAL_BACKOFF = "exponential"  # 지수 백오프
    LINEAR_BACKOFF = "linear"            # 선형 백오프
    IMMEDIATE = "immediate"              # 즉시 재시도


@dataclass
class RetryPolicy:
    """재시도 정책"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0  # 초
    max_delay: float = 60.0  # 초
    backoff_factor: float = 2.0
    jitter: bool = True  # 지연 시간에 무작위성 추가
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        OSError
    )
    retryable_status_codes: Tuple[int, ...] = (
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504  # Gateway Timeout
    )

    def calculate_delay(self, attempt: int) -> float:
        """재시도 지연 시간 계산"""
        if self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.backoff_factor ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * attempt
        elif self.strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        else:
            delay = self.base_delay

        # 최대 지연 제한
        delay = min(delay, self.max_delay)

        # 지터 추가 (무작위성)
        if self.jitter and delay > 0:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    def should_retry(self, exception: Exception) -> bool:
        """예외가 재시도 가능한지 확인"""
        return isinstance(exception, self.retryable_exceptions)

    def should_retry_status_code(self, status_code: int) -> bool:
        """상태 코드가 재시도 가능한지 확인"""
        return status_code in self.retryable_status_codes


class RetryableError(Exception):
    """재시도 가능한 에러"""
    pass


def with_retry(
    policy: Optional[RetryPolicy] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
):
    """
    재시도 데코레이터

    Args:
        policy: 재시도 정책
        on_retry: 재시도 시 호출할 콜백 함수

    Returns:
        데코레이터 함수

    사용 예시:
        ```python
        @with_retry()
        def fetch_data():
            # API 호출
            pass
        ```
    """
    if policy is None:
        policy = RetryPolicy()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, policy.max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    # 재시도 가능한 예외인지 확인
                    if not policy.should_retry(e):
                        logger.warning(
                            f"Non-retryable exception in {func.__name__}: {e}"
                        )
                        raise

                    # 마지막 시도면 재시도하지 않음
                    if attempt >= policy.max_retries:
                        logger.error(
                            f"Max retries ({policy.max_retries}) exceeded in {func.__name__}: {e}"
                        )
                        raise

                    # 지연 시간 계산
                    delay = policy.calculate_delay(attempt)

                    logger.warning(
                        f"Retry {attempt}/{policy.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {e}"
                    )

                    # 콜백 호출
                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            logger.error(
                                f"Error in retry callback: {callback_error}"
                            )

                    # 대기
                    time.sleep(delay)

            # 이론적으로 여기 도달하면 안 됨
            raise last_exception

        return wrapper
    return decorator


class RetryExecutor:
    """재시도 실행기"""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        """
        초기화

        Args:
            policy: 재시도 정책
        """
        self.policy = policy or RetryPolicy()
        self.logger = logging.getLogger(f"{__name__}.RetryExecutor")

    def execute(
        self,
        func: Callable,
        *args,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs
    ) -> Any:
        """
        재시도와 함께 함수 실행

        Args:
            func: 실행할 함수
            *args: 함수 인자
            on_retry: 재시도 시 콜백
            **kwargs: 함수 키워드 인자

        Returns:
            함수 결과
        """
        last_exception = None

        for attempt in range(1, self.policy.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # 재시도 가능한지 확인
                if not self.policy.should_retry(e):
                    self.logger.warning(
                        f"Non-retryable exception: {e}"
                    )
                    raise

                # 마지막 시도면 재시도하지 않음
                if attempt >= self.policy.max_retries:
                    self.logger.error(
                        f"Max retries exceeded: {e}"
                    )
                    raise

                # 지연 시간 계산
                delay = self.policy.calculate_delay(attempt)

                self.logger.warning(
                    f"Retry {attempt}/{self.policy.max_retries} "
                    f"after {delay:.2f}s: {e}"
                )

                # 콜백 호출
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception as callback_error:
                        self.logger.error(
                            f"Error in retry callback: {callback_error}"
                        )

                # 대기
                time.sleep(delay)

        raise last_exception


# 프리셋 정책
RETRY_POLICIES = {
    'conservative': RetryPolicy(
        max_retries=2,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=2.0,
        backoff_factor=2.0
    ),
    'moderate': RetryPolicy(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0,
        backoff_factor=2.0
    ),
    'aggressive': RetryPolicy(
        max_retries=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.5,
        backoff_factor=1.5
    ),
    'immediate': RetryPolicy(
        max_retries=3,
        strategy=RetryStrategy.IMMEDIATE
    )
}


def get_policy(name: str) -> RetryPolicy:
    """
    프리셋 정책 가져오기

    Args:
        name: 정책 이름 ('conservative', 'moderate', 'aggressive', 'immediate')

    Returns:
        RetryPolicy 객체
    """
    return RETRY_POLICIES.get(name.lower(), RETRY_POLICIES['moderate'])
