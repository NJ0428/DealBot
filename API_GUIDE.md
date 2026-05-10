# 🔌 DealBot REST API 가이드

DealBot REST API를 사용하여 웹 크롤링, 감정 분석, 데이터 수집 기능을 프로그래매틱하게 제어할 수 있습니다.

## 📋 목차

1. [API 개요](#api-개요)
2. [인증 설정](#인증-설정)
3. [API 엔드포인트](#api-엔드포인트)
4. [사용 예시](#사용-예시)
5. [에러 처리](#에러-처리)

## API 개요

### 기본 정보

- **기본 URL**: `http://localhost:5000/api/v1`
- **데이터 형식**: JSON
- **인증 방식**: API 키 기반 (X-API-Key-ID, X-API-Key-Secret 헤더)
- **Rate Limiting**: API 키당 설정 가능한 요청 한계

### API 버전

현재 버전: `v1`

### 특징

- 🔐 **안전한 인증**: API 키 기반 인증 시스템
- 📊 **Rate Limiting**: API 키당 요청 한계 설정
- 🎯 **권한 관리**: read, write, admin 권한 지원
- 📈 **사용량 추적**: API 키별 사용 통계 제공
- 🔄 **비동기 처리**: 병렬 크롤링 지원

## 인증 설정

### 1. API 키 획득

API를 사용하려면 먼저 API 키가 필요합니다.

#### 방법 1: 자동 생성 (최초 실행 시)

```bash
python api_server.py
```

서버를 처음 실행하면 기본 Admin API 키가 자동 생성됩니다.

#### 방법 2: API로 생성

```python
import requests

# Admin API 키로 인증
headers = {
    'X-API-Key-ID': 'admin_key_id',
    'X-API-Key-Secret': 'admin_key_secret',
    'Content-Type': 'application/json'
}

# 새 API 키 생성
data = {
    'name': 'My App Key',
    'rate_limit': 1000,
    'expires_in_days': 365,
    'permissions': ['read', 'write']
}

response = requests.post(
    'http://localhost:5000/api/v1/keys',
    headers=headers,
    json=data
)

api_key = response.json()['key']
print(f"Key ID: {api_key['key_id']}")
print(f"Key Secret: {api_key['key_secret']}")
```

### 2. 인증 헤더 설정

모든 API 요청에 인증 헤더를 포함해야 합니다:

```python
headers = {
    'X-API-Key-ID': 'your_key_id',
    'X-API-Key-Secret': 'your_key_secret',
    'Content-Type': 'application/json'
}
```

## API 엔드포인트

### 🏥 시스템 엔드포인트

#### 헬스체크

```http
GET /api/v1/health
```

**응답:**
```json
{
  "status": "healthy",
  "timestamp": "2024-05-07T12:00:00",
  "service": "DealBot REST API",
  "version": "1.0.0"
}
```

#### 서버 통계

```http
GET /api/v1/stats
```

**권한:** `read`

**응답:**
```json
{
  "api_keys_count": 5,
  "total_requests": 1250,
  "active_keys": 4,
  "timestamp": "2024-05-07T12:00:00"
}
```

### 🔑 API 키 관리

#### 모든 API 키 목록

```http
GET /api/v1/keys
```

**권한:** `admin`

**응답:**
```json
{
  "count": 2,
  "keys": [
    {
      "key_id": "dk_abc123...",
      "key_secret": "****xyz",
      "name": "Default Admin Key",
      "created_at": "2024-05-07T10:00:00",
      "expires_at": "2025-05-07T10:00:00",
      "is_active": true,
      "rate_limit": 10000,
      "usage_count": 150,
      "permissions": ["read", "write", "admin"]
    }
  ]
}
```

#### 새 API 키 생성

```http
POST /api/v1/keys
```

**권한:** `admin`

**요청:**
```json
{
  "name": "My App Key",
  "rate_limit": 1000,
  "expires_in_days": 365,
  "permissions": ["read", "write"]
}
```

**응답:**
```json
{
  "message": "API key created successfully",
  "key": {
    "key_id": "dk_new_key_123",
    "key_secret": "sk_secret_abc",
    "name": "My App Key",
    "created_at": "2024-05-07T12:00:00",
    "expires_at": "2025-05-07T12:00:00",
    "is_active": true,
    "rate_limit": 1000,
    "usage_count": 0,
    "permissions": ["read", "write"]
  }
}
```

#### 특정 API 키 조회

```http
GET /api/v1/keys/{key_id}
```

**권한:** `admin`

#### API 키 통계 조회

```http
GET /api/v1/keys/{key_id}/stats
```

**권한:** `admin`

**응답:**
```json
{
  "key_id": "dk_abc123",
  "name": "My App Key",
  "usage_count": 150,
  "rate_limit": 1000,
  "usage_percentage": 15.0,
  "last_used": "2024-05-07T12:00:00",
  "created_at": "2024-05-07T10:00:00",
  "expires_at": "2025-05-07T10:00:00",
  "is_active": true
}
```

#### API 키 활성화/비활성화

```http
POST /api/v1/keys/{key_id}/activate
POST /api/v1/keys/{key_id}/deactivate
```

**권한:** `admin`

#### API 키 삭제

```http
DELETE /api/v1/keys/{key_id}
```

**권한:** `admin`

#### Rate Limit 업데이트

```http
PUT /api/v1/keys/{key_id}/rate-limit
```

**권한:** `admin`

**요청:**
```json
{
  "rate_limit": 5000
}
```

#### 사용 횟수 초기화

```http
POST /api/v1/keys/{key_id}/reset-usage
```

**권한:** `admin`

### 🕷️ 크롤링 엔드포인트

#### 뉴스 크롤링

```http
POST /api/v1/crawl/news
```

**권한:** `write`

**요청:**
```json
{
  "keyword": "인공지능",
  "max_results": 20,
  "search_type": "naver",
  "enable_sentiment": true
}
```

**파라미터:**
- `keyword` (string, 필수): 검색 키워드
- `max_results` (int, 선택적, 기본값 20): 최대 결과 수 (1-100)
- `search_type` (string, 선택적, 기본값 "naver"): 검색 유형 ("naver", "google", "multiple")
- `enable_sentiment` (boolean, 선택적, 기본값 false): 감정 분석 활성화

**응답:**
```json
{
  "success": true,
  "keyword": "인공지능",
  "search_type": "naver",
  "count": 20,
  "results": [
    {
      "title": "AI 기술의 혁신",
      "url": "https://example.com/article1",
      "blog_name": "테크 블로그",
      "date": "2024.05.07",
      "summary": "AI 기술이快速发展하고 있다...",
      "status": "성공",
      "sentiment_label": "positive",
      "sentiment_score": 0.625,
      "collected_at": "2024-05-07 12:00:00"
    }
  ],
  "timestamp": "2024-05-07T12:00:00",
  "sentiment_stats": {
    "total_count": 20,
    "positive_count": 12,
    "negative_count": 3,
    "neutral_count": 5,
    "positive_ratio": 0.6,
    "negative_ratio": 0.15,
    "avg_sentiment_score": 0.35
  }
}
```

#### 다중 키워드 크롤링

```http
POST /api/v1/crawl/multiple
```

**권한:** `write`

**요청:**
```json
{
  "keywords": ["AI", "블록체인", "메타버스"],
  "max_results": 10,
  "use_async": true
}
```

**파라미터:**
- `keywords` (array, 필수): 검색 키워드 리스트 (최대 10개)
- `max_results` (int, 선택적, 기본값 20): 키워드당 최대 결과 수
- `use_async` (boolean, 선택적, 기본값 true): 비동기 병렬 처리

**응답:**
```json
{
  "success": true,
  "keywords": ["AI", "블록체인", "메타버스"],
  "async": true,
  "results": {
    "AI": {
      "count": 10,
      "data": [...]
    },
    "블록체인": {
      "count": 10,
      "data": [...]
    },
    "메타버스": {
      "count": 10,
      "data": [...]
    }
  },
  "total_count": 30,
  "timestamp": "2024-05-07T12:00:00"
}
```

### 🎭 감정 분석 엔드포인트

#### 단일 텍스트 감정 분석

```http
POST /api/v1/sentiment/analyze
```

**권한:** `read`

**요청:**
```json
{
  "text": "이 제품은 정말 좋습니다. 강력 추천합니다!"
}
```

**응답:**
```json
{
  "success": true,
  "result": {
    "label": "positive",
    "sentiment_score": 0.625,
    "positive_score": 0.75,
    "negative_score": 0.125,
    "confidence": 0.85,
    "positive_words": ["정말", "좋습니다", "강력", "추천"],
    "negative_words": [],
    "word_count": 6
  }
}
```

#### 배치 감정 분석

```http
POST /api/v1/sentiment/batch
```

**권한:** `read`

**요청:**
```json
{
  "texts": [
    "이 제품은 정말 좋아요!",
    "별로입니다. 다시는 안 사요.",
    "그냥 그렇네요."
  ]
}
```

**응답:**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "text": "이 제품은 정말 좋아요!",
      "label": "positive",
      "sentiment_score": 0.7
    },
    {
      "text": "별로입니다. 다시는 안 사요.",
      "label": "negative",
      "sentiment_score": -0.8
    },
    {
      "text": "그냥 그렇네요.",
      "label": "neutral",
      "sentiment_score": 0.0
    }
  ]
}
```

#### 감정 필터링

```http
POST /api/v1/sentiment/filter
```

**권한:** `read`

**요청:**
```json
{
  "results": [...],
  "sentiment": "positive",
  "min_score": 0.3
}
```

**응답:**
```json
{
  "success": true,
  "count": 5,
  "results": [...]
}
```

#### 감정 통계

```http
POST /api/v1/sentiment/stats
```

**권한:** `read`

**요청:**
```json
{
  "results": [...]
}
```

**응답:**
```json
{
  "success": true,
  "summary": {
    "total_count": 20,
    "positive_count": 12,
    "negative_count": 3,
    "neutral_count": 5,
    "positive_ratio": 0.6,
    "negative_ratio": 0.15,
    "avg_sentiment_score": 0.35
  },
  "distribution": {
    "positive": 12,
    "negative": 3,
    "neutral": 5
  }
}
```

## 사용 예시

### Python 예시

```python
import requests
import json

# API 설정
BASE_URL = "http://localhost:5000/api/v1"
API_KEY_ID = "your_key_id"
API_KEY_SECRET = "your_key_secret"

# 헤더 설정
headers = {
    'X-API-Key-ID': API_KEY_ID,
    'X-API-Key-Secret': API_KEY_SECRET,
    'Content-Type': 'application/json'
}

# 1. 헬스체크
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# 2. 뉴스 크롤링
data = {
    'keyword': '인공지능',
    'max_results': 10,
    'search_type': 'naver',
    'enable_sentiment': True
}

response = requests.post(f"{BASE_URL}/crawl/news", headers=headers, json=data)
result = response.json()
print(f"검색 결과: {result['count']}개")

# 3. 감정 분석
data = {
    'text': '이 제품은 정말 좋습니다!'
}

response = requests.post(f"{BASE_URL}/sentiment/analyze", headers=headers, json=data)
result = response.json()
print(f"감정: {result['result']['label']}")
```

### cURL 예시

```bash
# 헬스체크
curl http://localhost:5000/api/v1/health

# 뉴스 크롤링
curl -X POST http://localhost:5000/api/v1/crawl/news \
  -H "X-API-Key-ID: your_key_id" \
  -H "X-API-Key-Secret: your_key_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "인공지능",
    "max_results": 10,
    "search_type": "naver"
  }'

# 감정 분석
curl -X POST http://localhost:5000/api/v1/sentiment/analyze \
  -H "X-API-Key-ID: your_key_id" \
  -H "X-API-Key-Secret: your_key_secret" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "이 제품은 정말 좋습니다!"
  }'
