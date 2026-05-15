# 📊 DealBot 실시간 모니터링 대시보드 (향상된 버전)

WebSocket 기반 실시간 데이터 업데이트, 라이브 크롤링 진행률 표시, 키워드 트렌드 차트, 시스템 리소스 모니터링

## 🚀 주요 기능

### 1. 실시간 크롤링 진행률 표시
- WebSocket을 통한 실시간 진행률 업데이트
- 시각적 프로그레스 바 표시
- 현재 처리 중인 아이템 표시
- 경과 시간 및 남은 시간 예상

### 2. 라이브 통계 대시보드
- 총 크롤링 횟수
- 성공률 실시간 계산
- 진행 중인 작업 수
- 최근 성공 횟수
- 크롤링 소스별 통계

### 3. 📈 키워드 등장 차트
- 실시간 키워드 빈도 추적
- 인기 키워드 TOP 10 표시
- 키워드 검색 트렌드 이력
- Chart.js를 활용한 시각화
- 누적 검색 횟수 라인 차트

### 4. 💻 시스템 리소스 모니터링
- **CPU 사용량**: 코어별 및 전체 사용량 모니터링
- **메모리 사용량**: 사용량, 전체 용량, 사용 가능량
- **디스크 사용량**: 사용량, 전체 용량, 여유 공간
- **네트워크 사용량**: 전송/수신 데이터량
- **프로세스 수**: 현재 실행 중인 프로세스 수
- **실시간 차트**: CPU, 메모리, 디스크 사용량 추이

### 5. 작업 제어
- 실시간 작업 시작
- 작업 취소 기능
- 작업 상태 모니터링 (진행 중, 완료, 실패)
- 여러 작업 동시 실행 지원

### 6. 실시간 로그 및 알림
- 시스템 로그 실시간 표시
- 작업 시작/완료/실패 알림
- 컬러 코딩된 로그 메시지
- 탭 기반 UI로 정리된 정보 표시

## 📦 설치

```bash
pip install -r requirements.txt
```

### 추가 의존성
- flask-socketio: WebSocket 지원
- eventlet: 비동기 처리
- psutil: 시스템 리소스 모니터링
- Chart.js: 차트 시각화 (CDN)

## 🚀 사용법

### 1. 기본 실행 (표준 버전)

```bash
python realtime_dashboard.py
```

또는:

```bash
python realtime_dashboard_example.py
```

### 2. 향상된 버전 실행 (키워드 차트 + 리소스 모니터링)

```bash
python enhanced_realtime_dashboard.py
```

또는:

```bash
python enhanced_dashboard_example.py
```

### 3. 대시보드 접속

웹 브라우저에서 다음 주소로 접속:

```
http://localhost:5000
```

### 3. 크롤링 시작

1. 검색어 입력
2. 최대 결과 수 설정 (1-100)
3. 검색 유형 선택:
   - 네이버 블로그
   - 구글
   - 다중 검색
4. "크롤링 시작" 버튼 클릭

### 4. 대시보드 탭 사용

향상된 버전에서는 4개의 탭을 제공합니다:

#### 🚀 크롤링 탭
- 크롤링 제어
- 실시간 작업 진행률
- 최근 크롤링 결과

#### 📈 키워드 트렌드 탭
- 키워드 등장 빈도 차트
- 인기 키워드 TOP 10
- 키워드 트렌드 이력 차트

#### 💻 시스템 리소스 탭
- CPU, 메모리, 디스크 사용량
- 실시간 리소스 모니터링 차트
- 상세 리소스 정보

#### 📝 로그 탭
- 시스템 로그
- 작업 로그
- 컬러 코딩된 메시지

## 🌐 WebSocket 이벤트

### 클라이언트 → 서버

| 이벤트 | 설명 | 데이터 |
|--------|------|--------|
| `connect` | 연결 요청 | - |
| `disconnect` | 연결 해제 | - |
| `join_monitoring` | 모니터링 룸 참여 | - |
| `leave_monitoring` | 모니터링 룸 퇴장 | - |
| `request_stats` | 통계 요청 | - |
| `request_active_jobs` | 진행 중인 작업 요청 | - |
| `request_resource_history` | 리소스 이력 요청 | - |
| `cancel_job` | 작업 취소 | `{job_id: string}` |

### 서버 → 클라이언트

| 이벤트 | 설명 | 데이터 |
|--------|------|--------|
| `connected` | 연결 확인 | `{message, timestamp}` |
| `joined_monitoring` | 모니터링 룸 참여 완료 | `{message, room}` |
| `stats_update` | 통계 업데이트 | `Stats` 객체 |
| `job_started` | 작업 시작 | `JobProgress` 객체 |
| `job_progress` | 작업 진행률 업데이트 | `JobProgress` 객체 |
| `job_completed` | 작업 완료 | `JobProgress` 객체 |
| `job_failed` | 작업 실패 | `JobProgress` 객체 |
| `job_cancelled` | 작업 취소 | `JobProgress` 객체 |
| `active_jobs` | 진행 중인 작업 목록 | `JobProgress[]` |
| `resource_update` | 시스템 리소스 업데이트 | `ResourceData` 객체 |
| `resource_history` | 리소스 이력 업데이트 | `{history, count}` |

