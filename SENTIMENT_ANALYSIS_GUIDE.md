# 감정 분석 시스템 가이드

이 가이드는 머신러닝 기반 감정 분석 시스템의 사용법을 설명합니다.

## 목차

1. [개요](#개요)
2. [설치](#설치)
3. [기본 사용법](#기본-사용법)
4. [고급 기능](#고급-기능)
5. [API 레퍼런스](#api-레퍼런스)
6. [예시](#예시)
7. [FAQ](#faq)

---

## 개요

감정 분석 시스템은 수집된 뉴스/블로그 텍스트의 감정을 자동으로 분석하여 긍정·부정·중립으로 분류하고 점수화합니다.

### 주요 기능

- **한국어 감정 분석**: KoNLPy 기반 형태소 분석
- **감정 사전**: 500+ 개의 한국어 감정 단어 포함
- **다차원 점수**: 라벨 + 신뢰도 + 상세 점수 제공
- **필터링 & 정렬**: 감정 기반 데이터 필터링
- **커스터마이징**: 감정 사전, 임계값, 가중치 설정
- **일괄 처리**: 대량 텍스트 효율적 분석

### 감정 점스 척도

- **점수 범위**: -1.0 (완전 부정) ~ +1.0 (완전 긍정)
- **라벨 분류**:
  - `positive`: 긍정 (점수 > 임계값)
  - `negative`: 부정 (점수 < 임계값)
  - `neutral`: 중립 (임계값 사이)

---

## 설치

### 필수 의존성

```bash
pip install konlpy
```

### 선택사항 (고정확도)

```bash
# Transformer 기반 모델 사용 시
pip install transformers torch
```

### Java 설정 (KoNLPy용)

KoNLPy를 사용하려면 Java JDK 8 이상이 필요합니다.

**Windows:**
1. JDK 설치: [Oracle JDK](https://www.oracle.com/java/technologies/downloads/)
2. 환경변수 `JAVA_HOME` 설정
3. `PATH`에 `%JAVA_HOME%\bin` 추가

**macOS/Linux:**
```bash
# Homebrew (macOS)
brew install openjdk@11

# Ubuntu/Debian
sudo apt install openjdk-11-jdk
```

---

## 기본 사용법

### 1. 단일 텍스트 분석

```python
from sentiment_analyzer import SentimentAnalyzer

analyzer = SentimentAnalyzer()
result = analyzer.analyze("이 제품은 정말 좋습니다. 만족스럽습니다!")

print(f"감정: {result.label}")
print(f"점수: {result.sentiment_score:.3f}")
print(f"긍정 단어: {result.positive_words}")
print(f"부정 단어: {result.negative_words}")
```

**출력:**
```
감정: positive
점수: 0.850
긍정 단어: ['좋습니다', '만족스럽습니다']
부정 단어: []
```

### 2. 크롤링 데이터 분석

```python
from web_crawler import WebCrawler
from sentiment_analyzer import SentimentAnalyzer

crawler = WebCrawler()
analyzer = SentimentAnalyzer()

# 데이터 수집
data = crawler.search_google_news("인공지능", max_results=20)

# 감정 분석 적용
data = analyzer.analyze_data(data)

# 결과 확인
for item in data[:5]:
    print(f"제목: {item['title']}")
    print(f"감정: {item['sentiment_label']} (점수: {item['sentiment_score']:.3f})\n")
```

### 3. 감정 필터링

```python
from sentiment_analyzer import SentimentFilter

# 긍정 뉴스만 필터링
positive_news = SentimentFilter.filter_by_sentiment(data, 'positive', min_score=0.3)

# 부정 뉴스만 필터링
negative_news = SentimentFilter.filter_by_sentiment(data, 'negative', min_score=0.3)

# 긍정 점수 기준 정렬
sorted_news = SentimentFilter.sort_by_sentiment(data, 'positive', reverse=True)
```

---

## 고급 기능

### 1. 커스텀 설정

```python
from sentiment_analyzer import SentimentConfig, SentimentAnalyzer

config = SentimentConfig(
    # 형태소 분석기 타입
    tokenizer_type='okt',  # 'okt', 'mecab', 'komoran', 'hannanum', 'kkma'

    # 임계값 (긍정/부정 판단 기준)
    positive_threshold=0.2,   # 기본 0.1
    negative_threshold=-0.2,  # 기본 -0.1

    # 가중치
    positive_weight=1.0,      # 긍정 단어 가중치
    negative_weight=1.0,      # 부정 단어 가중치
    intensifier_weight=1.5,   # 강조어 가중치 (매우, 아주 등)
    negation_weight=-1.3,     # 부정어 가중치 (아니, 않 등)

    # 커스텀 감정 사전
    custom_dict_path='custom_dict.json'
)

analyzer = SentimentAnalyzer(config)
```

### 2. 커스텀 감정 사전

#### 템플릿 생성

```python
from sentiment_analyzer import create_custom_sentiment_dict

# 템플릿 파일 생성
create_custom_sentiment_dict('my_dict.json')
```

#### 사전 파일 형식

```json
{
  "positive": [
    "첨단",
    "최상",
    "탁월"
  ],
  "negative": [
    "미흡",
    "부족",
    "저조"
  ],
  "intensifiers": [
    "무척",
    "대단히"
  ],
  "negations": [
    "전혀",
    "도무지"
  ]
}
```

### 3. 형태소 분석기 선택

```python
# Okt (Twitter) - 기본값, 속도 빠름
analyzer = SentimentAnalyzer(SentimentConfig(tokenizer_type='okt'))

# Mecab - 가장 빠름, 설치 필요
analyzer = SentimentAnalyzer(SentimentConfig(tokenizer_type='mecab'))

# Komoran - 정확도 높음
analyzer = SentimentAnalyzer(SentimentConfig(tokenizer_type='komoran'))
```

### 4. 일괄 분석

```python
# 대량 텍스트 효율적 분석
texts = ["텍스트1", "텍스트2", ...]  # 수천 개 텍스트

results = analyzer.analyze_batch(texts)

# 결과 확인
for result in results:
    print(f"{result.label}: {result.sentiment_score:.3f}")
```

### 5. 통계 분석

```python
from sentiment_analyzer import SentimentFilter

# 감정 분포
distribution = SentimentFilter.get_sentiment_distribution(data)
print(distribution)
# {'positive': 45, 'negative': 12, 'neutral': 23}

# 요약 통계
summary = SentimentFilter.get_sentiment_summary(data)
print(f"총 {summary['total_count']}개")
print(f"긍정: {summary['positive_ratio']:.1%}")
print(f"부정: {summary['negative_ratio']:.1%}")
print(f"평균 점수: {summary['avg_sentiment_score']:.3f}")
```

---

## API 레퍼런스

### SentimentAnalyzer

```python
class SentimentAnalyzer:
    def __init__(self, config: Optional[SentimentConfig] = None)

    def analyze(self, text: str) -> SentimentResult:
        """단일 텍스트 감정 분석"""

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """여러 텍스트 일괄 분석"""

    def analyze_data(self, data: List[Dict]) -> List[Dict]:
        """크롤링 데이터 리스트에 감정 분석 결과 추가"""
```

### SentimentConfig

```python
@dataclass
class SentimentConfig:
    tokenizer_type: str = 'okt'
    positive_weight: float = 1.0
    negative_weight: float = 1.0
    intensifier_weight: float = 1.5
    negation_weight: float = -1.3
    positive_threshold: float = 0.1
    negative_threshold: float = -0.1
    use_basic_dict: bool = True
    custom_dict_path: Optional[str] = None
```

### SentimentResult

```python
@dataclass
class SentimentResult:
    text: str
    label: str  # 'positive', 'negative', 'neutral'
    confidence: float  # 0~1
    sentiment_score: float  # -1.0 ~ 1.0
    positive_score: float  # 0~1
    negative_score: float  # 0~1
    positive_words: List[str]
    negative_words: List[str]
    word_count: int
    analyzed_at: str
    analyzer_type: str

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
```

### SentimentFilter

```python
class SentimentFilter:
    @staticmethod
    def filter_by_sentiment(
        data: List[Dict],
        sentiment: str = 'positive',
        min_score: float = 0.0
    ) -> List[Dict]:
        """감정 라벨로 필터링"""

    @staticmethod
    def sort_by_sentiment(
        data: List[Dict],
        sentiment: str = 'positive',
        reverse: bool = True
    ) -> List[Dict]:
        """감정 점수로 정렬"""

    @staticmethod
    def get_sentiment_distribution(data: List[Dict]) -> Dict[str, int]:
        """감정 분포 통계"""

    @staticmethod
    def get_sentiment_summary(data: List[Dict]) -> Dict:
        """감정 요약 통계"""
```

---

## 예시

### 예시 1: 뉴스 감정 분석 자동화

```python
from web_crawler import WebCrawler
from sentiment_analyzer import SentimentAnalyzer, SentimentFilter
from email_notifier import EmailNotifier, EmailAuth

# 초기화
crawler = WebCrawler()
analyzer = SentimentAnalyzer()
notifier = EmailNotifier(EmailAuth())

# 데이터 수집 및 분석
data = crawler.search_google_news("AI", max_results=50)
data = analyzer.analyze_data(data)

# 긍정/부정 뉴스 분리
positive = SentimentFilter.filter_by_sentiment(data, 'positive', min_score=0.5)
negative = SentimentFilter.filter_by_sentiment(data, 'negative', min_score=0.5)

# 이메일 리포트
notifier.send_email(
    to_email="user@example.com",
    subject=f"AI 뉴스 감정 분석 리포트",
    body=f"""
    총 {len(data)}개 분석 완료

    긍정: {len(positive)}개 ({len(positive)/len(data):.1%})
    부정: {len(negative)}개 ({len(negative)/len(data):.1%})
    """
)
```

### 예시 2: 감정 트렌드 추적

```python
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 일별 감정 추이
days = 7
results_by_day = {}

for i in range(days):
    date = datetime.now() - timedelta(days=i)
    data = crawler.search_google_news("AI", max_results=20)
    data = analyzer.analyze_data(data)

    summary = SentimentFilter.get_sentiment_summary(data)
    results_by_day[date] = summary['avg_sentiment_score']

# 시각화
dates = list(reversed(results_by_day.keys()))
scores = [results_by_day[d] for d in dates]

plt.plot(dates, scores)
plt.title("일별 감정 점수 추이")
plt.xlabel("날짜")
plt.ylabel("평균 감정 점수")
plt.show()
```

---

## FAQ

### Q1: KoNLPy 설치 오류

**문제:** `OSError: Java gateway process exited` 오류 발생

**해결:**
1. Java JDK 8+ 설치
2. 환경변수 `JAVA_HOME` 설정
3. 터미널 재시작 후 재설치

### Q2: Mecab 설치 오류 (Windows)

**문제:** Mecab 형태소 분석기 로드 실패

**해결:**
```bash
pip install eunjeon  # Windows용 Mecab
```

코드에서:
```python
config = SentimentConfig(tokenizer_type='eunjeon')
```

### Q3: 분석 속도가 느린 경우

**해결:**
1. 캐싱 활성화: `WebCrawler(use_cache=True)`
2. 더 빠른 형태소 분석기 사용: `tokenizer_type='mecab'`
3. 일괄 처리: `analyze_batch()` 사용

### Q4: 분석 정확도가 낮은 경우

**해결:**
1. 커스텀 감정 사전 생성
2. 임계값 조정: `positive_threshold`, `negative_threshold`
3. 가중치 튜닝: `positive_weight`, `negative_weight`

### Q5: 영어/다른 언어 지원

현재 버전은 한국어 전용입니다. 다른 언어는:
1. Google Translation API로 번역 후 분석
2. 별도의 다국어 감정 분석기 구현

---

## 팁

### 성능 최적화

- 대량 데이터는 `analyze_batch()` 사용
- 반복 분석 시 캐싱 활성화
- 더 빠른 형태소 분석기 선택 (Mecab > Okt)

### 정확도 개선

- 도메인별 커스텀 감정 사전 생성
- 임계값을 데이터에 맞게 조정
- 제목과 내용의 가중치 조정

### 통합 활용

- 키워드 트렌드 분석과 결합
- 알림 시스템과 연동 (부정 뉴스 알림)
- 대시보드에서 실시간 감정 모니터링

---

## 추가 정보

- 전체 예시: `sentiment_example.py`
- 테스트 스크립트: `test_sentiment_analyzer.py`
- 이슈 리포트: GitHub Issues
