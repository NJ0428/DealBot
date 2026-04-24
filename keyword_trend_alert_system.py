#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인기 급상승 키워드 탐지 및 알림 시스템

키워드 트렌드 분석 결과를 바탕으로 급상승 키워드를 탐지하고
이메일 알림을 발송합니다.
"""

import sys
import os

# UTF-8 출력 설정 (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict
import logging

import pandas as pd
import numpy as np


# ============================================================================
# 설정 및 로깅
# ============================================================================

class AlertConfig:
    """알림 시스템 설정"""

    # 급상승 기준
    MIN_FREQUENCY_THRESHOLD: int = 5        # 최소 빈도수
    GROWTH_RATE_THRESHOLD: float = 50.0     # 성장률 임계값 (%)
    RANK_JUMP_THRESHOLD: int = 5            # 순위 상승 최소 기준
    VOLATILITY_THRESHOLD: float = 2.0       # 변동성 계수

    # 알림 설정
    ALERT_COOLDOWN_MINUTES: int = 60        # 알림 쿨다운 (분)
    MAX_KEYWORDS_PER_ALERT: int = 10        # 한 알림당 최대 키워드 수

    # 파일 경로
    ALERT_HISTORY_FILE: str = "alert_history.json"
    ALERT_LOG_DIR: str = "alerts"

    # 점수 계산 가중치
    GROWTH_WEIGHT: float = 0.4              # 성장률 가중치
    FREQUENCY_WEIGHT: float = 0.3           # 빈도수 가중치
    RANK_WEIGHT: float = 0.2                # 순위 상승 가중치
    VOLATILITY_WEIGHT: float = 0.1          # 변동성 가중치


def setup_logging(name: str = "keyword_alert") -> logging.Logger:
    """로그 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ============================================================================
# 급상승 키워드 탐지 클래스
# ============================================================================

