#!/usr/bin/env python3
"""
웹 주제 크롤러 및 Excel 저장 프로그램 (업그레이드 버전)
특정 주제/키워드로 웹에서 정보를 수집하고 Excel 파일로 저장합니다.

업그레이드 기능:
1. 결과 캐싱: 동일 키워드 검색 시 캐시 활용으로 속도 개선
2. 진행률 표시: 크롤링 진행 상황을 프로그레스 바로 시각화
3. 비동기 요청: aiohttp 활용으로 병렬 크롤링 지원
4. 프록시 지원: IP 차단 방지를 위한 프록시 로테이션
5. 로그 시스템: logging 모듈 도입으로 체계적인 로그 관리
6. 결과 필터링: 날짜 범위, 출처 등으로 결과 필터링 기능
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Callable
import json
import logging
import asyncio
import aiohttp
from pathlib import Path
from diskcache import Cache
from tqdm import tqdm
from requests.exceptions import RequestException, Timeout, HTTPError, ConnectionError
from dataclasses import dataclass, field


# ============================================================================
# 설정 및 로깅
# ============================================================================

class Config:
    """설정 상수"""
    # 요청 관련
    REQUEST_TIMEOUT: int = 10
    REQUEST_DELAY: float = 2.0

    # 결과 제한
    DEFAULT_MAX_RESULTS: int = 20
    DEFAULT_MAX_RESULTS_MULTIPLE: int = 10

    # 텍스트 처리 관련
    MIN_LINE_LENGTH: int = 50
    MAX_DESCRIPTION_LENGTH: int = 200
    MAX_CONTENT_PREVIEW_LENGTH: int = 500
    MAX_COLUMN_WIDTH: int = 50
    COLUMN_WIDTH_PADDING: int = 2

    # UI 관련
    MAX_TITLE_DISPLAY_LENGTH: int = 50

    # 캐싱 관련
    CACHE_DIR: str = ".cache"
    CACHE_EXPIRE_HOURS: int = 24

    # 프록시 관련
    PROXY_LIST_FILE: str = "proxies.txt"

    # 비동기 관련
    MAX_CONCURRENT_REQUESTS: int = 5

    # 로그 관련
    LOG_DIR: str = "logs"
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def setup_logging(log_dir: str = Config.LOG_DIR) -> logging.Logger:
    """
    로깅 시스템 설정

    Args:
        log_dir: 로그 파일 디렉토리

    Returns:
        설정된 로거 객체
    """
    # 로그 디렉토리 생성
    Path(log_dir).mkdir(exist_ok=True)

    # 로거 설정
    logger = logging.getLogger('WebCrawler')
    logger.setLevel(logging.DEBUG)

    # 파일 핸들러
    log_file = Path(log_dir) / f"crawler_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 포매터
    formatter = logging.Formatter(Config.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # 핸들러 추가
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# ============================================================================
# 결과 필터링
# ============================================================================

@dataclass
class FilterCriteria:
    """결과 필터링 기준"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    allowed_sources: Optional[Set[str]] = None
    blocked_sources: Optional[Set[str]] = None
    keywords_in_title: Optional[Set[str]] = None
    keywords_in_content: Optional[Set[str]] = None
    min_title_length: int = 0
    max_title_length: int = 9999


