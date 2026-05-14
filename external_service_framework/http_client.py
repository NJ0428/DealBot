#!/usr/bin/env python3
"""
HTTP 클라이언트 구현
동기 및 비동기 HTTP 클라이언트 제공
"""

import time
import logging
from typing import Optional, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import aiohttp
    import asyncio
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .base_client import (
    BaseClient, ServiceConfig, ServiceResponse,
    ServiceException, HttpMethod
)
from .retry_mechanism import RetryPolicy


# 로깅 설정
logger = logging.getLogger(__name__)


class SyncHTTPClient(BaseClient):
    """동기 HTTP 클라이언트 (requests 기반)"""

    def __init__(self, config: ServiceConfig, service_name: str,
                 retry_policy: Optional[RetryPolicy] = None):
        """
        초기화

        Args:
            config: 서비스 설정
            service_name: 서비스 이름
            retry_policy: 재시도 정책
        """
        super().__init__(config, service_name)
        self.retry_policy = retry_policy or RetryPolicy()

        # 세션 생성
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """요청 세션 생성"""
        session = requests.Session()

        # 재시도 전략 설정
        retry_strategy = Retry(
            total=self.retry_policy.max_retries,
            backoff_factor=self.retry_policy.backoff_factor,
            status_forcelist=self.retry_policy.retryable_status_codes,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.max_connections if hasattr(self.config, 'max_connections') else 10,
            pool_maxsize=self.config.max_connections if hasattr(self.config, 'max_connections') else 10
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 프록시 설정
        if self.config.proxy:
            session.proxies = {
                "http": self.config.proxy,
                "https": self.config.proxy
            }

        return session

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
        HTTP 요청 수행

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
        try:
            # 설정 검증
            self.validate_config()

            # URL 및 헤더 구성
            url = self._build_url(endpoint)
            merged_headers = self._merge_headers(headers)

            # 메서드 변환
            if isinstance(method, str):
                method = HttpMethod(method.upper())

            # 요청 로깅
            self._log_request(method.value, url, data, params)

            # 요청 옵션 구성
            request_kwargs = {
                'headers': merged_headers,
                'params': params,
                'timeout': self.config.timeout,
                'verify': self.config.verify_ssl
            }

            # 데이터 처리
            if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH]:
                request_kwargs['json'] = data
            elif data:
                request_kwargs['data'] = data

            # 추가 옵션
            request_kwargs.update(kwargs)

            # 요청 수행
            start_time = time.time()
            response = self.session.request(
                method.value,
                url,
                **request_kwargs
            )
            elapsed_time = time.time() - start_time

            # 응답 처리
            return self._process_response(response, elapsed_time)

        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout error: {e}")
            return ServiceResponse(
                success=False,
                status_code=408,
                error=f"Request timeout: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Connection error: {e}")
            return ServiceResponse(
                success=False,
                status_code=503,
                error=f"Connection error: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            return ServiceResponse(
                success=False,
                status_code=500,
                error=f"Request error: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return ServiceResponse(
                success=False,
                status_code=500,
                error=f"Unexpected error: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

    def _process_response(self, response: requests.Response,
                         elapsed_time: float) -> ServiceResponse:
        """응답 처리"""
        # 헤더 추출
        headers = dict(response.headers)

        try:
            # JSON 응답 파싱
            if response.content:
                try:
                    data = response.json()
                except ValueError:
                    data = response.text
            else:
                data = None

            # 성공 응답
            if response.ok:
                service_response = ServiceResponse(
                    success=True,
                    status_code=response.status_code,
                    data=data,
                    headers=headers,
                    elapsed_time=elapsed_time
                )
                self._log_response(service_response)
                return service_response

            # 에러 응답
            else:
                error_message = self._extract_error_message(data)
                service_response = ServiceResponse(
                    success=False,
                    status_code=response.status_code,
                    data=data,
                    error=error_message,
                    headers=headers,
                    elapsed_time=elapsed_time
                )
                self._log_response(service_response)
                return service_response

        except Exception as e:
            self.logger.error(f"Response processing error: {e}")
            return ServiceResponse(
                success=False,
                status_code=response.status_code,
                error=f"Response processing error: {str(e)}",
                headers=headers,
                elapsed_time=elapsed_time
            )

    def _extract_error_message(self, data: Any) -> str:
        """에러 메시지 추출"""
        if isinstance(data, dict):
            # 다양한 에러 형식 처리
            if 'error' in data:
                if isinstance(data['error'], str):
                    return data['error']
                elif isinstance(data['error'], dict):
                    return data['error'].get('message', str(data['error']))
            elif 'message' in data:
                return data['message']
            elif 'detail' in data:
                return data['detail']

        return str(data) if data else "Unknown error"

    def close(self):
        """세션 종료"""
        if hasattr(self, 'session'):
            self.session.close()

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.close()


class AsyncHTTPClient(BaseClient):
    """비동기 HTTP 클라이언트 (aiohttp 기반)"""

    def __init__(self, config: ServiceConfig, service_name: str,
                 retry_policy: Optional[RetryPolicy] = None):
        """
        초기화

        Args:
            config: 서비스 설정
            service_name: 서비스 이름
            retry_policy: 재시도 정책
        """
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp 패키지가 설치되지 않았습니다")

        super().__init__(config, service_name)
        self.retry_policy = retry_policy or RetryPolicy()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """세션 가져오기 또는 생성"""
        if self.session is None or self.session.closed:
            # 커넥터 설정
            connector = aiohttp.TCPConnector(
                limit=self.config.max_connections if hasattr(self.config, 'max_connections') else 10,
                verify_ssl=self.config.verify_ssl
            )

            # 타임아웃 설정
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)

            # 세션 생성
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.config.get_default_headers()
            )

        return self.session

    async def request(
        self,
        method: Union[HttpMethod, str],
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> ServiceResponse:
        """
        비동기 HTTP 요청 수행

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
        try:
            # 설정 검증
            self.validate_config()

            # URL 및 헤더 구성
            url = self._build_url(endpoint)
            merged_headers = self._merge_headers(headers)

            # 메서드 변환
            if isinstance(method, str):
                method = HttpMethod(method.upper())

            # 요청 로깅
            self._log_request(method.value, url, data, params)

            # 세션 가져오기
            session = await self._get_session()

            # 요청 옵션 구성
            request_kwargs = {
                'headers': merged_headers,
                'params': params,
                'data': data if method in [HttpMethod.POST, HttpMethod.PUT, HttpMethod.PATCH] else None
            }

            # 추가 옵션
            request_kwargs.update(kwargs)

            # 요청 수행
            start_time = time.time()

            async with session.request(method.value, url, **request_kwargs) as response:
                elapsed_time = time.time() - start_time

                # 헤더 추출
                headers = dict(response.headers)

                # 응답 데이터 읽기
                response_data = None
                try:
                    if response.content_length and response.content_length > 0:
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                except Exception as e:
                    self.logger.warning(f"Failed to read response data: {e}")

                # 성공 여부 확인
                if response.ok:
                    service_response = ServiceResponse(
                        success=True,
                        status_code=response.status,
                        data=response_data,
                        headers=headers,
                        elapsed_time=elapsed_time
                    )
                else:
                    error_message = self._extract_error_message(response_data)
                    service_response = ServiceResponse(
                        success=False,
                        status_code=response.status,
                        data=response_data,
                        error=error_message,
                        headers=headers,
                        elapsed_time=elapsed_time
                    )

                self._log_response(service_response)
                return service_response

        except asyncio.TimeoutError as e:
            self.logger.error(f"Timeout error: {e}")
            return ServiceResponse(
                success=False,
                status_code=408,
                error=f"Request timeout: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

        except aiohttp.ClientError as e:
            self.logger.error(f"Client error: {e}")
            return ServiceResponse(
                success=False,
                status_code=503,
                error=f"Client error: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return ServiceResponse(
                success=False,
                status_code=500,
                error=f"Unexpected error: {str(e)}",
                elapsed_time=time.time() - start_time if 'start_time' in locals() else 0
            )

    def _extract_error_message(self, data: Any) -> str:
        """에러 메시지 추출"""
        if isinstance(data, dict):
            if 'error' in data:
                if isinstance(data['error'], str):
                    return data['error']
                elif isinstance(data['error'], dict):
                    return data['error'].get('message', str(data['error']))
            elif 'message' in data:
                return data['message']
            elif 'detail' in data:
                return data['detail']

        return str(data) if data else "Unknown error"

    async def close(self):
        """세션 종료"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
