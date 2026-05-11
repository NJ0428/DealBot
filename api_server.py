#!/usr/bin/env python3
"""
REST API 서버
DealBot 기능을 REST API로 제공
"""

from flask import Flask, request, jsonify, make_response
from functools import wraps
import logging
from datetime import datetime
from pathlib import Path
import traceback

# 기존 크롤러 임포트
from web_crawler import WebCrawler, Config, setup_logging
from sentiment_analyzer import SentimentAnalyzer, SentimentFilter
from api_auth import APIKeyManager, APIKeyAuthMiddleware, get_api_key_manager, create_default_api_key

# 고급 Rate Limiting 임포트
try:
    from api_rate_limiter import (
        get_rate_limiter, RateLimitMiddleware,
        RateLimitPolicy, get_policy_for_tier
    )
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    logging.warning("고급 Rate Limiting 모듈을 찾을 수 없음. 기본 제한만 사용됩니다.")

# Swagger 문서화 임포트
try:
    from flasgger import Swagger
    SWAGGER_AVAILABLE = True
except ImportError:
    SWAGGER_AVAILABLE = False
    logging.warning("Flasgger를 찾을 수 없음. API 문서가 제공되지 않습니다.")

# Flask 앱 설정
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Swagger 설정
if SWAGGER_AVAILABLE:
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/v1/docs/"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "DealBot REST API",
            "description": "웹 크롤링, 감정 분석, 데이터 수집 API",
            "contact": {
                "name": "DealBot Support",
                "email": "support@dealbot.com"
            },
            "version": "1.0.0"
        },
        "host": "localhost:5000",
        "basePath": "/api/v1",
        "schemes": [
            "http",
            "https"
        ],
        "securityDefinitions": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key-ID",
                "description": "API Key ID 헤더. X-API-Key-Secret 헤더도 함께 필요합니다."
            }
        },
        "security": [
            {
                "ApiKeyAuth": []
            }
        ],
        "definitions": {
            "APIKey": {
                "type": "object",
                "properties": {
                    "key_id": {
                        "type": "string",
                        "example": "dk_abc123..."
                    },
                    "key_secret": {
                        "type": "string",
                        "example": "sk_secret..."
                    },
                    "name": {
                        "type": "string",
                        "example": "My API Key"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "expires_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "is_active": {
                        "type": "boolean"
                    },
                    "rate_limit": {
                        "type": "integer",
                        "example": 1000
                    },
                    "usage_count": {
                        "type": "integer",
                        "example": 150
                    },
                    "last_used": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "permissions": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "example": ["read", "write"]
                    },
                    "tier": {
                        "type": "string",
                        "enum": ["free", "basic", "pro", "enterprise"],
                        "example": "basic"
                    }
                }
            },
            "CrawlingResult": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string"
                    },
                    "url": {
                        "type": "string"
                    },
                    "blog_name": {
                        "type": "string"
                    },
                    "date": {
                        "type": "string"
                    },
                    "summary": {
                        "type": "string"
                    },
                    "status": {
                        "type": "string"
                    },
                    "sentiment_label": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"]
                    },
                    "sentiment_score": {
                        "type": "number",
                        "format": "float"
                    }
                }
            },
            "SentimentResult": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"]
                    },
                    "sentiment_score": {
                        "type": "number",
                        "format": "float"
                    },
                    "positive_score": {
                        "type": "number",
                        "format": "float"
                    },
                    "negative_score": {
                        "type": "number",
                        "format": "float"
                    },
                    "confidence": {
                        "type": "number",
                        "format": "float"
                    },
                    "positive_words": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "negative_words": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "word_count": {
                        "type": "integer"
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string"
                    },
                    "message": {
                        "type": "string"
                    }
                }
            }
        }
    }

    swagger = Swagger(app, config=swagger_config, template=swagger_template)

# 로거 설정
logger = setup_logging()

