# 다국어 지원 및 번역 기능 가이드

이 가이드는 DealBot의 다국어 지원 및 Google Translation API 연동 기능을 설명합니다.

## 📋 목차

1. [기능 개요](#기능-개요)
2. [설정 방법](#설정-방법)
3. [사용 방법](#사용-방법)
4. [API 예제](#api-예제)
5. [지원 언어](#지원-언어)
6. [문제 해결](#문제-해결)

## 🎯 기능 개요

### 주요 기능

- **Google Translation API 연동**: 강력한 번역 서비스 통합
- **다국어 키워드 검색**: 하나의 키워드를 여러 언어로 검색
- **자동 언어 감지**: 텍스트 언어 자동 인식
- **결과 번역**: 검색 결과를 원하는 언어로 번역
- **일괄 번역**: 여러 텍스트/키워드 동시 번역
- **캐싱 지원**: 번역 결과 캐싱으로 성능 최적화

### 지원 언어

- 한국어 (ko)
- 영어 (en)
- 일본어 (ja)
- 중국어 (zh)
- 스페인어 (es)
- 프랑스어 (fr)
- 독일어 (de)
- 러시아어 (ru)
- 아랍어 (ar)
- 포르투갈어 (pt)
- 이탈리아어 (it)
- 베트남어 (vi)
- 태국어 (th)
- 힌디어 (hi)

## 🔧 설정 방법

### 1. Google Cloud 프로젝트 설정

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스** → **라이브러리** 이동
4. "Cloud Translation API" 검색 및 활성화
5. **API 및 서비스** → **사용자 인증 정보** 이동
6. **사용자 인증 정보 만들기** → **서비스 계정** 선택
7. 서비스 계정 생성 및 JSON 키 파일 다운로드

### 2. 환경 설정

두 가지 인증 방법 중 하나를 선택하여 설정:

#### 방법 A: 서비스 계정 키 파일 사용

```json
{
  "credentials_path": "/path/to/your/service-account-key.json",
  "api_key": "",
  "default_target_language": "en",
  "supported_languages": ["ko", "en", "ja", "zh", "es"],
  "auto_detect_language": true,
  "translate_search_results": true,
  "translate_keywords": true,
  "cache_translations": true,
  "max_cache_size": 1000
}
```

#### 방법 B: API 키 사용

```json
{
  "credentials_path": "",
  "api_key": "YOUR_API_KEY_HERE",
  "default_target_language": "en",
  "supported_languages": ["ko", "en", "ja", "zh", "es"],
  "auto_detect_language": true,
  "translate_search_results": true,
  "translate_keywords": true,
  "cache_translations": true,
  "max_cache_size": 1000
}
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `google-cloud-translate>=3.12.0`
- `google-auth>=2.23.0`

## 📖 사용 방법

### 방법 1: 대화형 프로그램 사용

```bash
python web_crawler.py
```

1. "다국어/번역 기능 사용? (y/n)" 메시지에 `y` 입력
2. 크롤링 모드에서 "7. 다국어 검색" 선택
3. 검색 키워드 입력
4. 검색할 언어 코드 선택 (예: ko,en,ja,zh)
5. 결과 번역 옵션 선택

### 방법 2: Python API 사용

```python
from web_crawler import WebCrawler

# 크롤러 초기화 (번역 기능 활성화)
crawler = WebCrawler(enable_translation=True)

# 다국어 검색
results = crawler.search_multilingual(
    keyword="기후변화",
    languages=["ko", "en", "ja", "zh"],
    max_results=10,
    translate_results=True,
    target_language="en"
)

# 결과 확인
for lang, articles in results.items():
    print(f"{lang}: {len(articles)}개 항목")

crawler.close()
```

### 방법 3: 예제 스크립트 실행

```bash
python multilingual_search_example.py
```

사용 가능한 예제:
1. 기본 번역 기능 테스트
2. 다국어 검색
3. 번역된 검색 결과
4. 여러 키워드 일괄 번역
5. 언어 감지
6. 사용자 정의 다국어 검색

## 💻 API 예제

### 기본 번역

```python
from translation_service import TranslationService, TranslationConfig

# 서비스 초기화
config = TranslationConfig()
service = TranslationService(
    credentials_path=config.get_credentials_path(),
    api_key=config.get_api_key()
)

# 텍스트 번역
text = "안녕하세요, 반갑습니다."
translated = service.translate(text, "en")
print(f"번역 결과: {translated}")
```

### 언어 감지

```python
# 언어 감지
text = "Hello, nice to meet you."
detected = service.detect_language(text)
print(f"감지된 언어: {detected}")
```

### 다국어 키워드 준비

```python
from translation_service import MultiLanguageSearchHelper

helper = MultiLanguageSearchHelper(service)

# 키워드를 여러 언어로 번역
multilingual_keywords = helper.prepare_multilingual_keywords(
    "인공지능",
    ["en", "ja", "zh", "es"]
)

print(multilingual_keywords)
# {'ko': ['인공지능'], 'en': ['artificial intelligence', '인공지능'], ...}
```

### 일괄 번역

```python
# 여러 텍스트 동시 번역
texts = ["안녕하세요", "감사합니다", "죄송합니다"]
translated = service.translate_batch(texts, "en")

print(translated)
# ['Hello', 'Thank you', 'Sorry']
```

### 딕셔너리 값 번역

```python
# 딕셔너리의 특정 키 값들 번역
data = {
    "제목": "테스트 제목",
    "요약": "이것은 테스트 요약입니다.",
    "링크": "https://example.com"
}

translated_data = service.translate_dict_values(
    data,
    target_language="en",
    keys_to_translate={"제목", "요약"}
)

print(translated_data)
# {'제목': 'Test Title', '요약': 'This is a test summary.', '링크': 'https://example.com'}
```

## 🌍 지원 언어

### 전체 언어 목록

| 코드   | 언어      |
|--------|-----------|
| ko     | Korean    |
| en     | English   |
| ja     | Japanese  |
| zh     | Chinese   |
| es     | Spanish   |
| fr     | French    |
| de     | German    |
| ru     | Russian   |
| ar     | Arabic    |
| pt     | Portuguese|
| it     | Italian   |
| vi     | Vietnamese|
| th     | Thai      |
| hi     | Hindi     |

### 언어 코드 사용

```python
from translation_service import SupportedLanguage

# 언어 코드 확인
print(SupportedLanguage.KOREAN.value)      # 'ko'
print(SupportedLanguage.ENGLISH.value)     # 'en'

# 언어 이름 확인
print(SupportedLanguage.get_language_name("ko"))  # 'Korean'

# 모든 지원 언어
all_languages = SupportedLanguage.get_all_languages()
for code, name in all_languages.items():
    print(f"{code}: {name}")
```

## 🔍 문제 해결

### 1. 인증 오류

**문제**: `DefaultCredentialsError: Could not automatically determine credentials`

**해결 방법**:
1. 서비스 계정 키 파일 경로 확인
2. `translation_config.json` 파일의 `credentials_path` 또는 `api_key` 설정 확인
3. 파일 읽기 권한 확인

### 2. API 활성화 오류

**문제**: `Cloud Translation API has not been used in project`

**해결 방법**:
1. Google Cloud Console에서 Cloud Translation API 활성화
2. 프로젝트 ID 확인
3. API 사용량 및 할당량 확인

### 3. 할당량 초과

**문제**: `Quota exceeded` 오류

**해결 방법**:
1. Google Cloud Console에서 할당량 증가 요청
2. 캐싱 기능 활성화로 API 호출 감소
3. 요청 간격 조정

### 4. 테스트 실패

**문제**: 단위 테스트는 성공하지만 통합 테스트 실패

**해결 방법**:
1. Google Cloud 자격 증명 설정 확인
2. 네트워크 연결 확인
3. API 키 유효성 확인

### 5. 번역 품질

**문제**: 번역 결과가 예상과 다름

**해결 방법**:
1. 원본 텍스트의 문맥 확인
2. 언어 코드가 올바른지 확인
3. 전문 용어의 경우 별도 용어집 사용

## 📚 추가 자료

- [Google Cloud Translation API 문서](https://cloud.google.com/translate/docs)
- [Google Cloud Python 클라이언트 라이브러리](https://cloud.google.com/python/docs/reference/translate/latest)
- [Google Cloud Console](https://console.cloud.google.com/)

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