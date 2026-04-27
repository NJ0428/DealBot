#!/usr/bin/env python3
"""
RSS 피드 생성 모듈
수집한 뉴스/블로그 데이터를 RSS 2.0 형식으로 변환합니다.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging
from dataclasses import dataclass


# ============================================================================
# 설정 및 로깅
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================

@dataclass
class RSSFeedConfig:
    """RSS 피드 설정"""
    title: str
    description: str
    link: str
    language: str = "ko"
    managing_editor: str = ""
    web_master: str = ""
    category: str = ""


@dataclass
class RSSItem:
    """RSS 아이템 데이터 모델"""
    title: str
    link: str
    description: str
    pub_date: Optional[datetime] = None
    author: str = ""
    category: str = ""
    guid: str = ""
    source: str = ""
    content: str = ""  # 전체 내용 (content:encoded)


# ============================================================================
# RSS 피드 생성기
# ============================================================================

class RSSFeedGenerator:
    """RSS 2.0 피드 생성기"""

    def __init__(self, config: RSSFeedConfig):
        """
        RSS 피드 생성기 초기화

        Args:
            config: RSS 피드 설정
        """
        self.config = config

    def _create_rss_element(self) -> ET.Element:
        """RSS 루트 엘리먼트 생성"""
        rss = ET.Element("rss", version="2.0")
        rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
        rss.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        return rss

    def _create_channel_element(self, rss: ET.Element) -> ET.Element:
        """채널 엘리먼트 생성"""
        channel = ET.SubElement(rss, "channel")

        # 필수 엘리먼트
        title = ET.SubElement(channel, "title")
        title.text = self.config.title

        link = ET.SubElement(channel, "link")
        link.text = self.config.link

        description = ET.SubElement(channel, "description")
        description.text = self.config.description

        # 선택적 엘리먼트
        if self.config.language:
            language = ET.SubElement(channel, "language")
            language.text = self.config.language

        if self.config.managing_editor:
            managing_editor = ET.SubElement(channel, "managingEditor")
            managing_editor.text = self.config.managing_editor

        if self.config.web_master:
            web_master = ET.SubElement(channel, "webMaster")
            web_master.text = self.config.web_master

        # 현재 시간
        pub_date = ET.SubElement(channel, "lastBuildDate")
        pub_date.text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        if self.config.category:
            category = ET.SubElement(channel, "category")
            category.text = self.config.category

        # 생성기 정보
        generator = ET.SubElement(channel, "generator")
        generator.text = "DealBot RSS Feed Generator"

        return channel

    def _create_item_element(self, channel: ET.Element, item: RSSItem):
        """
        아이템 엘리먼트 생성

        Args:
            channel: 채널 엘리먼트
            item: RSS 아이템 데이터
        """
        item_elem = ET.SubElement(channel, "item")

        # 필수 엘리먼트
        title = ET.SubElement(item_elem, "title")
        title.text = item.title

        link = ET.SubElement(item_elem, "link")
        link.text = item.link

        description = ET.SubElement(item_elem, "description")
        description.text = item.description

        # 선택적 엘리먼트
        if item.pub_date:
            pub_date = ET.SubElement(item_elem, "pubDate")
            pub_date.text = item.pub_date.strftime("%a, %d %b %Y %H:%M:%S %z")

        if item.author:
            author = ET.SubElement(item_elem, "dc:creator")
            author.text = item.author

        if item.category:
            category = ET.SubElement(item_elem, "category")
            category.text = item.category

        if item.guid:
            guid = ET.SubElement(item_elem, "guid")
            guid.set("isPermaLink", "false")
            guid.text = item.guid
        else:
            guid = ET.SubElement(item_elem, "guid")
            guid.set("isPermaLink", "false")
            guid.text = item.link

        # 출처 정보
        if item.source:
            source = ET.SubElement(item_elem, "source")
            source.text = item.source

        # 전체 내용 (content:encoded)
        if item.content:
            content = ET.SubElement(item_elem, "content:encoded")
            content.text = item.content

    def generate_feed(self, items: List[RSSItem]) -> str:
        """
        RSS 피드 생성

        Args:
            items: RSS 아이템 리스트

        Returns:
            RSS XML 문자열
        """
        # RSS 엘리먼트 생성
        rss = self._create_rss_element()
        channel = self._create_channel_element(rss)

        # 아이템 추가
        for item in items:
            self._create_item_element(channel, item)

        # XML 포맷팅
        self._prettify(rss)

        # 문자열 변환
        return ET.tostring(rss, encoding="unicode", xml_declaration=True)

    def _prettify(self, elem: ET.Element):
        """XML 들여쓰기"""
        self._indent(elem)

    def _indent(self, elem: ET.Element, level: int = 0):
        """재귀적 들여쓰기"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def save_feed(self, items: List[RSSItem], output_path: str):
        """
        RSS 피드 생성 및 저장

        Args:
            items: RSS 아이템 리스트
            output_path: 출력 파일 경로
        """
        rss_xml = self.generate_feed(items)

        # 디렉토리 생성
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rss_xml)

        logger.info(f"RSS 피드 저장 완료: {output_path}")
        logger.info(f"총 {len(items)}개 아이템 포함")


