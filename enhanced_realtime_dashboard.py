#!/usr/bin/env python3
"""
WebSocket 기반 실시간 모니터링 대시보드 (향상된 버전)
DealBot 크롤러 진행률 실시간 표시 + 키워드 트렌드 차트 + 시스템 리소스 모니터링
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import deque, Counter
import json
import psutil
import random

# 기존 크롤러 임포트
from web_crawler import WebCrawler, Config, setup_logging
from sentiment_analyzer import SentimentAnalyzer, SentimentFilter

# Flask 앱 설정
app = Flask(__name__)
app.secret_key = 'dealbot-websocket-secret-key-enhanced'

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

# ============================================================================
# 실시간 통계 관리
# ============================================================================

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
        # 키워드 빈도 추적
        self.keyword_frequency = Counter()
        self.keyword_trends = deque(maxlen=20)  # 최근 20개 키워드 트렌드

    def update_stats(self, success: bool, search_type: str, keyword: str = None):
        self.last_update = datetime.now()
        self.total_crawls += 1
        if success:
            self.successful_crawls += 1
        else:
            self.failed_crawls += 1

        if search_type in self.crawling_sources:
            self.crawling_sources[search_type]['count'] += 1
            self.crawling_sources[search_type]['last_used'] = datetime.now().isoformat()

        # 키워드 빈도 업데이트
        if keyword:
            self.keyword_frequency[keyword] += 1
            self.keyword_trends.append({
                'keyword': keyword,
                'timestamp': datetime.now().isoformat(),
                'count': self.keyword_frequency[keyword]
            })

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
            'crawling_sources': self.crawling_sources,
            'keyword_frequency': dict(self.keyword_frequency.most_common(10)),
            'keyword_trends': list(self.keyword_trends)
        }

stats = RealTimeStats()

# ============================================================================
# 시스템 리소스 모니터링
# ============================================================================

class SystemMonitor:
    def __init__(self):
        self.monitoring_active = False
        self.monitor_thread = None
        self.update_interval = 2.0  # 2초마다 업데이트
        self.resource_history = deque(maxlen=60)  # 최근 60개 데이터 포인트 (2분)

    def get_current_resources(self):
        """현재 시스템 리소스 상태 조회"""
        try:
            # CPU 사용량
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # 메모리 사용량
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)

            # 디스크 사용량
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)

            # 네트워크 사용량
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024**2)
            network_recv_mb = network.bytes_recv / (1024**2)

            # 프로세스 수
            process_count = len(psutil.pids())

            # 시스템 부하 (Windows용 대안)
            try:
                load_avg = [0, 0, 0]  # Windows에서는 지원하지 않음
            except:
                load_avg = [0, 0, 0]

            resource_data = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'per_core': cpu_per_core,
                    'core_count': psutil.cpu_count()
                },
                'memory': {
                    'percent': memory_percent,
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2),
                    'available_gb': round(memory.available / (1024**3), 2)
                },
                'disk': {
                    'percent': disk_percent,
                    'used_gb': round(disk_used_gb, 2),
                    'total_gb': round(disk_total_gb, 2),
                    'free_gb': round(disk.free / (1024**3), 2)
                },
                'network': {
                    'sent_mb': round(network_sent_mb, 2),
                    'recv_mb': round(network_recv_mb, 2)
                },
                'process': {
                    'count': process_count
                },
                'load_avg': load_avg
            }

            return resource_data

        except Exception as e:
            logger.error(f"시스템 리소스 조회 오류: {e}")
            return None

    def start_monitoring(self):
        """시스템 리소스 모니터링 시작"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("시스템 리소스 모니터링 시작")

    def stop_monitoring(self):
        """시스템 리소스 모니터링 중지"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("시스템 리소스 모니터링 중지")

    def _monitor_loop(self):
        """모니터링 루프"""
        while self.monitoring_active:
            try:
                resource_data = self.get_current_resources()
                if resource_data:
                    self.resource_history.append(resource_data)

                    # WebSocket을 통해 실시간 업데이트 전송
                    socketio.emit('resource_update', resource_data, room='monitoring')

                    # 이력 데이터 전송 (주기적으로)
                    if len(self.resource_history) % 10 == 0:  # 20초마다
                        socketio.emit('resource_history', {
                            'history': list(self.resource_history),
                            'count': len(self.resource_history)
                        }, room='monitoring')

                time.sleep(self.update_interval)

            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(self.update_interval)

    def get_history(self):
        """리소스 이력 조회"""
        return list(self.resource_history)

    def get_summary(self):
        """리소스 요약 정보 조회"""
        if not self.resource_history:
            return None

        latest = self.resource_history[-1]
        return {
            'current': latest,
            'history_count': len(self.resource_history),
            'monitoring_active': self.monitoring_active
        }

# 시스템 모니터 인스턴스
system_monitor = SystemMonitor()

# ============================================================================
# 크롤링 진행 상태 관리
# ============================================================================

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
        self.progress_history = []  # 진행률 이력

    def update_progress(self, completed: int, failed: int = 0, current_target: str = None):
        self.completed = completed
        self.failed = failed
        self.current_target = current_target
        self.progress_percentage = (completed / self.total_targets * 100) if self.total_targets > 0 else 100

        # 진행률 이력 저장
        self.progress_history.append({
            'timestamp': datetime.now().isoformat(),
            'completed': completed,
            'failed': failed,
            'percentage': self.progress_percentage
        })

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
            'results_count': len(self.results),
            'progress_history': self.progress_history[-10:]  # 최근 10개만 반환
        }

def generate_job_id():
    """고유한 작업 ID 생성"""
    return f"job_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

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

    # 시스템 리소스 정보 전송
    resource_summary = system_monitor.get_summary()
    if resource_summary:
        emit('resource_update', resource_summary['current'])

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

    # 시스템 모니터링 시작 (첫 연결 시)
    if not system_monitor.monitoring_active:
        system_monitor.start_monitoring()

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

@socketio.on('request_resource_history')
def handle_request_resource_history():
    """리소스 이력 요청"""
    history = system_monitor.get_history()
    emit('resource_history', {
        'history': history,
        'count': len(history)
    })

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
    """메인 페이지 - 향상된 대시보드"""
    return render_template('enhanced_dashboard.html')

@app.route('/monitoring')
def monitoring():
    """모니터링 페이지"""
    return render_template('enhanced_dashboard.html')

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
            results = crawler.search_google_news(keyword, max_results=max_results,
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
        stats.update_stats(successful_count > 0, search_type, keyword)
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

@app.route('/api/resources')
def get_resources():
    """시스템 리소스 정보 조회"""
    resource_summary = system_monitor.get_summary()
    return jsonify({
        'success': True,
        'resources': resource_summary
    })

@app.route('/api/resources/history')
def get_resource_history():
    """리소스 이력 조회"""
    history = system_monitor.get_history()
    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })

@app.route('/health')
def health_check():
    """헬스체크"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'DealBot Enhanced Real-time Monitor'
    })