class TrendingKeywordDetector:
    """인기 급상승 키워드 탐지기"""

    def __init__(self, config: AlertConfig = None):
        """
        탐지기 초기화

        Args:
            config: 알림 설정
        """
        self.config = config or AlertConfig()
        self.logger = setup_logging()

        # 알림 히스토리 로드
        self.alert_history = self._load_alert_history()

        # 알림 로그 디렉토리 생성
        Path(self.config.ALERT_LOG_DIR).mkdir(exist_ok=True)

    def _load_alert_history(self) -> Dict:
        """알림 히스토리 로드"""
        try:
            if Path(self.config.ALERT_HISTORY_FILE).exists():
                with open(self.config.ALERT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"알림 히스토리 로드 실패: {e}")

        return {}

    def _save_alert_history(self):
        """알림 히스토리 저장"""
        try:
            with open(self.config.ALERT_HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"알림 히스토리 저장 실패: {e}")

    def detect_trending_keywords(self, trend_df: pd.DataFrame,
                                growth_df: pd.DataFrame = None) -> List[Dict]:
        """
        급상승 키워드 탐지

        Args:
            trend_df: 트렌드 데이터프레임
            growth_df: 성장률 데이터프레임 (선택사항)

        Returns:
            급상승 키워드 정보 리스트
        """
        if trend_df.empty:
            return []

        trending_keywords = []
        current_time = datetime.now()

        # 최근 데이터 필터링 (최근 2개 기간)
        latest_date = trend_df['date'].max()
        if isinstance(latest_date, str):
            latest_date = pd.to_datetime(latest_date)

        # 최근 기간 데이터
        recent_data = trend_df[trend_df['date'] >= latest_date - timedelta(days=7)]

        if recent_data.empty:
            return []

        # 각 키워드 분석
        for keyword in recent_data['keyword'].unique():
            keyword_data = recent_data[recent_data['keyword'] == keyword]

            # 빈도수
            total_freq = keyword_data['frequency'].sum()
            if total_freq < self.config.MIN_FREQUENCY_THRESHOLD:
                continue

            # 성장률 계산
            growth_rate = 0
            if growth_df is not None and not growth_df.empty:
                keyword_growth = growth_df[growth_df['keyword'] == keyword]
                if not keyword_growth.empty:
                    growth_rate = keyword_growth['growth_rate'].iloc[-1]

            # 순위 변화
            rank_change = self._calculate_rank_change(trend_df, keyword, latest_date)

            # 변동성 계산
            volatility = self._calculate_volatility(keyword_data)

            # 급상승 점수 계산
            trending_score = self._calculate_trending_score(
                growth_rate, total_freq, rank_change, volatility
            )

            # 급상승 키워드 판단
            if self._is_trending(growth_rate, rank_change, volatility, trending_score):
                trending_keywords.append({
                    'keyword': keyword,
                    'frequency': int(total_freq),
                    'growth_rate': float(growth_rate),
                    'rank_change': int(rank_change),
                    'volatility': float(volatility),
                    'trending_score': float(trending_score),
                    'detected_at': current_time.strftime('%Y-%m-%d %H:%M:%S')
                })

        # 점수순 정렬
        trending_keywords.sort(key=lambda x: x['trending_score'], reverse=True)

        self.logger.info(f"급상승 키워드 {len(trending_keywords)}개 탐지")

        return trending_keywords

    def _calculate_rank_change(self, trend_df: pd.DataFrame,
                              keyword: str, latest_date) -> int:
        """순위 변화 계산"""
        try:
            # 최근 2개 기간의 순위 계산
            recent_periods = trend_df[trend_df['date'] >= latest_date - timedelta(days=14)]

            if len(recent_periods['date'].unique()) < 2:
                return 0

            # 각 기간별 순위
            period_rankings = {}
            for period in recent_periods['date'].unique():
                period_data = recent_periods[recent_periods['date'] == period]
                keyword_freq = period_data.groupby('keyword')['frequency'].sum().rank(ascending=False)

                if keyword in keyword_freq.index:
                    period_rankings[period] = keyword_freq[keyword]

            if len(period_rankings) >= 2:
                sorted_periods = sorted(period_rankings.keys())
                latest_rank = period_rankings[sorted_periods[-1]]
                previous_rank = period_rankings[sorted_periods[-2]]

                return previous_rank - latest_rank  # 양수: 순위 상승

        except Exception as e:
            self.logger.error(f"순위 변화 계산 오류 ({keyword}): {e}")

        return 0

    def _calculate_volatility(self, keyword_data: pd.DataFrame) -> float:
        """변동성 계산 (변동계수)"""
        try:
            if len(keyword_data) < 2:
                return 0.0

            freqs = keyword_data['frequency'].values
            if len(freqs) < 2 or np.mean(freqs) == 0:
                return 0.0

            return float(np.std(freqs) / np.mean(freqs))

        except Exception as e:
            self.logger.error(f"변동성 계산 오류: {e}")
            return 0.0

    def _calculate_trending_score(self, growth_rate: float,
                                  frequency: int,
                                  rank_change: int,
                                  volatility: float) -> float:
        """급상승 점수 계산 (0-100)"""
        # 정규화된 점수 계산
        growth_score = min(abs(growth_rate) / 100, 1.0) * 100

        freq_score = min(frequency / 50, 1.0) * 100

        rank_score = min(max(rank_change, 0) / 10, 1.0) * 100

        volatility_score = min(volatility / 5, 1.0) * 100

        # 가중 평균
        weighted_score = (
            growth_score * self.config.GROWTH_WEIGHT +
            freq_score * self.config.FREQUENCY_WEIGHT +
            rank_score * self.config.RANK_WEIGHT +
            volatility_score * self.config.VOLATILITY_WEIGHT
        )

        return round(weighted_score, 2)

    def _is_trending(self, growth_rate: float,
                    rank_change: int,
                    volatility: float,
                    trending_score: float) -> bool:
        """급상승 키워드 판단"""
        # 최소 조건: 하나라도 충족하면 True
        conditions = [
            growth_rate >= self.config.GROWTH_RATE_THRESHOLD,  # 성장률 50% 이상
            rank_change >= self.config.RANK_JUMP_THRESHOLD,     # 순위 5계급 이상 상승
            trending_score >= 60.0                              # 종합 점수 60점 이상
        ]

        return any(conditions)

    def check_alert_cooldown(self, keyword: str) -> bool:
        """
        알림 쿨다운 체크

        Args:
            keyword: 키워드

        Returns:
            True: 알림 가능, False: 쿨다운 중
        """
        current_time = datetime.now()

        if keyword in self.alert_history:
            last_alert = datetime.fromisoformat(self.alert_history[keyword])
            time_diff = (current_time - last_alert).total_seconds() / 60

            if time_diff < self.config.ALERT_COOLDOWN_MINUTES:
                return False

        return True

    def update_alert_history(self, keyword: str):
        """
        알림 히스토리 업데이트

        Args:
            keyword: 키워드
        """
        self.alert_history[keyword] = datetime.now().isoformat()
        self._save_alert_history()


