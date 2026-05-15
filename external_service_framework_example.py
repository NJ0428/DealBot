#!/usr/bin/env python3
"""
외부 서비스 연동 프레임워크 사용 예시
"""

import sys
import os

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from external_service_framework import (
    SyncHTTPClient, AsyncHTTPClient,
    ServiceConfig, RetryPolicy, RetryStrategy,
    ErrorHandler, with_retry
)
import asyncio


def example_sync_client():
    """동기 HTTP 클라이언트 사용 예시"""
    print("=" * 60)
    print("동기 HTTP 클라이언트 예시")
    print("=" * 60)

    # 서비스 설정
    config = ServiceConfig(
        base_url="https://httpbin.org",
        timeout=10,
        user_agent="DealBot/1.0"
    )

    # 재시도 정책
    retry_policy = RetryPolicy(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=1.0
    )

    # 클라이언트 생성
    client = SyncHTTPClient(config, "httpbin", retry_policy)

    try:
        # GET 요청
        print("\n1. GET 요청:")
        response = client.get("/get", params={"param1": "value1"})
        print(f"성공: {response.success}")
        print(f"상태 코드: {response.status_code}")
        print(f"데이터: {response.data}")
        print(f"소요 시간: {response.elapsed_time:.2f}초")

        # POST 요청
        print("\n2. POST 요청:")
        response = client.post("/post", data={"key": "value"})
        print(f"성공: {response.success}")
        print(f"상태 코드: {response.status_code}")

        # 에러 처리
        print("\n3. 에러 처리 (404):")
        response = client.get("/status/404")
        print(f"성공: {response.success}")
        print(f"에러: {response.error}")

    finally:
        client.close()


async def example_async_client():
    """비동기 HTTP 클라이언트 사용 예시"""
    print("\n" + "=" * 60)
    print("비동기 HTTP 클라이언트 예시")
    print("=" * 60)

    # 서비스 설정
    config = ServiceConfig(
        base_url="https://httpbin.org",
        timeout=10
    )

    # 클라이언트 생성
    client = AsyncHTTPClient(config, "httpbin")

    try:
        # GET 요청
        print("\n1. 비동기 GET 요청:")
        response = await client.get("/get")
        print(f"성공: {response.success}")
        print(f"상태 코드: {response.status_code}")

        # POST 요청
        print("\n2. 비동기 POST 요청:")
        response = await client.post("/post", data={"test": "data"})
        print(f"성공: {response.success}")

    finally:
        await client.close()


def example_with_authentication():
    """인증이 필요한 API 예시"""
    print("\n" + "=" * 60)
    print("인증 API 예시")
    print("=" * 60)

    # API 키 인증 설정
    config = ServiceConfig(
        base_url="https://api.example.com",  # 예시 URL
        timeout=30,
        api_key_header="X-API-Key",
        api_key="your_api_key_here"
    )

    client = SyncHTTPClient(config, "api-example")

    try:
        # 인증이 필요한 엔드포인트 호출
        response = client.get("/v1/users")
        print(f"인증 요청: {response.success}")

    except Exception as e:
        print(f"에러 (예상됨): {e}")

    finally:
        client.close()


def example_error_handling():
    """에러 핸들링 예시"""
    print("\n" + "=" * 60)
    print("에러 핸들링 예시")
    print("=" * 60)

    # 에러 핸들러 생성
    error_handler = ErrorHandler()

    # 서비스 설정
    config = ServiceConfig(
        base_url="https://httpbin.org",
        timeout=5
    )

    client = SyncHTTPClient(config, "httpbin")

    try:
        # 정상 요청
        response = client.get("/get")
        error_handler.handle_error(
            error=None,
            service_name="httpbin",
            operation="GET /get"
        )

        # 에러 발생 요청
        response = client.get("/status/500")
        if not response.success:
            error_handler.handle_error(
                error=Exception(response.error),
                service_name="httpbin",
                operation="GET /status/500",
                details={"status_code": response.status_code}
            )

        # 에러 요약 출력
        summary = error_handler.get_error_summary()
        print(f"\n에러 요약:")
        print(f"총 에러 수: {summary.total_errors}")
        print(f"서비스별: {summary.errors_by_service}")

    finally:
        client.close()


def example_retry_decorator():
    """재시도 데코레이터 예시"""
    print("\n" + "=" * 60)
    print("재시도 데코레이터 예시")
    print("=" * 60)

    call_count = 0

    @with_retry(policy=RetryPolicy(
        max_retries=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF
    ))
    def unstable_function():
        nonlocal call_count
        call_count += 1
        print(f"시도 {call_count}...")

        if call_count < 3:
            raise ConnectionError("연결 실패")

        print("성공!")
        return "결과"

    try:
        result = unstable_function()
        print(f"최종 결과: {result}")
    except Exception as e:
        print(f"최대 재시도 초과: {e}")


def example_custom_service():
    """사용자 정의 서비스 연동 예시"""
    print("\n" + "=" * 60)
    print("사용자 정의 서비스 예시")
    print("=" * 60)

    # 사용자 정의 서비스 설정
    config = ServiceConfig(
        base_url="https://jsonplaceholder.typicode.com",
        timeout=15,
        headers={"Accept": "application/json"}
    )

    # 재시도 정책
    retry_policy = RetryPolicy(
        max_retries=2,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        base_delay=0.5
    )

    # 에러 핸들러
    error_handler = ErrorHandler()

    client = SyncHTTPClient(config, "jsonplaceholder", retry_policy)

    try:
        # 게시물 조회
        print("\n1. 게시물 조회:")
        response = client.get("/posts/1")
        if response.success:
            print(f"제목: {response.data['title']}")

        # 새 게시물 생성
        print("\n2. 새 게시물 생성:")
        new_post = {
            "title": "테스트 게시물",
            "body": "이것은 테스트입니다.",
            "userId": 1
        }
        response = client.post("/posts", data=new_post)
        if response.success:
            print(f"생성된 ID: {response.data['id']}")

        # 게시물 목록 조회
        print("\n3. 게시물 목록 조회:")
        response = client.get("/posts", params={"_limit": 5})
        if response.success:
            print(f"게시물 수: {len(response.data)}")

    except Exception as e:
        error_handler.handle_error(
            error=e,
            service_name="jsonplaceholder",
            operation="custom_operations"
        )

    finally:
        client.close()


def main():
    """메인 함수"""
    print("🚀 외부 서비스 연동 프레임워크 예시")

    # 동기 클라이언트
    example_sync_client()

    # 비동기 클라이언트 (asyncio 사용 가능한 경우)
    try:
        asyncio.run(example_async_client())
    except ImportError:
        print("\n⚠️  aiohttp가 설치되지 않아 비동기 예시를 건너뜁니다.")

    # 인증 예시
    example_with_authentication()

    # 에러 핸들링
    example_error_handling()

    # 재시도 데코레이터
    example_retry_decorator()

    # 사용자 정의 서비스
    example_custom_service()

    print("\n" + "=" * 60)
    print("✅ 모든 예시 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
