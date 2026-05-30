# 자동 리포트 생성 및 PDF 출력 시스템 사용 가이드

## 개요

DealBot 자동 리포트 생성 및 PDF 출력 시스템은 정기적인 리포트 자동 생성과 HTML 템플릿 기반의 PDF 변환 기능을 제공합니다.

## 주요 기능

### 1. 다양한 리포트 타입 지원
- **일일 요약 리포트**: 당일 데이터 기반의 빠른 분석
- **주간 분석 리포트**: 주간 트렌드와 성장 지표 분석
- **월간 개요 리포트**: 월간 포괄적 분석과 연간 비교
- **사용자 정의 리포트**: 맞춤형 요구사항에 맞는 리포트 생성

### 2. HTML 템플릿 기반 PDF 변환
- WeasyPrint를 활용한 고품질 PDF 생성
- 한글 완벽 지원
- 반응형 디자인과 인쇄 최적화

### 3. 정기 스케줄링
- APScheduler 기반의 유연한 스케줄링
- 크론 표현식 지원
- 실시간 작업 모니터링 및 제어

### 4. 이메일 알림 통합
- 리포트 생성 완료 시 자동 알림
- PDF 파일 첨부 지원
- 오류 발생 시 알림 기능

## 설치

### 필수 의존성 설치

```bash
pip install weasyprint pytz
```

또는 requirements.txt에 이미 포함되어 있으므로:

```bash
pip install -r requirements.txt
```

## 빠른 시작

### 기본 리포트 생성

```python
from report_system import ReportGenerator
from datetime import datetime

# 리포트 생성기 초기화
generator = ReportGenerator()

# 일일 리포트 생성
result = generator.generate_daily_report()

if result['success']:
    print(f"리포트 생성 완료: {result['output_path']}")
else:
    print(f"생성 실패: {result['error']}")
```

### HTML만 생성

```python
from report_system import ReportGenerator

generator = ReportGenerator()

# HTML만 생성 (PDF 변환 없음)
html_content = generator.generate_html_only('daily')

# HTML 파일로 저장
with open('report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
```

### 스케줄링 설정

```python
from report_system import ReportScheduler

# 스케줄러 초기화
scheduler = ReportScheduler()

# 기본 스케줄 설정 (설정 파일 기반)
scheduler.setup_default_schedules()

# 또는 개별 스케줄 등록
scheduler.schedule_daily_report("09:00")           # 매일 9시
scheduler.schedule_weekly_report("monday", "10:00") # 매주 월요일 10시
scheduler.schedule_monthly_report(1, "09:00")      # 매월 1일 9시

# 스케줄러 시작
scheduler.start()

# 종료하려면
# scheduler.shutdown()
```

## 설정

### 설정 파일 구조 (report_config.json)

```json
{
  "general": {
    "output_dir": "reports",
    "template_dir": "report_templates",
    "default_language": "ko",
    "timezone": "Asia/Seoul"
  },
  "pdf_settings": {
    "converter": "weasyprint",
    "page_size": "A4",
    "margin": "20mm",
    "orientation": "portrait",
    "encoding": "UTF-8",
    "compress": true,
    "dpi": 300
  },
  "report_types": {
    "daily": {
      "enabled": true,
      "schedule": "09:00",
      "retention_days": 30,
      "include_sections": [
        "summary",
        "top_keywords",
        "sentiment_overview",
        "recent_items",
        "quick_stats"
      ],
      "email_recipients": []
    },
    "weekly": {
      "enabled": true,
      "schedule": "monday 09:00",
      "retention_days": 90,
      "include_sections": [
        "weekly_summary",
        "keyword_trends",
        "sentiment_analysis",
        "growth_metrics",
        "recommendations"
      ],
      "email_recipients": []
    },
    "monthly": {
      "enabled": true,
      "schedule": "1st 09:00",
      "retention_days": 365,
      "include_sections": [
        "monthly_overview",
        "detailed_trends",
        "comprehensive_analysis",
        "yearly_comparison",
        "strategic_insights"
      ],
      "email_recipients": []
    }
  },
  "email_notification": {
    "enabled": false,
    "recipients": [],
    "subject_template": "Report: {report_type} - {date}",
    "attach_pdf": true
  }
}
```

### 설정 사용 예시

```python
from report_system.config import ReportConfig
from report_system import create_report_generator

# 설정 파일에서 로드
config = ReportConfig.from_json('report_config.json')

# 또는 기본 설정 사용
config = ReportConfig()

# 설정으로 리포트 생성기 생성
generator = create_report_generator('report_config.json')
```

## 고급 기능

### 사용자 정의 리포트

```python
from report_system import ReportGenerator, ReportParams
from datetime import datetime

generator = ReportGenerator()

# 사용자 정의 파라미터
params = ReportParams(
    report_type='custom',
    date=datetime.now(),
    keywords=['AI', '데이터', '기술'],
    include_sections=['summary', 'top_keywords'],
    custom_data={
        'title': '맞춤형 분석 리포트',
        'subtitle': '특정 키워드 집중 분석'
    }
)

result = generator.generate_custom_report(params)
```