# ============================================================================
# 알림 발송 클래스
# ============================================================================

class KeywordAlertSender:
    """키워드 알림 발송기"""

    def __init__(self, email_notifier=None, config: AlertConfig = None):
        """
        알림 발송기 초기화

        Args:
            email_notifier: 이메일 알림 시스템 (선택사항)
            config: 알림 설정
        """
        self.config = config or AlertConfig()
        self.email_notifier = email_notifier
        self.logger = setup_logging()

        # 알림 로그 디렉토리 생성
        Path(self.config.ALERT_LOG_DIR).mkdir(exist_ok=True)

    def send_trending_alert(self, trending_keywords: List[Dict],
                          recipients: List[str] = None) -> bool:
        """
        급상승 키워드 알림 발송

        Args:
            trending_keywords: 급상승 키워드 리스트
            recipients: 수신자 이메일 리스트

        Returns:
            발송 성공 여부
        """
        if not trending_keywords:
            self.logger.info("알림 발송할 키워드가 없습니다.")
            return False

        # 상위 N개만 발송
        top_keywords = trending_keywords[:self.config.MAX_KEYWORDS_PER_ALERT]

        # 알림 메시지 생성
        subject = f"🔥 인기 급상승 키워드 알림 ({len(top_keywords)}개)"
        message = self._create_alert_message(top_keywords)

        # 로그 저장
        self._save_alert_log(top_keywords)

        # 이메일 발송
        if self.email_notifier and recipients:
            try:
                for recipient in recipients:
                    self.email_notifier.send_email(
                        to_email=recipient,
                        subject=subject,
                        body=message
                    )
                self.logger.info(f"이메일 알림 발송 완료: {len(recipients)}명")
                return True

            except Exception as e:
                self.logger.error(f"이메일 발송 실패: {e}")

        # 콘솔 출력 (이메일 미설정 시)
        else:
            print("\n" + "="*60)
            print(f"🔥 {subject}")
            print("="*60)
            print(message)
            print("="*60 + "\n")

        return True

    def _create_alert_message(self, trending_keywords: List[Dict]) -> str:
        """알림 메시지 생성"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        message = f"""
🔥 인기 급상승 키워드 알림

감지 시간: {current_time}
"""

        for i, keyword_info in enumerate(trending_keywords, 1):
            message += f"""
{i}. {keyword_info['keyword']}
   - 빈도수: {keyword_info['frequency']}회
   - 성장률: {keyword_info['growth_rate']:.1f}%
   - 순위 변화: {keyword_info['rank_change']}계급
   - 급상승 점수: {keyword_info['trending_score']:.1f}점
"""

        message += "\n\n데이터 분석 시스템이 자동으로 생성했습니다."

        return message

    def _save_alert_log(self, trending_keywords: List[Dict]):
        """알림 로그 저장"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = Path(self.config.ALERT_LOG_DIR) / f"alert_{timestamp}.json"

            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(trending_keywords, f, ensure_ascii=False, indent=2)

            self.logger.info(f"알림 로그 저장: {log_file}")

        except Exception as e:
            self.logger.error(f"알림 로그 저장 실패: {e}")


