#!/usr/bin/env python3
"""
외부 서비스 연동 프레임워크 - 기본 클라이언트
재사용 가능한 HTTP 클라이언트 인터페이스 및 공통 기능 제공
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum


# 로깅 설정
logger = logging.getLogger(__name__)


class HttpMethod(Enum):
    """HTTP 메서드 열거형"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class ServiceConfig:
    """서비스 설정 데이터 클래스"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    headers: Dict[str, str] = field(default_factory=dict)
    auth_token: Optional[str] = None
    auth_header: str = "Authorization"
    api_key_header: Optional[str] = None
    api_key: Optional[str] = None
    proxy: Optional[str] = None
    user_agent: str = "DealBot/1.0"

    def get_auth_headers(self) -> Dict[str, str]:
        """인증 헤더 생성"""
        headers = {}

        if self.auth_token:
            headers[self.auth_header] = f"Bearer {self.auth_token}"

        if self.api_key and self.api_key_header:
            headers[self.api_key_header] = self.api_key

        return headers

    def get_default_headers(self) -> Dict[str, str]:
        """기본 헤더 반환"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        headers.update(self.headers)
        headers.update(self.get_auth_headers())
        return headers


@dataclass
class ServiceResponse:
    """서비스 응답 데이터 클래스"""
    success: bool
    status_code: int
    data: Any = None
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    elapsed_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'success': self.success,
            'status_code': self.status_code,
            'data': self.data,
            'error': self.error,
            'headers': self.headers,
            'elapsed_time': self.elapsed_time,
            'timestamp': self.timestamp
        }


class ServiceException(Exception):
    """서비스 예외 기본 클래스"""

    def __init__(self, service_name: str, message: str,
                 status_code: Optional[int] = None,
                 details: Optional[Dict] = None):
        self.service_name = service_name
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(f"[{service_name}] {message}")

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'service': self.service_name,
            'error': self.message,
            'status_code': self.status_code,
            'details': self.details
        }


class ConnectionError(ServiceException):
    """연결 오류"""

    def __init__(self, service_name: str, message: str,
                 details: Optional[Dict] = None):
        super().__init__(service_name, message, None, details)


class AuthenticationError(ServiceException):
    """인증 오류"""

    def __init__(self, service_name: str, message: str,
                 details: Optional[Dict] = None):
        super().__init__(service_name, message, 401, details)


class RateLimitError(ServiceException):
    """Rate Limit 오류"""

    def __init__(self, service_name: str, message: str,
                 retry_after: Optional[int] = None,
                 details: Optional[Dict] = None):
        self.retry_after = retry_after
        details = details or {}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(service_name, message, 429, details)


class ValidationError(ServiceException):
    """검증 오류"""

    def __init__(self, service_name: str, message: str,
                 details: Optional[Dict] = None):
        super().__init__(service_name, message, 400, details)


class BaseClient(ABC):
    """기본 클라이언트 추상 클래스"""

    def __init__(self, config: ServiceConfig, service_name: str):
        """
        초기화

        Args:
            config: 서비스 설정
            service_name: 서비스 이름 (로깅용)
        """
        self.config = config
        self.service_name = service_name
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

    @abstractmethod
    def request(
        self,
        method: Union[HttpMethod, str],
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> ServiceResponse:
        """
        HTTP 요청 수행 (추상 메서드)

        Args:
            method: HTTP 메서드
            endpoint: 엔드포인트 경로
            data: 요청 바디
            params: 쿼리 파라미터
            headers: 추가 헤더
            **kwargs: 추가 파라미터

        Returns:
            ServiceResponse 객체
        """
        pass

    def get(self, endpoint: str, params: Optional[Dict] = None,
            headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """GET 요청"""
        return self.request(HttpMethod.GET, endpoint, params=params,
                           headers=headers, **kwargs)

    def post(self, endpoint: str, data: Optional[Dict] = None,
             headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """POST 요청"""
        return self.request(HttpMethod.POST, endpoint, data=data,
                           headers=headers, **kwargs)

    def put(self, endpoint: str, data: Optional[Dict] = None,
            headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """PUT 요청"""
        return self.request(HttpMethod.PUT, endpoint, data=data,
                           headers=headers, **kwargs)

    def delete(self, endpoint: str, headers: Optional[Dict] = None,
               **kwargs) -> ServiceResponse:
        """DELETE 요청"""
        return self.request(HttpMethod.DELETE, endpoint,
                           headers=headers, **kwargs)

    def patch(self, endpoint: str, data: Optional[Dict] = None,
              headers: Optional[Dict] = None, **kwargs) -> ServiceResponse:
        """PATCH 요청"""
        return self.request(HttpMethod.PATCH, endpoint, data=data,
                           headers=headers, **kwargs)

    def _build_url(self, endpoint: str) -> str:
        """전체 URL 생성"""
        base_url = self.config.base_url.rstrip('/')
        endpoint = endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"

    def _merge_headers(self, headers: Optional[Dict] = None) -> Dict:
        """헤더 병합"""
        default_headers = self.config.get_default_headers()
        if headers:
            default_headers.update(headers)
        return default_headers

    def _log_request(self, method: str, url: str, data: Optional[Dict] = None,
                     params: Optional[Dict] = None):
        """요청 로깅"""
        self.logger.debug(f"Request: {method} {url}")
        if data:
            self.logger.debug(f"Data: {data}")
        if params:
            self.logger.debug(f"Params: {params}")

    def _log_response(self, response: ServiceResponse):
        """응답 로깅"""
        if response.success:
            self.logger.info(
                f"Success: {response.status_code} - {response.elapsed_time:.2f}s"
            )
        else:
            self.logger.error(
                f"Error: {response.status_code} - {response.error}"
            )

    def _handle_error(self, status_code: int, error_message: str,
                     details: Optional[Dict] = None) -> ServiceException:
        """에러 처리"""
        if status_code == 401:
            return AuthenticationError(self.service_name, error_message, details)
        elif status_code == 429:
            return RateLimitError(self.service_name, error_message,
                                details.get('retry_after') if details else None,
                                details)
        elif status_code == 400:
            return ValidationError(self.service_name, error_message, details)
        else:
            return ServiceException(self.service_name, error_message,
                                  status_code, details)

    def validate_config(self) -> bool:
        """설정 검증"""
        if not self.config.base_url:
            raise ValueError(f"base_url is required for {self.service_name}")

        if not self.config.base_url.startswith(('http://', 'https://')):
            raise ValueError(
                f"base_url must start with http:// or https:// for {self.service_name}"
            )

        if self.config.timeout <= 0:
            raise ValueError("timeout must be positive")

        return True