### PDF 고급 기능

```python
from report_system.pdf_converter import PDFConverter

converter = PDFConverter()

# PDF 정보 조회
info = converter.get_pdf_info('path/to/report.pdf')
print(f"페이지 수: {info['pages']}")
print(f"파일 크기: {info['size_mb']:.2f} MB")

# 워터마크 추가
converter.add_watermark('path/to/report.pdf', 'CONFIDENTIAL')

# 여러 PDF 병합
converter.merge_pdfs(
    ['report1.pdf', 'report2.pdf', 'report3.pdf'],
    'merged_report.pdf'
)

# PDF 최적화
converter.optimize_pdf('input.pdf', 'output.pdf')
```

### 스케줄링 고급 기능

```python
from report_system import ReportScheduler

scheduler = ReportScheduler()

# 작업 상태 확인
jobs = scheduler.get_all_jobs()
for job in jobs:
    print(f"{job['name']}: {job['next_run_time']}")

# 특정 작업 상세 조회
status = scheduler.get_job_status('daily_report_0900')

# 작업 일시 중지/재개
scheduler.pause_job('daily_report_0900')
scheduler.resume_job('daily_report_0900')

# 작업 시간 수정
scheduler.modify_job_time('daily_report_0900', '10:00')

# 사용자 정의 스케줄
def custom_callback():
    print("사용자 정의 작업 실행")
    # 사용자 정의 로직

scheduler.schedule_custom_report(
    callback=custom_callback,
    interval_minutes=30
)
```

### 이메일 알림

```python
from report_system import create_report_notifier, ReportGenerator

# 리포트 생성
generator = ReportGenerator()
report_result = generator.generate_daily_report()

# 알림기 초기화
notifier = create_report_notifier()

# 리포트 알림 전송
if report_result['success']:
    notifier.send_report_notification(
        report_result=report_result,
        recipients=['user@example.com'],
        custom_message="정기 리포트가 생성되었습니다."
    )

# 테스트 이메일 전송
notifier.send_test_email('admin@example.com')

# 오류 알림
notifier.send_error_notification(
    error_message="데이터 수집 실패",
    report_type="daily",
    recipients=['admin@example.com']
)
```

## 리포트 관리

### 리포트 이력 조회

```python
from report_system import ReportGenerator

generator = ReportGenerator()

# 전체 이력
history = generator.get_report_history(limit=10)

# 특정 타입 이력
daily_history = generator.get_report_history('daily', limit=5)

for report in history:
    print(f"{report['report_type']}: {report['date']}")
```

### 오래된 리포트 정리

```python
from report_system import ReportGenerator

generator = ReportGenerator()

# 전체 정리
result = generator.cleanup_old_reports()

# 특정 타입 정리
result = generator.cleanup_old_reports('daily')

print(f"삭제된 파일: {len(result['deleted'])}개")
print(f"확보된 공간: {result['freed_space'] / 1024 / 1024:.2f} MB")
```

## 템플릿 사용자 정의

### 템플릿 디렉토리 구조

```
report_templates/
├── base_report_template.html      # 기본 템플릿
├── daily_summary_template.html    # 일일 리포트 템플릿
├── weekly_analysis_template.html  # 주간 리포트 템플릿
├── monthly_overview_template.html # 월간 리포트 템플릿
└── components/                     # 컴포넌트 디렉토리
    ├── footer.html                # 푸터
    └── sections/                  # 섹션 컴포넌트
```

### 템플릿 변수

기본 템플릿에서 사용할 수 있는 변수:

- `{{ title }}`: 리포트 제목
- `{{ generated_at }}`: 생성 시간
- `{{ generated_date }}`: 생성 날짜
- `{{ company_name }}`: 회사명
- `{{ version }}`: 버전
- `{{ period }}`: 분석 기간

