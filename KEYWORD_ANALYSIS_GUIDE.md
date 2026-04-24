# 키워드 트렌드 분석 시스템 사용 가이드

KoNLPy 형태소 분석기를 활용한 한국어 키워드 추출 및 트렌드 분석 시스템입니다.

## 📋 목차

1. [기능 소개](#기능-소개)
2. [설치 방법](#설치-방법)
3. [빠른 시작](#빠른-시작)
4. [상세 사용법](#상세-사용법)
5. [API 레퍼런스](#api-레퍼런스)
6. [활용 예시](#활용-예시)

## 🚀 기능 소개

### 주요 기능

1. **한국어 형태소 분석**
   - KoNLPy 기반 형태소 분석 (Okt, Mecab, Komoran, Hannanum, Kkma)
   - 명사, 동사, 형용사 추출
   - 불용어 필터링

2. **키워드 트렌드 분석**
   - 일별/주별/월별 키워드 빈도 추이 분석
   - 키워드 성장률 계산
   - 인기 키워드 추출

3. **연관 키워드 분석**
   - 동시 출현 행렬 생성
   - 키워드 네트워크 분석
   - 클러스터링 및 유사 키워드 추출

4. **시각화**
   - 인터랙티브 트렌드 차트
   - 워드클라우드
   - 네트워크 그래프
   - 성장률 히트맵

## 📦 설치 방법

### 1. 사전 요구사항

**Java JDK 8 이상**
- KoNLPy는 Java 기반이므로 JDK가 필요합니다.
```bash
# Windows: Oracle JDK 또는 OpenJDK 설치
# macOS: brew install openjdk@11
# Linux: sudo apt install openjdk-11-jdk
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
```
konlpy>=0.6.0           # 한국어 형태소 분석
networkx>=3.1           # 네트워크 분석
wordcloud>=1.9.0        # 워드클라우드
scikit-learn>=1.3.0     # 머신러닝 (클러스터링)
numpy>=1.24.0           # 수치 연산
```

### 3. KoNLPy 설정 (선택사항)

Mecab 형태소 분석기를 사용하려면 추가 설치가 필요합니다.

**Windows:**
```bash
pip install eunjeon
```

**macOS/Linux:**
```bash
bash <(curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh)
```

## 🎯 빠른 시작

### 기본 사용법

```python
from keyword_trend_analyzer import KeywordTrendSystem

# 시스템 초기화
system = KeywordTrendSystem(analyzer_type='okt')

# 로그 파일 분석
results = system.analyze_from_logs('logs')

# 결과 요약 출력
system.print_summary(results)

# 리포트 생성
report_files = system.generate_report(results)
```

### 테스트 실행

```bash
python test_keyword_analyzer.py
```

## 📖 상세 사용법

### 1. 형태소 분석

```python
from keyword_trend_analyzer import KoreanMorphemeAnalyzer

# 분석기 초기화
analyzer = KoreanMorphemeAnalyzer(analyzer_type='okt')

text = "인공지능과 머신러닝 기술이 급격히 발전하고 있습니다."

# 명사 추출
nouns = analyzer.extract_nouns(text)
print(nouns)  # ['인공지능', '머신러닝', '기술', '발전']

# 품사 태깅
pos_tags = analyzer.extract_pos_tags(text)
print(pos_tags)  # [('인공지능', 'Noun'), ('머신러닝', 'Noun'), ...]

# 키워드 추출 (상위 N개)
keywords = analyzer.extract_keywords(text, top_n=5)
print(keywords)  # [('인공지능', 2), ('머신러닝', 1), ...]
```

### 2. 트렌드 분석

```python
from keyword_trend_analyzer import KeywordTrendAnalyzer

# 분석기 초기화
trend_analyzer = KeywordTrendAnalyzer()

# 문서 데이터 준비
documents = [
    {
        'title': 'AI 기술 동향',
        'content': '인공지능 기술이 발전하고 있습니다...',
        'date': '2026-04-01'
    },
    # ... 더 많은 문서
]

# 트렌드 분석 (주별)
trend_df = trend_analyzer.analyze_document_trend(documents, period='weekly')

# 성장률 계산
growth_df = trend_analyzer.calculate_keyword_growth(trend_df)

# 인기 키워드 추출 (최근 7일)
hot_keywords = trend_analyzer.get_hot_keywords(trend_df, period_days=7, top_n=10)
```

### 3. 연관 키워드 분석

```python
from keyword_trend_analyzer import RelatedKeywordAnalyzer
import networkx as nx

# 분석기 초기화
related_analyzer = RelatedKeywordAnalyzer()

# 문서 리스트
documents = ["문서 내용 1...", "문서 내용 2...", ...]

# 동시 출현 행렬 생성
co_occurrence = related_analyzer.extract_co_occurrence_matrix(documents)

# 네트워크 생성
network = related_analyzer.build_keyword_network(documents, top_n=50)

# 네트워크 분석
print(f"노드 수: {network.number_of_nodes()}")
print(f"엣지 수: {network.number_of_edges()}")

# 클러스터링
clusters = related_analyzer.detect_keyword_clusters(documents, n_clusters=5)

# 유사 키워드 찾기
similar = related_analyzer.find_similar_keywords(documents, '인공지능', top_n=10)
```

### 4. 시각화

```python
from keyword_trend_analyzer import KeywordVisualizer

visualizer = KeywordVisualizer()

# 트렌드 라인 차트
fig = visualizer.plot_trend_line(
    trend_df,
    keywords=['인공지능', '머신러닝'],  # None이면 상위 키워드 자동 선택
    save_path='charts/trend.html'
)

# 네트워크 그래프
fig = visualizer.plot_network_graph(
    network,
    layout='spring',  # spring, circular, random, shell
    save_path='charts/network.html'
)

# 워드클라우드
wc = visualizer.plot_wordcloud(
    documents,
    save_path='charts/wordcloud.png'
)

# 성장률 히트맵
fig = visualizer.plot_growth_heatmap(
    growth_df,
    save_path='charts/heatmap.html'
)
```

### 5. 통합 분석 시스템

```python
from keyword_trend_analyzer import KeywordTrendSystem

# 시스템 초기화
system = KeywordTrendSystem(analyzer_type='okt')

# 방법 1: 로그 파일 분석
results = system.analyze_from_logs('logs')

# 방법 2: 문서 직접 분석
documents = [
    {'title': '제목', 'content': '내용', 'date': '2026-04-01'},
    # ...
]
results = system.analyze_documents(documents)

# 결과 확인
system.print_summary(results)

# 리포트 생성
report_files = system.generate_report(results, output_dir='charts')

# 개별 분석 결과 접근
trend_data = results['trend_data']          # pd.DataFrame
growth_data = results['growth_data']        # pd.DataFrame
hot_keywords = results['hot_keywords']      # List[Tuple[str, int]]
network = results['network']                # nx.Graph
clusters = results['clusters']              # Dict[int, List[str]]
```

## 📚 API 레퍼런스

### AnalyzerConfig

분석기 설정 클래스

```python
class AnalyzerConfig:
    # 텍스트 처리
    MIN_WORD_LENGTH: int = 2          # 최소 단어 길이
    MAX_WORD_LENGTH: int = 20         # 최대 단어 길이
    MIN_KEYWORD_FREQ: int = 2         # 최소 키워드 빈도
    TOP_N_KEYWORDS: int = 50          # 추출할 상위 키워드 수

    # 형태소 분석
    POS_TAGS: List[str] = [...]       # 추출할 품사 태그
    STOP_WORDS: Set[str] = {...}      # 불용어 집합

    # 트렌드 분석
    TIME_PERIODS: List[str] = ['daily', 'weekly', 'monthly']

    # 네트워크 분석
    MIN_CO_OCCURRENCE: int = 2        # 최소 동시 출현 빈도
    MAX_EDGES: int = 100              # 최대 엣지 수
    MIN_CLUSTER_SIZE: int = 2         # 최소 클러스터 크기

    # 시각화
    CHART_DIR: str = "charts"         # 차트 저장 경로
```

### KoreanMorphemeAnalyzer

형태소 분석기 클래스

**메서드:**
- `extract_nouns(text: str) -> List[str]`: 명사 추출
- `extract_pos_tags(text: str, pos_tags: List[str]) -> List[Tuple[str, str]]`: 품사 태깅
- `extract_keywords(text: str, top_n: int) -> List[Tuple[str, int]]`: 키워드 추출
- `normalize_text(text: str) -> str`: 텍스트 정규화

### KeywordTrendAnalyzer

트렌드 분석기 클래스

**메서드:**
- `analyze_document_trend(documents: List[Dict], period: str) -> pd.DataFrame`: 문서 트렌드 분석
- `calculate_keyword_growth(trend_df: pd.DataFrame, top_n: int) -> pd.DataFrame`: 성장률 계산
- `get_hot_keywords(trend_df: pd.DataFrame, period_days: int, top_n: int) -> List[Tuple[str, int]]`: 인기 키워드 추출

### RelatedKeywordAnalyzer

연관 키워드 분석기 클래스

**메서드:**
- `extract_co_occurrence_matrix(documents: List[str]) -> Dict[Tuple[str, str], int]`: 동시 출현 행렬 생성
- `build_keyword_network(documents: List[str], top_n: int) -> nx.Graph`: 네트워크 생성
- `detect_keyword_clusters(documents: List[str], n_clusters: int) -> Dict[int, List[str]]`: 클러스터링
- `find_similar_keywords(documents: List[str], keyword: str, top_n: int) -> List[Tuple[str, float]]`: 유사 키워드 찾기

### KeywordVisualizer

시각화 클래스

**메서드:**
- `plot_trend_line(trend_df: pd.DataFrame, keywords: List[str], top_n: int, save_path: str) -> go.Figure`: 트렌드 차트
- `plot_wordcloud(documents: List[str], save_path: str) -> WordCloud`: 워드클라우드
- `plot_network_graph(G: nx.Graph, layout: str, save_path: str) -> go.Figure`: 네트워크 그래프
- `plot_growth_heatmap(growth_df: pd.DataFrame, save_path: str) -> go.Figure`: 성장률 히트맵

### KeywordTrendSystem

통합 분석 시스템 클래스

**메서드:**
- `analyze_from_logs(log_dir: str) -> Dict`: 로그 파일 분석
- `analyze_documents(documents: List[Dict]) -> Dict`: 문서 분석
- `generate_report(results: Dict, output_dir: str) -> Dict[str, str]`: 리포트 생성
- `print_summary(results: Dict)`: 결과 요약 출력

## 💡 활용 예시

### 예시 1: 웹 크롤러 데이터 분석

```python
from keyword_trend_analyzer import KeywordTrendSystem
import pandas as pd

# 시스템 초기화
system = KeywordTrendSystem()

# 웹 크롤러 결과 로드 (Excel)
df = pd.read_excel('crawl_results.xlsx')

# 문서 형식으로 변환
documents = []
for _, row in df.iterrows():
    documents.append({
        'title': row['title'],
        'content': row['description'],
        'date': row['date']
    })

# 분석
results = system.analyze_documents(documents)
system.print_summary(results)

# 리포트 생성
system.generate_report(results)
```

### 예시 2: 커스텀 설정 사용

```python
from keyword_trend_analyzer import KeywordTrendSystem, AnalyzerConfig

# 커스텀 설정
config = AnalyzerConfig()
config.MIN_WORD_LENGTH = 3          # 3글자 이상만 추출
config.MIN_KEYWORD_FREQ = 5         # 최소 5회 등장
config.STOP_WORDS.add('추가단어')    # 불용어 추가

# 시스템 초기화
system = KeywordTrendSystem(analyzer_type='mecab', config=config)

# 분석 실행
results = system.analyze_from_logs('logs')
```

### 예시 3: 실시간 키워드 모니터링

```python
from keyword_trend_analyzer import KeywordTrendAnalyzer
from datetime import datetime, timedelta

analyzer = KeywordTrendAnalyzer()

# 최신 문서 가져오기
recent_docs = get_recent_documents(days=7)  # 사용자 정의 함수

# 트렌드 분석
trend_df = analyzer.analyze_document_trend(recent_docs, period='daily')

# 급성장 키워드 찾기
growth_df = analyzer.calculate_keyword_growth(trend_df, top_n=50)

# 성장률 100% 이상 키워드
surging_keywords = growth_df[growth_df['growth_rate'] > 100]

print("급상승 키워드:")
for _, row in surging_keywords.iterrows():
    print(f"{row['keyword']}: {row['growth_rate']:.1f}%")
```

## 🎨 출력 형식

### 1. 트렌드 차트 (HTML)
- 인터랙티브한 Plotly 차트
- 키워드별 빈도 추이
- 마우스 오버시 상세 정보

### 2. 네트워크 그래프 (HTML)
- 노드: 키워드 (크기 = 빈도)
- 엣지: 동시 출현 관계 (두께 = 빈도)
- 인터랙티브 탐색

### 3. 워드클라우드 (PNG)
- 키워드 크기 = 빈도
- 색상으로 구분
- 고해상도 출력 (300 DPI)

### 4. JSON 리포트
- 구조화된 데이터
- 프로그래밍 방식 활용 가능
- UTF-8 인코딩

## ⚠️ 주의사항

### 1. Java 환경
- KoNLPy는 Java 기반입니다
- JDK 8 이상이 필요합니다
- JAVA_HOME 환경변수 설정 확인

### 2. 메모리 사용
- 대용량 문서 분석 시 메모리 사용량이 높을 수 있습니다
- 문서를 나누어 분석하거나 샘플링을 고려하세요

### 3. 형태소 분석기 선택
- **Okt**: 기본, 가장 안정적
- **Mecab**: 빠름, 추가 설치 필요
- **Komoran**: 정확도 높음
- **Hannanum**: 명사 위주
- **Kkma**: 상세 분석

### 4. 한글 폰트
- 워드클라우드 생성 시 한글 폰트 필요
- Windows: malgun.ttf (기본)
- macOS: AppleGothic 또는 나눔고딕

## 🔧 문제 해결

### KoNLPy 설치 오류

```bash
# Java 재설치
# Windows: 제어판 > 프로그램 제거 > Java 재설치
# macOS: brew reinstall openjdk@11

# JAVA_HOME 설정
# Windows: 시스템 환경 변수 추가
# macOS/Linux: export JAVA_HOME=/path/to/java
```

### 메모리 오류

```python
# 문서 샘플링
sample_documents = documents[:100]

# 또는 배치 처리
batch_size = 100
for i in range(0, len(documents), batch_size):
    batch = documents[i:i+batch_size]
    # 분석 실행
```

### 폰트 오류

```python
from keyword_trend_analyzer import AnalyzerConfig

config = AnalyzerConfig()
config.FONT_PATH = "/path/to/your/font.ttf"  # 폰트 경로 지정
```

## 📞 추가 도움

- 테스트: `python test_keyword_analyzer.py`
- 예제: `python keyword_trend_analyzer.py`
- 로그: `logs/` 디렉토리 확인
- 차트: `charts/` 디렉토리 확인

---

*마지막 업데이트: 2026-04-25*
