#!/usr/bin/env python3
"""
에러 핸들러
외부 서비스 연동 에러 처리, 로깅, 알림
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from .base_client import ServiceException


# 로깅 설정
logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """에러 컨텍스트"""
    service_name: str
    operation: str
    error: Exception
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'service': self.service_name,
            'operation': self.operation,
            'error': str(self.error),
            'error_type': type(self.error).__name__,
            'timestamp': self.timestamp,
            'details': self.details,
            'user_id': self.user_id,
            'request_id': self.request_id
        }


@dataclass
class ErrorSummary:
    """에러 요약"""
    total_errors: int = 0
    errors_by_service: Dict[str, int] = field(default_factory=dict)
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    recent_errors: List[ErrorContext] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_error(self, context: ErrorContext):
        """에러 추가"""
        self.total_errors += 1

        # 서비스별 에러 수
        service = context.service_name
        self.errors_by_service[service] = self.errors_by_service.get(service, 0) + 1

        # 에러 타입별 에러 수
        error_type = type(context.error).__name__
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        # 최근 에러 (최대 100개)
        self.recent_errors.append(context)
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)

        self.last_updated = datetime.now().isoformat()


class ErrorHandler:
    """에러 핸들러"""

    def __init__(self, enable_logging: bool = True,
                 enable_metrics: bool = True,
                 max_tracked_errors: int = 1000):
        """
        초기화

        Args:
            enable_logging: 로깅 활성화
            enable_metrics: 메트릭 활성화
            max_tracked_errors: 최대 추적 에러 수
        """
        self.enable_logging = enable_logging
        self.enable_metrics = enable_metrics
        self.max_tracked_errors = max_tracked_errors

        self.error_history: List[ErrorContext] = []
        self.error_summary = ErrorSummary()

        self.logger = logging.getLogger(f"{__name__}.ErrorHandler")

    def handle_error(
        self,
        error: Exception,
        service_name: str,
        operation: str,
        details: Optional[Dict] = None,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        raise_exception: bool = False
    ) -> Optional[Exception]:
        """
        에러 처리

        Args:
            error: 발생한 에러
            service_name: 서비스 이름
            operation: 작업 이름
            details: 추가 세부정보
            user_id: 사용자 ID
            request_id: 요청 ID
            raise_exception: 예외를 다시 발생시킬지 여부

        Returns:
            처리된 예외 (raise_exception=False인 경우)
        """
        # 에러 컨텍스트 생성
        context = ErrorContext(
            service_name=service_name,
            operation=operation,
            error=error,
            details=details or {},
            user_id=user_id,
            request_id=request_id
        )

        # 로깅
        if self.enable_logging:
            self._log_error(context)

        # 메트릭
        if self.enable_metrics:
            self._track_error(context)

        # 알림 (심각한 에러의 경우)
        if self._is_critical_error(error):
            self._send_alert(context)

        # 예외 재발생
        if raise_exception:
            raise error

        return error

    def _log_error(self, context: ErrorContext):
        """에러 로깅"""
        if isinstance(context.error, ServiceException):
            # 서비스 예외는 WARNING 수준
            self.logger.warning(
                f"[{context.service_name}] {context.operation}: {context.error}"
            )
        else:
            # 기타 예외는 ERROR 수준
            self.logger.error(
                f"[{context.service_name}] {context.operation}: {context.error}",
                exc_info=context.error
            )

    def _track_error(self, context: ErrorContext):
        """에러 추적"""
        # 이력에 추가
        self.error_history.append(context)

        # 최대 크기 제한
        if len(self.error_history) > self.max_tracked_errors:
            self.error_history = self.error_history[-self.max_tracked_errors:]

        # 요약 업데이트
        self.error_summary.add_error(context)

    def _is_critical_error(self, error: Exception) -> bool:
        """심각한 에러인지 확인"""
        # 인증 에러는 심각하지 않음 (클라이언트 오류이므로)
        if 'Authentication' in type(error).__name__:
            return False

        # 검증 에러는 심각하지 않음 (클라이언트 오류이므로)
        if 'Validation' in type(error).__name__:
            return False

        # 그 외 에러는 심각한 것으로 간주
        return True

    def _send_alert(self, context: ErrorContext):
        """알림 전송"""
        # 실제 구현에서는 Slack, 이메일 등으로 알림 전송
        self.logger.error(
            f"CRITICAL ERROR in {context.service_name}.{context.operation}: {context.error}"
        )

        # TODO: 실제 알림 시스템 연동
        # - Slack webhook
        # - Email notification
        # - PagerDuty 등

    def get_error_summary(self) -> ErrorSummary:
        """에러 요약 반환"""
        return self.error_summary

    def get_errors_by_service(self, service_name: str) -> List[ErrorContext]:
        """서비스별 에러 반환"""
        return [
            error for error in self.error_history
            if error.service_name == service_name
        ]

    def get_recent_errors(self, limit: int = 10) -> List[ErrorContext]:
        """최근 에러 반환"""
        return self.error_history[-limit:]

    def clear_history(self):
        """에러 이력 초기화"""
        self.error_history.clear()
        self.error_summary = ErrorSummary()
        self.logger.info("Error history cleared")

    def get_error_rate(self, service_name: Optional[str] = None,
                       minutes: int = 60) -> float:
        """
        에러율 계산

        Args:
            service_name: 서비스 이름 (None인 경우 전체)
            minutes: 계산 기간 (분)

        Returns:
            분당 에러 수
        """
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        relevant_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error.timestamp) >= cutoff_time
            and (service_name is None or error.service_name == service_name)
        ]

        return len(relevant_errors) / minutes


# 전역 에러 핸들러 인스턴스
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """전역 에러 핸들러 반환"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler
