#!/usr/bin/env python3
"""
머신러닝 기반 감정 분석 시스템
뉴스/블로그 텍스트의 긍정·부정·중립 감정을 분석하고 점수화합니다.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter

# 한글 형태소 분석
try:
    from konlpy.tag import Okt, Mecab, Komoran, Hannanum, Kkma
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    logging.warning("KoNLPY가 설치되지 않았습니다. 기본 토크나이저를 사용합니다.")

# 머신러닝 라이브러리 (선택사항)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from web_crawler import setup_logging

logger = setup_logging()


# ============================================================================
# 감정 사전 (한국어)
# ============================================================================

KOREAN_SENTIMENT_DICT = {
    'positive': {
        # 강한 긍정
        '최고', '강력하다', '혁신', '성공', '돌파', '기록', '상승', '증가', '확대',
        '약진', '도약', '발전', '개선', '향상', '선도', '우위', '경쟁력', '성장',
        '호조', '양호', '긍정', '밝다', '희망', '기대', '기회', '가능성', '잠재력',
        '효과', '성과', '달성', '완료', '해결', '개선', '진보', '혁신적', '뛰어나다',
        '탁월하다', '우수하다', '훌륭하다', '좋다', '즐겁다', '기쁘다', '만족',
        # 중간 긍정
        '안정', '유지', '지속', '정상', '적절', '합리', '원활', '순조', '평온',
        '편리', '유용', '효율', '생산', '참여', '협력', '지원', '후원', '격려',
        '인정', '칭찬', '축하', '환영', '감사', '사랑', '신뢰', '확신', '확신하다',
        # 약한 긍정
        '괜찮다', '나쁘지 않다', '그저그렇다', '무난하다', '적당하다'
    },
    'negative': {
        # 강한 부정
        '최악', '실패', '위기', '파산', '도산', '폐업', '해고', '축소', '감소',
        '하락', '반등', '급락', '폭락', '침체', '후퇴', '퇴보', '악화', '나빠지다',
        '어렵다', '힘들다', '고통', '고통스럽다', '비참', '절망', '绝望', '죽다',
        '죽임', '살해', '테러', '전쟁', '폭력', '범죄', '사기', '부정', '부정적',
        '위험', '위협', '손실', '피해', '손해', '해악', '독', '유해', '치명적',
        # 중간 부정
        '문제', '문제점', '단점', '약점', '결함', '오류', '버그', '장애', '고장',
        '불만', '불평', '항의', '비판', '비난', '공격', '반대', '거부', '기피',
        '거절', '거부', '무시', '무시하다', '무시당하다', '차별', '편견', '혐오',
        '증오', '싫다', '미워하다', '혐오하다', '역겨', '역겹다', '불쾌', '불쾌하다',
        # 약한 부정
        '걱정', '우려', '고민', '불안', '안타깝다', '아쉽다', '별로', '부족',
        '미흡', '부실', '약하다', '나쁘다', '안좋다', '못하다', '실패하다'
    },
    'intensifiers': {
        # 강조 표현
        '매우', '아주', '무척', '대단히', '정말', '진짜', '완전', '확실히',
        '분명', '의심할 여지 없이', '훨씬', '훨씬 더', '더욱', '더', '가장'
    },
    'negations': {
        # 부정 표현
        '아니', '않', '못', '못하다', '없', '없다', '아니하다', '아니다', '안'
    }
}


# ============================================================================
# 설정 및 데이터 클래스
# ============================================================================

@dataclass
class SentimentConfig:
    """감정 분석 설정"""
    # 형태소 분석기 타입
    tokenizer_type: str = 'okt'  # 'okt', 'mecab', 'komoran', 'hannanum', 'kkma', 'basic'

    # 감정 점수 가중치
    positive_weight: float = 1.0
    negative_weight: float = 1.0
    intensifier_weight: float = 1.5
    negation_weight: float = -1.3

    # 임계값
    positive_threshold: float = 0.1
    negative_threshold: float = -0.1

    # 기본 감정 사전 사용 여부
    use_basic_dict: bool = True

    # 커스텀 감정 사전 경로
    custom_dict_path: Optional[str] = None

    # ML 모델 사용 여부 (선택사항)
    use_ml_model: bool = False


@dataclass
class SentimentResult:
    """감정 분석 결과"""
    # 기본 정보
    text: str
    label: str  # 'positive', 'negative', 'neutral'
    confidence: float  # 0~1 사이 신뢰도

    # 점수
    sentiment_score: float  # -1.0 ~ 1.0 (음수: 부정, 양수: 긍정)
    positive_score: float  # 0~1 긍정 점수
    negative_score: float  # 0~1 부정 점수

    # 상세 정보
    positive_words: List[str] = field(default_factory=list)
    negative_words: List[str] = field(default_factory=list)
    word_count: int = 0

    # 메타데이터
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analyzer_type: str = 'basic'

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'sentiment_label': self.label,
            'sentiment_score': round(self.sentiment_score, 4),
            'positive_score': round(self.positive_score, 4),
            'negative_score': round(self.negative_score, 4),
            'confidence': round(self.confidence, 4),
            'positive_words': ', '.join(self.positive_words[:10]),  # 최대 10개
            'negative_words': ', '.join(self.negative_words[:10]),
            'word_count': self.word_count,
            'analyzed_at': self.analyzed_at
        }


# ============================================================================
# 형태소 분석기
# ============================================================================

class Tokenizer:
    """한국어 토크나이저"""

    def __init__(self, tokenizer_type: str = 'okt'):
        self.tokenizer_type = tokenizer_type
        self.tagger = None

        if KONLPY_AVAILABLE:
            try:
                if tokenizer_type == 'okt':
                    self.tagger = Okt()
                elif tokenizer_type == 'mecab':
                    self.tagger = Mecab()
                elif tokenizer_type == 'komoran':
                    self.tagger = Komoran()
                elif tokenizer_type == 'hannanum':
                    self.tagger = Hannanum()
                elif tokenizer_type == 'kkma':
                    self.tagger = Kkma()
                else:
                    logger.warning(f"알 수 없는 토크나이저 타입: {tokenizer_type}, 기본 토크나이저 사용")
                    self.tagger = Okt()
            except Exception as e:
                logger.warning(f"{tokenizer_type} 형태소 분석기 로드 실패: {e}, 기본 토크나이저 사용")
                self.tagger = Okt()

    def tokenize(self, text: str) -> List[str]:
        """텍스트를 형태소 단위로 분석"""
        if not text:
            return []

        text = self._preprocess(text)

        if self.tagger:
            try:
                # 형태소 분석 (명사, 동사, 형용사, 부사 추출)
                pos_tags = self.tagger.pos(text)
                # 의미 있는 품사만 추출
                meaningful_tags = ['Noun', 'Verb', 'Adjective', 'Adverb']
                tokens = [word for word, tag in pos_tags if tag in meaningful_tags and len(word) > 1]
                return tokens
            except Exception as e:
                logger.warning(f"형태소 분석 오류: {e}, 기본 방식 사용")

        # 기본 방식: 공백과 특수문자로 분리
        tokens = re.findall(r'[가-힣]{2,}', text)
        return tokens

    def _preprocess(self, text: str) -> str:
        """텍스트 전처리"""
        # URL 제거
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # 이메일 제거
        text = re.sub(r'\S+@\S+', '', text)
        # 특수문자 제거 (한글, 영어, 숫자, 공백 유지)
        text = re.sub(r'[^\w\s\uAC00-\uD7A3]', ' ', text)
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


# ============================================================================
# 감정 분석기
# ============================================================================

class SentimentAnalyzer:
    """감정 분석 메인 클래스"""

    def __init__(self, config: Optional[SentimentConfig] = None):
        self.config = config or SentimentConfig()
        self.tokenizer = Tokenizer(self.config.tokenizer_type)

        # 감정 사전 로드
        self.sentiment_dict = self._load_sentiment_dict()

        logger.info(f"감정 분석기 초기화 완료 (토크나이저: {self.config.tokenizer_type})")

    def _load_sentiment_dict(self) -> Dict:
        """감정 사전 로드"""
        # 기본 사전 복사
        sentiment_dict = {
            'positive': set(KOREAN_SENTIMENT_DICT['positive']),
            'negative': set(KOREAN_SENTIMENT_DICT['negative']),
            'intensifiers': set(KOREAN_SENTIMENT_DICT['intensifiers']),
            'negations': set(KOREAN_SENTIMENT_DICT['negations'])
        }

        # 커스텀 사전 로드
        if self.config.custom_dict_path:
            try:
                custom_path = Path(self.config.custom_dict_path)
                if custom_path.exists():
                    with open(custom_path, 'r', encoding='utf-8') as f:
                        custom_dict = json.load(f)

                    for category in ['positive', 'negative', 'intensifiers', 'negations']:
                        if category in custom_dict:
                            sentiment_dict[category].update(custom_dict[category])

                    logger.info(f"커스텀 감정 사전 로드 완료: {self.config.custom_dict_path}")
            except Exception as e:
                logger.warning(f"커스텀 사전 로드 실패: {e}")

        return sentiment_dict

    def analyze(self, text: str) -> SentimentResult:
        """텍스트 감정 분석"""
        if not text or not text.strip():
            return self._create_neutral_result(text or "")

        # 토큰화
        tokens = self.tokenizer.tokenize(text)
        if not tokens:
            return self._create_neutral_result(text)

        # 감정 단어 추출
        positive_words = []
        negative_words = []
        intensifiers_found = []
        negations_found = []

        for token in tokens:
            if token in self.sentiment_dict['positive']:
                positive_words.append(token)
            elif token in self.sentiment_dict['negative']:
                negative_words.append(token)
            elif token in self.sentiment_dict['intensifiers']:
                intensifiers_found.append(token)
            elif token in self.sentiment_dict['negations']:
                negations_found.append(token)

        # 감정 점수 계산
        sentiment_score = self._calculate_score(
            positive_words, negative_words,
            intensifiers_found, negations_found
        )

        # 라벨 결정
        if sentiment_score > self.config.positive_threshold:
            label = 'positive'
        elif sentiment_score < self.config.negative_threshold:
            label = 'negative'
        else:
            label = 'neutral'

        # 신뢰도 계산 (감정 단어가 많을수록 신뢰도 상승)
        total_emotion_words = len(positive_words) + len(negative_words)
        confidence = min(1.0, 0.5 + (total_emotion_words * 0.05))

        # 정규화된 점수 (0~1)
        positive_score = max(0, sentiment_score)
        negative_score = max(0, -sentiment_score)

        return SentimentResult(
            text=text[:200],  # 텍스트는 200자로 제한
            label=label,
            confidence=confidence,
            sentiment_score=sentiment_score,
            positive_score=positive_score,
            negative_score=negative_score,
            positive_words=positive_words,
            negative_words=negative_words,
            word_count=len(tokens),
            analyzer_type=self.config.tokenizer_type
        )

    def _calculate_score(
        self,
        positive_words: List[str],
        negative_words: List[str],
        intensifiers: List[str],
        negations: List[str]
    ) -> float:
        """감정 점수 계산"""
        # 기본 점수
        pos_score = len(positive_words) * self.config.positive_weight
        neg_score = len(negative_words) * self.config.negative_weight

        # 강조어 보정
        intensifier_count = len(intensifiers)
        if intensifier_count > 0:
            factor = self.config.intensifier_weight ** intensifier_count
            pos_score *= factor
            neg_score *= factor

        # 부정어 보정
        negation_count = len(negations)
        if negation_count > 0:
            # 부정어가 있으면 점수 반전
            factor = self.config.negation_weight ** negation_count
            total_score = (pos_score + neg_score) * factor
        else:
            total_score = pos_score - neg_score

        # 정규화 (-1 ~ 1 범위)
        max_score = max(abs(pos_score), abs(neg_score), 1)
        normalized_score = total_score / max_score

        return max(-1.0, min(1.0, normalized_score))

    def _create_neutral_result(self, text: str) -> SentimentResult:
        """중립 결과 생성"""
        return SentimentResult(
            text=text[:200] if text else "",
            label='neutral',
            confidence=0.0,
            sentiment_score=0.0,
            positive_score=0.0,
            negative_score=0.0,
            word_count=0
        )

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """여러 텍스트 일괄 분석"""
        results = []
        total = len(texts)

        for i, text in enumerate(texts):
            result = self.analyze(text)
            results.append(result)

            if (i + 1) % 10 == 0:
                logger.debug(f"감정 분석 진행: {i + 1}/{total}")

        return results

    def analyze_data(self, data: List[Dict]) -> List[Dict]:
        """크롤링 데이터에 감정 분석 결과 추가"""
        for item in data:
            title = item.get('title', '')
            content = item.get('content', '')

            # 제목과 내용 결합 (제목 가중치 높음)
            combined_text = f"{title} {title} {content}"

            # 감정 분석
            result = self.analyze(combined_text)

            # 결과에 추가
            item.update(result.to_dict())

        return data


# ============================================================================
# 감정 필터
# ============================================================================

class SentimentFilter:
    """감정 기반 데이터 필터링"""

    @staticmethod
    def filter_by_sentiment(
        data: List[Dict],
        sentiment: str = 'positive',
        min_score: float = 0.0
    ) -> List[Dict]:
        """
        감정 라벨로 필터링

        Args:
            data: 필터링할 데이터
            sentiment: 'positive', 'negative', 'neutral'
            min_score: 최소 감정 점수
        """
        return [
            item for item in data
            if item.get('sentiment_label') == sentiment
            and abs(item.get('sentiment_score', 0)) >= min_score
        ]

    @staticmethod
    def sort_by_sentiment(
        data: List[Dict],
        sentiment: str = 'positive',
        reverse: bool = True
    ) -> List[Dict]:
        """
        감정 점수로 정렬

        Args:
            data: 정렬할 데이터
            sentiment: 'positive' or 'negative'
            reverse: True면 내림차순
        """
        score_key = 'positive_score' if sentiment == 'positive' else 'negative_score'
        return sorted(data, key=lambda x: x.get(score_key, 0), reverse=reverse)

    @staticmethod
    def get_sentiment_distribution(data: List[Dict]) -> Dict[str, int]:
        """감정 분포 통계"""
        distribution = Counter(item.get('sentiment_label', 'neutral') for item in data)
        return dict(distribution)

    @staticmethod
    def get_sentiment_summary(data: List[Dict]) -> Dict:
        """감정 분석 요약 통계"""
        if not data:
            return {}

        positive_items = [d for d in data if d.get('sentiment_label') == 'positive']
        negative_items = [d for d in data if d.get('sentiment_label') == 'negative']
        neutral_items = [d for d in data if d.get('sentiment_label') == 'neutral']

        avg_scores = {
            'avg_positive_score': sum(d.get('positive_score', 0) for d in data) / len(data),
            'avg_negative_score': sum(d.get('negative_score', 0) for d in data) / len(data),
            'avg_sentiment_score': sum(d.get('sentiment_score', 0) for d in data) / len(data)
        }

        return {
            'total_count': len(data),
            'positive_count': len(positive_items),
            'negative_count': len(negative_items),
            'neutral_count': len(neutral_items),
            'positive_ratio': len(positive_items) / len(data) if data else 0,
            'negative_ratio': len(negative_items) / len(data) if data else 0,
            'neutral_ratio': len(neutral_items) / len(data) if data else 0,
            **avg_scores
        }


# ============================================================================
# 유틸리티
# ============================================================================

def create_custom_sentiment_dict(output_path: str = 'custom_sentiment_dict.json'):
    """커스텀 감정 사전 템플릿 생성"""
    template = {
        'positive': ['추가 긍정 단어1', '추가 긍정 단어2'],
        'negative': ['추가 부정 단어1', '추가 부정 단어2'],
        'intensifiers': ['추가 강조 단어1'],
        'negations': ['추가 부정 단어1']
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    logger.info(f"커스텀 감정 사전 템플릿 생성: {output_path}")
    return output_path


# ============================================================================
# 테스트 및 예시
# ============================================================================

if __name__ == '__main__':
    # 테스트 텍스트
    test_texts = [
        "이번 신제품은 정말 혁신적이고 기대가 됩니다. 성능이 매우 우수합니다.",
        "실망스럽습니다. 품질이 너무 나쁘고 문제가 많습니다.",
        "어제 회사에서 신제품 발표가 있었습니다. 흥미로운 기능들이 포함되어 있습니다.",
        "최악의 경험이었습니다. 다시는 이용하지 않겠습니다.",
        "아주 좋습니다. 강력하게 추천합니다!"
    ]

    # 분석기 초기화
    analyzer = SentimentAnalyzer()

    print("=" * 80)
    print("감정 분석 테스트")
    print("=" * 80)

    # 텍스트별 분석
    for i, text in enumerate(test_texts, 1):
        result = analyzer.analyze(text)

        print(f"\n[{i}] {text}")
        print(f"    라벨: {result.label}")
        print(f"    점수: {result.sentiment_score:.3f} (긍정: {result.positive_score:.3f}, 부정: {result.negative_score:.3f})")
        print(f"    신뢰도: {result.confidence:.3f}")
        print(f"    긍정 단어: {result.positive_words}")
        print(f"    부정 단어: {result.negative_words}")

    # 통계
    print("\n" + "=" * 80)
    print("감정 분포 통계")
    print("=" * 80)

    results = analyzer.analyze_batch(test_texts)

    # 더미 데이터 생성
    dummy_data = [{'title': text, 'sentiment_label': r.label, 'sentiment_score': r.sentiment_score,
                   'positive_score': r.positive_score, 'negative_score': r.negative_score}
                  for text, r in zip(test_texts, results)]

    summary = SentimentFilter.get_sentiment_summary(dummy_data)
    print(f"\n총 {summary['total_count']}개 분석:")
    print(f"  긍정: {summary['positive_count']}개 ({summary['positive_ratio']:.1%})")
    print(f"  부정: {summary['negative_count']}개 ({summary['negative_ratio']:.1%})")
    print(f"  중립: {summary['neutral_count']}개 ({summary['neutral_ratio']:.1%})")
    print(f"\n평균 감정 점수: {summary['avg_sentiment_score']:.3f}")