class ResultFilter:
    """결과 필터링 클래스"""

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """
        다양한 날짜 형식 파싱

        Args:
            date_str: 날짜 문자열

        Returns:
            datetime 객체 또는 None
        """
        if not date_str:
            return None

        # 다양한 날짜 형식 시도
        formats = [
            '%Y-%m-%d',
            '%Y.%m.%d',
            '%Y/%m/%d',
            '%Y년 %m월 %d일',
            '%Y%m%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        # 상대적 날짜 (예: "3일 전", "1주 전")
        if '일 전' in date_str:
            days = int(re.search(r'(\d+)일 전', date_str).group(1))
            return datetime.now() - timedelta(days=days)
        elif '주 전' in date_str:
            weeks = int(re.search(r'(\d+)주 전', date_str).group(1))
            return datetime.now() - timedelta(weeks=weeks)
        elif '시간 전' in date_str:
            hours = int(re.search(r'(\d+)시간 전', date_str).group(1))
            return datetime.now() - timedelta(hours=hours)

        return None

    @staticmethod
    def filter_by_date(data: List[Dict], start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict]:
        """
        날짜 범위로 필터링

        Args:
            data: 필터링할 데이터
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            필터링된 데이터
        """
        if not start_date and not end_date:
            return data

        filtered = []
        for item in data:
            # 다양한 날짜 필드 확인
            date_fields = ['날짜', '출처/날짜', '수집일시', 'date']
            item_date = None

            for field in date_fields:
                if field in item:
                    item_date = ResultFilter.parse_date(item[field])
                    if item_date:
                        break

            if item_date:
                if start_date and item_date < start_date:
                    continue
                if end_date and item_date > end_date:
                    continue

            filtered.append(item)

        return filtered

    @staticmethod
    def filter_by_source(data: List[Dict], allowed_sources: Optional[Set[str]] = None,
                         blocked_sources: Optional[Set[str]] = None) -> List[Dict]:
        """
        출처로 필터링

        Args:
            data: 필터링할 데이터
            allowed_sources: 허용할 출처 집합
            blocked_sources: 차단할 출처 집합

        Returns:
            필터링된 데이터
        """
        if not allowed_sources and not blocked_sources:
            return data

        filtered = []
        for item in data:
            # 다양한 출처 필드 확인
            source_fields = ['출처', '블로그', '출처/날짜', 'source']
            source = None

            for field in source_fields:
                if field in item and item[field]:
                    # 출처/날짜 같은 경우 출처만 추출
                    if field == '출처/날짜':
                        source = item[field].split('·')[0].strip() if '·' in item[field] else item[field]
                    else:
                        source = item[field]
                    break

            if not source:
                filtered.append(item)
                continue

            # 필터링 적용
            if allowed_sources and not any(allowed in source for allowed in allowed_sources):
                continue
            if blocked_sources and any(blocked in source for blocked in blocked_sources):
                continue

            filtered.append(item)

        return filtered

    @staticmethod
    def filter_by_keywords(data: List[Dict], keywords_in_title: Optional[Set[str]] = None,
                           keywords_in_content: Optional[Set[str]] = None) -> List[Dict]:
        """
        키워드로 필터링

        Args:
            data: 필터링할 데이터
            keywords_in_title: 제목에 포함되어야 할 키워드 집합
            keywords_in_content: 내용에 포함되어야 할 키워드 집합

        Returns:
            필터링된 데이터
        """
        if not keywords_in_title and not keywords_in_content:
            return data

        filtered = []
        for item in data:
            title = item.get('제목', '')
            content = item.get('요약', '')

            # 제목 필터링
            if keywords_in_title:
                if not any(keyword.lower() in title.lower() for keyword in keywords_in_title):
                    continue

            # 내용 필터링
            if keywords_in_content:
                if not any(keyword.lower() in content.lower() for keyword in keywords_in_content):
                    continue

            filtered.append(item)

        return filtered

    @staticmethod
    def filter_by_length(data: List[Dict], min_length: int = 0, max_length: int = 9999) -> List[Dict]:
        """
        제목 길이로 필터링

        Args:
            data: 필터링할 데이터
            min_length: 최소 길이
            max_length: 최대 길이

        Returns:
            필터링된 데이터
        """
        filtered = []
        for item in data:
            title = item.get('제목', '')
            if min_length <= len(title) <= max_length:
                filtered.append(item)

        return filtered

    @staticmethod
    def apply_filters(data: List[Dict], criteria: FilterCriteria) -> List[Dict]:
        """
        모든 필터 적용

        Args:
            data: 필터링할 데이터
            criteria: 필터링 기준

        Returns:
            필터링된 데이터
        """
        filtered = data

        # 날짜 필터링
        if criteria.start_date or criteria.end_date:
            filtered = ResultFilter.filter_by_date(filtered, criteria.start_date, criteria.end_date)
            logger.info(f"날짜 필터링 후: {len(filtered)}개 항목")

        # 출처 필터링
        if criteria.allowed_sources or criteria.blocked_sources:
            filtered = ResultFilter.filter_by_source(filtered, criteria.allowed_sources, criteria.blocked_sources)
            logger.info(f"출처 필터링 후: {len(filtered)}개 항목")

        # 키워드 필터링
        if criteria.keywords_in_title or criteria.keywords_in_content:
            filtered = ResultFilter.filter_by_keywords(filtered, criteria.keywords_in_title, criteria.keywords_in_content)
            logger.info(f"키워드 필터링 후: {len(filtered)}개 항목")

        # 길이 필터링
        if criteria.min_title_length > 0 or criteria.max_title_length < 9999:
            filtered = ResultFilter.filter_by_length(filtered, criteria.min_title_length, criteria.max_title_length)
            logger.info(f"길이 필터링 후: {len(filtered)}개 항목")

        return filtered


# ============================================================================
# 캐싱 시스템
# ============================================================================

class CacheManager:
    """캐시 관리 클래스"""

    def __init__(self, cache_dir: str = Config.CACHE_DIR, expire_hours: int = Config.CACHE_EXPIRE_HOURS):
        """
        캐시 매니저 초기화

        Args:
            cache_dir: 캐시 디렉토리
            expire_hours: 캐시 만료 시간 (시간)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache = Cache(str(self.cache_dir))
        self.expire_hours = expire_hours
        logger.info(f"캐시 시스템 초기화: {cache_dir}")

    def _generate_key(self, search_type: str, keyword: str, **kwargs) -> str:
        """
        캐시 키 생성

        Args:
            search_type: 검색 유형 (news, blog 등)
            keyword: 검색 키워드
            **kwargs: 추가 파라미터

        Returns:
            캐시 키
        """
        key_parts = [search_type, keyword]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)

    def get(self, search_type: str, keyword: str, **kwargs) -> Optional[List[Dict]]:
        """
        캐시된 결과 가져오기

        Args:
            search_type: 검색 유형
            keyword: 검색 키워드
            **kwargs: 추가 파라미터

        Returns:
            캐시된 데이터 또는 None
        """
        key = self._generate_key(search_type, keyword, **kwargs)
        cached = self.cache.get(key)

        if cached is not None:
            # 캐시 만료 확인
            cache_time = datetime.fromtimestamp(cached.get('timestamp', 0))
            if datetime.now() - cache_time < timedelta(hours=self.expire_hours):
                logger.info(f"캐시 적중: {key}")
                return cached.get('data')
            else:
                # 만료된 캐시 삭제
                self.cache.delete(key)
                logger.info(f"캐시 만료로 삭제: {key}")

        return None

    def set(self, search_type: str, keyword: str, data: List[Dict], **kwargs) -> None:
        """
        결과 캐싱

        Args:
            search_type: 검색 유형
            keyword: 검색 키워드
            data: 캐시할 데이터
            **kwargs: 추가 파라미터
        """
        key = self._generate_key(search_type, keyword, **kwargs)
        cache_value = {
            'timestamp': datetime.now().timestamp(),
            'data': data
        }
        self.cache.set(key, cache_value)
        logger.info(f"캐시 저장: {key} ({len(data)}개 항목)")

    def clear(self) -> None:
        """모든 캐시 삭제"""
        self.cache.clear()
        logger.info("모든 캐시 삭제 완료")

    def close(self) -> None:
        """캐시 닫기"""
        self.cache.close()


# ============================================================================
# 프록시 관리
# ============================================================================

class ProxyManager:
    """프록시 관리 클래스"""

    def __init__(self, proxy_file: str = Config.PROXY_LIST_FILE):
        """
        프록시 매니저 초기화

        Args:
            proxy_file: 프록시 리스트 파일 경로
        """
        self.proxy_file = Path(proxy_file)
        self.proxies: List[str] = []
        self.current_index = 0
        self._load_proxies()
        logger.info(f"프록시 매니저 초기화: {len(self.proxies)}개 프록시 로드됨")

    def _load_proxies(self) -> None:
        """프록시 리스트 파일에서 프록시 로드"""
        if self.proxy_file.exists():
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy and not proxy.startswith('#'):
                        self.proxies.append(proxy)
        else:
            logger.warning(f"프록시 파일을 찾을 수 없음: {self.proxy_file}")
            # 샘플 프록시 파일 생성
            self._create_sample_proxy_file()

    def _create_sample_proxy_file(self) -> None:
        """샘플 프록시 파일 생성"""
        sample_content = """# 프록시 리스트 파일
# 형식: http://user:pass@host:port 또는 http://host:port
# 예시:
# http://proxy1.example.com:8080
# http://user:password@proxy2.example.com:3128
# socks5://proxy3.example.com:1080
"""
        with open(self.proxy_file, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        logger.info(f"샘플 프록시 파일 생성: {self.proxy_file}")

    def get_next_proxy(self) -> Optional[str]:
        """
        다음 프록시 가져오기 (라운드 로빈)

        Returns:
            프록시 URL 또는 None
        """
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy

    def get_random_proxy(self) -> Optional[str]:
        """
        랜덤 프록시 가져오기

        Returns:
            프록시 URL 또는 None
        """
        if not self.proxies:
            return None
        import random
        return random.choice(self.proxies)


# ============================================================================
# 비동기 크롤러
# ============================================================================

class AsyncWebCrawler:
    """비동기 웹 크롤러 클래스"""

    def __init__(self, proxies: Optional[List[str]] = None, max_concurrent: int = Config.MAX_CONCURRENT_REQUESTS):
        """
        비동기 크롤러 초기화

        Args:
            proxies: 프록시 리스트
            max_concurrent: 최대 동시 요청 수
        """
        self.proxies = proxies or []
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"비동기 크롤러 초기화: 최대 {max_concurrent}개 동시 요청")

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str,
                          proxy: Optional[str] = None) -> Optional[str]:
        """
        비동기로 페이지 가져오기

        Args:
            session: aiohttp 세션
            url: 가져올 URL
            proxy: 프록시 URL

        Returns:
            페이지 HTML 또는 None
        """
        async with self.semaphore:
            try:
                timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
                async with session.get(url, proxy=proxy, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status}: {url}")
                        return None
            except asyncio.TimeoutError:
                logger.warning(f"요청 시간 초과: {url}")
                return None
            except Exception as e:
                logger.error(f"요청 오류 ({url}): {e}")
                return None

    async def search_multiple_keywords(self, keywords: List[str],
                                       search_func: Callable,
                                       max_results: int = Config.DEFAULT_MAX_RESULTS_MULTIPLE) -> Dict[str, List[Dict]]:
        """
        여러 키워드를 비동기로 검색

        Args:
            keywords: 검색할 키워드 리스트
            search_func: 검색 함수 (동기 함수여야 함)
            max_results: 최대 결과 수

        Returns:
            {키워드: 검색결과} 딕셔너리
        """
        results = {}

        # 진행률 표시
        with tqdm(total=len(keywords), desc="키워드 검색", unit="키워드") as pbar:
            async def search_keyword(keyword: str) -> tuple:
                # 동기 검색 함수를 스레드 풀에서 실행
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, search_func, keyword, max_results)
                pbar.update(1)
                return keyword, result

            # 모든 키워드 검색
            tasks = [search_keyword(keyword) for keyword in keywords]
            completed = await asyncio.gather(*tasks)

            for keyword, result in completed:
                results[keyword] = result

        return results


# ============================================================================
# 메인 크롤러 클래스
# ============================================================================

class WebCrawler:
    """웹 크롤러 클래스 (업그레이드 버전)"""

    def __init__(self, base_url: str = "https://news.google.com", use_cache: bool = True,
                 use_proxy: bool = False):
        """
        웹 크롤러 초기화

        Args:
            base_url: 기본 URL
            use_cache: 캐시 사용 여부
            use_proxy: 프록시 사용 여부
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.crawled_data: List[Dict[str, str]] = []

        # 캐시 매니저
        self.use_cache = use_cache
        self.cache_manager = CacheManager() if use_cache else None

        # 프록시 매니저
        self.use_proxy = use_proxy
        self.proxy_manager = ProxyManager() if use_proxy else None

        # 비동기 크롤러
        self.async_crawler = None
        if use_proxy and self.proxy_manager:
            self.async_crawler = AsyncWebCrawler(proxies=self.proxy_manager.proxies)

        logger.info(f"웹 크롤러 초기화 (캐시: {use_cache}, 프록시: {use_proxy})")

    def _get_proxy(self) -> Optional[Dict[str, str]]:
        """
        프록시 가져오기

        Returns:
            프록시 딕셔너리 또는 None
        """
        if not self.use_proxy or not self.proxy_manager:
            return None

        proxy_url = self.proxy_manager.get_next_proxy()
        if proxy_url:
            return {'http': proxy_url, 'https': proxy_url}
        return None

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        요청 수행 (프록시 지원)

        Args:
            url: 요청 URL
            params: 요청 파라미터

        Returns:
            응답 객체 또는 None
        """
        try:
            proxies = self._get_proxy()
            response = self.session.get(url, params=params, timeout=Config.REQUEST_TIMEOUT,
                                       proxies=proxies)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"요청 실패 ({url}): {e}")
            return None

    def search_google_news(self, keyword: str, max_results: int = Config.DEFAULT_MAX_RESULTS,
                           use_cache: Optional[bool] = None,
                           filter_criteria: Optional[FilterCriteria] = None) -> List[Dict[str, str]]:
        """
        Google News에서 키워드 검색 결과 크롤링

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수
            use_cache: 캐시 사용 여부 (None인 경우 초기 설정 사용)
            filter_criteria: 필터링 기준

        Returns:
            크롤링된 데이터 리스트
        """
        # 캐시 확인
        if use_cache is None:
            use_cache = self.use_cache

        if use_cache and self.cache_manager:
            cached = self.cache_manager.get('news', keyword, max_results=max_results)
            if cached is not None:
                logger.info(f"캐시된 결과 사용: {keyword}")
                return cached

        search_url = f"{self.base_url}/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

        response = self._make_request(search_url)
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        articles: List[Dict[str, str]] = []

        # 진행률 표시
        article_elements = soup.find_all('article')
        with tqdm(total=min(len(article_elements), max_results),
                 desc=f"Google News: {keyword}", unit="항목") as pbar:

            article_count = 0
            for article in article_elements:
                if article_count >= max_results:
                    break

                try:
                    # 제목 추출
                    title_elem = article.find('a', {'data-n-t': '1'}) or article.find('h3')
                    title = title_elem.get_text(strip=True) if title_elem else "제목 없음"

                    # 링크 추출
                    link_elem = article.find('a', {'data-n-t': '1'})
                    if link_elem and link_elem.get('href'):
                        link = link_elem['href']
                        if link.startswith('./'):
                            link = self.base_url + link[1:]
                    else:
                        link = "링크 없음"

                    # 요약 내용 추출
                    summary_elem = article.find('div', class_='OdIdWd')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    # 출처 및 날짜 추출
                    source_elem = article.find('div', class_='CEljJd')
                    source_date = source_elem.get_text(strip=True) if source_elem else ""

                    article_data: Dict[str, str] = {
                        '키워드': keyword,
                        '제목': title,
                        '요약': summary,
                        '출처/날짜': source_date,
                        '링크': link,
                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    articles.append(article_data)
                    article_count += 1

                    pbar.update(1)
                    pbar.set_postfix({"현재": f"{article_count}개"})

                except (AttributeError, KeyError, IndexError) as e:
                    logger.warning(f"아티클 파싱 오류: {e}")
                    continue

        # 필터링 적용
        if filter_criteria:
            articles = ResultFilter.apply_filters(articles, filter_criteria)

        # 캐시 저장
        if use_cache and self.cache_manager:
            self.cache_manager.set('news', keyword, articles, max_results=max_results)

        self.crawled_data.extend(articles)
        logger.info(f"Google News 검색 완료: {keyword} ({len(articles)}개 항목)")

        return articles

    def search_naver_blog(self, keyword: str, max_results: int = Config.DEFAULT_MAX_RESULTS,
                          use_cache: Optional[bool] = None,
                          filter_criteria: Optional[FilterCriteria] = None) -> List[Dict[str, str]]:
        """
        네이버 블로그 검색 결과 크롤링

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수
            use_cache: 캐시 사용 여부
            filter_criteria: 필터링 기준

        Returns:
            크롤링된 데이터 리스트
        """
        # 캐시 확인
        if use_cache is None:
            use_cache = self.use_cache

        if use_cache and self.cache_manager:
            cached = self.cache_manager.get('blog', keyword, max_results=max_results)
            if cached is not None:
                logger.info(f"캐시된 결과 사용: {keyword}")
                return cached

        search_url = "https://search.naver.com/search.naver"
        params: Dict[str, str] = {
            'where': 'view',
            'sm': 'tab_jum',
            'query': keyword
        }

        response = self._make_request(search_url, params)
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        articles: List[Dict[str, str]] = []

        # 진행률 표시
        post_elements = soup.select('.view_wrap')
        with tqdm(total=min(len(post_elements), max_results),
                 desc=f"네이버 블로그: {keyword}", unit="항목") as pbar:

            for post in post_elements[:max_results]:
                try:
                    # 제목 추출
                    title_elem = post.select_one('.title_link')
                    title = title_elem.get_text(strip=True) if title_elem else "제목 없음"
                    link = title_elem.get('href', '') if title_elem else ""

                    # 요약 추출
                    summary_elem = post.select_one('.dsc_link')
                    summary = summary_elem.get_text(strip=True) if summary_elem else ""

                    # 블로그 정보 추출
                    blog_info = post.select_one('.name')
                    blog_name = blog_info.get_text(strip=True) if blog_info else ""

                    # 날짜 추출
                    date_elem = post.select_one('.sub_time')
                    date_str = date_elem.get_text(strip=True) if date_elem else ""

                    article_data: Dict[str, str] = {
                        '키워드': keyword,
                        '제목': title,
                        '요약': summary,
                        '블로그': blog_name,
                        '날짜': date_str,
                        '링크': link,
                        '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    articles.append(article_data)
                    pbar.update(1)

                except (AttributeError, KeyError, IndexError) as e:
                    logger.warning(f"포스트 파싱 오류: {e}")
                    continue

        # 필터링 적용
        if filter_criteria:
            articles = ResultFilter.apply_filters(articles, filter_criteria)

        # 캐시 저장
        if use_cache and self.cache_manager:
            self.cache_manager.set('blog', keyword, articles, max_results=max_results)

        self.crawled_data.extend(articles)
        logger.info(f"네이버 블로그 검색 완료: {keyword} ({len(articles)}개 항목)")

        return articles

    def search_multiple_keywords(self, keywords: List[str],
                                 max_results: int = Config.DEFAULT_MAX_RESULTS_MULTIPLE,
                                 use_async: bool = False) -> Dict[str, List[Dict[str, str]]]:
        """
        여러 키워드 검색

        Args:
            keywords: 검색할 키워드 리스트
            max_results: 각 키워드당 최대 결과 수
            use_async: 비동기 검색 사용 여부

        Returns:
            {키워드: 검색결과} 딕셔너리
        """
        results = {}

        if use_async and self.async_crawler:
            # 비동기 검색
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(
                self.async_crawler.search_multiple_keywords(
                    keywords,
                    self.search_google_news,
                    max_results
                )
            )
        else:
            # 동기 검색 (진행률 표시 포함)
            with tqdm(total=len(keywords), desc="키워드 검색", unit="키워드") as pbar:
                for keyword in keywords:
                    logger.info(f"검색 시작: {keyword}")
                    data = self.search_google_news(keyword, max_results)
                    results[keyword] = data
                    pbar.update(1)
                    time.sleep(Config.REQUEST_DELAY)  # 요청 간격

        return results

    def crawl_custom_url(self, url: str, selector: Optional[str] = None) -> List[Dict[str, str]]:
        """
        사용자 정의 URL 크롤링

        Args:
            url: 크롤링할 URL
            selector: CSS 선택자 (선택사항)

        Returns:
            크롤링된 데이터 리스트
        """
        response = self._make_request(url)
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')

        # 페이지 제목
        page_title_elem = soup.find('title')
        page_title = page_title_elem.get_text(strip=True) if page_title_elem else url

        # 메타 데이터
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '') if meta_desc else ""

        # 본문 텍스트 추출
        if selector:
            elements = soup.select(selector)
            content = '\n'.join([elem.get_text(strip=True) for elem in elements])
        else:
            # 기본 본문 추출
            for tag in ['script', 'style', 'nav', 'header', 'footer']:
                for elem in soup.find_all(tag):
                    elem.decompose()
            content = soup.get_text(separator='\n', strip=True)
            content = '\n'.join(line for line in content.split('\n') if len(line) > Config.MIN_LINE_LENGTH)

        article_data: Dict[str, str] = {
            'URL': url,
            '페이지 제목': page_title,
            '설명': description[:Config.MAX_DESCRIPTION_LENGTH] if description else "",
            '본문 미리보기': content[:Config.MAX_CONTENT_PREVIEW_LENGTH] + '...' if len(content) > Config.MAX_CONTENT_PREVIEW_LENGTH else content,
            '수집일시': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        self.crawled_data.append(article_data)
        logger.info(f"사용자 정의 URL 크롤링 완료: {url}")

        return [article_data]

    def clear_cache(self) -> None:
        """캐시 비우기"""
        if self.cache_manager:
            self.cache_manager.clear()
            logger.info("캐시 비움")

    def close(self) -> None:
        """리소스 정리"""
        if self.cache_manager:
            self.cache_manager.close()
        self.session.close()
        logger.info("크롤러 리소스 정리 완료")


# ============================================================================
# Excel 익스포터
# ============================================================================

class ExcelExporter:
    """Excel 저장 클래스"""

    @staticmethod
    def _adjust_column_width(worksheet) -> None:
        """
        Excel 워크시트의 열 너비를 자동 조정

        Args:
            worksheet: openpyxl 워크시트 객체
        """
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except (AttributeError, TypeError):
                    pass
            adjusted_width = min(max_length + Config.COLUMN_WIDTH_PADDING, Config.MAX_COLUMN_WIDTH)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    @staticmethod
    def save_to_excel(data: List[Dict[str, str]], filename: Optional[str] = None,
                      sheet_name: str = "크롤링_결과") -> str:
        """
        크롤링 데이터를 Excel 파일로 저장

        Args:
            data: 저장할 데이터 리스트
            filename: 파일명 (지정하지 않으면 자동 생성)
            sheet_name: 시트명

        Returns:
            저장된 파일 경로
        """
        if not data:
            logger.warning("저장할 데이터가 없습니다.")
            return ""

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crawling_result_{timestamp}.xlsx"

        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        try:
            df = pd.DataFrame(data)

            # Excel 파일 생성
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # 워크시트 및 열 너비 자동 조정
                worksheet = writer.sheets[sheet_name]
                ExcelExporter._adjust_column_width(worksheet)

            logger.info(f"Excel 파일 저장 완료: {filename} ({len(data)}개 항목)")
            return filename

        except Exception as e:
            logger.error(f"Excel 저장 오류: {e}")
            return ""

    @staticmethod
    def save_multiple_sheets(data_dict: Dict[str, List[Dict[str, str]]],
                             filename: Optional[str] = None) -> str:
        """
        여러 시트에 데이터 저장

        Args:
            data_dict: {시트명: 데이터} 딕셔너리
            filename: 파일명

        Returns:
            저장된 파일 경로
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"crawling_result_{timestamp}.xlsx"

        if not filename.endswith('.xlsx'):
            filename += '.xlsx'

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for sheet_name, data in data_dict.items():
                    if data:
                        df = pd.DataFrame(data)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)

                        # 열 너비 자동 조정
                        worksheet = writer.sheets[sheet_name]
                        ExcelExporter._adjust_column_width(worksheet)

            total_items = sum(len(data) for data in data_dict.values())
            logger.info(f"Excel 파일 저장 완료: {filename} ({len(data_dict)}개 시트, {total_items}개 항목)")

            return filename

        except Exception as e:
            logger.error(f"Excel 저장 오류: {e}")
            return ""


