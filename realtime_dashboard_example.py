#!/usr/bin/env python3
"""
실시간 대시보드 사용 예시
WebSocket 기반 라이브 크롤링 모니터링
"""

from realtime_dashboard import app, socketio

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 DealBot 실시간 모니터링 대시보드 시작")
    print("=" * 60)
    print("\n📱 접속 주소: http://localhost:5000")
    print("🌐 WebSocket이 활성화되어 실시간 업데이트를 지원합니다")
    print("\n🎯 주요 기능:")
    print("   - 실시간 크롤링 진행률 표시")
    print("   - 라이브 통계 업데이트")
    print("   - 작업 제어 (시작/취소)")
    print("   - 실시간 로그 및 알림")
    print("\n⌨️  종료하려면 Ctrl+C를 누르세요")
    print("=" * 60 + "\n")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True)