## 📊 데이터 구조

### Stats 객체
```javascript
{
  last_update: string,           // 마지막 업데이트 시간
  total_crawls: number,          // 총 크롤링 횟수
  successful_crawls: number,     // 성공한 크롤링 횟수
  failed_crawls: number,         // 실패한 크롤링 횟수
  active_jobs: number,           // 진행 중인 작업 수
  success_rate: number,          // 성공률 (%)
  recent_results: Array,         // 최근 결과 목록
  crawling_sources: {            // 소스별 통계
    naver: { count, last_used },
    google: { count, last_used },
    multiple: { count, last_used }
  },
  keyword_frequency: Object,     // 키워드 빈도 {keyword: count}
  keyword_trends: Array          // 키워드 트렌드 이력
}
```

### ResourceData 객체 (시스템 리소스)
```javascript
{
  timestamp: string,
  cpu: {
    percent: number,             // 전체 CPU 사용율 (%)
    per_core: Array<number>,     // 코어별 사용율
    core_count: number           // CPU 코어 수
  },
  memory: {
    percent: number,             // 메모리 사용율 (%)
    used_gb: number,             // 사용량 (GB)
    total_gb: number,            // 전체 용량 (GB)
    available_gb: number         // 사용 가능량 (GB)
  },
  disk: {
    percent: number,             // 디스크 사용율 (%)
    used_gb: number,             // 사용량 (GB)
    total_gb: number,            // 전체 용량 (GB)
    free_gb: number              // 여유 공간 (GB)
  },
  network: {
    sent_mb: number,             // 전송 데이터량 (MB)
    recv_mb: number              // 수신 데이터량 (MB)
  },
  process: {
    count: number                // 프로세스 수
  },
  load_avg: Array<number>        // 시스템 부하 평균
}
```

### JobProgress 객체
```javascript
{
  job_id: string,                // 작업 ID
  keyword: string,               // 검색어
  total_targets: number,         // 총 대상 수
  completed: number,             // 완료된 수
  failed: number,                // 실패한 수
  progress_percentage: number,   // 진행률 (%)
  status: string,                // 상태 (running, completed, failed)
  current_target: string,        // 현재 처리 중인 대상
  start_time: string,            // 시작 시간
  end_time: string,              // 종료 시간
  error_message: string,         // 오류 메시지
  elapsed_time: number,          // 경과 시간 (초)
  results_count: number          // 결과 수
}
```

## 🔧 API 엔드포인트

### HTTP 엔드포인트

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/` | GET | 대시보드 메인 페이지 |
| `/monitoring` | GET | 모니터링 페이지 |
| `/health` | GET | 헬스체크 |
| `/api/crawl/start` | POST | 크롤링 시작 |
| `/api/jobs` | GET | 모든 작업 목록 조회 |
| `/api/jobs/<job_id>` | GET | 특정 작업 조회 |
| `/api/stats` | GET | 통계 정보 조회 |
| `/api/resources` | GET | 시스템 리소스 정보 조회 |
| `/api/resources/history` | GET | 리소스 이력 조회 |

### 크롤링 시작 API

```bash
POST /api/crawl/start
Content-Type: application/json

{
  "keyword": "검색어",
  "max_results": 20,
  "search_type": "naver"
}
```

응답:
```json
{
  "success": true,
  "job_id": "job_20240515_123456",
  "message": "크롤링이 시작되었습니다"
}
```

## 🎨 UI 기능

### 대시보드 레이아웃

#### 통계 카드 (상단)
- 총 크롤링 횟수
- 성공률
- 진행 중인 작업 수
- 최근 성공 횟수
- 연결 상태 표시

#### 탭 기반 UI

**1. 🚀 크롤링 탭**
- 크롤링 제어 폼
- 실시간 작업 진행률
- 최근 크롤링 결과

**2. 📈 키워드 트렌드 탭**
- 키워드 빈도 막대 차트
- 인기 키워드 TOP 10 목록
- 키워드 트렌드 라인 차트

**3. 💻 시스템 리소스 탭**
- CPU 사용량 및 코어 정보
- 메모리 사용량 상세 정보
- 디스크 사용량 상세 정보
- 네트워크 사용량
- 프로세스 수
- 실시간 리소스 모니터링 라인 차트

**4. 📝 로그 탭**
- 시스템 로그
- 작업 로그
- 오류 로그
- 컬러 코딩된 메시지

## 📝 진행률 콜백 구현

크롤러에서 진행률 콜백 함수를 사용하여 실시간 업데이트:

```python
def progress_callback(completed: int, total: int, current_target: str = None) -> bool:
    """
    진행률 콜백 함수

    Args:
        completed: 완료된 항목 수
        total: 총 항목 수
        current_target: 현재 처리 중인 항목

    Returns:
        bool: 계속 진행하면 True, 중단하면 False
    """
    # WebSocket을 통해 진행률 전송
    socketio.emit('job_progress', {
        'completed': completed,
        'total': total,
        'current_target': current_target
    })

    return True  # 계속 진행