# ============================================================================
# 메인 함수
# ============================================================================

def main() -> None:
    """메인 함수 - 대화형 프로그램"""

    print("=" * 60)
    print("🕷️  웹 주제 크롤러 및 Excel 저장 프로그램 (업그레이드 버전)")
    print("=" * 60)

    # 크롤러 설정
    print("\n[설정]")
    use_cache = input("캐시 사용? (y/n, 기본값: y): ").strip().lower() != 'n'
    use_proxy = input("프록시 사용? (y/n, 기본값: n): ").strip().lower() == 'y'

    crawler = WebCrawler(use_cache=use_cache, use_proxy=use_proxy)
    exporter = ExcelExporter()

    # 크롤링 모드 선택
    print("\n[크롤링 모드 선택]")
    print("1. Google News 검색")
    print("2. 네이버 블로그 검색")
    print("3. 사용자 정의 URL 크롤링")
    print("4. 다중 키워드 검색 (Google News)")
    print("5. 필터링 옵션 적용 검색")

    mode = input("\n모드를 선택하세요 (1-5): ").strip()

    all_data: Dict[str, List[Dict[str, str]]] = {}
    filter_criteria = None

    if mode == "1":
        # Google News 검색
        keyword = input("검색 키워드: ").strip()
        max_results_input = input(f"최대 결과 수 (기본값: {Config.DEFAULT_MAX_RESULTS}): ").strip()
        max_results = int(max_results_input) if max_results_input.isdigit() else Config.DEFAULT_MAX_RESULTS

        print(f"\n🔍 '{keyword}' 검색 중...")
        data = crawler.search_google_news(keyword, max_results)

        if data:
            all_data[f"News_{keyword}"] = data

    elif mode == "2":
        # 네이버 블로그 검색
        keyword = input("검색 키워드: ").strip()

        print(f"\n🔍 네이버 블로그 '{keyword}' 검색 중...")
        data = crawler.search_naver_blog(keyword)

        if data:
            all_data[f"Blog_{keyword}"] = data

    elif mode == "3":
        # 사용자 정의 URL
        url = input("크롤링할 URL: ").strip()
        selector_input = input("CSS 선택자 (선택사항, 엔터로 건너뜀): ").strip()
        selector = selector_input if selector_input else None

        print(f"\n🔍 URL 크롤링 중...")
        data = crawler.crawl_custom_url(url, selector)

        if data:
            all_data["Custom_URL"] = data

    elif mode == "4":
        # 다중 키워드 검색
        keywords_input = input("검색할 키워드들 (쉼표로 구분): ").strip()
        keywords = [k.strip() for k in keywords_input.split(',')]

        max_results_input = input(f"각 키워드당 최대 결과 수 (기본값: {Config.DEFAULT_MAX_RESULTS_MULTIPLE}): ").strip()
        max_results = int(max_results_input) if max_results_input.isdigit() else Config.DEFAULT_MAX_RESULTS_MULTIPLE

        use_async = input("비동기 검색 사용? (y/n, 기본값: n): ").strip().lower() == 'y'

        results = crawler.search_multiple_keywords(keywords, max_results, use_async)
        all_data.update({f"News_{k}": v for k, v in results.items()})

    elif mode == "5":
        # 필터링 옵션 적용 검색
        print("\n[필터링 옵션 설정]")
        keyword = input("검색 키워드: ").strip()

        # 날짜 필터
        start_date_str = input("시작 날짜 (YYYY-MM-DD, 엔터로 건너뜀): ").strip()
        end_date_str = input("종료 날짜 (YYYY-MM-DD, 엔터로 건너뜀): ").strip()

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

        # 출처 필터
        allowed_str = input("허용할 출처 (쉼표로 구분, 엔터로 건너뜀): ").strip()
        allowed_sources = set(allowed_str.split(',')) if allowed_str else None

        blocked_str = input("차단할 출처 (쉼표로 구분, 엔터로 건너뜀): ").strip()
        blocked_sources = set(blocked_str.split(',')) if blocked_str else None

        filter_criteria = FilterCriteria(
            start_date=start_date,
            end_date=end_date,
            allowed_sources=allowed_sources,
            blocked_sources=blocked_sources
        )

        print(f"\n🔍 '{keyword}' 검색 중 (필터 적용)...")
        data = crawler.search_google_news(keyword, Config.DEFAULT_MAX_RESULTS, filter_criteria=filter_criteria)

        if data:
            all_data[f"Filtered_{keyword}"] = data

    else:
        print("❌ 잘못된 선택입니다.")
        crawler.close()
        return

    # Excel 저장
    if all_data:
        print("\n" + "=" * 60)

        if len(all_data) == 1:
            # 단일 시트
            sheet_name, data = list(all_data.items())[0]
            filename_input = input("\n저장할 파일명 (엔터 시 자동 생성): ").strip()
            filename = filename_input if filename_input else None
            exporter.save_to_excel(data, filename, sheet_name)
        else:
            # 다중 시트
            filename_input = input("\n저장할 파일명 (엔터 시 자동 생성): ").strip()
            filename = filename_input if filename_input else None
            exporter.save_multiple_sheets(all_data, filename)

        print("\n✨ 프로그램 완료!")
    else:
        print("\n⚠ 수집된 데이터가 없습니다.")

    # 리소스 정리
    crawler.close()


if __name__ == "__main__":
    main()
