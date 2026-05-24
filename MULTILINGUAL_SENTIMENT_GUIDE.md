# 다국어 감정 분석 기능 가이드

이 가이드는 DealBot의 다국어 감정 분석 기능을 사용하는 방법을 설명합니다.

## 📋 목차

1. [기능 개요](#기능-개요)
2. [설치 및 설정](#설치-및-설정)
3. [지원 언어](#지원-언어)
4. [사용 방법](#사용-방법)
5. [API 예제](#api-예제)
6. [데이터 구조](#데이터-구조)
7. [문제 해결](#문제-해결)

## 🎯 기능 개요

### 주요 기능

- **다국어 감정 분석**: 8개 이상의 언어에서 감정 분석
- **언어 자동 감지**: 텍스트 언어 자동 인식
- **번역 통합**: Google Translation API와 연동하여 정확도 향상
- **언어별 사전**: 각 언어에 맞는 감정 사전 제공
- **실시간 분석**: 데이터 수집 시 자동 감정 분석
- **필터링 기능**: 언어와 감정 기반 데이터 필터링
- **통계 분석**: 언어별 감정 분포 및 통계 제공

### 감정 점스 척도

- **점수 범위**: -1.0 (완전 부정) ~ +1.0 (완전 긍정)
- **라벨 분류**:
  - `positive`: 긍정 (점수 > 0.1)
  - `negative`: 부정 (점수 < -0.1)
  - `neutral`: 중립 (-0.1 <= 점수 <= 0.1)

## 🔧 설치 및 설정

### 필수 의존성

```bash
# 한국어 형태소 분석
pip install konlpy

# 번역 서비스 (선택사항)
pip install google-cloud-translate>=3.12.0
pip install google-auth>=2.23.0
```

### Java 설정 (KoNLPy용)

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

### 설정 파일

`translation_config.json` 파일에서 번역 서비스 설정:

```json
{
  "credentials_path": "/path/to/your/service-account-key.json",
  "api_key": "",
  "default_target_language": "en",
  "supported_languages": ["ko", "en", "ja", "zh", "es", "fr", "de", "ru"],
  "translate_search_results": true,
  "auto_detect_language": true
}
```

## 🌍 지원 언어

### 전체 언어 목록

| 코드   | 언어      | 감정 사전 | 번역 지원 |
|--------|-----------|------------|----------|
| ko     | Korean    | ✅         | ✅       |
| en     | English   | ✅         | ✅       |
| ja     | Japanese  | ✅         | ✅       |
| zh     | Chinese   | ✅         | ✅       |
| es     | Spanish   | ✅         | ✅       |
| fr     | French    | ✅         | ✅       |
| de     | German    | ✅         | ✅       |
| ru     | Russian   | ✅         | ✅       |
| ar     | Arabic    | ⭕          | ✅       |
| pt     | Portuguese| ⭕          | ✅       |

✅ = 완전 지원, ⭕ = 부분 지원

## 📖 사용 방법

### 방법 1: 대화형 프로그램 사용

```bash
python web_crawler.py
```

1. "다국어 감정 분석 사용? (y/n)" 메시지에 `y` 입력
2. 모드 9 "다국어 감정 분석 테스트" 선택
3. 원하는 감정 분석 옵션 선택:
   - 단일 텍스트 분석
   - 검색 데이터 감정 분석
   - 감정 기반 필터링
   - 감정 통계 요약
   - 언어별 감정 분석
   - 활성화/비활성화

### 방법 2: Python API 사용

#### 기본 다국어 감정 분석

```python
from multilingual_sentiment_analyzer import MultilingualSentimentAnalyzer, MultilingualSentimentConfig

# 설정
config = MultilingualSentimentConfig(
    use_translation=True,
    enabled_languages=['ko', 'en', 'ja', 'zh', 'es']
)

# 분석기 초기화
analyzer = MultilingualSentimentAnalyzer(config)

# 텍스트 분석
result = analyzer.analyze("이 제품은 정말 혁신적입니다. 성능이 우수합니다.")

print(f"감정: {result.label}")
print(f"점수: {result.sentiment_score:.3f}")
print(f"감지 언어: {result.detected_language}")
```

#### 다국어 텍스트 분석

```python
# 다양한 언어 텍스트
texts = [
    ("이 제품은 정말 혁신적입니다.", "ko"),
    ("This product is innovative.", "en"),
    ("この製品は革新的です。", "ja"),
    ("这个产品很有创新性。", "zh")
]

for text, expected_lang in texts:
    result = analyzer.analyze(text)
    print(f"{expected_lang}: {result.label} ({result.sentiment_score:.3f})")
```

#### 크롤링 데이터에 감정 분석 적용

```python
from web_crawler import WebCrawler

# 크롤러 초기화 (다국어 감정 분석 활성화)
crawler = WebCrawler(
    enable_translation=True,
    enable_multilingual_sentiment=True
)

# 검색 (자동으로 감정 분석 적용)
data = crawler.search_google_news("인공지능", max_results=10)

# 결과 확인
for item in data:
    print(f"제목: {item['제목']}")
    print(f"감정: {item['sentiment_label']} (점수: {item['sentiment_score']:.3f})")
    print(f"감지 언어: {item['detected_language']}")

crawler.close()
```

#### 언어 및 감정 기반 필터링

```python
# 긍정 감정만 필터링
positive_data = crawler.filter_by_language_and_sentiment(data, 'positive')

# 한국어 부정 감정만 필터링
korean_negative = crawler.filter_by_language_and_sentiment(
    data, 'negative', language='ko', min_score=0.3
)

# 영어 긍정 감정만 필터링
english_positive = crawler.filter_by_language_and_sentiment(
    data, 'positive', language='en', min_score=0.5
)
```

#### 감정 통계 분석

```python
# 전체 통계
summary = crawler.get_sentiment_summary(data)

print(f"총 분석: {summary['total_count']}개")
print(f"긍정: {summary['positive_count']}개 ({summary['positive_ratio']:.1%})")
print(f"부정: {summary['negative_count']}개 ({summary['negative_ratio']:.1%})")
print(f"중립: {summary['neutral_count']}개 ({summary['neutral_ratio']:.1%})")
print(f"평균 점수: {summary['avg_sentiment_score']:.3f}")

# 언어별 분포
lang_dist = summary['language_distribution']
for lang, counts in lang_dist.items():
    print(f"{lang}: 긍정 {counts['positive']}, 부정 {counts['negative']}, 중립 {counts['neutral']}")
```

### 방법 3: 테스트 스크립트 실행

```bash
python test_multilingual_sentiment.py
```

테스트 항목:
1. 기본 다국어 감정 분석
2. 부정 감정 분석
3. 중립 감정 분석
4. 언어 감지
5. 일괄 분석
6. 데이터 통합
7. 다국어 필터
8. 설정

## 💻 API 예제

### 단일 텍스트 분석

```python
analyzer = MultilingualSentimentAnalyzer()

# 한국어 텍스트
result = analyzer.analyze("정말 좋은 제품입니다. 강력 추천합니다!")

# 영어 텍스트
result_en = analyzer.analyze("This is an excellent product. Highly recommended!")

# 일본어 텍스트
result_ja = analyzer.analyze("本当に良い製品です。強くお勧めします！")
```

### 일괄 분석

```python
texts = [
    "정말 좋은 제품입니다.",
    "품질이 좋지 않습니다.",
    "기능이 개선되었습니다.",
    "문제가 많습니다.",
    "보통 수준입니다."
]

results = analyzer.analyze_batch(texts)

for i, result in enumerate(results, 1):
    print(f"{i}. {result.label} ({result.sentiment_score:.3f})")
```

### 언어 감지

```python
text = "This is an English text."
detected_lang = analyzer.detect_language(text)
print(f"감지된 언어: {detected_lang}")
```

### 데이터 통합 분석

```python
# 크롤링 데이터
data = [
    {
        'title': '혁신적인 신제품 출시',
        'content': '이번 신제품은 정말 혁신적입니다.',
        'source': 'test'
    },
    {
        'title': 'Product Issues',
        'content': 'The product has several issues.',
        'source': 'test'
    }
]

# 감정 분석 적용
analyzed_data = analyzer.analyze_data(data)

# 결과 확인
for item in analyzed_data:
    print(f"제목: {item['title']}")
    print(f"감정: {item['sentiment_label']} ({item['sentiment_score']:.3f})")
    print(f"감지 언어: {item['detected_language']}")
```

### 사용자 정의 설정

```python
from multilingual_sentiment_analyzer import MultilingualSentimentConfig

config = MultilingualSentimentConfig(
    use_translation=True,
    enabled_languages=['ko', 'en', 'ja'],
    default_language='en',
    auto_detect_language=True,
    combine_results=True,
    prefer_original_language=True
)

analyzer = MultilingualSentimentAnalyzer(config)
```

## 📊 데이터 구조

### 감정 분석 결과 구조

```python
{
    # 기본 정보
    'text': '분석된 텍스트',
    'detected_language': 'ko',
    'sentiment_label': 'positive',
    'sentiment_score': 0.850,
    'positive_score': 0.850,
    'negative_score': 0.000,
    'confidence': 0.915,

    # 언어별 결과
    'ko_sentiment_score': 0.850,
    'ko_sentiment_label': 'positive',
    'en_sentiment_score': 0.780,
    'en_sentiment_label': 'positive',

    # 번역 정보
    'translation_used': True,
    'translated_text': 'This product is truly innovative...',

    # 상세 정보
    'positive_words': '혁신적, 우수, 좋은',
    'negative_words': '',
    'word_count': 5,

    # 메타데이터
    'analyzed_at': '2024-01-01T12:00:00',
    'analyzer_type': 'multilingual'
}
```

### Excel 저장 시 필드

감정 분석된 데이터를 Excel로 저장하면 다음과 같은 열이 생성됩니다:

| 제목 | 감정라벨 | 감정점수 | 긍정점수 | 부정점수 | 감지언어 | 번역사용 | 긍정단어 | 부정단어 |
|------|----------|----------|----------|----------|----------|----------|----------|----------|
| 혁신적 제품 | positive | 0.850 | 0.850 | 0.000 | ko | true | 혁신적, 우수 | |

## 🔍 문제 해결

### 1. 감정 분석이 정확하지 않을 때

**문제**: 감정 분석 결과가 예상과 다름

**해결 방법**:
1. 언어 감지가 올바른지 확인
2. 번역 서비스가 활성화되어 있는지 확인
3. 감정 사전에 해당 단어가 있는지 확인
4. 임계값 조정 (설정 파일)

### 2. 언어 감지 오류

**문제**: 언어가 올바르게 감지되지 않음

**해결 방법**:
1. 번역 서비스가 활성화되어 있는지 확인
2. Google Cloud 자격 증명 확인
3. 텍스트가 너무 짧지 않은지 확인
4. 수동으로 언어 지정 가능

### 3. 성능 문제

**문제**: 대량 데이터 분석 시 속도가 느림

**해결 방법**:
1. 번역 서비스 비활성화 (정확도 약간 감소)
2. 분석할 언어 수 줄이기
3. 배치 처리로 나누어 분석
4. 캐싱 활용

### 4. 한국어 분석 오류

**문제**: KoNLPy 관련 오류 발생

**해결 방법**:
1. Java JDK 8+ 설치 확인
2. 환경변수 `JAVA_HOME` 설정 확인
3. KoNLPY 재설치: `pip install --upgrade konlpy`
4. 다른 형태소 분석기 사용 (Mecab, Komoran)

### 5. 번역 오류

**문제**: 번역 관련 오류 발생

**해결 방법**:
1. Google Cloud Translation API 활성화 확인
2. API 할당량 확인
3. 자격 증명 파일 경로 확인
4. 번역 없이 분석 모드 사용

## 🚀 성능 최적화 팁

1. **언어 제한**: 필요한 언어만 지정
2. **번역 제어**: 정확도가 중요할 때만 번역 사용
3. **배치 처리**: 대량 데이터는 작은 단위로 처리
4. **캐싱 활용**: 중복 분석 방지
5. **비동기 처리**: 향후 비동기 분석 기능 활용

## 📈 활용 예시

### 1. 다국어 뉴스 감정 모니터링

```python
# 여러 국가 뉴스 수집 및 감정 분석
keywords = ['artificial intelligence', '인공지능', '人工知能', '人工知能']

results = {}
for keyword in keywords:
    data = crawler.search_google_news(keyword, 10)
    results[keyword] = data

# 전체 감정 통계
all_data = []
for keyword, data in results.items():
    all_data.extend(data)

summary = crawler.get_sentiment_summary(all_data)
```

### 2. 언어별 감정 비교

```python
# 같은 주제를 다른 언어로 검색
topic = "climate change"

data_en = crawler.search_google_news(topic, 10)  # 영어
data_ko = crawler.search_google_news("기후변화", 10)  # 한국어
data_ja = crawler.search_google_news("気候変動", 10)  # 일본어

# 각 언어별 감정 분석
for lang, data in [("en", data_en), ("ko", data_ko), ("ja", data_ja)]:
    summary = crawler.get_sentiment_summary(data)
    print(f"{lang}: 평균 점수 {summary['avg_sentiment_score']:.3f}")
```

### 3. 부정 뉴스 알림

```python
# 특정 키워드의 부정 뉴스 모니터링
keyword = "주식"
data = crawler.search_google_news(keyword, 20)

# 부정 뉴스 필터링
negative_news = crawler.filter_by_language_and_sentiment(
    data, 'negative', min_score=0.3
)

if len(negative_news) > 5:
    print("⚠️ 부정 뉴스가 많습니다! 주의 필요")
```

## 📚 추가 자료

- [감정 분석 가이드](SENTIMENT_ANALYSIS_GUIDE.md)
- [다국어 번역 가이드](MULTILINGUAL_GUIDE.md)
- [자동 번역 가이드](AUTO_TRANSLATION_GUIDE.md)
- [Google Cloud Translation API 문서](https://cloud.google.com/translate/docs)

## 🤝 기여

이 프로젝트에 기여하고 싶으시다면 다음을 확인해주세요:
1. 새로운 언어 감정 사전 추가
2. 기존 감정 사전 개선
3. 성능 최적화
4. 테스트 케이스 작성
5. 문서 업데이트

## 📄 라이선스

이 프로젝트는 [라이선스 이름] 라이선스 하에 제공됩니다.

## 📞 지원

문의사항이나 버그 리포트는 다음을 통해 접수해주세요:
- 이슈 트래커: [GitHub Issues](#)
- 이메일: [support@example.com](mailto:support@example.com)