# 크롤러에서 사용
results = crawler.search_naver_blog(
    keyword="검색어",
    max_results=20,
    progress_callback=progress_callback
)
```

## 🔍 모니터링 기능

### 연결 상태 모니터링
- WebSocket 연결 상태 표시
- 연결/해제 알림
- 자동 재연결 (브라우저 지원)

### 실시간 통계
- 1분마다 자동 통계 갱신
- 수동 통계 요청 지원
- 이력 데이터 유지
- 키워드 빈도 실시간 추적

### 시스템 리소스 모니터링 (향상된 버전)
- 2초마다 자동 리소스 업데이트
- CPU, 메모리, 디스크, 네트워크 실시간 모니터링
- 리소스 사용량 이력 유지 (최근 60개 포인트)
- 경고 색상 표시 (녹색: <50%, 노란색: 50-80%, 빨간색: >80%)
- 실시간 차트 업데이트

### 키워드 트렌드 분석 (향상된 버전)
- 검색 키워드 빈도 자동 추적
- 인기 키워드 TOP 10 실시간 표시
- 키워드 검색 트렌드 이력
- 누적 검색 횟수 시각화

### 작업 관리
- 다중 작업 동시 실행
- 작업별 진행률 추적
- 작업 취소 지원
- 완료/실패 상태 관리
- 작업 진행률 이력

## 🧪 테스트

### 표준 버전 테스트
```bash
python test_realtime_dashboard.py
```

### 향상된 버전 테스트
```bash
python test_enhanced_dashboard.py
```

### 테스트 항목
- 서버 헬스체크
- 시스템 리소스 조회
- 리소스 이력 조회
- 크롤링 시작
- 통계 및 키워드 트렌드
- 다중 크롤링 시나리오
- 리소스 모니터링 동작

## 🐛 문제 해결

### 연결 문제
- 방화벽 확인 (포트 5000)
- WebSocket 지원 브라우저 사용
- 네트워크 연결 상태 확인

### 크롤링 오류
- 검색어 유효성 확인
- 최대 결과 수 범위 확인 (1-100)
- 인터넷 연결 상태 확인

### 진행률 업데이트 안 됨
- WebSocket 연결 상태 확인
- 브라우저 콘솔 오류 확인
- 서버 로그 확인

### 시스템 리소스 모니터링 문제
- psutil 패키지 설치 확인: `pip install psutil`
- 운영체제 호환성 확인
- 권한 문제 확인 (리소스 접근 권한)

### 차트 표시 문제
- Chart.js CDN 연결 확인
- 브라우저 콘솔 오류 확인
- 인터넷 연결 상태 확인

## 📈 성능 최적화

### 클라이언트
- 주기적 업데이트 간격 조정
- 불필요한 DOM 업데이트 방지
- 결과 캐싱 활용

### 서버
- 이벤트 루프 최적화
- 메모리 사용량 모니터링
- 작업 크기 제한

## 🚧 향후 개발

- [ ] 사용자 인증 및 권한 관리
- [ ] 크롤링 스케줄링 기능
- [ ] 결과 내보내기 기능 (CSV, Excel)
- [ ] 고급 차트 및 그래프 시각화
- [ ] 알림 설정 (이메일, Slack 등)
- [ ] 크롤링 히스토리 관리
- [ ] 필터링 및 검색 기능 강화
- [ ] 더 많은 시스템 메트릭 (GPU, 온도 등)
- [ ] 분석 리포트 자동 생성
- [ ] 키워드 관련도 분석

## 📊 버전 비교

### 표준 버전 (realtime_dashboard.py)
- ✅ 실시간 크롤링 진행률
- ✅ 라이브 통계 업데이트
- ✅ 작업 제어 기능
- ✅ 실시간 로그

### 향상된 버전 (enhanced_realtime_dashboard.py)
- ✅ 표준 버전의 모든 기능
- ✅ 키워드 등장 빈도 차트
- ✅ 인기 키워드 TOP 10
- ✅ 키워드 트렌드 이력 분석
- ✅ 시스템 리소스 모니터링
- ✅ CPU, 메모리, 디스크, 네트워크 차트
- ✅ 탭 기반 UI
- ✅ 상세 리소스 정보

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

## 🤝 기여

버그 리포트, 기능 요청, 코드 기여를 환영합니다!

---

**WebSocket 기반 실시간 모니터링으로 크롤링 작업을 효율적으로 관리하세요! 🚀**