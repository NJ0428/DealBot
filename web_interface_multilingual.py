#!/usr/bin/env python3
"""
다국어 지원 Flask 웹 인터페이스
DealBot 크롤러를 위한 다국어 웹 UI 제공
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, g, make_response
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from pathlib import Path
import logging
from io import BytesIO
import pandas as pd

# 기존 크롤러 임포트
from web_crawler import WebCrawler, Config, setup_logging

# 다국어 감정 분석 임포트
from multilingual_sentiment_analyzer import MultilingualSentimentAnalyzer, MultilingualSentimentConfig

# 다국어 UI 임포트
from multilingual_ui import (
    I18N, LanguageCode, LanguageInfo, UITranslations,
    get_i18n, set_language, get_current_language, translate, t,
    with_i18n, detect_browser_language, get_language_switcher_html,
    get_language_select_html, TranslationFileManager
)

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'dealbot-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['TRANSLATIONS_FOLDER'] = 'translations'

# 로거 설정
logger = setup_logging()

# 디렉토리 생성
for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER'],
                app.config['DOWNLOAD_FOLDER'], app.config['TRANSLATIONS_FOLDER']]:
    Path(folder).mkdir(exist_ok=True)

# 크롤러 및 감정 분석기 인스턴스
crawler = WebCrawler()
multilingual_sentiment_analyzer = None

# 다국어 번역 파일 내보내기
try:
    TranslationFileManager.export_all_languages(app.config['TRANSLATIONS_FOLDER'])
except Exception as e:
    logger.warning(f"번역 파일 내보내기 실패: {e}")

# 다국어 감정 분석기 초기화
try:
    sentiment_config = MultilingualSentimentConfig()
    multilingual_sentiment_analyzer = MultilingualSentimentAnalyzer(sentiment_config)
    logger.info("다국어 감정 분석기 초기화 성공")
except Exception as e:
    logger.warning(f"다국어 감정 분석기 초기화 실패: {e}")


# ============================================================================
# 템플릿 필터
# ============================================================================

@app.context_processor
def inject_i18n():
    """I18N 컨텍스트 프로세서"""
    i18n = get_i18n()
    current_language = i18n.get_language()
    language_info = i18n.get_language_info()
    supported_languages = i18n.get_supported_languages()

    return {
        'i18n': i18n,
        'current_language': current_language,
        'language_info': language_info,
        'supported_languages': supported_languages,
        't': i18n.t,
        'translate': i18n.translate
    }


@app.before_request
def before_request():
    """요청 전 언어 설정"""
    # URL 파라미터, 헤더, 쿠키에서 언어 감지
    language = request.args.get('lang') or \
                request.cookies.get('language') or \
                detect_browser_language()

    # 언어 설정
    set_language(language)


# ============================================================================
# 언어 전환 API
# ============================================================================

@app.route('/api/language', methods=['GET', 'POST'])
def language_api():
    """언어 설정 API"""
    if request.method == 'POST':
        data = request.get_json()
        language = data.get('language')

        if language and LanguageInfo.is_supported(language):
            # 쿠키에 언어 저장
            response = make_response(jsonify({
                'success': True,
                'language': language,
                'message': f"Language changed to {LanguageInfo.get_language_name(language)}"
            }))
            response.set_cookie('language', language, max_age=60*60*24*30)  # 30일
            return response
        else:
            return jsonify({'success': False, 'error': 'Invalid language'}), 400

    else:  # GET
        i18n = get_i18n()
        return jsonify({
            'current_language': i18n.get_language(),
            'supported_languages': i18n.get_supported_languages(),
            'translations': i18n.get_current_translations()
        })


@app.route('/api/translations/<language>')
def get_translations(language: str):
    """특정 언어의 번역 가져오기"""
    if LanguageInfo.is_supported(language):
        translations = UITranslations.get_translations_for_language(language)
        language_info = LanguageInfo.get_language_info(language)

        return jsonify({
            'success': True,
            'language': language,
            'language_info': language_info,
            'translations': translations
        })
    else:
        return jsonify({'success': False, 'error': 'Language not supported'}), 404


# ============================================================================
# 기본 라우트
# ============================================================================

@app.route('/')
@with_i18n
def index():
    """메인 페이지"""
    return render_template('index_multilingual.html')


@app.route('/search', methods=['POST'])
@with_i18n
def search():
    """검색 처리"""
    try:
        # 폼 데이터 가져오기
        keyword = request.form.get('keyword', '').strip()
        max_results = int(request.form.get('max_results', Config.DEFAULT_MAX_RESULTS))
        search_type = request.form.get('search_type', 'naver')
        enable_sentiment = request.form.get('enable_sentiment') == 'true'

        if not keyword:
            error_msg = t('errors', 'keyword_required')
            flash(error_msg, 'error')
            return redirect(url_for('index'))

        logger.info(f"검색 요청: keyword={keyword}, max_results={max_results}, type={search_type}, sentiment={enable_sentiment}")

        # 크롤링 수행
        if search_type == 'naver':
            results = crawler.search_naver_blog(keyword, max_results=max_results)
        elif search_type == 'google':
            results = crawler.search_google_news(keyword, max_results=max_results)
        else:
            results = crawler.search_multiple_sources(keyword, max_results=max_results)

        # 다국어 감정 분석 (옵션)
        sentiment_stats = None
        if enable_sentiment and results and multilingual_sentiment_analyzer:
            try:
                results = multilingual_sentiment_analyzer.analyze_data(results)
                from multilingual_sentiment_analyzer import MultilingualSentimentFilter
                sentiment_stats = MultilingualSentimentFilter.get_multilingual_summary(results)
                logger.info(f"감정 분석 완료: 긍정 {sentiment_stats.get('positive_count', 0)}, "
                           f"부정 {sentiment_stats.get('negative_count', 0)}")
            except Exception as e:
                logger.warning(f"감정 분석 실패: {e}")

        # 결과 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        result_filename = f"{secure_filename(keyword)}_{timestamp}.xlsx"
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)

        # 엑셀 파일 생성
        df = pd.DataFrame(results)
        excel_path = crawler.save_to_excel(results, result_path)

        # 결과 요약 통계
        stats = {
            'total_count': len(results),
            'successful_count': len([r for r in results if r.get('status') == '성공']),
            'failed_count': len([r for r in results if r.get('status') != '성공']),
            'keyword': keyword,
            'timestamp': timestamp,
            'filename': result_filename,
            'sentiment_enabled': enable_sentiment
        }

        # 감정 통계 추가
        if sentiment_stats:
            stats.update({
                'positive_count': sentiment_stats.get('positive_count', 0),
                'negative_count': sentiment_stats.get('negative_count', 0),
                'neutral_count': sentiment_stats.get('neutral_count', 0),
                'positive_ratio': sentiment_stats.get('positive_ratio', 0),
                'negative_ratio': sentiment_stats.get('negative_ratio', 0),
                'avg_sentiment_score': sentiment_stats.get('avg_sentiment_score', 0)
            })

        logger.info(f"검색 완료: {stats['total_count']}개 결과, 파일={result_filename}")

        return render_template('results_multilingual.html',
                             results=results[:50],
                             stats=stats,
                             keyword=keyword,
                             result_filename=result_filename)

    except Exception as e:
        logger.error(f"검색 오류: {str(e)}")
        error_msg = t('errors', 'search_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_file(filename):
    """결과 파일 다운로드"""
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path,
                           as_attachment=True,
                           download_name=filename,
                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            error_msg = t('errors', 'file_not_found')
            flash(error_msg, 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"다운로드 오류: {str(e)}")
        error_msg = t('errors', 'download_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/download_csv/<filename>')
def download_csv(filename):
    """CSV 형식으로 다운로드"""
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(file_path):
            # 엑셀 파일을 CSV로 변환
            df = pd.read_excel(file_path)

            # CSV 파일 생성
            csv_filename = filename.replace('.xlsx', '.csv')
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
            csv_buffer.seek(0)

            return send_file(csv_buffer,
                           as_attachment=True,
                           download_name=csv_filename,
                           mimetype='text/csv')
        else:
            error_msg = t('errors', 'file_not_found')
            flash(error_msg, 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"CSV 다운로드 오류: {str(e)}")
        error_msg = t('errors', 'download_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/history')
@with_i18n
def history():
    """검색 이력 페이지"""
    try:
        results_folder = Path(app.config['RESULTS_FOLDER'])
        files = []

        if results_folder.exists():
            for file_path in sorted(results_folder.glob('*.xlsx'), key=lambda x: x.stat().st_mtime, reverse=True):
                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'size': f"{stat.st_size / 1024:.1f} KB",
                    'created': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        return render_template('history_multilingual.html', files=files)

    except Exception as e:
        logger.error(f"이력 조회 오류: {str(e)}")
        error_msg = t('errors', 'history_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/settings')
@with_i18n
def settings():
    """설정 페이지"""
    try:
        i18n = get_i18n()

        # 현재 설정 (실제로는 설정 파일에서 로드)
        settings_data = {
            'current_language': i18n.get_language(),
            'max_results': Config.DEFAULT_MAX_RESULTS,
            'enable_sentiment': multilingual_sentiment_analyzer is not None,
            'supported_languages': i18n.get_supported_languages()
        }

        return render_template('settings_multilingual.html', settings=settings_data)

    except Exception as e:
        logger.error(f"설정 페이지 오류: {str(e)}")
        error_msg = t('errors', 'settings_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/settings', methods=['POST'])
@with_i18n
def save_settings():
    """설정 저장"""
    try:
        language = request.form.get('language')
        max_results = request.form.get('max_results', Config.DEFAULT_MAX_RESULTS)

        # 언어 설정
        if language and LanguageInfo.is_supported(language):
            response = make_response(redirect(url_for('settings')))
            response.set_cookie('language', language, max_age=60*60*24*30)
            set_language(language)
            return response

        # 설정 저장 (실제로는 설정 파일에 저장)
        success_msg = t('settings', 'settings_saved')
        flash(success_msg, 'success')

        return redirect(url_for('settings'))

    except Exception as e:
        logger.error(f"설정 저장 오류: {str(e)}")
        error_msg = t('errors', 'save_settings_failed')
        flash(f'{error_msg}: {str(e)}', 'error')
        return redirect(url_for('settings'))


# ============================================================================
# 감정 분석 API
# ============================================================================

@app.route('/api/analyze_sentiment', methods=['POST'])
@with_i18n
def api_analyze_sentiment():
    """다국어 텍스트 감정 분석 API"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            error_msg = t('errors', 'text_required')
            return jsonify({'success': False, 'error': error_msg}), 400

        # 감정 분석
        if multilingual_sentiment_analyzer:
            result = multilingual_sentiment_analyzer.analyze(text)

            return jsonify({
                'success': True,
                'result': result.to_dict()
            })
        else:
            return jsonify({'success': False, 'error': 'Sentiment analyzer not available'}), 503

    except Exception as e:
        logger.error(f"감정 분석 API 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/filter_sentiment', methods=['POST'])
@with_i18n
def api_filter_sentiment():
    """감정 필터링 API"""
    try:
        data = request.get_json()
        sentiment_type = data.get('sentiment', 'positive')
        min_score = float(data.get('min_score', 0.0))
        results = data.get('results', [])

        if not results:
            error_msg = t('errors', 'no_results')
            return jsonify({'success': False, 'error': error_msg}), 400

        # 감정 필터링
        from multilingual_sentiment_analyzer import MultilingualSentimentFilter
        filtered = MultilingualSentimentFilter.filter_by_sentiment(results, sentiment_type, min_score)

        return jsonify({
            'success': True,
            'count': len(filtered),
            'results': filtered
        })

    except Exception as e:
        logger.error(f"감정 필터링 API 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sentiment_stats', methods=['POST'])
@with_i18n
def api_sentiment_stats():
    """감정 통계 API"""
    try:
        data = request.get_json()
        results = data.get('results', [])

        if not results:
            error_msg = t('errors', 'no_results')
            return jsonify({'success': False, 'error': error_msg}), 400

        # 통계 계산
        from multilingual_sentiment_analyzer import MultilingualSentimentFilter
        summary = MultilingualSentimentFilter.get_multilingual_summary(results)
        distribution = MultilingualSentimentFilter.get_language_sentiment_distribution(results)

        return jsonify({
            'success': True,
            'summary': summary,
            'distribution': distribution
        })

    except Exception as e:
        logger.error(f"감정 통계 API 오류: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 헬스체크 및 기타 API
# ============================================================================

@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DealBot Multilingual Web Interface',
        'supported_languages': list(LanguageInfo.SUPPORTED_LANGUAGES.keys())
    })


# ============================================================================
# 다국어 템플릿 생성
# ============================================================================

def create_multilingual_templates():
    """다국어 HTML 템플릿 생성"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    # 베이스 템플릿
    base_template = '''<!DOCTYPE html>
<html lang="{{ current_language }}" dir="{{ language_info.direction }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}{{ t('common', 'app_name') }}{% endblock %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&family=Noto+Sans+JP:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Sans KR', 'Noto Sans JP', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .header-info h1 {
            color: #333;
            margin-bottom: 5px;
            font-size: 24px;
        }

        .header-info p {
            color: #666;
            font-size: 14px;
        }

        .nav {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .nav a {
            text-decoration: none;
            color: #667eea;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background 0.3s;
            font-weight: 500;
        }

        .nav a:hover {
            background: #f0f0f0;
        }

        .nav a.active {
            background: #667eea;
            color: white;
        }

        .content {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .alert {
            padding: 12px 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .footer {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 14px;
        }

        .language-switcher {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
        }

        .lang-btn {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 20px;
            padding: 6px 12px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
        }

        .lang-btn:hover {
            background: #e9ecef;
            border-color: #adb5bd;
        }

        .lang-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        .flag {
            font-size: 16px;
        }

        .lang-name {
            font-weight: 500;
        }

        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
            font-weight: 600;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn-secondary {
            background: #6c757d;
        }

        .btn-success {
            background: #28a745;
        }

        {% block extra_css %}{% endblock %}
    </style>

    <script>
        function changeLanguage(lang) {
            fetch('/api/language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ language: lang })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert(data.error || 'Language change failed');
                }
            })
            .catch(error => {
                console.error('Language change error:', error);
                alert('Language change failed');
            });
        }

        function translateText(category, key, params = {}) {
            let text = translations[category]?.[key] || key;
            Object.keys(params).forEach(param => {
                text = text.replace(`{${param}}`, params[param]);
            });
            return text;
        }
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div class="header-info">
                    <h1>🕷️ {{ t('common', 'app_name') }}</h1>
                    <p>{{ t('common', 'app_subtitle') }}</p>
                </div>

                <div class="language-switcher">
                    {% for lang_code, lang_info in supported_languages.items() %}
                    <button class="lang-btn {{ 'active' if lang_code == current_language else '' }}"
                            onclick="changeLanguage('{{ lang_code }}')"
                            title="{{ lang_info.native_name }}">
                        <span class="flag">{{ lang_info.flag }}</span>
                        <span class="lang-name">{{ lang_info.native_name }}</span>
                    </button>
                    {% endfor %}
                </div>
            </div>

            <nav class="nav">
                <a href="{{ url_for('index') }}">{{ t('nav', 'search') }}</a>
                <a href="{{ url_for('history') }}">{{ t('nav', 'results') }}</a>
                <a href="{{ url_for('settings') }}">{{ t('nav', 'settings') }}</a>
            </nav>
        </div>

        <div class="content">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {% block content %}{% endblock %}
        </div>

        <div class="footer">
            <p>© 2024 {{ t('common', 'app_name') }} | Powered by Flask & BeautifulSoup</p>
        </div>
    </div>

    <script>
        const translations = {{ i18n.get_current_translations() | tojson }};
    </script>

    {% block extra_js %}{% endblock %}
</body>
</html>'''

    # 인덱스 페이지
    index_template = '''{% extends "base.html" %}

{% block title %}{{ t('search_page', 'title') }} - {{ t('common', 'app_name') }}{% endblock %}

{% block extra_css %}
<style>
    .search-form {
        max-width: 600px;
        margin: 0 auto;
    }

    .form-group {
        margin-bottom: 20px;
    }

    .form-group label {
        display: block;
        margin-bottom: 8px;
        color: #333;
        font-weight: 600;
    }

    .radio-group {
        display: flex;
        gap: 20px;
        margin-top: 8px;
        flex-wrap: wrap;
    }

    .radio-item {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .features {
        margin-top: 30px;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
    }

    .feature-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
    }

    .feature-icon {
        font-size: 24px;
        margin-bottom: 10px;
    }

    .feature-title {
        font-weight: 600;
        margin-bottom: 8px;
        color: #333;
    }

    .feature-desc {
        font-size: 14px;
        color: #666;
    }

    .checkbox-item {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }
</style>
{% endblock %}

{% block content %}
<div class="search-form">
    <h2 style="text-align: center; margin-bottom: 30px; color: #333;">
        🔍 {{ t('search_page', 'title') }}
    </h2>

    <form method="POST" action="{{ url_for('search') }}">
        <div class="form-group">
            <label for="keyword">{{ t('search_page', 'keyword_label') }}</label>
            <input type="text" id="keyword" name="keyword" class="form-control"
                   placeholder="{{ t('search_page', 'keyword_placeholder') }}" required>
        </div>

        <div class="form-group">
            <label for="max_results">{{ t('search_page', 'max_results_label') }}</label>
            <input type="number" id="max_results" name="max_results" class="form-control"
                   value="20" min="1" max="100">
        </div>

        <div class="form-group">
            <label>{{ t('search_page', 'search_type_label') }}</label>
            <div class="radio-group">
                <div class="radio-item">
                    <input type="radio" id="naver" name="search_type" value="naver" checked>
                    <label for="naver">{{ t('search_page', 'naver_blog') }}</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="google" name="search_type" value="google">
                    <label for="google">{{ t('search_page', 'google_news') }}</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="multiple" name="search_type" value="multiple">
                    <label for="multiple">{{ t('search_page', 'multiple_search') }}</label>
                </div>
            </div>
        </div>

        {% if multilingual_sentiment_analyzer %}
        <div class="form-group">
            <div class="checkbox-item">
                <input type="checkbox" id="enable_sentiment" name="enable_sentiment">
                <label for="enable_sentiment">{{ t('search_page', 'enable_sentiment') }}</label>
            </div>
        </div>
        {% endif %}

        <button type="submit" class="btn">{{ t('search_page', 'start_search') }}</button>
    </form>

    <div class="features">
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">{{ t('search_page', 'fast_search') }}</div>
            <div class="feature-desc">{{ t('search_page', 'fast_search_desc') }}</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">{{ t('search_page', 'excel_save') }}</div>
            <div class="feature-desc">{{ t('search_page', 'excel_save_desc') }}</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <div class="feature-title">{{ t('search_page', 'multilingual') }}</div>
            <div class="feature-desc">{{ t('search_page', 'multilingual_desc') }}</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <div class="feature-title">{{ t('search_page', 'sentiment_analysis') }}</div>
            <div class="feature-desc">{{ t('search_page', 'sentiment_analysis_desc') }}</div>
        </div>
    </div>
</div>
{% endblock %}'''

    # 결과 페이지
    results_template = '''{% extends "base.html" %}

{% block title %}{{ t('results_page', 'title') }} - {{ t('common', 'app_name') }}{% endblock %}

{% block extra_css %}
<style>
    .stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 15px;
        margin-bottom: 30px;
    }

    .stat-card {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
    }

    .stat-value {
        font-size: 32px;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 5px;
    }

    .stat-label {
        font-size: 14px;
        color: #666;
    }

    .download-buttons {
        display: flex;
        gap: 10px;
        margin-bottom: 30px;
        justify-content: center;
        flex-wrap: wrap;
    }

    .btn-download {
        background: #28a745;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        transition: background 0.3s;
    }

    .btn-download:hover {
        background: #218838;
    }

    .btn-secondary {
        background: #6c757d;
    }

    .btn-secondary:hover {
        background: #5a6268;
    }

    .results-table {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }

    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }

    th {
        background: #f8f9fa;
        font-weight: 600;
        color: #333;
    }

    tr:hover {
        background: #f8f9fa;
    }

    .status-success {
        color: #28a745;
        font-weight: 600;
    }

    .status-error {
        color: #dc3545;
        font-weight: 600;
    }

    .sentiment-positive {
        color: #28a745;
        font-weight: 600;
    }

    .sentiment-negative {
        color: #dc3545;
        font-weight: 600;
    }

    .sentiment-neutral {
        color: #6c757d;
        font-weight: 600;
    }

    .back-button {
        display: inline-block;
        margin-bottom: 20px;
        color: #667eea;
        text-decoration: none;
    }

    .back-button:hover {
        text-decoration: underline;
    }

    .language-tag {
        background: #e9ecef;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        color: #495057;
    }
</style>
{% endblock %}

{% block content %}
<a href="{{ url_for('index') }}" class="back-button">← {{ t('results_page', 'back_to_search') }}</a>

<h2 style="margin-bottom: 20px; color: #333;">📊 {{ t('results_page', 'title') }}: {{ keyword }}</h2>

<div class="stats">
    <div class="stat-card">
        <div class="stat-value">{{ stats.total_count }}</div>
        <div class="stat-label">{{ t('results_page', 'total_results') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.successful_count }}</div>
        <div class="stat-label">{{ t('results_page', 'successful') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.failed_count }}</div>
        <div class="stat-label">{{ t('results_page', 'failed') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="font-size: 18px;">{{ stats.timestamp }}</div>
        <div class="stat-label">{{ t('results_page', 'search_time') }}</div>
    </div>
</div>

{% if stats.sentiment_enabled %}
<div class="stats">
    <div class="stat-card">
        <div class="stat-value">{{ stats.positive_count }}</div>
        <div class="stat-label">{{ t('sentiment', 'positive_words') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.negative_count }}</div>
        <div class="stat-label">{{ t('sentiment', 'negative_words') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.neutral_count }}</div>
        <div class="stat-label">{{ t('sentiment', 'neutral') }}</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="font-size: 20px;">{{ stats.avg_sentiment_score|round(3) }}</div>
        <div class="stat-label">{{ t('sentiment', 'sentiment_score') }}</div>
    </div>
</div>
{% endif %}

<div class="download-buttons">
    <a href="{{ url_for('download_file', filename=result_filename) }}"
       class="btn-download">
        📥 {{ t('results_page', 'download_excel') }}
    </a>
    <a href="{{ url_for('download_csv', filename=result_filename) }}"
       class="btn-download btn-secondary">
        📄 {{ t('results_page', 'download_csv') }}
    </a>
</div>

<div class="results-table">
    <h3 style="margin-bottom: 15px; color: #333;">
        {{ t('results_page', 'results_list') }} ({{ t('results_page', 'first_n_items') }})
    </h3>
    <table>
        <thead>
            <tr>
                <th>{{ t('results_page', 'table_headers').index }}</th>
                <th>{{ t('results_page', 'table_headers').title }}</th>
                <th>{{ t('results_page', 'table_headers').url }}</th>
                <th>{{ t('results_page', 'table_headers').blog_name }}</th>
                <th>{{ t('results_page', 'table_headers').date }}</th>
                <th>{{ t('results_page', 'table_headers').status }}</th>
                {% if stats.sentiment_enabled %}
                <th>{{ t('results_page', 'table_headers').sentiment }}</th>
                <th>{{ t('results_page', 'table_headers').language }}</th>
                <th>{{ t('results_page', 'table_headers').score }}</th>
                {% endif %}
            </tr>
        </thead>
        <tbody>
            {% for result in results %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>
                    <a href="{{ result.url }}" target="_blank"
                       style="color: #667eea; text-decoration: none;">
                        {{ result.title[:50] }}...
                    </a>
                </td>
                <td>
                    <small style="color: #666;">{{ result.url[:50] }}...</small>
                </td>
                <td>{{ result.blog_name or '-' }}</td>
                <td>{{ result.date or '-' }}</td>
                <td class="{% if result.status == '성공' %}status-success{% else %}status-error{% endif %}">
                    {{ result.status }}
                </td>
                {% if stats.sentiment_enabled %}
                <td>
                    {% if result.sentiment_label %}
                    <span class="sentiment-{{ result.sentiment_label }}">
                        {{ result.sentiment_label }}
                    </span>
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>
                    {% if result.detected_language %}
                    <span class="language-tag">{{ result.detected_language }}</span>
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>
                    {% if result.sentiment_score %}
                    {{ result.sentiment_score|round(3) }}
                    {% else %}
                    -
                    {% endif %}
                </td>
                {% endif %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''

    # 이력 페이지
    history_template = '''{% extends "base.html" %}

{% block title %}{{ t('nav', 'results') }} - {{ t('common', 'app_name') }}{% endblock %}

{% block extra_css %}
<style>
    .back-button {
        display: inline-block;
        margin-bottom: 20px;
        color: #667eea;
        text-decoration: none;
    }

    .back-button:hover {
        text-decoration: underline;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }

    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }

    th {
        background: #f8f9fa;
        font-weight: 600;
        color: #333;
    }

    tr:hover {
        background: #f8f9fa;
    }

    .btn-action {
        background: #667eea;
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        text-decoration: none;
        font-size: 14px;
        transition: background 0.3s;
    }

    .btn-action:hover {
        background: #5568d3;
    }

    .empty-state {
        text-align: center;
        padding: 40px;
        color: #666;
    }
</style>
{% endblock %}

{% block content %}
<a href="{{ url_for('index') }}" class="back-button">← {{ t('common', 'home') }}</a>

<h2 style="margin-bottom: 20px; color: #333;">📋 {{ t('nav', 'results') }}</h2>

{% if files %}
<div style="overflow-x: auto;">
    <table>
        <thead>
            <tr>
                <th>{{ t('results_page', 'table_headers').filename }}</th>
                <th>{{ t('common', 'size') }}</th>
                <th>{{ t('common', 'date') }}</th>
                <th>{{ t('common', 'action') }}</th>
            </tr>
        </thead>
        <tbody>
            {% for file in files %}
            <tr>
                <td>{{ file.filename }}</td>
                <td>{{ file.size }}</td>
                <td>{{ file.created }}</td>
                <td>
                    <a href="{{ url_for('download_file', filename=file.filename) }}"
                       class="btn-action">
                        {{ t('common', 'download') }}
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="empty-state">
    <p>{{ t('common', 'no_results') }}</p>
    <a href="{{ url_for('index') }}" style="color: #667eea;">{{ t('search_page', 'start_search') }}</a>
</div>
{% endif %}
{% endblock %}'''

    # 설정 페이지
    settings_template = '''{% extends "base.html" %}

{% block title %}{{ t('nav', 'settings') }} - {{ t('common', 'app_name') }}{% endblock %}

{% block extra_css %}
<style>
    .settings-container {
        max-width: 800px;
        margin: 0 auto;
    }

    .settings-section {
        background: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .settings-section h3 {
        margin-bottom: 20px;
        color: #333;
        font-size: 18px;
    }

    .form-group {
        margin-bottom: 20px;
    }

    .form-group label {
        display: block;
        margin-bottom: 8px;
        color: #333;
        font-weight: 600;
    }

    .btn-group {
        display: flex;
        gap: 10px;
        margin-top: 20px;
    }

    .language-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }

    .language-option {
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s;
    }

    .language-option:hover {
        border-color: #667eea;
        background: #f0f4ff;
    }

    .language-option.active {
        border-color: #667eea;
        background: #667eea;
        color: white;
    }

    .language-option.active .lang-code,
    .language-option.active .lang-name {
        color: white;
    }

    .lang-code {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }

    .lang-name {
        font-weight: 600;
        color: #333;
    }

    .switch-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .switch {
        position: relative;
        display: inline-block;
        width: 50px;
        height: 24px;
    }

    .switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }

    .slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        transition: .4s;
        border-radius: 24px;
    }

    .slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
    }

    input:checked + .slider {
        background-color: #667eea;
    }

    input:checked + .slider:before {
        transform: translateX(26px);
    }
</style>
{% endblock %}

{% block content %}
<div class="settings-container">
    <h2 style="margin-bottom: 30px; color: #333;">⚙️ {{ t('nav', 'settings') }}</h2>

    <form method="POST" action="{{ url_for('save_settings') }}">
        <!-- 언어 설정 -->
        <div class="settings-section">
            <h3>🌐 {{ t('settings', 'language_settings') }}</h3>

            <div class="form-group">
                <label>{{ t('settings', 'interface_language') }}</label>
                <div class="language-grid">
                    {% for lang_code, lang_info in supported_languages.items() %}
                    <div class="language-option {{ 'active' if lang_code == current_language else '' }}"
                            onclick="selectLanguage('{{ lang_code }}')">
                        <div class="lang-code">{{ lang_info.flag }} {{ lang_code }}</div>
                        <div class="lang-name">{{ lang_info.native_name }}</div>
                        <input type="hidden" name="language" value="{{ lang_code }}">
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- 검색 설정 -->
        <div class="settings-section">
            <h3>🔍 {{ t('settings', 'search_settings') }}</h3>

            <div class="form-group">
                <label for="max_results">{{ t('settings', 'default_max_results') }}</label>
                <input type="number" id="max_results" name="max_results" class="form-control"
                       value="{{ settings.max_results }}" min="1" max="100">
            </div>

            {% if settings.enable_sentiment %}
            <div class="form-group">
                <div class="switch-container">
                    <label class="switch">
                        <input type="checkbox" id="enable_sentiment" name="enable_sentiment" checked>
                        <span class="slider"></span>
                    </label>
                    <span>{{ t('settings', 'enable_sentiment') }}</span>
                </div>
            </div>
            {% endif %}
        </div>

        <div class="btn-group">
            <button type="submit" class="btn">{{ t('settings', 'save_settings') }}</button>
            <button type="button" class="btn btn-secondary" onclick="resetSettings()">
                {{ t('settings', 'reset_to_default') }}
            </button>
        </div>
    </form>
</div>

<script>
    function selectLanguage(lang) {
        // 모든 옵션 비활성화
        document.querySelectorAll('.language-option').forEach(option => {
            option.classList.remove('active');
        });

        // 선택한 옵션 활성화
        event.target.closest('.language-option').classList.add('active');

        // 언어 변경
        changeLanguage(lang);
    }

    function resetSettings() {
        if (confirm('{{ t('common', 'reset') }}?')) {
            location.reload();
        }
    }
</script>
{% endblock %}'''

    # 템플릿 파일들 저장
    templates = {
        'base.html': base_template,
        'index_multilingual.html': index_template,
        'results_multilingual.html': results_template,
        'history_multilingual.html': history_template,
        'settings_multilingual.html': settings_template
    }

    for filename, content in templates.items():
        template_path = templates_dir / filename
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"다국어 템플릿 생성 완료: {template_path}")


# ============================================================================
# 메인 실행 함수
# ============================================================================

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🌐 DealBot 다국어 웹 인터페이스 시작")
    print("=" * 60)

    # 다국어 템플릿 생성
    create_multilingual_templates()

    # Flask 서버 시작
    print("\n✅ 다국어 템플릿 생성 완료")
    print("🚀 웹 서버 시작 중...")
    print(f"📱 접속 주소: http://localhost:5000")
    print(f"📋 헬스체크: http://localhost:5000/health")
    print(f"🌍 지원 언어: {len(LanguageInfo.SUPPORTED_LANGUAGES)}개")
    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)


if __name__ == '__main__':
    main()