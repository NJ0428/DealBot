#!/usr/bin/env python3
"""
WebSocket 기반 실시간 모니터링 대시보드
DealBot 크롤러 진행률 실시간 표시
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
from datetime import datetime
from pathlib import Path
import logging
from collections import deque
import json

# 기존 크롤러 임포트
from web_crawler import WebCrawler, Config, setup_logging
from sentiment_analyzer import SentimentAnalyzer, SentimentFilter

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'dealbot-websocket-secret-key'

# SocketIO 설정
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# 로거 설정
logger = setup_logging()

# 크롤러 및 감정 분석기 인스턴스
crawler = WebCrawler()
sentiment_analyzer = SentimentAnalyzer()

# 크롤링 작업 관리
crawling_jobs = {}
job_lock = threading.Lock()

# 실시간 통계 관리
class RealTimeStats:
    def __init__(self):
        self.last_update = datetime.now()
        self.total_crawls = 0
        self.successful_crawls = 0
        self.failed_crawls = 0
        self.active_jobs = 0
        self.recent_results = deque(maxlen=10)  # 최근 10개 결과 저장
        self.crawling_sources = {
            'naver': {'count': 0, 'last_used': None},
            'google': {'count': 0, 'last_used': None},
            'multiple': {'count': 0, 'last_used': None}
        }

    def update_stats(self, success: bool, search_type: str):
        self.last_update = datetime.now()
        self.total_crawls += 1
        if success:
            self.successful_crawls += 1
        else:
            self.failed_crawls += 1

        if search_type in self.crawling_sources:
            self.crawling_sources[search_type]['count'] += 1
            self.crawling_sources[search_type]['last_used'] = datetime.now().isoformat()

    def add_result(self, keyword: str, count: int, success: bool):
        self.recent_results.append({
            'keyword': keyword,
            'count': count,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

    def to_dict(self):
        return {
            'last_update': self.last_update.isoformat(),
            'total_crawls': self.total_crawls,
            'successful_crawls': self.successful_crawls,
            'failed_crawls': self.failed_crawls,
            'active_jobs': self.active_jobs,
            'success_rate': (self.successful_crawls / self.total_crawls * 100) if self.total_crawls > 0 else 0,
            'recent_results': list(self.recent_results),
            'crawling_sources': self.crawling_sources
        }

stats = RealTimeStats()

class CrawlingProgress:
    def __init__(self, job_id: str, keyword: str, total_targets: int):
        self.job_id = job_id
        self.keyword = keyword
        self.total_targets = total_targets
        self.completed = 0
        self.failed = 0
        self.results = []
        self.start_time = datetime.now()
        self.end_time = None
        self.status = 'running'  # running, completed, failed
        self.error_message = None
        self.progress_percentage = 0.0
        self.current_target = None

    def update_progress(self, completed: int, failed: int = 0, current_target: str = None):
        self.completed = completed
        self.failed = failed
        self.current_target = current_target
        self.progress_percentage = (completed / self.total_targets * 100) if self.total_targets > 0 else 100

    def add_result(self, result: dict):
        self.results.append(result)

    def complete(self, success: bool = True, error_message: str = None):
        self.end_time = datetime.now()
        self.status = 'completed' if success else 'failed'
        self.error_message = error_message
        self.progress_percentage = 100.0

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'keyword': self.keyword,
            'total_targets': self.total_targets,
            'completed': self.completed,
            'failed': self.failed,
            'progress_percentage': round(self.progress_percentage, 2),
            'status': self.status,
            'current_target': self.current_target,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'elapsed_time': (datetime.now() - self.start_time).total_seconds(),
            'results_count': len(self.results)
        }

def generate_job_id():
    """고유한 작업 ID 생성"""
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ============================================================================
# WebSocket 이벤트 핸들러
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결 시"""
    logger.info(f"클라이언트 연결됨: {request.sid}")

    # 현재 상태 전송
    emit('connected', {
        'message': '서버에 연결되었습니다',
        'timestamp': datetime.now().isoformat()
    })

    # 현재 통계 전송
    emit('stats_update', stats.to_dict())

    # 진행 중인 작업 정보 전송
    with job_lock:
        active_jobs = [job.to_dict() for job in crawling_jobs.values() if job.status == 'running']

    emit('active_jobs', active_jobs)

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제 시"""
    logger.info(f"클라이언트 연결 해제: {request.sid}")

@socketio.on('join_monitoring')
def handle_join_monitoring():
    """모니터링 룸 참여"""
    room = 'monitoring'
    join_room(room)
    logger.info(f"클라이언트 {request.sid}가 모니터링 룸에 참여했습니다")

    emit('joined_monitoring', {
        'message': '모니터링 룸에 참여했습니다',
        'room': room
    })

@socketio.on('leave_monitoring')
def handle_leave_monitoring():
    """모니터링 룸 퇴장"""
    room = 'monitoring'
    leave_room(room)
    logger.info(f"클라이언트 {request.sid}가 모니터링 룸에서 퇴장했습니다")

@socketio.on('request_stats')
def handle_request_stats():
    """통계 요청"""
    emit('stats_update', stats.to_dict())

@socketio.on('request_active_jobs')
def handle_request_active_jobs():
    """진행 중인 작업 요청"""
    with job_lock:
        active_jobs = [job.to_dict() for job in crawling_jobs.values() if job.status == 'running']

    emit('active_jobs', active_jobs)

@socketio.on('cancel_job')
def handle_cancel_job(data):
    """작업 취소"""
    job_id = data.get('job_id')

    with job_lock:
        if job_id in crawling_jobs:
            job = crawling_jobs[job_id]
            job.complete(success=False, error_message='사용자에 의해 취소됨')
            stats.active_jobs -= 1

            socketio.emit('job_cancelled', job.to_dict(), room='monitoring')
            socketio.emit('stats_update', stats.to_dict(), room='monitoring')

            return {'success': True, 'message': '작업이 취소되었습니다'}

    return {'success': False, 'message': '작업을 찾을 수 없습니다'}

# ============================================================================
# HTTP 라우트
# ============================================================================

@app.route('/')
def index():
    """메인 페이지 - 대시보드"""
    return render_template('dashboard.html')

@app.route('/monitoring')
def monitoring():
    """모니터링 페이지"""
    return render_template('monitoring.html')

@app.route('/api/crawl/start', methods=['POST'])
def start_crawling():
    """크롤링 시작"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()
        max_results = int(data.get('max_results', Config.DEFAULT_MAX_RESULTS))
        search_type = data.get('search_type', 'naver')

        if not keyword:
            return jsonify({'error': '검색어를 입력해주세요.'}), 400

        # 작업 ID 생성
        job_id = generate_job_id()

        # 진행 상태 생성
        progress = CrawlingProgress(job_id, keyword, max_results)

        with job_lock:
            crawling_jobs[job_id] = progress
            stats.active_jobs += 1

        # 백그라운드에서 크롤링 실행
        thread = threading.Thread(
            target=run_crawling_job,
            args=(job_id, keyword, max_results, search_type)
        )
        thread.daemon = True
        thread.start()

        # 작업 시작 알림
        socketio.emit('job_started', progress.to_dict(), room='monitoring')
        socketio.emit('stats_update', stats.to_dict(), room='monitoring')

        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': '크롤링이 시작되었습니다'
        })

    except Exception as e:
        logger.error(f"크롤링 시작 오류: {str(e)}")
        return jsonify({'error': str(e)}), 500

