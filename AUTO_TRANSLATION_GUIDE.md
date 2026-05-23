# 수집 데이터 자동 번역 기능 가이드

이 가이드는 DealBot의 수집 데이터 자동 번역 기능을 사용하는 방법을 설명합니다.

## 📋 목차

1. [기능 개요](#기능-개요)
2. [설정 방법](#설정-방법)
3. [사용 방법](#사용-방법)
4. [API 예제](#api-예제)
5. [데이터 구조](#데이터-구조)
6. [문제 해결](#문제-해결)

## 🎯 기능 개요

### 주요 기능

- **자동 번역**: 웹 크롤링 시 수집된 데이터를 자동으로 번역
- **필드 선택**: 번역할 데이터 필드 선택 가능 (제목, 요약 등)
- **원본 보존**: 번역된 데이터와 원본 데이터 모두 보존
- **진행률 표시**: 대량 데이터 번역 시 진행률 시각화
- **유연한 제어**: 런타임에 자동 번역 기능 활성화/비활성화

### 자동 번역 과정

1. 데이터 수집 (Google News, 네이버 블로그 등)
2. 번역 서비스 가용성 확인
3. 지정된 필드 자동 번역
4. 번역 결과를 새 필드에 저장
5. 원본 데이터와 번역 데이터 함께 저장

## 🔧 설정 방법

### 1. Google Cloud 프로젝트 설정

자동 번역 기능을 사용하려면 Google Translation API가 필요합니다:

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스** → **라이브러리** 이동
4. "Cloud Translation API" 검색 및 활성화
5. **API 및 서비스** → **사용자 인증 정보** 이동
6. **사용자 인증 정보 만들기** → **서비스 계정** 선택
7. 서비스 계정 생성 및 JSON 키 파일 다운로드

### 2. 번역 설정 파일 구성

`translation_config.json` 파일에서 자동 번역 설정:

```json
{
  "credentials_path": "/path/to/your/service-account-key.json",
  "api_key": "",
  "default_target_language": "en",
  "supported_languages": ["ko", "en", "ja", "zh", "es"],
  "auto_detect_language": true,
  "translate_search_results": true,  // 자동 번역 활성화
  "translate_keywords": true,
  "cache_translations": true,
  "max_cache_size": 1000
}
```

### 3. 크롤러 초기화 설정

```python
from web_crawler import WebCrawler

# 자동 번역 활성화로 크롤러 초기화
crawler = WebCrawler(
    enable_translation=True,
    auto_translate_collected=True  # 자동 번역 활성화
)
```

## 📖 사용 방법

### 방법 1: 대화형 프로그램 사용

```bash
python web_crawler.py
```

1. "다국어/번역 기능 사용? (y/n)" 메시지에 `y` 입력
2. "수집 데이터 자동 번역? (y/n)" 메시지에 `y` 입력
3. 원하는 모드 선택 (1-8)
4. 크롤링 시작 시 자동으로 번역 수행

### 방법 2: Python API 사용

#### 기본 자동 번역

```python
from web_crawler import WebCrawler

# 크롤러 초기화 (자동 번역 활성화)
crawler = WebCrawler(
    enable_translation=True,
    auto_translate_collected=True
)

# 검색 수행 (결과가 자동으로 번역됨)
results = crawler.search_google_news("인공지능", max_results=10)

# 결과 확인
for item in results:
    print(f"원본: {item['제목']}")
    print(f"번역: {item.get('제목_translated', 'N/A')}")

crawler.close()
```

#### 사용자 정의 필드 번역

```python
# 특정 필드만 번역
crawler = WebCrawler(
    enable_translation=True,
    auto_translate_collected=True,
    translate_fields={'제목'}  # 제목만 번역
)

results = crawler.search_naver_blog("기술", max_results=5)
```

#### 런타임 설정 변경

```python
# 자동 번역 비활성화 상태로 시작
crawler = WebCrawler(enable_translation=True)

# 필요할 때 자동 번역 활성화
crawler.enable_auto_translation(True)

# 번역 필드 변경
crawler.enable_auto_translation(True, {'제목', '요약'})

# 상태 확인
status = crawler.get_auto_translation_status()
print(f"자동 번역: {status['enabled']}")
print(f"번역 필드: {status['translate_fields']}")
```

#### 수동 번역

```python
# 자동 번역 없이 검색
crawler = WebCrawler(enable_translation=True, auto_translate_collected=False)
results = crawler.search_google_news("블록체인", max_results=5)

# 나중에 수동으로 번역
translated_results = crawler.auto_translate_batch(results)

# 단일 아이템 번역
translated_item = crawler.auto_translate_item(results[0])
```

### 방법 3: 테스트 스크립트 실행

```bash
python test_auto_translation.py
```

테스트 항목:
1. 기본 자동 번역 기능
2. 사용자 정의 필드 자동 번역
3. 수동 번역 기능
4. 상태 관리

## 💻 API 예제

### 자동 번역 상태 확인

```python
crawler = WebCrawler(enable_translation=True)
status = crawler.get_auto_translation_status()

print(f"서비스 사용 가능: {status['available']}")
print(f"자동 번역 활성화: {status['enabled']}")
print(f"번역 필드: {status['translate_fields']}")
print(f"목표 언어: {status['default_target_language']}")
```

### 자동 번역 활성화/비활성화

```python
# 활성화
crawler.enable_auto_translation(True)

# 비활성화
crawler.enable_auto_translation(False)

# 필드 지정 활성화
crawler.enable_auto_translation(True, {'제목', '요약', '설명'})
```

### 단일 아이템 번역

```python
# 번역할 데이터
item = {
    '제목': '한국어 제목',
    '요약': '한국어 요약 내용',
    '링크': 'https://example.com'
}

# 번역 수행
translated_item = crawler.auto_translate_item(item, target_language='en')

# 결과
# {
#     '제목': '한국어 제목',
#     '요약': '한국어 요약 내용',
#     '링크': 'https://example.com',
#     '제목_translated': 'Korean Title',
#     '요약_translated': 'Korean summary content',
#     '제목_lang': 'en',
#     '요약_lang': 'en'
# }
```

### 일괄 번역

```python
items = [
    {'제목': '첫 번째 기사', '요약': '첫 번째 요약'},
    {'제목': '두 번째 기사', '요약': '두 번째 요약'},
    {'제목': '세 번째 기사', '요약': '세 번째 요약'}
]

# 일괄 번역 (진행률 표시 포함)
translated_items = crawler.auto_translate_batch(items, target_language='ja')
```

## 📊 데이터 구조

### 번역된 데이터 구조

자동 번역이 적용된 데이터는 다음과 같은 구조를 가집니다:

```python
{
    # 원본 데이터 필드
    '키워드': '인공지능',
    '제목': '원본 제목',
    '요약': '원본 요약 내용',
    '출처/날짜': '출처 · 2024.01.01',
    '링크': 'https://example.com/article',
    '수집일시': '2024-01-01 12:00:00',

    # 자동으로 추가된 번역 필드
    '제목_translated': 'Translated Title',
    '요약_translated': 'Translated summary content',
    '제목_lang': 'en',        # 번역된 언어 코드
    '요약_lang': 'en'
}
```

### Excel 저장 시 필드

자동 번역된 데이터를 Excel로 저장하면 다음과 같은 열이 생성됩니다:

| 키워드 | 제목 | 제목_translated | 요약 | 요약_translated | 출처/날짜 | 링크 | 수집일시 |
|--------|------|-----------------|------|-----------------|-----------|------|----------|
| 인공지능 | 원본 제목 | Translated Title | 원본 요약 | Translated Summary | 출처 | 링크 | 2024-01-01 |

## 🔍 문제 해결

### 1. 번역이 되지 않을 때

**문제**: 데이터가 수집되지만 번역되지 않음

**해결 방법**:
1. 번역 서비스 상태 확인: `crawler.get_auto_translation_status()`
2. Google Cloud 자격 증명 확인
3. `auto_translate_collected=True` 설정 확인
4. API 할당량 확인

### 2. 특정 필드만 번역하고 싶을 때

**문제**: 모든 필드가 번역되어 불필요한 API 호출

**해결 방법**:
```python
# 번역할 필드 명시적 지정
crawler.enable_auto_translation(True, {'제목'})
```

### 3. 번역 속도가 느릴 때

**문제**: 대량 데이터 번역 시 속도가 느림

**해결 방법**:
1. 번역할 필드 수 줄이기
2. 결과 수 줄이기 (`max_results` 감소)
3. 번역 캐싱 활성화 확인
4. 비동기 처리 고려

### 4. 메모리 사용량이 높을 때

**문제**: 대량 데이터 처리 시 메모리 부족

**해결 방법**:
1. 작은 단위로 데이터 처리
2. 처리 후 데이터 정기적 저장
3. `auto_translate_batch` 대신 개별 `auto_translate_item` 사용

### 5. 번역 품질 문제

**문제**: 번역 결과가 만족스럽지 않음

**해결 방법**:
1. 원본 텍스트의 문맥 확인
2. 전문 용어의 경우 별도 용어집 사용 고려
3. 다른 언어로 번역 시도
4. 수동으로 중요한 부분만 번역

## 🚀 성능 최적화 팁

1. **캐싱 활용**: 번역 결과 캐싱으로 중복 번역 방지
2. **필드 최적화**: 필요한 필드만 번역하여 API 호출 감소
3. **배치 처리**: 대량 데이터는 작은 단위로 나누어 처리
4. **비동기 처리**: 향후 비동기 번역 기능 활용
5. **모니터링**: API 사용량과 비용 모니터링

## 📚 추가 자료

- [Google Cloud Translation API 문서](https://cloud.google.com/translate/docs)
- [Google Cloud Python 클라이언트 라이브러리](https://cloud.google.com/python/docs/reference/translate/latest)
- [다국어 지원 가이드](MULTILINGUAL_GUIDE.md)

## 🤝 기여

이 프로젝트에 기여하고 싶으시다면 다음을 확인해주세요:
1. [코드 컨벤션](#) 준수
2. 테스트 코드 작성
3. 문서 업데이트

## 📄 라이선스

이 프로젝트는 [라이선스 이름] 라이선스 하에 제공됩니다.

## 📞 지원

문의사항이나 버그 리포트는 다음을 통해 접수해주세요:
- 이슈 트래커: [GitHub Issues](#)
- 이메일: [support@example.com](mailto:support@example.com)