# API 키 관리자 및 인증 미들웨어
api_key_manager = get_api_key_manager()
auth_middleware = APIKeyAuthMiddleware(api_key_manager)

# Rate Limiting 미들웨어
if RATE_LIMITING_AVAILABLE:
    rate_limiter = get_rate_limiter()
    rate_limit_middleware = RateLimitMiddleware(rate_limiter)
    logger.info("고급 Rate Limiting 활성화")
else:
    rate_limit_middleware = None
    logger.info("레거시 Rate Limiting 사용")

# 크롤러 및 감정 분석기 인스턴스
crawler = WebCrawler()
sentiment_analyzer = SentimentAnalyzer()

def require_auth(permission: str = 'read'):
    """API 인증 데코레이터"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # API 키 헤더 확인
            key_id = request.headers.get('X-API-Key-ID')
            key_secret = request.headers.get('X-API-Key-Secret')

            if not key_id or not key_secret:
                logger.warning("API 키 헤더 누락")
                return jsonify({
                    'error': 'Authentication required',
                    'message': 'X-API-Key-ID and X-API-Key-Secret headers are required'
                }), 401

            # API 키 검증
            api_key = auth_middleware.authenticate(key_id, key_secret)
            if not api_key:
                logger.warning(f"API 인증 실패: {key_id}")
                return jsonify({
                    'error': 'Authentication failed',
                    'message': 'Invalid API key or secret'
                }), 401

            # 권한 확인
            if not auth_middleware.check_permission(api_key, permission):
                logger.warning(f"권한 부족: {key_id} -> {permission}")
                return jsonify({
                    'error': 'Permission denied',
                    'message': f'Permission "{permission}" required'
                }), 403

            # 고급 Rate Limiting 확인
            if RATE_LIMITING_AVAILABLE and rate_limit_middleware:
                # API 키의 티어에 따른 정책 가져오기
                policy = get_policy_for_tier(api_key.tier)

                # 엔드포인트 이름 추출
                endpoint = f"{request.method} {request.endpoint}"

                # Rate Limiting 체크
                allowed, result = rate_limit_middleware.check_rate_limit(
                    key_id=key_id,
                    endpoint=endpoint,
                    policy=policy
                )

                if not allowed:
                    logger.warning(f"Rate limit 초과: {key_id}")
                    response = jsonify(result)
                    response.status_code = 429
                    response.headers['Retry-After'] = str(result.get('retry_after', 60))
                    return response

                # 응답 헤더에 Rate Limiting 정보 추가
                response = make_response()
                for key, value in result.items():
                    response.headers[key] = str(value)
            else:
                # 레거시 Rate Limiting 확인
                if api_key.is_rate_limited():
                    logger.warning(f"Rate limit 초과: {key_id}")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Rate limit of {api_key.rate_limit} requests exceeded'
                    }), 429
                response = None

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def handle_errors(f):
    """에러 핸들링 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API 오류: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    return decorated_function

