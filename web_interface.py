#!/usr/bin/env python3
"""
Flask 기반 웹 인터페이스
DealBot 크롤러를 위한 간단한 웹 UI 제공
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from pathlib import Path
import logging
from io import BytesIO
import pandas as pd

# 기존 크롤러 임포트
from web_crawler import WebCrawler, Config, setup_logging

# 감정 분석 임포트
from sentiment_analyzer import SentimentAnalyzer, SentimentFilter

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'dealbot-secret-key-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['DOWNLOAD_FOLDER'] = 'downloads'

# 로거 설정
logger = setup_logging()

# 디렉토리 생성
for folder in [app.config['UPLOAD_FOLDER'], app.config['RESULTS_FOLDER'], app.config['DOWNLOAD_FOLDER']]:
    Path(folder).mkdir(exist_ok=True)

# 크롤러 및 감정 분석기 인스턴스
crawler = WebCrawler()
sentiment_analyzer = SentimentAnalyzer()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """검색 처리"""
    try:
        # 폼 데이터 가져오기
        keyword = request.form.get('keyword', '').strip()
        max_results = int(request.form.get('max_results', Config.DEFAULT_MAX_RESULTS))
        search_type = request.form.get('search_type', 'naver')
        enable_sentiment = request.form.get('enable_sentiment') == 'true'  # 감정 분석 옵션

        if not keyword:
            flash('검색어를 입력해주세요.', 'error')
            return redirect(url_for('index'))

        logger.info(f"검색 요청: keyword={keyword}, max_results={max_results}, type={search_type}, sentiment={enable_sentiment}")

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
                'positive_count': sentiment_stats['positive_count'],
                'negative_count': sentiment_stats['negative_count'],
                'neutral_count': sentiment_stats['neutral_count'],
                'positive_ratio': sentiment_stats['positive_ratio'],
                'negative_ratio': sentiment_stats['negative_ratio'],
                'avg_sentiment_score': sentiment_stats['avg_sentiment_score']
            })

        logger.info(f"검색 완료: {stats['total_count']}개 결과, 파일={result_filename}")

        return render_template('results.html',
                             results=results[:50],  # 처음 50개만 표시
                             stats=stats,
                             keyword=keyword,
                             result_filename=result_filename)

    except Exception as e:
        logger.error(f"검색 오류: {str(e)}")
        flash(f'검색 중 오류가 발생했습니다: {str(e)}', 'error')
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
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"다운로드 오류: {str(e)}")
        flash(f'다운로드 중 오류가 발생했습니다: {str(e)}', 'error')
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
            flash('파일을 찾을 수 없습니다.', 'error')
            return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"CSV 다운로드 오류: {str(e)}")
        flash(f'CSV 다운로드 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/history')
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

        return render_template('history.html', files=files)

    except Exception as e:
        logger.error(f"이력 조회 오류: {str(e)}")
        flash(f'이력 조회 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/search', methods=['POST'])
def api_search():
    """AJAX 검색 API"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        max_results = int(data.get('max_results', Config.DEFAULT_MAX_RESULTS))
        search_type = data.get('search_type', 'naver')

        if not keyword:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400

        logger.info(f"API 검색 요청: keyword={keyword}, max_results={max_results}")

        # 크롤링 수행
        if search_type == 'naver':
            results = crawler.search_naver_blog(keyword, max_results=max_results)
        elif search_type == 'google':
            results = crawler.search_google(keyword, max_results=max_results)
        else:
            results = crawler.search_multiple_sources(keyword, max_results=max_results)

        return jsonify({
            'success': True,
            'count': len(results),
            'results': results[:20]  # 처음 20개만 반환
        })

    except Exception as e:
        logger.error(f"API 검색 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DealBot Web Interface'
    })