# ============================================================================
# 통합 알림 시스템
# ============================================================================

class KeywordAlertSystem:
    """키워드 알림 시스템 (메인 클래스)"""

    def __init__(self, email_notifier=None, config: AlertConfig = None):
        """
        알림 시스템 초기화

        Args:
            email_notifier: 이메일 알림 시스템 (선택사항)
            config: 알림 설정
        """
        self.config = config or AlertConfig()
        self.detector = TrendingKeywordDetector(config)
        self.sender = KeywordAlertSender(email_notifier, config)
        self.logger = setup_logging()

    def monitor_and_alert(self, trend_df: pd.DataFrame,
                         growth_df: pd.DataFrame = None,
                         recipients: List[str] = None) -> Dict:
        """
        키워드 모니터링 및 알림 발송

        Args:
            trend_df: 트렌드 데이터프레임
            growth_df: 성장률 데이터프레임
            recipients: 수신자 이메일 리스트

        Returns:
            모니터링 결과
        """
        self.logger.info("키워드 모니터링 시작...")

        # 급상승 키워드 탐지
        trending_keywords = self.detector.detect_trending_keywords(
            trend_df, growth_df
        )

        if not trending_keywords:
            self.logger.info("급상승 키워드 없음")
            return {
                'detected': 0,
                'alerted': 0,
                'keywords': []
            }

        # 쿨다운 체크 및 알림 발송
        alert_keywords = []
        for keyword_info in trending_keywords:
            keyword = keyword_info['keyword']

            if self.detector.check_alert_cooldown(keyword):
                alert_keywords.append(keyword_info)
                self.detector.update_alert_history(keyword)

        # 알림 발송
        if alert_keywords:
            self.sender.send_trending_alert(alert_keywords, recipients)

        return {
            'detected': len(trending_keywords),
            'alerted': len(alert_keywords),
            'keywords': alert_keywords
        }

    def get_trending_report(self, trend_df: pd.DataFrame,
                           growth_df: pd.DataFrame = None) -> str:
        """
        급상승 키워드 리포트 생성

        Args:
            trend_df: 트렌드 데이터프레임
            growth_df: 성장률 데이터프레임

        Returns:
            리포트 문자열
        """
        trending_keywords = self.detector.detect_trending_keywords(
            trend_df, growth_df
        )

        if not trending_keywords:
            return "급상승 키워드가 없습니다."

        report = "="*60 + "\n"
        report += "🔥 인기 급상승 키워드 리포트\n"
        report += "="*60 + "\n\n"

        for i, kw in enumerate(trending_keywords[:20], 1):
            report += f"{i}. {kw['keyword']}\n"
            report += f"   빈도: {kw['frequency']}회 | "
            report += f"성장: {kw['growth_rate']:.1f}% | "
            report += f"점수: {kw['trending_score']:.1f}\n"

        report += "\n" + "="*60 + "\n"

        return report


# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    print("인기 급상승 키워드 탐지 및 알림 시스템")
    print("="*60)

    # 알림 시스템 초기화
    alert_system = KeywordAlertSystem()

    # 테스트 데이터 생성
    test_trend_data = pd.DataFrame({
        'date': pd.date_range(end=datetime.now(), periods=14, freq='D'),
        'keyword': ['AI'] * 7 + ['블록체인'] * 7,
        'frequency': [10, 12, 15, 20, 30, 50, 80,  # AI (급상승)
                     100, 95, 90, 85, 80, 75, 70]   # 블록체인 (하락)
    })

    # 모니터링 및 알림
    result = alert_system.monitor_and_alert(test_trend_data)

    print(f"\n탐지된 키워드: {result['detected']}개")
    print(f"알림 발송: {result['alerted']}개")

    # 리포트 출력
    print(alert_system.get_trending_report(test_trend_data))


if __name__ == "__main__":
    main()
