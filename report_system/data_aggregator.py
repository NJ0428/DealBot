"""
데이터 수집 및 집계 모듈

기존 분석 시스템에서 데이터를 수집하고 집계합니다.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import pandas as pd
import pytz

logger = logging.getLogger(__name__)


@dataclass
class AggregatedData:
    """집계된 데이터 구조"""
    summary: Dict[str, Any]
    keyword_data: List[Dict[str, Any]]
    sentiment_data: Dict[str, Any]
    trend_data: Optional[pd.DataFrame] = None
    growth_metrics: Optional[Dict[str, Any]] = None
    custom_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_data is None:
            self.custom_data = {}


class DataAggregator:
    """데이터 수집 및 집계 클래스"""

    def __init__(self, timezone: str = "Asia/Seoul"):
        self.timezone = pytz.timezone(timezone)
        self.trend_analyzer = None
        self.sentiment_analyzer = None
        self.crawler = None

        # 지연 로드 방식으로 분석기 초기화
        self._initialize_analyzers()

    def _initialize_analyzers(self):
        """분석기 초기화 (지연 로드)"""
        try:
            from keyword_trend_analyzer import KeywordTrendAnalyzer
            self.trend_analyzer = KeywordTrendAnalyzer()
            logger.info("KeywordTrendAnalyzer 초기화 완료")
        except Exception as e:
            logger.warning(f"KeywordTrendAnalyzer 초기화 실패: {e}")

        try:
            from sentiment_analyzer import SentimentAnalyzer
            self.sentiment_analyzer = SentimentAnalyzer()
            logger.info("SentimentAnalyzer 초기화 완료")
        except Exception as e:
            logger.warning(f"SentimentAnalyzer 초기화 실패: {e}")

        try:
            from web_crawler import WebCrawler
            self.crawler = WebCrawler()
            logger.info("WebCrawler 초기화 완료")
        except Exception as e:
            logger.warning(f"WebCrawler 초기화 실패: {e}")

    def get_daily_data(self, date: datetime) -> AggregatedData:
        """일일 데이터 수집"""
        logger.info(f"일일 데이터 수집 시작: {date.date()}")

        # 타임존 변환
        if date.tzinfo is None:
            date = self.timezone.localize(date)

        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        # 기본 데이터 수집
        summary = self._collect_summary(start_date, end_date)
        keyword_data = self._collect_keyword_data(start_date, end_date)
        sentiment_data = self._collect_sentiment_data(start_date, end_date)

        return AggregatedData(
            summary=summary,
            keyword_data=keyword_data,
            sentiment_data=sentiment_data,
            trend_data=None,
            growth_metrics=None
        )

    def get_weekly_data(self, start_date: datetime, end_date: datetime) -> AggregatedData:
        """주간 데이터 수집"""
        logger.info(f"주간 데이터 수집 시작: {start_date.date()} ~ {end_date.date()}")

        # 타임존 변환
        if start_date.tzinfo is None:
            start_date = self.timezone.localize(start_date)
        if end_date.tzinfo is None:
            end_date = self.timezone.localize(end_date)

        # 데이터 수집
        summary = self._collect_summary(start_date, end_date)
        keyword_data = self._collect_keyword_data(start_date, end_date)
        sentiment_data = self._collect_sentiment_data(start_date, end_date)
        trend_data = self._collect_trend_data(start_date, end_date)
        growth_metrics = self._calculate_growth_metrics(start_date, end_date)

        return AggregatedData(
            summary=summary,
            keyword_data=keyword_data,
            sentiment_data=sentiment_data,
            trend_data=trend_data,
            growth_metrics=growth_metrics
        )

    def get_monthly_data(self, year: int, month: int) -> AggregatedData:
        """월간 데이터 수집"""
        logger.info(f"월간 데이터 수집 시작: {year}년 {month}월")

        # 월간 기간 설정
        start_date = self.timezone.localize(datetime(year, month, 1))
        if month == 12:
            end_date = self.timezone.localize(datetime(year + 1, 1, 1))
        else:
            end_date = self.timezone.localize(datetime(year, month + 1, 1))

        # 데이터 수집
        summary = self._collect_summary(start_date, end_date)
        keyword_data = self._collect_keyword_data(start_date, end_date)
        sentiment_data = self._collect_sentiment_data(start_date, end_date)
        trend_data = self._collect_trend_data(start_date, end_date)
        growth_metrics = self._calculate_growth_metrics(start_date, end_date)

        # 연간 비교 데이터 추가
        yearly_comparison = self._get_yearly_comparison(year, month)

        return AggregatedData(
            summary=summary,
            keyword_data=keyword_data,
            sentiment_data=sentiment_data,
            trend_data=trend_data,
            growth_metrics=growth_metrics,
            custom_data={"yearly_comparison": yearly_comparison}
        )

    def get_keyword_trends(self, keywords: List[str], period: str = "daily") -> pd.DataFrame:
        """키워드 트렌드 데이터 가져오기"""
        if not self.trend_analyzer:
            logger.warning("KeywordTrendAnalyzer가 초기화되지 않음")
            return pd.DataFrame()

        try:
            # 기간 설정
            end_date = datetime.now(self.timezone)
            if period == "daily":
                start_date = end_date - timedelta(days=7)
            elif period == "weekly":
                start_date = end_date - timedelta(weeks=4)
            elif period == "monthly":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)

            # 트렌드 분석
            trend_data = []
            for keyword in keywords:
                try:
                    # 키워드별 트렌드 분석 로직
                    keyword_data = {
                        'keyword': keyword,
                        'period': period,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                    trend_data.append(keyword_data)
                except Exception as e:
                    logger.error(f"키워드 '{keyword}' 트렌드 분석 실패: {e}")
                    continue

            return pd.DataFrame(trend_data)

        except Exception as e:
            logger.error(f"키워드 트렌드 데이터 수집 실패: {e}")
            return pd.DataFrame()

    def get_sentiment_summary(self, data: List[Dict]) -> Dict:
        """감성 분석 요약"""
        if not self.sentiment_analyzer:
            logger.warning("SentimentAnalyzer가 초기화되지 않음")
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_score': 0.0
            }

        try:
            sentiment_results = []
            for item in data:
                if 'text' in item:
                    try:
                        result = self.sentiment_analyzer.analyze(item['text'])
                        sentiment_results.append(result)
                    except Exception as e:
                        logger.error(f"감성 분석 실패: {e}")
                        continue

            if not sentiment_results:
                return self._get_empty_sentiment_summary()

            # 감성 분석 집계
            total = len(sentiment_results)
            positive = sum(1 for r in sentiment_results if r.label == 'positive')
            negative = sum(1 for r in sentiment_results if r.label == 'negative')
            neutral = sum(1 for r in sentiment_results if r.label == 'neutral')
            average_score = sum(r.sentiment_score for r in sentiment_results) / total

            return {
                'total': total,
                'positive': positive,
                'negative': negative,
                'neutral': neutral,
                'positive_rate': positive / total if total > 0 else 0,
                'negative_rate': negative / total if total > 0 else 0,
                'neutral_rate': neutral / total if total > 0 else 0,
                'average_score': average_score
            }

        except Exception as e:
            logger.error(f"감성 분석 요약 실패: {e}")
            return self._get_empty_sentiment_summary()

    def _collect_summary(self, start_date: datetime, end_date: datetime) -> Dict:
        """요약 데이터 수집"""
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'duration_days': (end_date - start_date).days
            },
            'generated_at': datetime.now(self.timezone).isoformat(),
            'timezone': str(self.timezone)
        }

    def _collect_keyword_data(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """키워드 데이터 수집"""
        # 실제 구현에서는 크롤러 또는 데이터베이스에서 데이터 가져오기
        # 여기서는 예시 데이터 반환
        return [
            {
                'keyword': 'AI',
                'count': 150,
                'growth_rate': 12.5,
                'sentiment': 'positive'
            },
            {
                'keyword': '데이터',
                'count': 120,
                'growth_rate': 8.3,
                'sentiment': 'neutral'
            }
        ]

    def _collect_sentiment_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """감성 데이터 수집"""
        # 실제 구현에서는 감성 분석기에서 데이터 가져오기
        return {
            'total_items': 500,
            'positive': 300,
            'negative': 100,
            'neutral': 100,
            'average_score': 0.4,
            'top_positive_words': ['혁신', '성장', '기회'],
            'top_negative_words': ['위험', '우려', '문제']
        }

    def _collect_trend_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """트렌드 데이터 수집"""
        if not self.trend_analyzer:
            return pd.DataFrame()

        try:
            # 실제 구현에서는 트렌드 분석기에서 데이터 가져오기
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            data = {
                'date': dates,
                'total_keywords': len(dates) * [100],
                'positive_sentiment': len(dates) * [60],
                'negative_sentiment': len(dates) * [20]
            }
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"트렌드 데이터 수집 실패: {e}")
            return pd.DataFrame()

    def _calculate_growth_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """성장 지표 계산"""
        try:
            # 이전 기간과 비교하여 성장률 계산
            period_length = (end_date - start_date).days
            previous_start = start_date - timedelta(days=period_length)
            previous_end = start_date

            # 성장 지표 (실제 구현에서는 데이터베이스에서 가져오기)
            return {
                'current_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'total_items': 500
                },
                'previous_period': {
                    'start': previous_start.isoformat(),
                    'end': previous_end.isoformat(),
                    'total_items': 450
                },
                'growth_rate': ((500 - 450) / 450) * 100,
                'growth_percentage': 11.11
            }
        except Exception as e:
            logger.error(f"성장 지표 계산 실패: {e}")
            return {}

    def _get_yearly_comparison(self, year: int, month: int) -> Dict:
        """연간 비교 데이터"""
        try:
            current_year_data = {
                'year': year,
                'month': month,
                'total_items': 500,
                'avg_sentiment': 0.4
            }

            # 작년 같은 달 데이터
            previous_year_data = {
                'year': year - 1,
                'month': month,
                'total_items': 420,
                'avg_sentiment': 0.35
            }

            # YoY 성장률
            yoy_growth = ((current_year_data['total_items'] - previous_year_data['total_items']) /
                         previous_year_data['total_items']) * 100

            return {
                'current_year': current_year_data,
                'previous_year': previous_year_data,
                'yoy_growth': yoy_growth,
                'sentiment_change': current_year_data['avg_sentiment'] - previous_year_data['avg_sentiment']
            }
        except Exception as e:
            logger.error(f"연간 비교 데이터 수집 실패: {e}")
            return {}

    def _get_empty_sentiment_summary(self) -> Dict:
        """빈 감성 분석 요약"""
        return {
            'total': 0,
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'positive_rate': 0.0,
            'negative_rate': 0.0,
            'neutral_rate': 0.0,
            'average_score': 0.0
        }

    def get_recent_items(self, limit: int = 10) -> List[Dict]:
        """최근 항목 가져오기"""
        # 실제 구현에서는 데이터베이스에서 최신 항목 가져오기
        return [
            {
                'title': '샘플 뉴스 제목',
                'url': 'https://example.com/news/1',
                'published_at': datetime.now(self.timezone).isoformat(),
                'summary': '샘플 뉴스 요약',
                'keywords': ['AI', '기술'],
                'sentiment': 'positive'
            }
        ] * limit