@app.route('/api/analyze_sentiment', methods=['POST'])
def api_analyze_sentiment():
    """텍스트 감정 분석 API"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': '텍스트를 입력해주세요.'}), 400

        # 감정 분석
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

    except Exception as e:
        logger.error(f"감정 분석 API 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter_sentiment', methods=['POST'])
def api_filter_sentiment():
    """감정 필터링 API"""
    try:
        data = request.get_json()
        sentiment_type = data.get('sentiment', 'positive')  # 'positive', 'negative', 'neutral'
        min_score = float(data.get('min_score', 0.0))
        results = data.get('results', [])

        if not results:
            return jsonify({'error': '결과 데이터가 없습니다.'}), 400

        # 감정 필터링
        filtered = SentimentFilter.filter_by_sentiment(results, sentiment_type, min_score)

        return jsonify({
            'success': True,
            'count': len(filtered),
            'results': filtered
        })

    except Exception as e:
        logger.error(f"감정 필터링 API 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sentiment_stats', methods=['POST'])
def api_sentiment_stats():
    """감정 통계 API"""
    try:
        data = request.get_json()
        results = data.get('results', [])

        if not results:
            return jsonify({'error': '결과 데이터가 없습니다.'}), 400

        # 통계 계산
        summary = SentimentFilter.get_sentiment_summary(results)
        distribution = SentimentFilter.get_sentiment_distribution(results)

        return jsonify({
            'success': True,
            'summary': summary,
            'distribution': distribution
        })

    except Exception as e:
        logger.error(f"감정 통계 API 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_templates():
    """HTML 템플릿 생성"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    # 베이스 템플릿
    base_template = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DealBot - 웹 크롤러{% endblock %}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, sans-serif;
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

        .header h1 {
            color: #333;
            margin-bottom: 5px;
        }

        .header p {
            color: #666;
            font-size: 14px;
        }

        .nav {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }

        .nav a {
            text-decoration: none;
            color: #667eea;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background 0.3s;
        }

        .nav a:hover {
            background: #f0f0f0;
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

        .footer {
            text-align: center;
            color: white;
            margin-top: 20px;
            font-size: 14px;
        }

        {% block extra_css %}{% endblock %}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🕷️ DealBot</h1>
            <p>웹 주제 크롤러 및 Excel 저장 프로그램</p>
            <nav class="nav">
                <a href="{{ url_for('index') }}">홈</a>
                <a href="{{ url_for('history') }}">검색 이력</a>
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
            <p>© 2024 DealBot | Powered by Flask & BeautifulSoup</p>
        </div>
    </div>

    {% block extra_js %}{% endblock %}
</body>
</html>'''

    # 인덱스 페이지
    index_template = '''{% extends "base.html" %}

{% block title %}검색 - DealBot{% endblock %}

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
    }

    .btn:hover {
        transform: translateY(-2px);
    }

    .radio-group {
        display: flex;
        gap: 20px;
        margin-top: 8px;
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
</style>
{% endblock %}

{% block content %}
<div class="search-form">
    <h2 style="text-align: center; margin-bottom: 30px; color: #333;">🔍 웹 검색</h2>

    <form method="POST" action="{{ url_for('search') }}">
        <div class="form-group">
            <label for="keyword">검색어</label>
            <input type="text" id="keyword" name="keyword" class="form-control"
                   placeholder="검색어를 입력하세요..." required>
        </div>

        <div class="form-group">
            <label for="max_results">최대 결과 수</label>
            <input type="number" id="max_results" name="max_results" class="form-control"
                   value="20" min="1" max="100">
        </div>

        <div class="form-group">
            <label>검색 유형</label>
            <div class="radio-group">
                <div class="radio-item">
                    <input type="radio" id="naver" name="search_type" value="naver" checked>
                    <label for="naver">네이버 블로그</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="google" name="search_type" value="google">
                    <label for="google">구글</label>
                </div>
                <div class="radio-item">
                    <input type="radio" id="multiple" name="search_type" value="multiple">
                    <label for="multiple">다중 검색</label>
                </div>
            </div>
        </div>

        <button type="submit" class="btn">검색 시작</button>
    </form>

    <div class="features">
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">빠른 검색</div>
            <div class="feature-desc">최적화된 크롤링으로 빠른 결과 제공</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Excel 저장</div>
            <div class="feature-desc">검색 결과를 엑셀 파일로 다운로드</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔔</div>
            <div class="feature-title">RSS 피드</div>
            <div class="feature-desc">RSS 피드 구독 및 알림 기능</div>
        </div>
    </div>
</div>
{% endblock %}'''

    # 결과 페이지
    results_template = '''{% extends "base.html" %}

{% block title %}검색 결과 - DealBot{% endblock %}

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

    .back-button {
        display: inline-block;
        margin-bottom: 20px;
        color: #667eea;
        text-decoration: none;
    }

    .back-button:hover {
        text-decoration: underline;
    }
</style>
{% endblock %}

{% block content %}
<a href="{{ url_for('index') }}" class="back-button">← 다시 검색</a>

<h2 style="margin-bottom: 20px; color: #333;">📊 검색 결과: {{ keyword }}</h2>

<div class="stats">
    <div class="stat-card">
        <div class="stat-value">{{ stats.total_count }}</div>
        <div class="stat-label">총 결과 수</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.successful_count }}</div>
        <div class="stat-label">성공</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{{ stats.failed_count }}</div>
        <div class="stat-label">실패</div>
    </div>
    <div class="stat-card">
        <div class="stat-value" style="font-size: 18px;">{{ stats.timestamp }}</div>
        <div class="stat-label">검색 시간</div>
    </div>
</div>

<div class="download-buttons">
    <a href="{{ url_for('download_file', filename=result_filename) }}"
       class="btn-download">
        📥 Excel 다운로드
    </a>
    <a href="{{ url_for('download_csv', filename=result_filename) }}"
       class="btn-download btn-secondary">
        📄 CSV 다운로드
    </a>
</div>

<div class="results-table">
    <h3 style="margin-bottom: 15px; color: #333;">결과 목록 (처음 50개)</h3>
    <table>
        <thead>
            <tr>
                <th>순번</th>
                <th>제목</th>
                <th>URL</th>
                <th>블로그명</th>
                <th>날짜</th>
                <th>상태</th>
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
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}'''

    # 이력 페이지
    history_template = '''{% extends "base.html" %}

{% block title %}검색 이력 - DealBot{% endblock %}

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
<a href="{{ url_for('index') }}" class="back-button">← 홈으로</a>

<h2 style="margin-bottom: 20px; color: #333;">📋 검색 이력</h2>

{% if files %}
<div style="overflow-x: auto;">
    <table>
        <thead>
            <tr>
                <th>파일명</th>
                <th>크기</th>
                <th>생성일</th>
                <th>작업</th>
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
                        다운로드
                    </a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% else %}
<div class="empty-state">
    <p>저장된 검색 결과가 없습니다.</p>
    <a href="{{ url_for('index') }}" style="color: #667eea;">검색 시작하기</a>
</div>
{% endif %}
{% endblock %}'''

    # 템플릿 파일들 저장
    templates = {
        'base.html': base_template,
        'index.html': index_template,
        'results.html': results_template,
        'history.html': history_template
    }

    for filename, content in templates.items():
        template_path = templates_dir / filename
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"템플릿 생성 완료: {template_path}")

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🕷️ DealBot 웹 인터페이스 시작")
    print("=" * 50)

    # 템플릿 생성
    create_templates()

    # Flask 서버 시작
    print("\n✅ 템플릿 생성 완료")
    print("🚀 웹 서버 시작 중...")
    print(f"📱 접속 주소: http://localhost:5000")
    print(f"📋 헬스체크: http://localhost:5000/health")
    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 50 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()