# ============================================================================
# 헬스체크 & 시스템 엔드포인트
# ============================================================================

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """
    헬스체크
    ---
    tags:
      - 시스템
    responses:
      200:
        description: 서버 정상 작동
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
            timestamp:
              type: string
              format: date-time
            service:
              type: string
              example: DealBot REST API
            version:
              type: string
              example: 1.0.0
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DealBot REST API',
        'version': '1.0.0'
    })

@app.route('/api/v1/stats', methods=['GET'])
@require_auth('read')
@handle_errors
def get_stats():
    """
    API 서버 통계 조회
    ---
    tags:
      - 시스템
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: 서버 통계 정보
        schema:
          type: object
          properties:
            api_keys_count:
              type: integer
            total_requests:
              type: integer
            active_keys:
              type: integer
            timestamp:
              type: string
              format: date-time
      401:
        description: 인증 실패
    """
    api_keys = api_key_manager.list_api_keys()
    total_usage = sum(key['usage_count'] for key in api_keys)

    return jsonify({
        'api_keys_count': len(api_keys),
        'total_requests': total_usage,
        'active_keys': len([k for k in api_keys if k['is_active']]),
        'timestamp': datetime.now().isoformat()
    })

# ============================================================================
# API 키 관리 엔드포인트
# ============================================================================

@app.route('/api/v1/keys', methods=['GET'])
@require_auth('admin')
@handle_errors
def list_api_keys():
    """
    모든 API 키 목록 조회
    ---
    tags:
      - API 키 관리
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: API 키 목록
        schema:
          type: object
          properties:
            count:
              type: integer
            keys:
              type: array
              items:
                $ref: '#/definitions/APIKey'
      401:
        description: 인증 실패
      403:
        description: 권한 부족 (admin 필요)
    """
    keys = api_key_manager.list_api_keys()
    return jsonify({
        'count': len(keys),
        'keys': keys
    })

@app.route('/api/v1/keys', methods=['POST'])
@require_auth('admin')
@handle_errors
def create_api_key():
    """
    새 API 키 생성
    ---
    tags:
      - API 키 관리
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: My API Key
            rate_limit:
              type: integer
              example: 1000
            expires_in_days:
              type: integer
              example: 365
            permissions:
              type: array
              items:
                type: string
              example: ['read', 'write']
            tier:
              type: string
              enum: [free, basic, pro, enterprise]
              example: basic
    responses:
      201:
        description: API 키 생성 성공
        schema:
          type: object
          properties:
            message:
              type: string
            key:
              $ref: '#/definitions/APIKey'
      400:
        description: 잘못된 요청
    """
    data = request.get_json()

    name = data.get('name', 'Unnamed Key')
    rate_limit = data.get('rate_limit', 1000)
    expires_in_days = data.get('expires_in_days')
    permissions = data.get('permissions', ['read', 'write'])
    tier = data.get('tier', 'basic')  # 티어 정보 추가

    # 입력값 검증
    if not isinstance(name, str) or len(name) == 0:
        return jsonify({'error': 'Invalid name'}), 400

    if not isinstance(rate_limit, int) or rate_limit <= 0:
        return jsonify({'error': 'Invalid rate limit'}), 400

    if expires_in_days is not None and (not isinstance(expires_in_days, int) or expires_in_days <= 0):
        return jsonify({'error': 'Invalid expires_in_days'}), 400

    if not isinstance(permissions, list) or not all(isinstance(p, str) for p in permissions):
        return jsonify({'error': 'Invalid permissions'}), 400

    # 티어 검증
    if tier not in ['free', 'basic', 'pro', 'enterprise']:
        return jsonify({'error': 'Invalid tier (must be free, basic, pro, or enterprise)'}), 400

    # API 키 생성 (티어 정보 포함)
    api_key = api_key_manager.create_api_key(
        name=name,
        rate_limit=rate_limit,
        expires_in_days=expires_in_days,
        permissions=permissions
    )

    # 티어 정보 설정 (APIKeyManager에서 지원하지 않으면 직접 설정)
    api_key.tier = tier

    return jsonify({
        'message': 'API key created successfully',
        'key': api_key.to_dict()
    }), 201

@app.route('/api/v1/keys/<key_id>', methods=['GET'])
@require_auth('admin')
@handle_errors
def get_api_key(key_id: str):
    """특정 API 키 조회"""
    api_key = api_key_manager.get_api_key(key_id)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    key_info = api_key.to_dict()
    key_info['key_secret'] = '****' + key_info['key_secret'][-4:]

    return jsonify(key_info)

@app.route('/api/v1/keys/<key_id>/stats', methods=['GET'])
@require_auth('admin')
@handle_errors
def get_api_key_stats(key_id: str):
    """API 키 사용 통계"""
    stats = api_key_manager.get_usage_stats(key_id)
    if not stats:
        return jsonify({'error': 'API key not found'}), 404

    return jsonify(stats)

@app.route('/api/v1/keys/<key_id>/activate', methods=['POST'])
@require_auth('admin')
@handle_errors
def activate_api_key(key_id: str):
    """API 키 활성화"""
    if api_key_manager.activate_api_key(key_id):
        return jsonify({'message': 'API key activated successfully'})
    return jsonify({'error': 'API key not found'}), 404

@app.route('/api/v1/keys/<key_id>/deactivate', methods=['POST'])
@require_auth('admin')
@handle_errors
def deactivate_api_key(key_id: str):
    """API 키 비활성화"""
    if api_key_manager.deactivate_api_key(key_id):
        return jsonify({'message': 'API key deactivated successfully'})
    return jsonify({'error': 'API key not found'}), 404

@app.route('/api/v1/keys/<key_id>', methods=['DELETE'])
@require_auth('admin')
@handle_errors
def delete_api_key(key_id: str):
    """API 키 삭제"""
    if api_key_manager.delete_api_key(key_id):
        return jsonify({'message': 'API key deleted successfully'})
    return jsonify({'error': 'API key not found'}), 404

@app.route('/api/v1/keys/<key_id>/rate-limit', methods=['PUT'])
@require_auth('admin')
@handle_errors
def update_rate_limit(key_id: str):
    """Rate limit 업데이트"""
    data = request.get_json()
    rate_limit = data.get('rate_limit')

    if not isinstance(rate_limit, int) or rate_limit <= 0:
        return jsonify({'error': 'Invalid rate limit'}), 400

    if api_key_manager.update_rate_limit(key_id, rate_limit):
        return jsonify({'message': 'Rate limit updated successfully'})
    return jsonify({'error': 'API key not found'}), 404

@app.route('/api/v1/keys/<key_id>/reset-usage', methods=['POST'])
@require_auth('admin')
@handle_errors
def reset_usage_count(key_id: str):
    """사용 횟수 초기화"""
    if api_key_manager.reset_usage_count(key_id):
        return jsonify({'message': 'Usage count reset successfully'})
    return jsonify({'error': 'API key not found'}), 404

# ============================================================================
# 크롤링 엔드포인트
# ============================================================================

@app.route('/api/v1/crawl/news', methods=['POST'])
@require_auth('write')
@handle_errors
def crawl_news():
    """
    뉴스 크롤링
    ---
    tags:
      - 크롤링
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - keyword
          properties:
            keyword:
              type: string
              example: 인공지능
            max_results:
              type: integer
              minimum: 1
              maximum: 100
              default: 20
              example: 20
            search_type:
              type: string
              enum: [naver, google, multiple]
              default: naver
              example: naver
            enable_sentiment:
              type: boolean
              default: false
              example: true
    responses:
      200:
        description: 크롤링 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            keyword:
              type: string
            search_type:
              type: string
            count:
              type: integer
            results:
              type: array
              items:
                $ref: '#/definitions/CrawlingResult'
            timestamp:
              type: string
              format: date-time
            sentiment_stats:
              type: object
      400:
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        schema:
          $ref: '#/definitions/ErrorResponse'
      403:
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    keyword = data.get('keyword', '').strip()
    max_results = data.get('max_results', Config.DEFAULT_MAX_RESULTS)
    search_type = data.get('search_type', 'naver')
    enable_sentiment = data.get('enable_sentiment', False)

    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400

    if not isinstance(max_results, int) or max_results <= 0 or max_results > 100:
        return jsonify({'error': 'Invalid max_results (1-100)'}), 400

    logger.info(f"크롤링 요청: keyword={keyword}, max_results={max_results}, type={search_type}")

    # 크롤링 수행
    if search_type == 'naver':
        results = crawler.search_naver_blog(keyword, max_results=max_results)
    elif search_type == 'google':
        results = crawler.search_google(keyword, max_results=max_results)
    else:
        results = crawler.search_multiple_sources(keyword, max_results=max_results)

    # 감정 분석 (옵션)
    sentiment_stats = None
    if enable_sentiment and results:
        try:
            results = sentiment_analyzer.analyze_data(results)
            sentiment_stats = SentimentFilter.get_sentiment_summary(results)
            logger.info(f"감정 분석 완료: 긍정 {sentiment_stats['positive_count']}, 부정 {sentiment_stats['negative_count']}")
        except Exception as e:
            logger.warning(f"감정 분석 실패: {e}")

    response = {
        'success': True,
        'keyword': keyword,
        'search_type': search_type,
        'count': len(results),
        'results': results,
        'timestamp': datetime.now().isoformat()
    }

    if sentiment_stats:
        response['sentiment_stats'] = sentiment_stats

    return jsonify(response)