def run_crawling_job(job_id: str, keyword: str, max_results: int, search_type: str):
    """백그라운드 크롤링 작업 실행"""
    progress = None

    try:
        with job_lock:
            progress = crawling_jobs.get(job_id)

        if not progress:
            logger.error(f"작업을 찾을 수 없음: {job_id}")
            return

        logger.info(f"크롤링 작업 시작: {job_id}, keyword={keyword}, type={search_type}")

        # 크롤링 진행 상황 업데이트 함수
        def progress_callback(current, total, url=None):
            with job_lock:
                if progress.status != 'running':
                    return False  # 작업이 중단된 경우

                progress.update_progress(current, 0, url)

                # 실시간으로 진행 상황 전송
                socketio.emit('job_progress', progress.to_dict(), room='monitoring')

            return True

        # 크롤링 수행
        results = []
        if search_type == 'naver':
            results = crawler.search_naver_blog(keyword, max_results=max_results,
                                                progress_callback=progress_callback)
        elif search_type == 'google':
            results = crawler.search_google(keyword, max_results=max_results,
                                          progress_callback=progress_callback)
        else:
            results = crawler.search_multiple_sources(keyword, max_results=max_results,
                                                     progress_callback=progress_callback)

        # 결과 저장
        successful_count = len([r for r in results if r.get('status') == '성공'])
        failed_count = len([r for r in results if r.get('status') != '성공'])

        with job_lock:
            progress.update_progress(successful_count, failed_count)
            progress.results = results
            progress.complete(success=True)

        # 통계 업데이트
        stats.update_stats(successful_count > 0, search_type)
        stats.add_result(keyword, successful_count, successful_count > 0)
        stats.active_jobs -= 1

        # 완료 알림
        socketio.emit('job_completed', progress.to_dict(), room='monitoring')
        socketio.emit('stats_update', stats.to_dict(), room='monitoring')

        logger.info(f"크롤링 작업 완료: {job_id}, 성공: {successful_count}, 실패: {failed_count}")

    except Exception as e:
        logger.error(f"크롤링 작업 오류: {job_id}, error={str(e)}")

        with job_lock:
            if progress:
                progress.complete(success=False, error_message=str(e))
                stats.active_jobs -= 1

        # 오류 알림
        socketio.emit('job_failed', progress.to_dict() if progress else {'job_id': job_id, 'error': str(e)}, room='monitoring')
        socketio.emit('stats_update', stats.to_dict(), room='monitoring')