# ============================================================================
# HTML 템플릿 생성
# ============================================================================

def create_enhanced_templates():
    """향상된 HTML 템플릿 생성"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    # 향상된 대시보드 템플릿
    enhanced_dashboard_template = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 DealBot 향상된 실시간 모니터링</title>
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
            max-width: 1600px;
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

        .resource-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .resource-item:last-child {
            border-bottom: none;
        }

        .resource-label {
            font-weight: 600;
            color: #333;
        }

        .resource-value {
            font-weight: bold;
            color: #667eea;
        }

        .resource-bar-container {
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 5px;
        }

        .resource-bar {
            height: 100%;
            transition: width 0.5s ease;
            border-radius: 10px;
        }

        .resource-bar.low { background: #28a745; }
        .resource-bar.medium { background: #ffc107; }
        .resource-bar.high { background: #dc3545; }

        .chart-container {
            height: 300px;
            margin-bottom: 20px;
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

        .keyword-item {
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 5px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .keyword-name {
            font-weight: 600;
            color: #333;
        }

        .keyword-count {
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: bold;
        }

        .tab-container {
            margin-bottom: 20px;
        }

        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .tab {
            padding: 10px 20px;
            background: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            color: #666;
            transition: all 0.3s;
        }

        .tab.active {
            background: #667eea;
            color: white;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 DealBot 향상된 실시간 모니터링</h1>
            <p>WebSocket 기반 라이브 크롤링 대시보드 + 키워드 트렌드 + 시스템 리소스 모니터링</p>
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

        <!-- 탭 컨테이너 -->
        <div class="tab-container">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('crawling')">🚀 크롤링</button>
                <button class="tab" onclick="switchTab('keywords')">📈 키워드 트렌드</button>
                <button class="tab" onclick="switchTab('resources')">💻 시스템 리소스</button>
                <button class="tab" onclick="switchTab('logs')">📝 로그</button>
            </div>

            <!-- 크롤링 탭 -->
            <div id="crawlingTab" class="tab-content active">
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

                <div class="grid">
                    <div class="card">
                        <h3>📈 최근 크롤링 결과</h3>
                        <div class="recent-results" id="recentResults">
                            <p style="text-align: center; color: #999;">결과가 없습니다</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 키워드 트렌드 탭 -->
            <div id="keywordsTab" class="tab-content">
                <div class="grid">
                    <div class="card">
                        <h3>📈 키워드 등장 차트</h3>
                        <div class="chart-container">
                            <canvas id="keywordChart"></canvas>
                        </div>
                    </div>
                    <div class="card">
                        <h3>🔥 인기 키워드 TOP 10</h3>
                        <div id="keywordList">
                            <p style="text-align: center; color: #999;">키워드 데이터가 없습니다</p>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h3>📊 키워드 트렌드 이력</h3>
                    <div class="chart-container">
                        <canvas id="keywordTrendChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- 시스템 리소스 탭 -->
            <div id="resourcesTab" class="tab-content">
                <div class="grid">
                    <div class="card">
                        <h3>💻 시스템 리소스 상태</h3>
                        <div class="resource-item">
                            <span class="resource-label">CPU 사용량</span>
                            <span class="resource-value" id="cpuValue">0%</span>
                        </div>
                        <div class="resource-bar-container">
                            <div class="resource-bar" id="cpuBar" style="width: 0%"></div>
                        </div>

                        <div class="resource-item" style="margin-top: 15px;">
                            <span class="resource-label">메모리 사용량</span>
                            <span class="resource-value" id="memoryValue">0%</span>
                        </div>
                        <div class="resource-bar-container">
                            <div class="resource-bar" id="memoryBar" style="width: 0%"></div>
                        </div>

                        <div class="resource-item" style="margin-top: 15px;">
                            <span class="resource-label">디스크 사용량</span>
                            <span class="resource-value" id="diskValue">0%</span>
                        </div>
                        <div class="resource-bar-container">
                            <div class="resource-bar" id="diskBar" style="width: 0%"></div>
                        </div>

                        <div class="resource-item" style="margin-top: 15px;">
                            <span class="resource-label">프로세스 수</span>
                            <span class="resource-value" id="processValue">0</span>
                        </div>
                    </div>

                    <div class="card">
                        <h3>📊 리소스 상세 정보</h3>
                        <div class="resource-item">
                            <span class="resource-label">CPU 코어 수</span>
                            <span class="resource-value" id="cpuCores">-</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">메모리 사용량</span>
                            <span class="resource-value" id="memoryUsed">0 GB</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">메모리 전체</span>
                            <span class="resource-value" id="memoryTotal">0 GB</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">디스크 사용량</span>
                            <span class="resource-value" id="diskUsed">0 GB</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">디스크 전체</span>
                            <span class="resource-value" id="diskTotal">0 GB</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">네트워크 전송</span>
                            <span class="resource-value" id="networkSent">0 MB</span>
                        </div>
                        <div class="resource-item">
                            <span class="resource-label">네트워크 수신</span>
                            <span class="resource-value" id="networkRecv">0 MB</span>
                        </div>
                    </div>
                </div>

                <div class="card">
                    <h3>📈 실시간 리소스 모니터링</h3>
                    <div class="chart-container">
                        <canvas id="resourceChart"></canvas>
                    </div>
                </div>
            </div>

            <!-- 로그 탭 -->
            <div id="logsTab" class="tab-content">
                <div class="card">
                    <h3>📝 실시간 로그</h3>
                    <div class="log-container" id="logContainer">
                        <div class="log-entry">
                            <span class="log-time">[시스템]</span>
                            향상된 대시보드가 초기화되었습니다
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Socket.io 클라이언트 설정
        const socket = io();

        // 차트 변수
        let keywordChart = null;
        let keywordTrendChart = null;
        let resourceChart = null;
        let resourceHistoryData = {
            labels: [],
            cpu: [],
            memory: [],
            disk: []
        };

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
            updateKeywordCharts(data);
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

        // 리소스 업데이트
        socket.on('resource_update', (data) => {
            updateResources(data);
        });

        // 리소스 이력 업데이트
        socket.on('resource_history', (data) => {
            updateResourceHistory(data.history);
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

        function updateResources(data) {
            if (!data) return;

            // CPU
            const cpuPercent = data.cpu.percent;
            document.getElementById('cpuValue').textContent = cpuPercent.toFixed(1) + '%';
            document.getElementById('cpuBar').style.width = cpuPercent + '%';
            updateResourceBarColor('cpuBar', cpuPercent);
            document.getElementById('cpuCores').textContent = data.cpu.core_count;

            // 메모리
            const memoryPercent = data.memory.percent;
            document.getElementById('memoryValue').textContent = memoryPercent.toFixed(1) + '%';
            document.getElementById('memoryBar').style.width = memoryPercent + '%';
            updateResourceBarColor('memoryBar', memoryPercent);
            document.getElementById('memoryUsed').textContent = data.memory.used_gb + ' GB';
            document.getElementById('memoryTotal').textContent = data.memory.total_gb + ' GB';

            // 디스크
            const diskPercent = data.disk.percent;
            document.getElementById('diskValue').textContent = diskPercent.toFixed(1) + '%';
            document.getElementById('diskBar').style.width = diskPercent + '%';
            updateResourceBarColor('diskBar', diskPercent);
            document.getElementById('diskUsed').textContent = data.disk.used_gb + ' GB';
            document.getElementById('diskTotal').textContent = data.disk.total_gb + ' GB';

            // 프로세스
            document.getElementById('processValue').textContent = data.process.count;

            // 네트워크
            document.getElementById('networkSent').textContent = data.network.sent_mb + ' MB';
            document.getElementById('networkRecv').textContent = data.network.recv_mb + ' MB';

            // 차트 데이터 업데이트
            updateResourceChartData(data);
        }

        function updateResourceBarColor(barId, percent) {
            const bar = document.getElementById(barId);
            bar.classList.remove('low', 'medium', 'high');

            if (percent < 50) {
                bar.classList.add('low');
            } else if (percent < 80) {
                bar.classList.add('medium');
            } else {
                bar.classList.add('high');
            }
        }

        function updateResourceChartData(data) {
            const now = new Date();
            const timeLabel = now.toLocaleTimeString();

            resourceHistoryData.labels.push(timeLabel);
            resourceHistoryData.cpu.push(data.cpu.percent);
            resourceHistoryData.memory.push(data.memory.percent);
            resourceHistoryData.disk.push(data.disk.percent);

            // 최근 30개 데이터만 유지
            if (resourceHistoryData.labels.length > 30) {
                resourceHistoryData.labels.shift();
                resourceHistoryData.cpu.shift();
                resourceHistoryData.memory.shift();
                resourceHistoryData.disk.shift();
            }

            updateResourceChart();
        }

        function updateKeywordCharts(stats) {
            // 키워드 빈도 차트 업데이트
            updateKeywordFrequencyChart(stats.keyword_frequency);

            // 키워드 트렌드 차트 업데이트
            updateKeywordTrendChart(stats.keyword_trends);

            // 키워드 목록 업데이트
            updateKeywordList(stats.keyword_frequency);
        }

        function updateKeywordFrequencyChart(keywordFrequency) {
            if (!keywordFrequency || Object.keys(keywordFrequency).length === 0) return;

            const keywords = Object.keys(keywordFrequency);
            const counts = Object.values(keywordFrequency);

            if (keywordChart) {
                keywordChart.data.labels = keywords;
                keywordChart.data.datasets[0].data = counts;
                keywordChart.update();
            } else {
                const ctx = document.getElementById('keywordChart').getContext('2d');
                keywordChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: keywords,
                        datasets: [{
                            label: '검색 횟수',
                            data: counts,
                            backgroundColor: 'rgba(102, 126, 234, 0.6)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
            }
        }

        function updateKeywordTrendChart(keywordTrends) {
            if (!keywordTrends || keywordTrends.length === 0) return;

            const labels = keywordTrends.map(t => formatTime(t.timestamp));
            const counts = keywordTrends.map(t => t.count);

            if (keywordTrendChart) {
                keywordTrendChart.data.labels = labels;
                keywordTrendChart.data.datasets[0].data = counts;
                keywordTrendChart.update();
            } else {
                const ctx = document.getElementById('keywordTrendChart').getContext('2d');
                keywordTrendChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: '누적 검색 횟수',
                            data: counts,
                            borderColor: 'rgba(102, 126, 234, 1)',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    stepSize: 1
                                }
                            }
                        }
                    }
                });
            }
        }

        function updateKeywordList(keywordFrequency) {
            const container = document.getElementById('keywordList');

            if (!keywordFrequency || Object.keys(keywordFrequency).length === 0) {
                container.innerHTML = '<p style="text-align: center; color: #999;">키워드 데이터가 없습니다</p>';
                return;
            }

            const sortedKeywords = Object.entries(keywordFrequency)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);

            container.innerHTML = sortedKeywords.map(([keyword, count]) => `
                <div class="keyword-item">
                    <span class="keyword-name">${keyword}</span>
                    <span class="keyword-count">${count}회</span>
                </div>
            `).join('');
        }

        function updateResourceChart() {
            if (resourceChart) {
                resourceChart.data.labels = resourceHistoryData.labels;
                resourceChart.data.datasets[0].data = resourceHistoryData.cpu;
                resourceChart.data.datasets[1].data = resourceHistoryData.memory;
                resourceChart.data.datasets[2].data = resourceHistoryData.disk;
                resourceChart.update();
            } else {
                const ctx = document.getElementById('resourceChart').getContext('2d');
                resourceChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: resourceHistoryData.labels,
                        datasets: [
                            {
                                label: 'CPU (%)',
                                data: resourceHistoryData.cpu,
                                borderColor: 'rgba(255, 99, 132, 1)',
                                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                                fill: false
                            },
                            {
                                label: 'Memory (%)',
                                data: resourceHistoryData.memory,
                                borderColor: 'rgba(54, 162, 235, 1)',
                                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                                fill: false
                            },
                            {
                                label: 'Disk (%)',
                                data: resourceHistoryData.disk,
                                borderColor: 'rgba(75, 192, 192, 1)',
                                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }
        }

        function updateResourceHistory(history) {
            if (!history || history.length === 0) return;

            resourceHistoryData.labels = [];
            resourceHistoryData.cpu = [];
            resourceHistoryData.memory = [];
            resourceHistoryData.disk = [];

            history.forEach(data => {
                const time = new Date(data.timestamp).toLocaleTimeString();
                resourceHistoryData.labels.push(time);
                resourceHistoryData.cpu.push(data.cpu.percent);
                resourceHistoryData.memory.push(data.memory.percent);
                resourceHistoryData.disk.push(data.disk.percent);
            });

            updateResourceChart();
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

        // 탭 전환 함수
        function switchTab(tabName) {
            // 모든 탭과 컨텐츠 숨기기
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // 선택한 탭과 컨텐츠 표시
            document.querySelectorAll(`.tab[onclick="switchTab('${tabName}')"]`).forEach(tab => tab.classList.add('active'));
            document.getElementById(`${tabName}Tab`).classList.add('active');
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

        // 페이지 로드 시 리소스 이력 요청
        setTimeout(() => {
            if (socket.connected) {
                socket.emit('request_resource_history');
            }
        }, 1000);
    </script>
</body>
</html>'''

    # 템플릿 저장
    enhanced_dashboard_path = templates_dir / 'enhanced_dashboard.html'
    with open(enhanced_dashboard_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_dashboard_template)

    logger.info(f"향상된 대시보드 템플릿 생성 완료: {enhanced_dashboard_path}")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("📊 DealBot 향상된 실시간 모니터링 대시보드 시작")
    print("=" * 60)

    # 템플릿 생성
    create_enhanced_templates()

    # 서버 정보 출력
    print("\n✅ 템플릿 생성 완료")
    print("🚀 WebSocket 서버 시작 중...")
    print(f"📱 대시보드 주소: http://localhost:5000")
    print(f"📋 헬스체크: http://localhost:5000/health")
    print("\n🌐 향상된 WebSocket 기능:")
    print("   - 실시간 크롤링 진행률 표시")
    print("   - 라이브 통계 업데이트")
    print("   - 실시간 로그 및 알림")
    print("   - 작업 제어 (시작/취소)")
    print("   - 🎨 키워드 등장 차트")
    print("   - 📈 키워드 트렌드 분석")
    print("   - 💻 시스템 리소스 모니터링")
    print("   - 📊 CPU, 메모리, 디스크, 네트워크 실시간 모니터링")
    print("   - 🔄 리소스 사용량 이력 차트")

    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 60 + "\n")

    # SocketIO 서버 시작
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main()