# ============================================================================
# 데이터 변환 헬퍼
# ============================================================================

class WebCrawlerToRSSConverter:
    """웹 크롤러 데이터를 RSS 아이템으로 변환"""

    @staticmethod
    def convert_to_rss_items(crawled_data: List[Dict],
                            use_summary: bool = True,
                            max_description_length: int = 500) -> List[RSSItem]:
        """
        크롤링 데이터를 RSS 아이템 리스트로 변환

        Args:
            crawled_data: 크롤링 데이터 리스트
            use_summary: 요약 사용 여부
            max_description_length: 최대 설명 길이

        Returns:
            RSS 아이템 리스트
        """
        rss_items = []

        for data in crawled_data:
            # 제목 추출
            title = data.get('title', '제목 없음')

            # 링크 추출
            link = data.get('link', '')

            # 설명/요약 추출
            if use_summary:
                description = data.get('summary', data.get('description', ''))
            else:
                description = data.get('description', '')

            # 길이 제한
            if len(description) > max_description_length:
                description = description[:max_description_length] + "..."

            # 발행일 추출
            pub_date = None
            date_str = data.get('date')
            if date_str:
                try:
                    # 다양한 날짜 형식 처리
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                        "%a, %d %b %Y %H:%M:%S %z",
                        "%Y년 %m월 %d일"
                    ]:
                        try:
                            pub_date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.warning(f"날짜 파싱 오류: {date_str}, {e}")

            # 출처/작성자 추출
            source = data.get('source', data.get('author', ''))

            # 카테고리 추출
            category = data.get('category', data.get('keyword', ''))

            # GUID 생성 (링크 또는 해시)
            guid = link

            # 전체 내용 (content:encoded)
            content = data.get('content', data.get('summary', ''))

            # RSS 아이템 생성
            rss_item = RSSItem(
                title=title,
                link=link,
                description=description,
                pub_date=pub_date,
                author=source,
                category=category,
                guid=guid,
                source=source,
                content=content
            )

            rss_items.append(rss_item)

        # 날짜순 정렬 (최신순)
        rss_items.sort(key=lambda x: x.pub_date or datetime.min, reverse=True)

        return rss_items


# ============================================================================
# 멀티피드 생성기
# ============================================================================