@app.route('/api/v1/crawl/multiple', methods=['POST'])
@require_auth('write')
@handle_errors
def crawl_multiple():
    """
    다중 키워드 크롤링
    ---
    tags:
      - 크롤링
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - keywords
          properties:
            keywords:
              type: array
              items:
                type: string
              minItems: 1
              maxItems: 10
              example: [AI, 블록체인, 메타버스]
            max_results:
              type: integer
              minimum: 1
              maximum: 100
              default: 20
            use_async:
              type: boolean
              default: true
    responses:
      200:
        description: 다중 크롤링 성공
      400:
        schema:
          $ref: '#/definitions/ErrorResponse'
      401:
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    keywords = data.get('keywords', [])
    max_results = data.get('max_results', Config.DEFAULT_MAX_RESULTS)
    use_async = data.get('use_async', True)

    if not isinstance(keywords, list) or len(keywords) == 0:
        return jsonify({'error': 'Keywords list is required'}), 400

    if len(keywords) > 10:
        return jsonify({'error': 'Maximum 10 keywords allowed'}), 400

    logger.info(f"다중 크롤링 요청: keywords={keywords}, async={use_async}")

    # 다중 키워드 크롤링
    results = crawler.search_multiple_keywords(
        keywords=keywords,
        max_results=max_results,
        use_async=use_async
    )

    response = {
        'success': True,
        'keywords': keywords,
        'async': use_async,
        'results': {k: {'count': len(v), 'data': v} for k, v in results.items()},
        'total_count': sum(len(v) for v in results.values()),
        'timestamp': datetime.now().isoformat()
    }

    return jsonify(response)

# ============================================================================
# 감정 분석 엔드포인트
# ============================================================================

@app.route('/api/v1/sentiment/analyze', methods=['POST'])
@require_auth('read')
@handle_errors
def analyze_sentiment():
    """
    단일 텍스트 감정 분석
    ---
    tags:
      - 감정 분석
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              example: 이 제품은 정말 좋습니다!
    responses:
      200:
        description: 감정 분석 성공
        schema:
          type: object
          properties:
            success:
              type: boolean
            result:
              $ref: '#/definitions/SentimentResult'
      400:
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    text = data.get('text', '').strip()

    if not text:
        return jsonify({'error': 'Text is required'}), 400

    result = sentiment_analyzer.analyze(text)

    return jsonify({
        'success': True,
        'result': {
            'label': result.label,
            'sentiment_score': result.sentiment_score,
            'positive_score': result.positive_score,
            'negative_score': result.negative_score,
            'confidence': result.confidence,
            'positive_words': result.positive_words[:10],
            'negative_words': result.negative_words[:10],
            'word_count': result.word_count
        }
    })

