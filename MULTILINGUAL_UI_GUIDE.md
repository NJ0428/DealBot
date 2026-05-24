# 다국어 UI 지원 가이드

이 가이드는 DealBot 웹 인터페이스의 다국어 지원 기능을 사용하는 방법을 설명합니다.

## 📋 목차

1. [기능 개요](#기능-개요)
2. [지원 언어](#지원-언어)
3. [설치 및 실행](#설치-및-실행)
4. [사용 방법](#사용-방법)
5. [API 레퍼런스](#api-레퍼런스)
6. [커스터마이징](#커스터마이징)
7. [문제 해결](#문제-해결)

## 🎯 기능 개요

### 주요 기능

- **11개 언어 지원**: 한국어, 영어, 일본어, 중국어, 스페인어, 프랑스어, 독일어, 러시아어, 아랍어, 포르투갈어, 이탈리아어
- **자동 언어 감지**: 브라우저 언어 자동 감지 및 설정
- **실시간 언어 전환**: UI 언어 즉시 전환
- **RTL 언어 지원**: 아랍어 등 오른쪽에서 왼쪽으로 쓰는 언어 지원
- **테마 통합**: 다국어 폰트 및 레이아웃 자동 적용
- **번역 파일 관리**: JSON 기반 번역 파일 관리 시스템

### 지원 언어

| 코드   | 언어      | 네이티브 이름 | 방향 | 폰트 지원 |
|--------|-----------|-------------|------|-----------|
| ko     | Korean    | 한국어      | LTR  | ✅         |
| en     | English   | English     | LTR  | ✅         |
| ja     | Japanese  | 日本語      | LTR  | ✅         |
| zh     | Chinese   | 中文        | LTR  | ✅         |
| es     | Spanish   | Español     | LTR  | ✅         |
| fr     | French    | Français    | LTR  | ✅         |
| de     | German    | Deutsch     | LTR  | ✅         |
| ru     | Russian   | Русский     | LTR  | ✅         |
| ar     | Arabic    | العربية    | RTL  | ✅         |
| pt     | Portuguese| Português   | LTR  | ✅         |
| it     | Italian   | Italiano    | LTR  ✅         |

## 🌍 지원 언어

### 전체 언어 정보

- **Korean (ko)**: 한국어, 네이티브 이름 "한국어"
- **English (en)**: 영어, 네이티브 이름 "English"
- **Japanese (ja)**: 일본어, 네이티브 이름 "日本語"
- **Chinese (zh)**: 중국어, 네이티브 이름 "中文"
- **Spanish (es)**: 스페인어, 네이티브 이름 "Español"
- **French (fr)**: 프랑스어, 네이티브 이름 "Français"
- **German (de)**: 독일어, 네이티브 이름 "Deutsch"
- **Russian (ru)**: 러시아어, 네이티브 이름 "Русский"
- **Arabic (ar)**: 아랍어, 네이티브 이름 "العربية"
- **Portuguese (pt)**: 포르투갈어, 네이티브 이름 "Português"
- **Italian (it)**: 이탈리아어, 네이티브 이름 "Italiano"

## 🔧 설치 및 실행

### 1. 의존성 설치

```bash
# 기존 패키지
pip install flask pandas

# 다국어 폰트 지원 (자동 적용됨)
# Google Fonts에서 Noto Sans 시리즈 자동 로드
```

### 2. 서버 시작

```bash
python web_interface_multilingual.py
```

### 3. 접속

- **기본 URL**: http://localhost:5000
- **헬스체크**: http://localhost:5000/health

## 📖 사용 방법

### 방법 1: 브라우저 언어 설정

브라우저 기본 언어 설정에 따라 자동으로 언어가 설정됩니다.

**Chrome/Edge:**
1. 설정 → 언어
2. 선호하는 언어를 맨 위로 이동
3. 페이지 새로고침

**Firefox:**
1. 설정 → 일반 → 언어
2. 선호하는 언어 선택
3. 페이지 새로고침

### 방법 2: UI 언어 전환기

웹 인터페이스 상단에 있는 언어 전환기를 클릭하여 언어를 즉시 변경할 수 있습니다.

### 방법 3: URL 파라미터

URL에 언어 코드를 추가하여 특정 언어로 접속:

```bash
http://localhost:5000/?lang=en  # 영어
http://localhost:5000/?lang=ja  # 일본어
http://localhost:5000/?lang=ko  # 한국어
```

### 방법 4: 쿠키 설정

쿠키에 언어 설정이 저장되며, 다음 방문 시에도 유지됩니다.

## 💻 API 예제

### 언어 설정 API

```python
import requests

# 언어 변경
response = requests.post('http://localhost:5000/api/language', json={
    'language': 'en'
})

print(response.json())
# {'success': True, 'language': 'en', 'message': 'Language changed to English'}
```

### 번역 가져오기

```python
# 현재 언어 설정 확인
response = requests.get('http://localhost:5000/api/language')
current_data = response.json()

print(f"현재 언어: {current_data['current_language']}")
print(f"지원 언어: {current_data['supported_languages']}")
```

### 특정 언어 번역 가져오기

```python
# 영어 번역 가져오기
response = requests.get('http://localhost:5000/api/translations/en')

translations = response.json()
print(f"언어: {translations['language']}")
print(f"카테고리: {list(translations['translations'].keys())}")
```

### 감정 분석 API (다국어)

```python
# 다국어 텍스트 감정 분석
response = requests.post('http://localhost:5000/api/analyze_sentiment', json={
    'text': '이 제품은 정말 혁신적입니다.'
})

result = response.json()
print(f"감정: {result['result']['sentiment_label']}")
print(f"점수: {result['result']['sentiment_score']:.3f}")
print(f"감지 언어: {result['result']['detected_language']}")
```

## 🎨 커스터마이징

### 사용자 정의 번역 추가

```python
from multilingual_ui import UITranslations, LanguageCode

# 사용자 정의 번역 추가
custom_translations = {
    LanguageCode.KOREAN: "사용자 정의 환영 메시지",
    LanguageCode.ENGLISH: "Custom welcome message",
    LanguageCode.JAPANESE: "カスタムウェルカムメッセージ"
}

UITranslations.add_custom_translation('custom', 'welcome_message', custom_translations)
```

### 번역 파일 내보내기

```python
from multilingual_ui import TranslationFileManager

# 모든 언어의 번역 파일 내보내기
TranslationFileManager.export_all_languages('my_translations')

# 특정 언어만 내보내기
TranslationFileManager.save_translations_to_file('ko', 'translations_ko.json')
```

### 번역 파일 로드

```python
# 번역 파일에서 번역 로드
translations = TranslationFileManager.load_translations_from_file('translations_ko.json')
```

### 사용자 정의 번역 로드

```python
from multilingual_ui import UITranslations

# 기존 번역에 사용자 정의 번역 추가 (기존 번역 유지)
UITranslations.add_custom_translation(
    'custom',
    'special_feature',
    {
        LanguageCode.KOREAN: "특수 기능",
        LanguageCode.ENGLISH: "Special Feature"
    }
)
```

## 🔍 페이지별 번역

### 공통 번역

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| app_name | DealBot | DealBot | DealBot | DealBot |
| search | 검색 | Search | 検索 | 搜索 |
| download | 다운로드 | Download | ダウンロード | 下载 |
| home | 홈 | Home | ホーム | 首页 |
| loading | 로딩 중... | Loading... | 読み込み中... | 加载中... |

### 검색 페이지

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| title | 웹 검색 | Web Search | Web検索 | 网络搜索 |
| keyword_label | 검색어 | Keyword | 検索キーワード | 搜索关键词 |
| start_search | 검색 시작 | Start Search | 検索開始 | 开始搜索 |
| naver_blog | 네이버 블로그 | Naver Blog | NAVERブログ | Naver博客 |

### 결과 페이지

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| title | 검색 결과 | Search Results | 検索結果 | 搜索结果 |
| download_excel | Excel 다운로드 | Download Excel | Excelダウンロード | 下载Excel |
| total_results | 총 결과 수 | Total Results | 総結果数 | 总结果数 |

### 감정 분석

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| title | 감정 분석 | Sentiment Analysis | 感情分析 | 情感分析 |
| positive_score | 긍정 점수 | Positive Score | 肯定的スコア | 积极得分 |
| negative_score | 부정 점수 | Negative Score | 否定的スコア | 消极得分 |
| detected_language | 감지 언어 | Detected Language | 検出された言語 | 检测到的语言 |

### 설정 페이지

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| title | 설정 | Settings | 設定 | 设置 |
| language_settings | 언어 설정 | Language Settings | 言語設定 | 语言设置 |
| interface_language | 인터페이스 언어 | Interface Language | インターフェース言語 | 界面语言 |
| save_settings | 설정 저장 | Save Settings | 設定を保存 | 保存设置 |

### 에러 메시지

| 키 | 한국어 | 영어 | 일본어 | 중국어 |
|----|--------|------|--------|--------|
| keyword_required | 검색어를 입력해주세요. | Please enter a keyword. | 検索キーワードを入力してください。 | 请输入搜索关键词。 |
| search_failed | 검색 중 오류가 발생했습니다. | An error occurred during search. | 検索中にエラーが発生しました。 | 搜索过程中发生错误。 |
| file_not_found | 파일을 찾을 수 없습니다. | File not found. | ファイルが見つかりません。 | 文件未找到。 |

## 🌐 RTL 언어 지원

아랍어와 같은 RTL (오른쪽에서 왼쪽으로 쓰는) 언어의 경우:

- HTML `dir="rtl"` 속성 자동 적용
- 레이아웃 자동 조정
- 텍스트 정렬 자동 변경
- 폼 요소 방향 자동 조정

```html
<html lang="ar" dir="rtl">
<head>
    <!-- 자동으로 RTL 스타일 적용됨 -->
</head>
<body>
    <!-- 오른쪽에서 왼쪽으로 정렬 -->
    <div class="content">...</div>
</body>
</html>
```

## 🔧 설정 옵션

### 기본 언어 변경

```python
from multilingual_ui import I18N, LanguageCode

# 영어를 기본 언어로 설정
i18n = I18N(default_language=LanguageCode.ENGLISH)
```

### 지원 언어 제한

```python
# 특정 언어만 지원
supported = [LanguageCode.KOREAN, LanguageCode.ENGLISH, LanguageCode.JAPANESE]
```

### 번역 파일 경로 설정

```python
# 커스텀 번역 파일 경로
app.config['TRANSLATIONS_FOLDER'] = 'custom_translations'
```

## 🚀 성능 최적화

1. **번역 캐싱**: 번역 결과를 메모리에 캐싱하여 반복 로드 방지
2. **지연 로딩**: 번역 파일을 필요할 때만 로드
3. **압축 전송**: JSON 압축으로 번역 파일 크기 감소
4. **CDN 폰트**: Google Fonts CDN을 통한 폰트 로드 최적화

## 🧪 테스트

### 테스트 실행

```bash
python test_multilingual_ui.py
```

테스트 항목:
1. 번역 시스템 기본 기능
2. 언어 감지
3. 언어 전환
4. HTML 생성
5. 파일 작업
6. 에러 메시지
7. 페이지별 번역
8. 사용자 정의 번역
9. 번역 내보내기
10. RTL 언어 지원

### 테스트 결과 확인

```bash
# 성공적 테스트 결과
🎉 모든 테스트가 성공적으로 완료되었습니다!

총계: 10/10 테스트 통과
```

## 📱 모바일 지원

- 반응형 디자인으로 모바일과 데스크톑 모두 지원
- 터치 친화형 언어 전환기
- 모바일 최적화된 레이아웃
- 네이티브 언어 이름 표시

## 🎨 테마 및 디자인

### 언어별 폰트

시스템이 각 언어에 맞는 폰트를 자동으로 로드합니다:

- 한국어: Noto Sans KR
- 일본어: Noto Sans JP
- 중국어: Noto Sans SC
- 영어/기타: Noto Sans

### 색상 테마

```css
/* 기본 테마 */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* RTL 언어 전용 */
[dir="rtl"] .header-content {
    flex-direction: row-reverse;
}

/* 언어 전환기 스타일 */
.language-switcher {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
```

## 🔍 문제 해결

### 1. 언어가 변경되지 않을 때

**문제**: 언어 전환 버튼을 클릭해도 언어가 변경되지 않음

**해결 방법**:
1. 쿠키 및 캐시 삭제
2. 페이지 강제 새로고침 (Ctrl+F5 또는 Cmd+Shift+R)
3. 브라우저 언어 설정 확인
4. 콘솔 상태 확인

### 2. 번역이 로드되지 않을 때

**문제**: 일부 텍스트가 번역되지 않고 원본 키 표시

**해결 방법**:
1. 번역 JSON 파일 구조 확인
2. 카테고리 및 키 이름 확인
3. 언어 코드가 올바른지 확인
4. 캐시 비우기 후 재시도

### 3. 폰트가 올바르게 표시되지 않을 때

**문제**: 특정 언어의 폰트가 적용되지 않음

**해결 방법**:
1. 인터넷 연결 확인 (Google Fonts CDN)
2. 브라우저 캐시 삭제
3. CSS 폰트 패밀리 지연 확인
4. 폰트 로드 순서 확인

### 4. 레이아웃이 깨진 경우

**문제**: RTL 언어에서 레이아웃이 올바르게 적용되지 않음

**해결 방법**:
1. HTML `dir` 속성 확인
2. CSS RTL 스타일 확인
3. CSS 우선순위 확인
4. 브라우저 호환성 확인

### 5. 서버 시작 오류

**문제**: 서버 시작 시 템릿 생성 오류 발생

**해결 방법**:
1. `templates` 디렉토리 권한 확인
2. 디스크 공간 확인
3. Python 버전 호환성 확인
4. 의존 패키지 설치 확인

## 📚 추가 자료

- [Flask 문서](https://flask.palletsprojects.com/)
- [Jinja2 템플릿 문서](https://jinja.palletsprojects.com/)
- [Google Fonts](https://fonts.google.com/)
- [다국어 웹 디자인 가이드](https://www.w3.org/International/)

## 🤝 기여

이 프로젝트에 기여하고 싶으시다면 다음을 확인해주세요:
1. 새로운 언어 번역 추가
2. 기존 번역 개선
3. 새로운 UI 테마 제작
4. 언어별 UX 개선
5. 테스트 케이스 작성

## 📄 라이선스

이 프로젝트는 [라이선스 이름] 라이선스 하에 제공됩니다.

## 📞 지원

문의사항이나 버그 리포트는 다음을 통해 접수해주세요:
- 이슈 트래커: [GitHub Issues](#)
- 이메일: [support@example.com](mailto:support@example.com)

---

**팁**: 다국어 UI 지원을 통해 전 세계 사용자에게 더 나은 경험을 제공하세요! 🌍