@app.route('/api/jobs')
def list_jobs():
    """모든 작업 목록 조회"""
    with job_lock:
        jobs = [job.to_dict() for job in crawling_jobs.values()]

    return jsonify({
        'success': True,
        'jobs': jobs,
        'count': len(jobs)
    })

@app.route('/api/jobs/<job_id>')
def get_job(job_id: str):
    """특정 작업 조회"""
    with job_lock:
        job = crawling_jobs.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'success': True,
        'job': job.to_dict()
    })

@app.route('/api/stats')
def get_stats():
    """통계 정보 조회"""
    return jsonify({
        'success': True,
        'stats': stats.to_dict()
    })

@app.route('/health')
def health_check():
    """헬스체크"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DealBot Real-time Monitor'
    })

# ============================================================================
# HTML 템플릿 생성
# ============================================================================

def create_templates():
    """HTML 템플릿 생성"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    # 대시보드 템플릿
    dashboard_template = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 DealBot 실시간 모니터링</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            max-width: 1400px;
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

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ccc;
            margin-left: 10px;
        }

        .status-indicator.connected {
            background: #28a745;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .stat-card {
            text-align: center;
        }

        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .card h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 18px;
        }

        .job-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #667eea;
        }

        .job-item.completed {
            border-left-color: #28a745;
        }

        .job-item.failed {
            border-left-color: #dc3545;
        }

        .job-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        .job-title {
            font-weight: 600;
            color: #333;
        }

        .job-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }

        .job-status.running {
            background: #fff3cd;
            color: #856404;
        }

        .job-status.completed {
            background: #d4edda;
            color: #155724;
        }

        .job-status.failed {
            background: #f8d7da;
            color: #721c24;
        }

        .progress-bar {
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 5px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }

        .progress-text {
            font-size: 12px;
            color: #666;
            display: flex;
            justify-content: space-between;
        }

        .job-details {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }

        .form-group {
            margin-bottom: 15px;
        }

        .form-group label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 600;
        }

        .form-control {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            font-size: 14px;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            font-size: 14px;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .btn-danger {
            background: #dc3545;
            padding: 6px 12px;
            font-size: 12px;
            width: auto;
        }

        .recent-results {
            max-height: 300px;
            overflow-y: auto;
        }

        .result-item {
            padding: 10px;
            border-bottom: 1px solid #e9ecef;
            font-size: 13px;
        }

        .result-item:last-child {
            border-bottom: none;
        }

        .result-keyword {
            font-weight: 600;
            color: #333;
        }

        .result-count {
            color: #667eea;
            font-weight: bold;
        }

        .result-time {
            color: #666;
            font-size: 11px;
        }

        .success {
            color: #28a745;
        }

        .failed {
            color: #dc3545;
        }

        .log-container {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            max-height: 300px;
            overflow-y: auto;
        }

        .log-entry {
            margin-bottom: 5px;
            padding: 5px;
            border-left: 2px solid #667eea;
            padding-left: 10px;
        }

        .log-entry.error {
            border-left-color: #dc3545;
        }

        .log-entry.success {
            border-left-color: #28a745;
        }

        .log-time {
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 DealBot 실시간 모니터링</h1>
            <p>WebSocket 기반 라이브 크롤링 대시보드</p>
            <div style="margin-top: 10px;">
                <span id="connectionStatus" class="status-indicator"></span>
                <span id="connectionText">연결 대기 중...</span>
            </div>
        </div>

        <!-- 통계 카드 -->
        <div class="grid">
            <div class="card stat-card">
                <div class="stat-value" id="totalCrawls">0</div>
                <div class="stat-label">총 크롤링</div>
            </div>
            <div class="card stat-card">
                <div class="stat-value" id="successRate">0%</div>
                <div class="stat-label">성공률</div>
            </div>
            <div class="card stat-card">
                <div class="stat-value" id="activeJobs">0</div>
                <div class="stat-label">진행 중인 작업</div>
            </div>
            <div class="card stat-card">
                <div class="stat-value" id="recentSuccess">0</div>
                <div class="stat-label">최근 성공</div>
            </div>
        </div>

        <!-- 크롤링 제어 및 진행률 -->
        <div class="grid">
            <div class="card">
                <h3>🚀 크롤링 시작</h3>
                <form id="crawlForm">
                    <div class="form-group">
                        <label for="keyword">검색어</label>
                        <input type="text" id="keyword" class="form-control"
                               placeholder="검색어를 입력하세요..." required>
                    </div>
                    <div class="form-group">
                        <label for="maxResults">최대 결과 수</label>
                        <input type="number" id="maxResults" class="form-control"
                               value="20" min="1" max="100">
                    </div>
                    <div class="form-group">
                        <label for="searchType">검색 유형</label>
                        <select id="searchType" class="form-control">
                            <option value="naver">네이버 블로그</option>
                            <option value="google">구글</option>
                            <option value="multiple">다중 검색</option>
                        </select>
                    </div>
                    <button type="submit" class="btn">크롤링 시작</button>
                </form>
            </div>

            <div class="card">
                <h3>📋 실시간 작업 진행률</h3>
                <div id="jobsContainer">
                    <p style="text-align: center; color: #999;">진행 중인 작업이 없습니다</p>
                </div>
            </div>
        </div>

        <!-- 최근 결과 및 로그 -->
        <div class="grid">
            <div class="card">
                <h3>📈 최근 크롤링 결과</h3>
                <div class="recent-results" id="recentResults">
                    <p style="text-align: center; color: #999;">결과가 없습니다</p>
                </div>
            </div>

            <div class="card">
                <h3>📝 실시간 로그</h3>
                <div class="log-container" id="logContainer">
                    <div class="log-entry">
                        <span class="log-time">[시스템]</span>
                        대시보드가 초기화되었습니다
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Socket.io 클라이언트 설정
        const socket = io();

        // 연결 상태 관리
        socket.on('connect', () => {
            console.log('서버에 연결되었습니다');
            updateConnectionStatus(true);
            addLog('서버에 연결되었습니다', 'success');

            // 모니터링 룸 참여
            socket.emit('join_monitoring');
        });

        socket.on('disconnect', () => {
            console.log('서버 연결이 해제되었습니다');
            updateConnectionStatus(false);
            addLog('서버 연결이 해제되었습니다', 'error');
        });

        socket.on('connected', (data) => {
            addLog('연결 확인: ' + data.message, 'success');
        });

        socket.on('joined_monitoring', (data) => {
            addLog('모니터링 룸 참여: ' + data.message, 'success');
        });

        // 통계 업데이트
        socket.on('stats_update', (data) => {
            updateStats(data);
        });

        // 작업 시작
        socket.on('job_started', (data) => {
            addJob(data);
            addLog(`작업 시작: ${data.keyword}`, 'info');
        });

        // 작업 진행률 업데이트
        socket.on('job_progress', (data) => {
            updateJobProgress(data);
        });

        // 작업 완료
        socket.on('job_completed', (data) => {
            completeJob(data);
            addLog(`작업 완료: ${data.keyword} - ${data.results_count}개 결과`, 'success');
        });

        // 작업 실패
        socket.on('job_failed', (data) => {
            failJob(data);
            addLog(`작업 실패: ${data.keyword} - ${data.error_message || '알 수 없는 오류'}`, 'error');
        });

        // 진행 중인 작업 목록
        socket.on('active_jobs', (jobs) => {
            jobs.forEach(job => addJob(job));
        });

        // UI 업데이트 함수들
        function updateConnectionStatus(connected) {
            const indicator = document.getElementById('connectionStatus');
            const text = document.getElementById('connectionText');

            if (connected) {
                indicator.classList.add('connected');
                text.textContent = '연결됨';
            } else {
                indicator.classList.remove('connected');
                text.textContent = '연결 해제됨';
            }
        }

        function updateStats(stats) {
            document.getElementById('totalCrawls').textContent = stats.total_crawls;
            document.getElementById('successRate').textContent = stats.success_rate.toFixed(1) + '%';
            document.getElementById('activeJobs').textContent = stats.active_jobs;

            // 최근 성공 횟수 계산
            const recentSuccess = stats.recent_results.filter(r => r.success).length;
            document.getElementById('recentSuccess').textContent = recentSuccess;

            // 최근 결과 업데이트
            updateRecentResults(stats.recent_results);
        }

        function updateRecentResults(results) {
            const container = document.getElementById('recentResults');

            if (!results || results.length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #999;">결과가 없습니다</p>';
                return;
            }

            container.innerHTML = results.map(result => `
                <div class="result-item">
                    <div class="result-keyword">${result.keyword}</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                        <span class="result-count ${result.success ? 'success' : 'failed'}">
                            ${result.success ? '✓' : '✗'} ${result.count}개 결과
                        </span>
                        <span class="result-time">${formatTime(result.timestamp)}</span>
                    </div>
                </div>
            `).join('');
        }

        function addJob(job) {
            const container = document.getElementById('jobsContainer');

            // "진행 중인 작업이 없습니다" 메시지 제거
            if (container.querySelector('p')) {
                container.innerHTML = '';
            }

            // 이미 존재하는 작업인지 확인
            if (document.getElementById(`job-${job.job_id}`)) {
                return;
            }

            const jobElement = document.createElement('div');
            jobElement.id = `job-${job.job_id}`;
            jobElement.className = `job-item ${job.status}`;
            jobElement.innerHTML = `
                <div class="job-header">
                    <span class="job-title">${job.keyword}</span>
                    <span class="job-status ${job.status}">${getStatusText(job.status)}</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${job.progress_percentage}%"></div>
                </div>
                <div class="progress-text">
                    <span>${job.completed}/${job.total_targets} 완료</span>
                    <span>${job.progress_percentage.toFixed(1)}%</span>
                </div>
                <div class="job-details">
                    경과 시간: ${formatElapsedTime(job.elapsed_time)} |
                    실패: ${job.failed}
                </div>
                <div style="margin-top: 10px; text-align: right;">
                    <button class="btn btn-danger" onclick="cancelJob('${job.job_id}')">취소</button>
                </div>
            `;

            container.appendChild(jobElement);
        }

        function updateJobProgress(job) {
            const jobElement = document.getElementById(`job-${job.job_id}`);
            if (!jobElement) {
                addJob(job);
                return;
            }

            jobElement.className = `job-item ${job.status}`;
            jobElement.querySelector('.progress-fill').style.width = `${job.progress_percentage}%`;
            jobElement.querySelector('.progress-text').innerHTML = `
                <span>${job.completed}/${job.total_targets} 완료</span>
                <span>${job.progress_percentage.toFixed(1)}%</span>
            `;
            jobElement.querySelector('.job-details').innerHTML = `
                경과 시간: ${formatElapsedTime(job.elapsed_time)} |
                실패: ${job.failed} |
                현재: ${job.current_target || '처리 중...'}
            `;
            jobElement.querySelector('.job-status').textContent = getStatusText(job.status);
            jobElement.querySelector('.job-status').className = `job-status ${job.status}`;
        }

        function completeJob(job) {
            const jobElement = document.getElementById(`job-${job.job_id}`);
            if (jobElement) {
                jobElement.className = `job-item ${job.status}`;
                jobElement.querySelector('.progress-fill').style.width = '100%';
                jobElement.querySelector('.progress-text').innerHTML = `
                    <span>${job.completed}/${job.total_targets} 완료</span>
                    <span>100%</span>
                `;
                jobElement.querySelector('.job-details').innerHTML = `
                    완료 시간: ${formatTime(job.end_time)} |
                    총 결과: ${job.results_count}개 |
                    성공: ${job.completed} |
                    실패: ${job.failed}
                `;
                jobElement.querySelector('.job-status').textContent = getStatusText(job.status);
                jobElement.querySelector('.job-status').className = `job-status ${job.status}`;

                // 취소 버튼 제거
                const cancelBtn = jobElement.querySelector('.btn-danger');
                if (cancelBtn) {
                    cancelBtn.remove();
                }
            }
        }

        function failJob(job) {
            const jobElement = document.getElementById(`job-${job.job_id}`);
            if (jobElement) {
                jobElement.className = `job-item failed`;
                jobElement.querySelector('.job-status').textContent = '실패';
                jobElement.querySelector('.job-status').className = 'job-status failed';
                jobElement.querySelector('.job-details').innerHTML = `
                    오류: ${job.error_message || '알 수 없는 오류'} |
                    완료: ${job.completed}/${job.total_targets}
                `;

                // 취소 버튼 제거
                const cancelBtn = jobElement.querySelector('.btn-danger');
                if (cancelBtn) {
                    cancelBtn.remove();
                }
            }
        }

        function cancelJob(jobId) {
            if (confirm('이 작업을 취소하시겠습니까?')) {
                socket.emit('cancel_job', { job_id: jobId });
                addLog(`작업 취소 요청: ${jobId}`, 'info');
            }
        }

        function addLog(message, type = 'info') {
            const container = document.getElementById('logContainer');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            entry.innerHTML = `<span class="log-time">[${new Date().toLocaleTimeString()}]</span> ${message}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        // 폼 제출 처리
        document.getElementById('crawlForm').addEventListener('submit', (e) => {
            e.preventDefault();

            const keyword = document.getElementById('keyword').value.trim();
            const maxResults = parseInt(document.getElementById('maxResults').value);
            const searchType = document.getElementById('searchType').value;

            if (!keyword) {
                alert('검색어를 입력해주세요');
                return;
            }

            // 서버에 크롤링 요청
            fetch('/api/crawl/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    keyword: keyword,
                    max_results: maxResults,
                    search_type: searchType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`크롤링 요청 전송: ${keyword}`, 'success');
                    document.getElementById('keyword').value = '';
                } else {
                    addLog(`크롤링 요청 실패: ${data.error}`, 'error');
                    alert('크롤링 시작 실패: ' + data.error);
                }
            })
            .catch(error => {
                addLog(`요청 오류: ${error}`, 'error');
                alert('요청 중 오류가 발생했습니다');
            });
        });

        // 유틸리티 함수들
        function formatTime(timestamp) {
            if (!timestamp) return '-';
            const date = new Date(timestamp);
            return date.toLocaleTimeString();
        }

        function formatElapsedTime(seconds) {
            if (!seconds) return '0초';
            const minutes = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return minutes > 0 ? `${minutes}분 ${secs}초` : `${secs}초`;
        }

        function getStatusText(status) {
            const statusMap = {
                'running': '진행 중',
                'completed': '완료',
                'failed': '실패'
            };
            return statusMap[status] || status;
        }

        // 주기적 통계 요청 (1분마다)
        setInterval(() => {
            if (socket.connected) {
                socket.emit('request_stats');
            }
        }, 60000);
    </script>
</body>
</html>'''

    # 템플릿 저장
    dashboard_path = templates_dir / 'dashboard.html'
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dashboard_template)

    logger.info(f"대시보드 템플릿 생성 완료: {dashboard_path}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📊 DealBot 실시간 모니터링 대시보드 시작")
    print("=" * 60)

    # 템플릿 생성
    create_templates()

    # 서버 정보 출력
    print("\n✅ 템플릿 생성 완료")
    print("🚀 WebSocket 서버 시작 중...")
    print(f"📱 대시보드 주소: http://localhost:5000")
    print(f"📋 헬스체크: http://localhost:5000/health")
    print("\n🌐 WebSocket 기능:")
    print("   - 실시간 크롤링 진행률 표시")
    print("   - 라이브 통계 업데이트")
    print("   - 실시간 로그 및 알림")
    print("   - 작업 제어 (시작/취소)")

    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 60 + "\n")

    # SocketIO 서버 시작
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()