@app.route('/api/v1/sentiment/batch', methods=['POST'])
@require_auth('read')
@handle_errors
def analyze_sentiment_batch():
    """
    배치 텍스트 감정 분석
    ---
    tags:
      - 감정 분석
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - texts
          properties:
            texts:
              type: array
              items:
                type: string
              minItems: 1
              maxItems: 100
              example: [좋아요!, 별로입니다., 그냥 그렇네요.]
    responses:
      200:
        description: 배치 감정 분석 성공
      400:
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json()

    texts = data.get('texts', [])

    if not isinstance(texts, list) or len(texts) == 0:
        return jsonify({'error': 'Texts list is required'}), 400

    if len(texts) > 100:
        return jsonify({'error': 'Maximum 100 texts allowed'}), 400

    results = []
    for text in texts:
        if text.strip():
            result = sentiment_analyzer.analyze(text.strip())
            results.append({
                'text': text[:100] + '...' if len(text) > 100 else text,
                'label': result.label,
                'sentiment_score': result.sentiment_score
            })

    return jsonify({
        'success': True,
        'count': len(results),
        'results': results
    })

@app.route('/api/v1/sentiment/filter', methods=['POST'])
@require_auth('read')
@handle_errors
def filter_sentiment():
    """감정 필터링"""
    data = request.get_json()

    sentiment_type = data.get('sentiment', 'positive')
    min_score = float(data.get('min_score', 0.0))
    results = data.get('results', [])

    if not results:
        return jsonify({'error': 'Results data is required'}), 400

    filtered = SentimentFilter.filter_by_sentiment(results, sentiment_type, min_score)

    return jsonify({
        'success': True,
        'count': len(filtered),
        'results': filtered
    })

@app.route('/api/v1/sentiment/stats', methods=['POST'])
@require_auth('read')
@handle_errors
def sentiment_stats():
    """감정 통계"""
    data = request.get_json()

    results = data.get('results', [])

    if not results:
        return jsonify({'error': 'Results data is required'}), 400

    summary = SentimentFilter.get_sentiment_summary(results)
    distribution = SentimentFilter.get_sentiment_distribution(results)

    return jsonify({
        'success': True,
        'summary': summary,
        'distribution': distribution
    })

# ============================================================================
# Rate Limiting 엔드포인트
# ============================================================================

@app.route('/api/v1/keys/<key_id>/rate-limit', methods=['GET'])
@require_auth('admin')
@handle_errors
def get_key_rate_limit(key_id: str):
    """
    API 키의 현재 Rate Limiting 정보 조회
    ---
    tags:
      - Rate Limiting
    parameters:
      - in: path
        name: key_id
        type: string
        required: true
    responses:
      200:
        description: Rate Limiting 정보
        schema:
          type: object
          properties:
            minute:
              type: object
            hour:
              type: object
            day:
              type: object
      404:
        description: API 키를 찾을 수 없음
    """
    if not RATE_LIMITING_AVAILABLE or not rate_limit_middleware:
        return jsonify({'error': 'Advanced rate limiting not available'}), 501

    api_key = api_key_manager.get_api_key(key_id)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    info = rate_limit_middleware.get_rate_limit_info(key_id)
    return jsonify(info)

@app.route('/api/v1/keys/<key_id>/rate-policy', methods=['POST'])
@require_auth('admin')
@handle_errors
def update_rate_policy(key_id: str):
    """
    API 키의 Rate Limiting 정책 업데이트
    ---
    tags:
      - Rate Limiting
    parameters:
      - in: path
        name: key_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            tier:
              type: string
              enum: [free, basic, pro, enterprise]
            custom_policy:
              type: object
              properties:
                requests_per_minute:
                  type: integer
                requests_per_hour:
                  type: integer
                requests_per_day:
                  type: integer
    responses:
      200:
        description: 정책 업데이트 성공
      404:
        description: API 키를 찾을 수 없음
    """
    if not RATE_LIMITING_AVAILABLE:
        return jsonify({'error': 'Advanced rate limiting not available'}), 501

    api_key = api_key_manager.get_api_key(key_id)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    data = request.get_json()
    tier = data.get('tier')
    custom_policy = data.get('custom_policy')

    if tier:
        if tier not in ['free', 'basic', 'pro', 'enterprise']:
            return jsonify({'error': 'Invalid tier'}), 400
        api_key.tier = tier
        api_key_manager._save_keys()

    if custom_policy:
        # 커스텀 정책 설정
        api_key.rate_limit_policy = custom_policy
        api_key_manager._save_keys()

    return jsonify({
        'message': 'Rate policy updated successfully',
        'tier': api_key.tier,
        'policy': api_key.rate_limit_policy
    })

@app.route('/api/v1/keys/<key_id>/reset-rate-limit', methods=['POST'])
@require_auth('admin')
@handle_errors
def reset_key_rate_limit(key_id: str):
    """
    API 키의 Rate Limiting 사용량 초기화
    ---
    tags:
      - Rate Limiting
    parameters:
      - in: path
        name: key_id
        type: string
        required: true
    responses:
      200:
        description: 초기화 성공
      404:
        description: API 키를 찾을 수 없음
    """
    if not RATE_LIMITING_AVAILABLE or not rate_limit_middleware:
        return jsonify({'error': 'Advanced rate limiting not available'}), 501

    api_key = api_key_manager.get_api_key(key_id)
    if not api_key:
        return jsonify({'error': 'API key not found'}), 404

    rate_limit_middleware.reset_user_limit(key_id)
    return jsonify({'message': 'Rate limit reset successfully'})

@app.route('/api/v1/rate-limits/status', methods=['GET'])
@require_auth('admin')
@handle_errors
def get_rate_limits_status():
    """
    전체 Rate Limiting 상태 조회
    ---
    tags:
      - Rate Limiting
    responses:
      200:
        description: 전체 Rate Limiting 상태
    """
    if not RATE_LIMITING_AVAILABLE or not rate_limit_middleware:
        return jsonify({'error': 'Advanced rate limiting not available'}), 501

    keys = api_key_manager.list_api_keys()
    status = []

    for key_info in keys:
        key_id = key_info['key_id']
        try:
            stats = rate_limiter.get_stats(key_id)
            status.append(stats)
        except Exception as e:
            logger.error(f"Error getting stats for {key_id}: {e}")

    return jsonify({
        'total_keys': len(keys),
        'active_keys': len([k for k in keys if k['is_active']]),
        'rate_limiting_enabled': True,
        'storage_type': 'Redis' if REDIS_AVAILABLE else 'Memory',
        'stats': status
    })

# ============================================================================
# 에러 핸들러
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """404 에러 핸들러"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """405 에러 핸들러"""
    return jsonify({
        'error': 'Method not allowed',
        'message': 'The method is not allowed for the requested endpoint'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """500 에러 핸들러"""
    logger.error(f"내부 서버 오류: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🔌 DealBot REST API 서버 시작")
    print("=" * 60)

    # 기본 API 키 생성
    default_key = create_default_api_key()
    if default_key:
        print("\n🔑 기본 API 키가 생성되었습니다:")
        print(f"   Key ID: {default_key.key_id}")
        print(f"   Key Secret: {default_key.key_secret}")
        print(f"   Name: {default_key.name}")
        print(f"   Rate Limit: {default_key.rate_limit}")
        print(f"   Permissions: {default_key.permissions}")
        print("\n⚠️  이 정보는 안전하게 보관하세요!")

    # 서버 정보 출력
    print("\n📡 API 서버 정보:")
    print(f"   주소: http://localhost:5000")
    print(f"   헬스체크: http://localhost:5000/api/v1/health")
    print(f"   API 문서: http://localhost:5000/api/v1/docs")

    print("\n🔑 인증 방법:")
    print("   Headers:")
    print("     X-API-Key-ID: your_key_id")
    print("     X-API-Key-Secret: your_key_secret")

    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 60 + "\n")

    # Flask 서버 시작
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()