```

### JavaScript 예시

```javascript
// API 설정
const BASE_URL = 'http://localhost:5000/api/v1';
const headers = {
  'X-API-Key-ID': 'your_key_id',
  'X-API-Key-Secret': 'your_key_secret',
  'Content-Type': 'application/json'
};

// 뉴스 크롤링
async function crawlNews(keyword) {
  const response = await fetch(`${BASE_URL}/crawl/news`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
      keyword: keyword,
      max_results: 10,
      search_type: 'naver'
    })
  });

  const result = await response.json();
  console.log(`검색 결과: ${result.count}개`);
  return result;
}

// 감정 분석
async function analyzeSentiment(text) {
  const response = await fetch(`${BASE_URL}/sentiment/analyze`, {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({ text })
  });

  const result = await response.json();
  console.log(`감정: ${result.result.label}`);
  return result;
}

// 사용 예시
crawlNews('인공지능');
analyzeSentiment('이 제품은 정말 좋습니다!');
```

## 에러 처리

### 에러 응답 형식

```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

### HTTP 상태 코드

| 코드 | 설명 |
|-----|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 실패 |
| 403 | 권한 부족 |
| 404 | 리소스를 찾을 수 없음 |
| 429 | Rate limit 초과 |
| 500 | 서버 오류 |

### 일반적인 에러

#### 인증 실패 (401)

```json
{
  "error": "Authentication failed",
  "message": "Invalid API key or secret"
}
```

#### 권한 부족 (403)

```json
{
  "error": "Permission denied",
  "message": "Permission 'admin' required"
}
```

#### Rate Limit 초과 (429)

```json
{
  "error": "Rate limit exceeded",
  "message": "Rate limit of 1000 requests exceeded"
}
```

## 📝 주의사항

1. **API 키 보안**: API 키와 시크릿을 안전하게 보관하세요
2. **Rate Limit**: API 키당 요청 한계를 확인하세요
3. **권한 관리**: 필요한 최소 권한만 부여하세요
4. **에러 처리**: 적절한 에러 처리를 구현하세요
5. **HTTPS**: 프로덕션 환경에서는 HTTPS를 사용하세요

## 🚀 시작하기

1. API 서버 시작:
```bash
python api_server.py
```

2. API 키 확인 (최초 실행 시 생성됨)

3. API 요청 테스트:
```bash
python api_example.py
```

## 📞 지원

- GitHub Issues: https://github.com/your-repo/issues
- 이메일: support@dealbot.com

---

**마지막 업데이트**: 2024-05-07
**API 버전**: v1.0.0