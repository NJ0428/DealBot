#!/usr/bin/env python3
"""
웹 주제 크롤러 및 Excel 저장 프로그램
특정 주제/키워드로 웹에서 정보를 수집하고 Excel 파일로 저장합니다.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import json
from requests.exceptions import RequestException, Timeout, HTTPError, ConnectionError


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


class WebCrawler:
    """웹 크롤러 클래스"""

    def __init__(self, base_url: str = "https://news.google.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.crawled_data: List[Dict[str, str]] = []

    def search_google_news(self, keyword: str, max_results: int = Config.DEFAULT_MAX_RESULTS) -> List[Dict[str, str]]:
        """
        Google News에서 키워드 검색 결과 크롤링

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수

        Returns:
            크롤링된 데이터 리스트
        """
        search_url = f"{self.base_url}/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            response = self.session.get(search_url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            articles: List[Dict[str, str]] = []
            article_count = 0

            # 뉴스 아티클 요소 찾기
            for article in soup.find_all('article'):
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

                    print(f"✓ {article_count}. {title[:Config.MAX_TITLE_DISPLAY_LENGTH]}...")

                except (AttributeError, KeyError, IndexError) as e:
                    print(f"⚠ 아티클 파싱 오류: {e}")
                    continue

            self.crawled_data.extend(articles)
            return articles

        except Timeout:
            print(f"❌ 요청 시간 초과: {search_url}")
            return []
        except HTTPError as e:
            print(f"❌ HTTP 오류: {e.response.status_code}")
            return []
        except ConnectionError:
            print(f"❌ 연결 오류: 인터넷 연결을 확인하세요")
            return []
        except RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return []

    def search_naver_blog(self, keyword: str, max_results: int = Config.DEFAULT_MAX_RESULTS) -> List[Dict[str, str]]:
        """
        네이버 블로그 검색 결과 크롤링

        Args:
            keyword: 검색 키워드
            max_results: 최대 결과 수

        Returns:
            크롤링된 데이터 리스트
        """
        search_url = "https://search.naver.com/search.naver"
        params: Dict[str, str] = {
            'where': 'view',
            'sm': 'tab_jum',
            'query': keyword
        }

        try:
            response = self.session.get(search_url, params=params, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            articles: List[Dict[str, str]] = []

            # 블로그 포스트 요소 찾기
            for post in soup.select('.view_wrap'):
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

                except (AttributeError, KeyError, IndexError) as e:
                    print(f"⚠ 포스트 파싱 오류: {e}")
                    continue

            self.crawled_data.extend(articles)
            return articles

        except Timeout:
            print(f"❌ 요청 시간 초과: {search_url}")
            return []
        except HTTPError as e:
            print(f"❌ HTTP 오류: {e.response.status_code}")
            return []
        except ConnectionError:
            print(f"❌ 연결 오류: 인터넷 연결을 확인하세요")
            return []
        except RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return []

    def crawl_custom_url(self, url: str, selector: Optional[str] = None) -> List[Dict[str, str]]:
        """
        사용자 정의 URL 크롤링

        Args:
            url: 크롤링할 URL
            selector: CSS 선택자 (선택사항)

        Returns:
            크롤링된 데이터 리스트
        """
        try:
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()

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
            return [article_data]

        except Timeout:
            print(f"❌ 요청 시간 초과: {url}")
            return []
        except HTTPError as e:
            print(f"❌ HTTP 오류: {e.response.status_code}")
            return []
        except ConnectionError:
            print(f"❌ 연결 오류: 인터넷 연결을 확인하세요")
            return []
        except RequestException as e:
            print(f"❌ 요청 오류: {e}")
            return []


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
    def save_to_excel(data: List[Dict[str, str]], filename: Optional[str] = None, sheet_name: str = "크롤링_결과") -> str:
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
            print("⚠ 저장할 데이터가 없습니다.")
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

            print(f"\n✅ Excel 파일 저장 완료: {filename}")
            print(f"   - 총 {len(data)}개 항목 저장됨")
            print(f"   - 시트명: {sheet_name}")

            return filename

        except (IOError, OSError) as e:
            print(f"❌ 파일 저장 오류: {e}")
            return ""
        except Exception as e:
            print(f"❌ Excel 저장 오류: {e}")
            return ""

    @staticmethod
    def save_multiple_sheets(data_dict: Dict[str, List[Dict[str, str]]], filename: Optional[str] = None) -> str:
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
            print(f"\n✅ Excel 파일 저장 완료: {filename}")
            print(f"   - 총 {len(data_dict)}개 시트, {total_items}개 항목")

            return filename

        except (IOError, OSError) as e:
            print(f"❌ 파일 저장 오류: {e}")
            return ""
        except Exception as e:
            print(f"❌ Excel 저장 오류: {e}")
            return ""


def main() -> None:
    """메인 함수 - 대화형 프로그램"""

    print("=" * 60)
    print("🕷️  웹 주제 크롤러 및 Excel 저장 프로그램")
    print("=" * 60)

    crawler = WebCrawler()
    exporter = ExcelExporter()

    # 크롤링 모드 선택
    print("\n[크롤링 모드 선택]")
    print("1. Google News 검색")
    print("2. 네이버 블로그 검색")
    print("3. 사용자 정의 URL 크롤링")
    print("4. 다중 키워드 검색 (Google News)")

    mode = input("\n모드를 선택하세요 (1-4): ").strip()

    all_data: Dict[str, List[Dict[str, str]]] = {}

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

        for keyword in keywords:
            print(f"\n🔍 '{keyword}' 검색 중...")
            data = crawler.search_google_news(keyword, max_results)

            if data:
                all_data[f"News_{keyword}"] = data

            time.sleep(Config.REQUEST_DELAY)  # 요청 간격

    else:
        print("❌ 잘못된 선택입니다.")
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


if __name__ == "__main__":
    main()
