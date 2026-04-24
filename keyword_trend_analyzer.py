#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 트렌드 분석 시스템
KoNLPy 형태소 분석기를 활용한 한국어 키워드 추출 및 트렌드 분석

기능:
1. 한국어 형태소 분석 (KoNLPy)
2. 키워드 등장 빈도 추이 분석 (일주일/한 달 단위)
3. 연관 키워드 추출 및 네트워크 분석
4. 시각화 및 리포팅
"""

import sys
import os

# UTF-8 출력 설정 (Windows)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Python 3.7 이전 버전 호환성

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set, Optional
from pathlib import Path
from collections import Counter, defaultdict
import json

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import networkx as nx
from wordcloud import WordCloud
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# KoNLPy 형태소 분석기
try:
    from konlpy.tag import Okt, Mecab, Komoran, Hannanum, Kkma
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("KoNLPy가 설치되지 않았습니다. 'pip install konlpy'로 설치해주세요.")
    print("Java JDK 8 이상이 필요합니다.")


# ============================================================================
# 설정 및 로깅
# ============================================================================

class AnalyzerConfig:
    """분석기 설정"""

    # 텍스트 처리
    MIN_WORD_LENGTH: int = 2
    MAX_WORD_LENGTH: int = 20
    MIN_KEYWORD_FREQ: int = 2
    TOP_N_KEYWORDS: int = 50

    # 형태소 분석
    POS_TAGS: List[str] = ['Noun', 'Verb', 'Adjective', 'Adverb']
    STOP_WORDS: Set[str] = {
        '이', '그', '저', '것', '수', '등', '및', '또', '때문', '더', '가', '도', '은', '는',
        '이', '가', '을', '를', '의', '에', '에서', '으로', '와', '과', '하다', '되다', '있다',
        '없다', '아니다', '그렇다', '어떻다', '이렇다', '그렇다'
    }

    # 트렌드 분석
    TIME_PERIODS: List[str] = ['daily', 'weekly', 'monthly']

    # 네트워크 분석
    MIN_CO_OCCURRENCE: int = 2
    MAX_EDGES: int = 100
    MIN_CLUSTER_SIZE: int = 2

    # 시각화
    CHART_DIR: str = "charts"
    WORDCLOUD_WIDTH: int = 800
    WORDCLOUD_HEIGHT: int = 600
    NETWORK_WIDTH: int = 1000
    NETWORK_HEIGHT: int = 800

    # 폰트 (한글 지원)
    FONT_PATH: str = "C:/Windows/Fonts/malgun.ttf"  # Windows 맑은 고딕


def setup_logging(name: str = "keyword_analyzer") -> logging.Logger:
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
# 형태소 분석 클래스
# ============================================================================

class KoreanMorphemeAnalyzer:
    """한국어 형태소 분석기"""

    def __init__(self, analyzer_type: str = 'okt', config: AnalyzerConfig = None):
        """
        형태소 분석기 초기화

        Args:
            analyzer_type: 사용할 형태소 분석기 타입 ('okt', 'mecab', 'komoran', 'hannanum', 'kkma')
            config: 분석기 설정
        """
        if not KONLPY_AVAILABLE:
            raise ImportError("KoNLPy가 설치되지 않았습니다.")

        self.config = config or AnalyzerConfig()
        self.logger = setup_logging()

        # 형태소 분석기 로드
        try:
            if analyzer_type == 'okt':
                self.morpheme = Okt()
            elif analyzer_type == 'mecab':
                self.morpheme = Mecab()
            elif analyzer_type == 'komoran':
                self.morpheme = Komoran()
            elif analyzer_type == 'hannanum':
                self.morpheme = Hannanum()
            elif analyzer_type == 'kkma':
                self.morpheme = Kkma()
            else:
                self.morpheme = Okt()

            self.analyzer_type = analyzer_type
            self.logger.info(f"{analyzer_type} 형태소 분석기 로드 완료")

        except Exception as e:
            self.logger.warning(f"{analyzer_type} 로드 실패: {e}, Okt로 대체")
            self.morpheme = Okt()
            self.analyzer_type = 'okt'

    def extract_nouns(self, text: str) -> List[str]:
        """
        명사 추출

        Args:
            text: 분석할 텍스트

        Returns:
            추출된 명사 리스트
        """
        try:
            nouns = self.morpheme.nouns(text)
            # 불용어 및 길이 필터링
            filtered = [
                word for word in nouns
                if self.config.MIN_WORD_LENGTH <= len(word) <= self.config.MAX_WORD_LENGTH
                and word not in self.config.STOP_WORDS
            ]
            return filtered
        except Exception as e:
            self.logger.error(f"명사 추출 오류: {e}")
            return []

    def extract_pos_tags(self, text: str, pos_tags: List[str] = None) -> List[Tuple[str, str]]:
        """
        품사 태깅 및 추출

        Args:
            text: 분석할 텍스트
            pos_tags: 추출할 품사 태그 리스트

        Returns:
            (단어, 품사) 튜플 리스트
        """
        if pos_tags is None:
            pos_tags = self.config.POS_TAGS

        try:
            pos_result = self.morpheme.pos(text)

            # 한국어 품사 태그 매핑
            tag_mapping = {
                'Noun': ['Noun', 'NNG', 'NNP', 'NNB', 'NNM', 'NR'],
                'Verb': ['Verb', 'VV', 'VX', 'VCP', 'VCN'],
                'Adjective': ['Adjective', 'VA', 'VAA', 'VAC'],
                'Adverb': ['Adverb', 'MAG', 'MAJ']
            }

            filtered = []
            for word, tag in pos_result:
                # 해당 품사인지 확인
                is_target = False
                for pos_tag in pos_tags:
                    if tag in tag_mapping.get(pos_tag, []):
                        is_target = True
                        break

                if is_target and len(word) >= self.config.MIN_WORD_LENGTH:
                    if word not in self.config.STOP_WORDS:
                        filtered.append((word, tag))

            return filtered
        except Exception as e:
            self.logger.error(f"품사 태깅 오류: {e}")
            return []

    def extract_keywords(self, text: str, top_n: int = None) -> List[Tuple[str, int]]:
        """
        키워드 추출 (명사 기반 빈도수)

        Args:
            text: 분석할 텍스트
            top_n: 추출할 상위 키워드 수

        Returns:
            (키워드, 빈도수) 튜플 리스트
        """
        top_n = top_n or self.config.TOP_N_KEYWORDS

        nouns = self.extract_nouns(text)
        word_freq = Counter(nouns)

        return word_freq.most_common(top_n)

    def normalize_text(self, text: str) -> str:
        """
        텍스트 정규화

        Args:
            text: 정규화할 텍스트

        Returns:
            정규화된 텍스트
        """
        # 특수문자 제거
        text = re.sub(r'[^\w\s]', ' ', text)
        # 숫자 제거
        text = re.sub(r'\d+', ' ', text)
        # 영어 소문자 변환
        text = text.lower()
        # 공백 정리
        text = ' '.join(text.split())

        return text


# ============================================================================
# 트렌드 분석 클래스
# ============================================================================

class KeywordTrendAnalyzer:
    """키워드 트렌드 분석기"""

    def __init__(self, morpheme_analyzer: KoreanMorphemeAnalyzer = None,
                 config: AnalyzerConfig = None):
        """
        트렌드 분석기 초기화

        Args:
            morpheme_analyzer: 형태소 분석기 인스턴스
            config: 분석기 설정
        """
        self.morpheme = morpheme_analyzer or KoreanMorphemeAnalyzer()
        self.config = config or AnalyzerConfig()
        self.logger = setup_logging()

    def analyze_document_trend(self, documents: List[Dict[str, str]],
                               period: str = 'daily') -> pd.DataFrame:
        """
        문서들의 키워드 트렌드 분석

        Args:
            documents: [{'title': str, 'content': str, 'date': str}, ...] 형태의 문서 리스트
            period: 분석 기간 ('daily', 'weekly', 'monthly')

        Returns:
            키워드 빈도 추이 데이터프레임
        """
        # 날짜 변환
        df = pd.DataFrame(documents)

        if 'date' not in df.columns:
            self.logger.error("문서에 'date' 필드가 없습니다.")
            return pd.DataFrame()

        df['date'] = pd.to_datetime(df['date'])

        # 기간별 그룹핑
        if period == 'daily':
            df['period'] = df['date'].dt.date
        elif period == 'weekly':
            df['period'] = df['date'].dt.to_period('W').dt.start_time
        elif period == 'monthly':
            df['period'] = df['date'].dt.to_period('M').dt.start_time
        else:
            raise ValueError(f"지원하지 않는 기간: {period}")

        # 기간별 키워드 추출
        period_keywords = defaultdict(lambda: Counter())

        for _, row in df.iterrows():
            period = row['period']
            content = f"{row.get('title', '')} {row.get('content', '')}"

            keywords = self.morpheme.extract_nouns(content)
            period_keywords[period].update(keywords)

        # 데이터프레임 생성
        trend_data = []
        for period, counter in period_keywords.items():
            for keyword, freq in counter.items():
                if freq >= self.config.MIN_KEYWORD_FREQ:
                    trend_data.append({
                        'date': period,
                        'keyword': keyword,
                        'frequency': freq
                    })

        trend_df = pd.DataFrame(trend_data)

        if not trend_df.empty:
            trend_df = trend_df.sort_values(['date', 'frequency'], ascending=[True, False])

        self.logger.info(f"트렌드 분석 완료: {len(trend_df)}개 데이터 포인트")

        return trend_df

    def calculate_keyword_growth(self, trend_df: pd.DataFrame,
                                 top_n: int = 20) -> pd.DataFrame:
        """
        키워드 성장률 계산

        Args:
            trend_df: 트렌드 데이터프레임
            top_n: 분석할 상위 키워드 수

        Returns:
            성장률 데이터프레임
        """
        if trend_df.empty:
            return pd.DataFrame()

        # 피벗 테이블 생성
        pivot_df = trend_df.pivot(index='keyword', columns='date', values='frequency').fillna(0)

        # 상위 키워드 선택
        top_keywords = pivot_df.sum(axis=1).nlargest(top_n).index
        pivot_df = pivot_df.loc[top_keywords]

        # 성장률 계산
        growth_data = []
        for keyword in pivot_df.index:
            freqs = pivot_df.loc[keyword].values
            dates = pivot_df.columns

            for i in range(1, len(freqs)):
                if freqs[i-1] > 0:
                    growth_rate = ((freqs[i] - freqs[i-1]) / freqs[i-1]) * 100
                else:
                    growth_rate = 100 if freqs[i] > 0 else 0

                growth_data.append({
                    'keyword': keyword,
                    'date': dates[i],
                    'frequency': freqs[i],
                    'growth_rate': growth_rate
                })

        growth_df = pd.DataFrame(growth_data)

        self.logger.info(f"성장률 분석 완료: {len(growth_df)}개 데이터 포인트")

        return growth_df

    def get_hot_keywords(self, trend_df: pd.DataFrame,
                         period_days: int = 7,
                         top_n: int = 10) -> List[Tuple[str, int]]:
        """
        최신 인기 키워드 추출

        Args:
            trend_df: 트렌드 데이터프레임
            period_days: 분석 기간 (일)
            top_n: 추출할 키워드 수

        Returns:
            (키워드, 빈도수) 튜플 리스트
        """
        if trend_df.empty:
            return []

        # 최근 데이터 필터링
        latest_date = trend_df['date'].max()
        cutoff_date = latest_date - timedelta(days=period_days)

        recent_df = trend_df[trend_df['date'] >= cutoff_date]

        # 기간별 합계 계산
        keyword_freq = recent_df.groupby('keyword')['frequency'].sum().nlargest(top_n)

        return list(keyword_freq.items())


# ============================================================================
# 연관 키워드 분석 클래스
# ============================================================================

class RelatedKeywordAnalyzer:
    """연관 키워드 및 네트워크 분석기"""

    def __init__(self, morpheme_analyzer: KoreanMorphemeAnalyzer = None,
                 config: AnalyzerConfig = None):
        """
        연관 키워드 분석기 초기화

        Args:
            morpheme_analyzer: 형태소 분석기 인스턴스
            config: 분석기 설정
        """
        self.morpheme = morpheme_analyzer or KoreanMorphemeAnalyzer()
        self.config = config or AnalyzerConfig()
        self.logger = setup_logging()

    def extract_co_occurrence_matrix(self, documents: List[str]) -> Dict[Tuple[str, str], int]:
        """
        동시 출현 행렬 생성

        Args:
            documents: 문서 리스트

        Returns:
            {(키워드1, 키워드2): 빈도수} 형태의 동시 출현 행렬
        """
        co_occurrence = defaultdict(int)

        for doc in documents:
            keywords = set(self.morpheme.extract_nouns(doc))
            keywords = [k for k in keywords if len(k) >= self.config.MIN_WORD_LENGTH]

            # 모든 키워드 쌍에 대해 빈도 계산
            for i, kw1 in enumerate(keywords):
                for kw2 in keywords[i+1:]:
                    if kw1 != kw2:
                        # 정렬하여 일관성 유지
                        pair = tuple(sorted([kw1, kw2]))
                        co_occurrence[pair] += 1

        # 최소 빈도 필터링
        filtered = {k: v for k, v in co_occurrence.items()
                   if v >= self.config.MIN_CO_OCCURRENCE}

        self.logger.info(f"동시 출현 쌍 추출: {len(filtered)}개")

        return filtered

    def build_keyword_network(self, documents: List[str],
                              top_n: int = 50) -> nx.Graph:
        """
        키워드 네트워크 생성

        Args:
            documents: 문서 리스트
            top_n: 포함할 상위 키워드 수

        Returns:
            NetworkX 그래프 객체
        """
        # 모든 키워드 추출 및 빈도 계산
        all_keywords = []
        for doc in documents:
            keywords = self.morpheme.extract_nouns(doc)
            all_keywords.extend(keywords)

        keyword_freq = Counter(all_keywords)
        top_keywords = set([kw for kw, _ in keyword_freq.most_common(top_n)])

        # 동시 출현 행렬 생성
        co_occurrence = self.extract_co_occurrence_matrix(documents)

        # 그래프 생성
        G = nx.Graph()

        # 노드 추가 (상위 키워드만)
        for keyword in top_keywords:
            G.add_node(keyword, frequency=keyword_freq[keyword])

        # 엣지 추가
        edge_count = 0
        for (kw1, kw2), weight in co_occurrence.items():
            if kw1 in top_keywords and kw2 in top_keywords:
                G.add_edge(kw1, kw2, weight=weight)
                edge_count += 1
                if edge_count >= self.config.MAX_EDGES:
                    break

        self.logger.info(f"네트워크 생성: {G.number_of_nodes()}개 노드, {G.number_of_edges()}개 엣지")

        return G

    def detect_keyword_clusters(self, documents: List[str],
                                n_clusters: int = 5) -> Dict[int, List[str]]:
        """
        키워드 클러스터링 (K-means)

        Args:
            documents: 문서 리스트
            n_clusters: 클러스터 수

        Returns:
            {클러스터ID: [키워드 리스트]} 형태의 딕셔너리
        """
        # TF-IDF 벡터화
        all_keywords_list = []
        for doc in documents:
            keywords = self.morpheme.extract_nouns(doc)
            all_keywords_list.append(' '.join(keywords))

        if not all_keywords_list:
            return {}

        # TF-IDF
        vectorizer = TfidfVectorizer(min_df=2, max_df=0.8)
        try:
            tfidf_matrix = vectorizer.fit_transform(all_keywords_list)
            feature_names = vectorizer.get_feature_names_out()
        except ValueError:
            self.logger.warning("TF-IDF 벡터화 실패 (데이터 부족)")
            return {}

        # K-means 클러스터링
        n_clusters = min(n_clusters, len(feature_names))
        if n_clusters < 2:
            return {}

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans.fit(tfidf_matrix)

        # 클러스터별 상위 키워드 추출
        clusters = {}
        center_indices = kmeans.cluster_centers_.argsort()[:, ::-1]

        for i in range(n_clusters):
            top_indicators = center_indices[i, :10]  # 상위 10개
            top_keywords = [feature_names[ind] for ind in top_indicators]
            clusters[i] = top_keywords

        self.logger.info(f"클러스터링 완료: {len(clusters)}개 클러스터")

        return clusters

    def find_similar_keywords(self, documents: List[str],
                              keyword: str,
                              top_n: int = 10) -> List[Tuple[str, float]]:
        """
        유사한 키워드 찾기 (코사인 유사도)

        Args:
            documents: 문서 리스트
            keyword: 기준 키워드
            top_n: 추출할 유사 키워드 수

        Returns:
            (키워드, 유사도) 튜플 리스트
        """
        # TF-IDF 벡터화
        all_keywords_list = []
        for doc in documents:
            keywords = self.morpheme.extract_nouns(doc)
            all_keywords_list.append(' '.join(keywords))

        if not all_keywords_list:
            return []

        vectorizer = TfidfVectorizer(min_df=2)
        try:
            tfidf_matrix = vectorizer.fit_transform(all_keywords_list)
            feature_names = vectorizer.get_feature_names_out()
        except ValueError:
            return []

        # 키워드 인덱스 찾기
        if keyword not in feature_names:
            self.logger.warning(f"키워드 '{keyword}'를 찾을 수 없습니다.")
            return []

        keyword_idx = list(feature_names).index(keyword)
        keyword_vector = tfidf_matrix[:, keyword_idx].toarray()

        # 코사인 유사도 계산
        similarities = []
        for i, fname in enumerate(feature_names):
            if i != keyword_idx:
                feature_vector = tfidf_matrix[:, i].toarray()
                similarity = cosine_similarity(keyword_vector.T, feature_vector.T)[0][0]
                if similarity > 0:
                    similarities.append((fname, similarity))

        # 상위 유사 키워드 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:top_n]


# ============================================================================
# 시각화 클래스
# ============================================================================

class KeywordVisualizer:
    """키워드 시각화 클래스"""

    def __init__(self, config: AnalyzerConfig = None):
        """
        시각화 도구 초기화

        Args:
            config: 분석기 설정
        """
        self.config = config or AnalyzerConfig()
        self.logger = setup_logging()

        # 출력 디렉토리 생성
        Path(self.config.CHART_DIR).mkdir(exist_ok=True)

    def plot_trend_line(self, trend_df: pd.DataFrame,
                       keywords: List[str] = None,
                       top_n: int = 10,
                       save_path: str = None) -> go.Figure:
        """
        키워드 트렌드 라인 차트

        Args:
            trend_df: 트렌드 데이터프레임
            keywords: 표시할 키워드 리스트 (None이면 상위 N개)
            top_n: 표시할 상위 키워드 수
            save_path: 저장 경로

        Returns:
            Plotly Figure 객체
        """
        if trend_df.empty:
            self.logger.warning("트렌드 데이터가 없습니다.")
            return None

        # 상위 키워드 선택
        if keywords is None:
            top_keywords = trend_df.groupby('keyword')['frequency'].sum().nlargest(top_n).index
        else:
            top_keywords = keywords

        plot_df = trend_df[trend_df['keyword'].isin(top_keywords)]

        # 인터랙티브 차트 생성
        fig = go.Figure()

        for keyword in top_keywords:
            keyword_data = plot_df[plot_df['keyword'] == keyword].sort_values('date')
            fig.add_trace(go.Scatter(
                x=keyword_data['date'],
                y=keyword_data['frequency'],
                mode='lines+markers',
                name=keyword,
                line=dict(width=2),
                marker=dict(size=6),
                hovertemplate=f'<b>{keyword}</b><br>날짜: %{{x}}<br>빈도: %{{y}}<extra></extra>'
            ))

        fig.update_layout(
            title='키워드 트렌드 분석',
            xaxis_title='날짜',
            yaxis_title='빈도수',
            hovermode='x unified',
            template='plotly_white',
            height=600,
            showlegend=True
        )

        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"트렌드 차트 저장: {save_path}")

        return fig

    def plot_wordcloud(self, documents: List[str],
                       save_path: str = None) -> WordCloud:
        """
        워드클라우드 생성

        Args:
            documents: 문서 리스트
            save_path: 저장 경로

        Returns:
            WordCloud 객체
        """
        # 모든 텍스트 합치기
        all_text = ' '.join(documents)

        # 형태소 분석
        from konlpy.tag import Okt
        okt = Okt()
        nouns = okt.nouns(all_text)

        # 불용어 제거
        nouns = [word for word in nouns
                if len(word) >= 2 and word not in self.config.STOP_WORDS]

        if not nouns:
            self.logger.warning("워드클라우드 생성을 위한 키워드가 없습니다.")
            return None

        # 빈도 계산
        word_freq = Counter(nouns)

        # 워드클라우드 생성
        try:
            wordcloud = WordCloud(
                width=self.config.WORDCLOUD_WIDTH,
                height=self.config.WORDCLOUD_HEIGHT,
                font_path=self.config.FONT_PATH if Path(self.config.FONT_PATH).exists() else None,
                background_color='white',
                colormap='viridis',
                max_words=100,
                relative_scaling=0.5,
                min_font_size=10
            ).generate_from_frequencies(word_freq)

            # 시각화
            plt.figure(figsize=(12, 8))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.title('키워드 워드클라우드', fontsize=20, fontweight='bold')
            plt.tight_layout(pad=0)

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"워드클라우드 저장: {save_path}")
                plt.close()
            else:
                plt.show()

            return wordcloud

        except Exception as e:
            self.logger.error(f"워드클라우드 생성 오류: {e}")
            return None

    def plot_network_graph(self, G: nx.Graph,
                          layout: str = 'spring',
                          save_path: str = None) -> go.Figure:
        """
        키워드 네트워크 그래프

        Args:
            G: NetworkX 그래프 객체
            layout: 레이아웃 타입 ('spring', 'circular', 'random', 'shell')
            save_path: 저장 경로

        Returns:
            Plotly Figure 객체
        """
        if G.number_of_nodes() == 0:
            self.logger.warning("네트워크 그래프에 노드가 없습니다.")
            return None

        # 레이아웃 계산
        if layout == 'spring':
            pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == 'circular':
            pos = nx.circular_layout(G)
        elif layout == 'random':
            pos = nx.random_layout(G)
        elif layout == 'shell':
            pos = nx.shell_layout(G)
        else:
            pos = nx.spring_layout(G)

        # 엣지 추적
        edge_x = []
        edge_y = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        # 엣지 트레이스
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # 노드 추적
        node_x = []
        node_y = []
        node_text = []
        node_size = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_size.append(G.nodes[node]['frequency'])

        # 노드 크기 정규화
        if node_size:
            max_size = max(node_size)
            node_size = [10 + (size / max_size) * 50 for size in node_size]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=node_size,
                color='lightseagreen',
                line=dict(width=2, color='white')
            )
        )

        # 그래프 생성
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=dict(text='키워드 연관 네트워크', font=dict(size=16)),
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20, l=5, r=5, t=40),
                           annotations=[dict(
                               text="",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                       ))

        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"네트워크 그래프 저장: {save_path}")

        return fig

    def plot_growth_heatmap(self, growth_df: pd.DataFrame,
                           save_path: str = None) -> go.Figure:
        """
        키워드 성장률 히트맵

        Args:
            growth_df: 성장률 데이터프레임
            save_path: 저장 경로

        Returns:
            Plotly Figure 객체
        """
        if growth_df.empty:
            self.logger.warning("성장률 데이터가 없습니다.")
            return None

        # 피벗 테이블 생성
        pivot_df = growth_df.pivot(index='keyword', columns='date', values='growth_rate')

        # 히트맵 생성
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=[str(d) for d in pivot_df.columns],
            y=pivot_df.index,
            colorscale='RdYlGn',
            colorbar=dict(title='성장률 (%)')
        ))

        fig.update_layout(
            title='키워드 성장률 히트맵',
            xaxis_title='날짜',
            yaxis_title='키워드',
            height=max(400, len(pivot_df) * 30)
        )

        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"성장률 히트맵 저장: {save_path}")

        return fig


# ============================================================================
# 통합 분석 클래스
# ============================================================================

class KeywordTrendSystem:
    """키워드 트렌드 분석 시스템 (메인 클래스)"""

    def __init__(self, analyzer_type: str = 'okt', config: AnalyzerConfig = None):
        """
        시스템 초기화

        Args:
            analyzer_type: 형태소 분석기 타입
            config: 분석기 설정
        """
        self.config = config or AnalyzerConfig()
        self.logger = setup_logging()

        # 분석기 초기화
        self.morpheme_analyzer = KoreanMorphemeAnalyzer(analyzer_type, config)
        self.trend_analyzer = KeywordTrendAnalyzer(self.morpheme_analyzer, config)
        self.related_analyzer = RelatedKeywordAnalyzer(self.morpheme_analyzer, config)
        self.visualizer = KeywordVisualizer(config)

        self.logger.info("키워드 트렌드 분석 시스템 초기화 완료")

    def analyze_from_logs(self, log_dir: str = 'logs') -> Dict:
        """
        로그 파일에서 키워드 트렌드 분석

        Args:
            log_dir: 로그 디렉토리 경로

        Returns:
            분석 결과 딕셔너리
        """
        log_path = Path(log_dir)

        if not log_path.exists():
            self.logger.error(f"로그 디렉토리가 존재하지 않습니다: {log_dir}")
            return {}

        # 로그 파일 읽기
        log_files = list(log_path.glob('*.log'))

        if not log_files:
            self.logger.warning(f"로그 파일이 없습니다: {log_dir}")
            return {}

        documents = []
        for log_file in sorted(log_files):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 로그에서 날짜 추출 (파일명에서)
                    date_str = log_file.stem.split('_')[-1]
                    try:
                        date = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d')
                    except:
                        date = datetime.now().strftime('%Y-%m-%d')

                    documents.append({
                        'title': log_file.name,
                        'content': content,
                        'date': date
                    })
            except Exception as e:
                self.logger.error(f"로그 파일 읽기 오류 ({log_file}): {e}")

        return self.analyze_documents(documents)

    def analyze_documents(self, documents: List[Dict[str, str]]) -> Dict:
        """
        문서들의 종합 키워드 분석

        Args:
            documents: [{'title': str, 'content': str, 'date': str}, ...] 형태의 문서 리스트

        Returns:
            분석 결과 딕셔너리
        """
        self.logger.info(f"문서 분석 시작: {len(documents)}개 문서")

        results = {}

        # 1. 트렌드 분석
        try:
            trend_df = self.trend_analyzer.analyze_document_trend(documents, period='weekly')
            results['trend_data'] = trend_df

            if not trend_df.empty:
                # 성장률 계산
                growth_df = self.trend_analyzer.calculate_keyword_growth(trend_df)
                results['growth_data'] = growth_df

                # 인기 키워드
                hot_keywords = self.trend_analyzer.get_hot_keywords(trend_df)
                results['hot_keywords'] = hot_keywords
        except Exception as e:
            self.logger.error(f"트렌드 분석 오류: {e}")

        # 2. 연관 키워드 분석
        try:
            content_list = [f"{d.get('title', '')} {d.get('content', '')}" for d in documents]

            # 네트워크 생성
            network = self.related_analyzer.build_keyword_network(content_list)
            results['network'] = network

            # 클러스터링
            clusters = self.related_analyzer.detect_keyword_clusters(content_list)
            results['clusters'] = clusters
        except Exception as e:
            self.logger.error(f"연관 키워드 분석 오류: {e}")

        self.logger.info("문서 분석 완료")

        return results

    def generate_report(self, results: Dict, output_dir: str = None) -> Dict[str, str]:
        """
        분석 리포트 생성

        Args:
            results: 분석 결과 딕셔너리
            output_dir: 출력 디렉토리

        Returns:
            생성된 파일 경로 딕셔너리
        """
        output_dir = output_dir or self.config.CHART_DIR
        Path(output_dir).mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_files = {}

        # 1. 트렌드 차트
        if 'trend_data' in results and not results['trend_data'].empty:
            trend_path = f"{output_dir}/keyword_trend_{timestamp}.html"
            fig = self.visualizer.plot_trend_line(
                results['trend_data'],
                save_path=trend_path
            )
            if fig:
                report_files['trend_chart'] = trend_path

        # 2. 성장률 히트맵
        if 'growth_data' in results and not results['growth_data'].empty:
            heatmap_path = f"{output_dir}/growth_heatmap_{timestamp}.html"
            fig = self.visualizer.plot_growth_heatmap(
                results['growth_data'],
                save_path=heatmap_path
            )
            if fig:
                report_files['heatmap'] = heatmap_path

        # 3. 네트워크 그래프
        if 'network' in results:
            network_path = f"{output_dir}/keyword_network_{timestamp}.html"
            fig = self.visualizer.plot_network_graph(
                results['network'],
                save_path=network_path
            )
            if fig:
                report_files['network'] = network_path

        # 4. 워드클라우드 (문서가 있는 경우)
        if 'trend_data' in results and not results['trend_data'].empty:
            wordcloud_path = f"{output_dir}/wordcloud_{timestamp}.png"
            # 문서 내용이 필요하므로 별도 처리 필요

        # 5. JSON 리포트
        json_path = f"{output_dir}/analysis_report_{timestamp}.json"

        # JSON 직렬화 가능한 데이터만 추출
        json_data = {}
        if 'hot_keywords' in results:
            json_data['hot_keywords'] = [(k, int(f)) for k, f in results['hot_keywords']]
        if 'clusters' in results:
            json_data['clusters'] = {str(k): v for k, v in results['clusters'].items()}

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        report_files['json_report'] = json_path

        self.logger.info(f"리포트 생성 완료: {len(report_files)}개 파일")

        return report_files

    def print_summary(self, results: Dict):
        """
        분석 결과 요약 출력

        Args:
            results: 분석 결과 딕셔너리
        """
        print("\n" + "="*60)
        print("키워드 트렌드 분석 결과 요약")
        print("="*60)

        # 인기 키워드
        if 'hot_keywords' in results:
            print("\n🔥 상위 인기 키워드:")
            for i, (keyword, freq) in enumerate(results['hot_keywords'][:10], 1):
                print(f"  {i}. {keyword} ({freq}회)")

        # 클러스터
        if 'clusters' in results:
            print("\n📊 키워드 클러스터:")
            for cluster_id, keywords in results['clusters'].items():
                print(f"  클러스터 {cluster_id}: {', '.join(keywords[:5])}")

        # 네트워크 통계
        if 'network' in results:
            G = results['network']
            print(f"\n🌐 네트워크 통계:")
            print(f"  - 노드 수: {G.number_of_nodes()}")
            print(f"  - 엣지 수: {G.number_of_edges()}")
            print(f"  - 연결 밀도: {nx.density(G):.4f}")

            # 중심성 상위 키워드
            centrality = nx.degree_centrality(G)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  - 중심성 상위 키워드: {', '.join([kw for kw, _ in top_central])}")

        print("\n" + "="*60 + "\n")


# ============================================================================
# 메인 실행
# ============================================================================

def main():
    """메인 실행 함수"""
    print("키워드 트렌드 분석 시스템")
    print("="*60)

    # 시스템 초기화
    try:
        system = KeywordTrendSystem(analyzer_type='okt')
    except ImportError as e:
        print(f"\n오류: {e}")
        print("\n설치 방법:")
        print("1. Java JDK 8 이상 설치")
        print("2. pip install konlpy")
        print("3. pip install networkx wordcloud scikit-learn")
        return

    # 로그 파일 분석
    print("\n로그 파일 분석 중...")
    results = system.analyze_from_logs('logs')

    if not results:
        print("분석 결과가 없습니다.")
        return

    # 결과 출력
    system.print_summary(results)

    # 리포트 생성
    print("\n리포트 생성 중...")
    report_files = system.generate_report(results)

    print("\n생성된 리포트:")
    for report_type, file_path in report_files.items():
        print(f"  - {report_type}: {file_path}")

    print("\n분석 완료!")


if __name__ == "__main__":
    main()