class MultiFeedGenerator:
    """여러 키워드/주제의 피드를 개별적으로 생성"""

    def __init__(self, base_config: RSSFeedConfig):
        """
        멀티피드 생성기 초기화

        Args:
            base_config: 기본 피드 설정
        """
        self.base_config = base_config
        self.generators: Dict[str, RSSFeedGenerator] = {}

    def add_feed(self, keyword: str, title_override: str = None):
        """
        피드 추가

        Args:
            keyword: 키워드
            title_override: 제목 오버라이드
        """
        # 키워드별 제목 생성
        if title_override:
            title = title_override
        else:
            title = f"{self.base_config.title} - {keyword}"

        # 피드 설정
        config = RSSFeedConfig(
            title=title,
            description=f"{keyword} 관련 뉴스/블로그 피드",
            link=self.base_config.link,
            language=self.base_config.language
        )

        # 생성기 저장
        self.generators[keyword] = RSSFeedGenerator(config)
        logger.info(f"피드 추가됨: {keyword} -> {title}")

    def generate_feeds(self,
                      data_by_keyword: Dict[str, List[Dict]],
                      output_dir: str = "rss_feeds") -> Dict[str, str]:
        """
        여러 피드 생성 및 저장

        Args:
            data_by_keyword: 키워드별 데이터 딕셔너리
            output_dir: 출력 디렉토리

        Returns:
            키워드별 피드 파일 경로 딕셔너리
        """
        feed_paths = {}
        converter = WebCrawlerToRSSConverter()

        for keyword, data in data_by_keyword.items():
            # 피드 생성기가 없으면 추가
            if keyword not in self.generators:
                self.add_feed(keyword)

            # RSS 아이템 변환
            rss_items = converter.convert_to_rss_items(data)

            # 피드 파일 경로
            filename = f"{keyword}.xml"
            output_path = str(Path(output_dir) / filename)

            # 피드 생성 및 저장
            generator = self.generators[keyword]
            generator.save_feed(rss_items, output_path)

            feed_paths[keyword] = output_path

        return feed_paths

    def generate_combined_feed(self,
                              data_by_keyword: Dict[str, List[Dict]],
                              output_path: str = "rss_feeds/combined.xml"):
        """
        통합 피드 생성

        Args:
            data_by_keyword: 키워드별 데이터 딕셔너리
            output_path: 출력 파일 경로
        """
        converter = WebCrawlerToRSSConverter()
        all_items = []

        # 모든 데이터를 하나의 리스트로 변환
        for keyword, data in data_by_keyword.items():
            rss_items = converter.convert_to_rss_items(data)

            # 카테고리에 키워드 정보 추가
            for item in rss_items:
                if not item.category:
                    item.category = keyword
                all_items.append(item)

        # 날짜순 정렬 (최신순)
        all_items.sort(key=lambda x: x.pub_date or datetime.min, reverse=True)

        # 통합 피드 생성
        combined_config = RSSFeedConfig(
            title=f"{self.base_config.title} - 전체",
            description=f"전체 키워드 통합 뉴스/블로그 피드",
            link=self.base_config.link,
            language=self.base_config.language
        )

        generator = RSSFeedGenerator(combined_config)
        generator.save_feed(all_items, output_path)

        logger.info(f"통합 피드 생성 완료: {output_path} (총 {len(all_items)}개 아이템)")


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_feed_from_crawler_data(keyword: str,
                                  crawled_data: List[Dict],
                                  output_dir: str = "rss_feeds") -> str:
    """
    크롤러 데이터로부터 RSS 피드 생성 (유틸리티 함수)

    Args:
        keyword: 키워드
        crawled_data: 크롤링 데이터
        output_dir: 출력 디렉토리

    Returns:
        생성된 RSS 피드 파일 경로
    """
    # 피드 설정
    config = RSSFeedConfig(
        title=f"DealBot - {keyword}",
        description=f"{keyword} 관련 뉴스/블로그 피드",
        link="https://github.com/yourusername/DealBot",
        language="ko"
    )

    # RSS 아이템 변환
    converter = WebCrawlerToRSSConverter()
    rss_items = converter.convert_to_rss_items(crawled_data)

    # 피드 생성
    generator = RSSFeedGenerator(config)
    output_path = str(Path(output_dir) / f"{keyword}.xml")
    generator.save_feed(rss_items, output_path)

    return output_path


if __name__ == "__main__":
    # 테스트 코드
    from datetime import timedelta

    # 테스트 데이터 생성
    test_data = [
        {
            'title': 'AI 기술의 혁신',
            'link': 'https://example.com/ai1',
            'description': '인공지능 기술이 새로운 전기를 맞이하고 있습니다.',
            'date': '2026-04-26 10:00:00',
            'source': '테크미디어'
        },
        {
            'title': '블록체인의 미래',
            'link': 'https://example.com/blockchain1',
            'description': '블록체인 기술이 금융 산업을 변화시키고 있습니다.',
            'date': '2026-04-26 09:00:00',
            'source': '코인뉴스'
        },
        {
            'title': '메타버스 플랫폼 경쟁',
            'link': 'https://example.com/metaverse1',
            'description': '메타버스 플랫폼 간 경쟁이 치열해지고 있습니다.',
            'date': '2026-04-25 15:00:00',
            'source': 'VR타임즈'
        }
    ]

    # RSS 피드 생성
    feed_path = create_feed_from_crawler_data("AI", test_data)
    print(f"RSS 피드 생성 완료: {feed_path}")

    # 멀티피드 테스트
    multi_data = {
        "AI": test_data,
        "Blockchain": test_data,
        "Metaverse": test_data
    }

    base_config = RSSFeedConfig(
        title="DealBot Multi-Feed",
        description="다중 키워드 피드",
        link="https://github.com/yourusername/DealBot"
    )

    multi_gen = MultiFeedGenerator(base_config)
    feed_paths = multi_gen.generate_feeds(multi_data)
    print(f"생성된 피드: {feed_paths}")

    # 통합 피드 생성
    multi_gen.generate_combined_feed(multi_data)