### 사용자 정의 템플릿 예시

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        /* 사용자 정의 스타일 */
        body { font-family: 'Noto Sans KR', sans-serif; }
        .custom-section { background-color: #f0f0f0; }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    <p>생성일: {{ generated_at }}</p>

    <!-- 사용자 정의 콘텐츠 -->
    <div class="custom-section">
        <h2>사용자 정의 섹션</h2>
        <p>{{ custom_content }}</p>
    </div>

    <!-- 기본 섹션 -->
    {{ summary_content }}
    {{ top_keywords }}

</body>
</html>
```

## 테스트

### 테스트 실행

```bash
python test_report_system.py
```

### 개별 테스트

```python
import unittest
from test_report_system import TestReportGenerator, TestPDFConverter

# 특정 테스트만 실행
suite = unittest.TestSuite()
suite.addTest(TestReportGenerator('test_daily_report_generation'))
suite.addTest(TestPDFConverter('test_pdf_filename_generation'))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
```

## 예제 실행

### 전체 예제 실행

```bash
python report_system_example.py
```

### 개별 예제 실행

```python
# 예제 파일에서 원하는 함수 주석 해제
from report_system_example import example_1_basic_report_generation

example_1_basic_report_generation()
```

## 문제 해결

### WeasyPrint 관련 문제

**문제**: WeasyPrint import 오류

**해결**:
```bash
pip install weasyprint
# 또는
pip install --upgrade weasyprint
```

### 한글 폰트 관련 문제

**문제**: 한글이 제대로 표시되지 않음

**해결**: 시스템에 한글 폰트가 설치되어 있는지 확인:
```bash
# Windows
# 제어판 > 글꼴에서 Noto Sans KR 또는 맑은 고딕 확인

# Linux
sudo apt-get install fonts-noto-cjk
```

### 스케줄링 관련 문제

**문제**: 스케줄러가 작동하지 않음

**해결**:
1. APScheduler가 설치되어 있는지 확인
2. 타임존 설정이 올바른지 확인
3. 로그를 확인하여 에러 메시지 확인

```python
# 로깅 레벨 설정
import logging
logging.basicConfig(level=logging.DEBUG)
```

### PDF 변환 관련 문제

**문제**: PDF 변환 실패

**해결**:
1. WeasyPrint 의존성 확인
2. HTML 유효성 검사
3. 디스크 공간 확인

```python
# HTML 유효성 테스트
html_content = generator.generate_html_only('daily')
# 브라우저에서 HTML 열어서 확인
```

## 아키텍처

### 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│                     ReportScheduler                         │
│              (APScheduler 기반 스케줄링)                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   ReportGenerator                           │
│                  (리포트 생성 조율)                         │
└────────┬──────────────────┬──────────────────┬──────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│DataAggregator│   │HTMLTemplate  │   │PDFConverter  │
│  (데이터 수집) │   │  (HTML 렌더링)│   │  (PDF 변환)   │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 데이터 흐름

1. **스케줄링**: ReportScheduler가 정해진 시간에 리포트 생성 요청
2. **데이터 수집**: DataAggregator가 기존 분석 시스템에서 데이터 수집
3. **템플릿 렌더링**: HTMLReportTemplate가 데이터로 HTML 생성
4. **PDF 변환**: PDFConverter가 HTML을 PDF로 변환
5. **알림**: ReportNotifier가 이메일 등으로 알림 전송

## 성능 최적화

### 캐싱 활용

```python
from report_system.html_report_template import HTMLReportTemplate

# 템플릿 캐싱 자동 활성화
template = HTMLReportTemplate()
# 템플릿 파일은 자동으로 캐싱됨
```

### 비동기 처리

```python
import asyncio
from report_system import ReportGenerator

async def async_generate_reports():
    generator = ReportGenerator()

    # 여러 리포트 동시 생성
    tasks = [
        asyncio.to_thread(generator.generate_daily_report),
        asyncio.to_thread(generator.generate_weekly_report),
        asyncio.to_thread(generator.generate_monthly_report, 2025, 5)
    ]

    results = await asyncio.gather(*tasks)
    return results

# 실행
results = asyncio.run(async_generate_reports())
```

### 배치 처리

```python
from report_system.pdf_converter import PDFConverter

converter = PDFConverter()

# 여러 HTML 파일 일괄 변환
html_files = [
    (html_content1, 'report1.pdf'),
    (html_content2, 'report2.pdf'),
    (html_content3, 'report3.pdf')
]

results = converter.batch_convert_html_to_pdf(html_files, 'output_dir')
print(f"성공: {len(results['success'])}, 실패: {len(results['failed'])}")
```

## 보안 고려사항

### 파일 시스템 보안

```python
from report_system.pdf_converter import validate_pdf_path

# PDF 경로 유효성 검사
if validate_pdf_path(user_input_path):
    # 안전한 경로만 처리
    converter.convert_html_to_pdf(html_content, user_input_path)
```

### 입력 검증

```python
from report_system.config import ReportParams

# 파라미터 유효성 검사
params = ReportParams(
    report_type='daily',
    date=datetime.now()
)

if params.validate():
    # 유효한 파라미터만 처리
    generator.generate_custom_report(params)
```

## 모니터링 및 로깅

### 로깅 설정

```python
import logging

# 상세 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_system.log'),
        logging.StreamHandler()
    ]
)

# 특정 모듈 로깅 레벨 설정
logging.getLogger('report_system.pdf_converter').setLevel(logging.INFO)
```

### 상태 모니터링

```python
from report_system import ReportScheduler

scheduler = ReportScheduler()

# 시스템 상태 확인
jobs = scheduler.get_all_jobs()
for job in jobs:
    status = scheduler.get_job_status(job['id'])
    print(f"작업: {status['name']}")
    print(f"상태: {status['status']}")
    print(f"다음 실행: {status['next_run_time']}")
    print(f"오류 횟수: {status.get('error_count', 0)}")
```

## 추가 자료

- **WeasyPrint 문서**: https://doc.courtbouillon.org/weasyprint/
- **APScheduler 문서**: https://apscheduler.readthedocs.io/
- **DealBot 메인 문서**: README.md

## 지원 및 피드백

문제가 발생하거나 기능 요청이 있으시면:
1. 이슈 트래커에 버그 리포트
2. 기능 요청 제출
3. 코드 기여 환영

## 라이선스

이 시스템은 DealBot 프로젝트의 일부로 제공됩니다.