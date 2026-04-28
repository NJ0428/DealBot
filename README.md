# 🕷️ 웹 주제 크롤러 및 Excel 저장 프로그램

특정 주제/키워드로 웹에서 정보를 수집하고 Excel 파일로 저장하는 파이썬 프로그램입니다.

## ✨ 주요 기능

### 🆕 RSS 피드 자동 생성

- 📡 **RSS 2.0 지원**: 표준 RSS 2.0 형식으로 피드 생성
- 🔄 **자동 업데이트**: APScheduler 기반 정기적 자동 크롤링 및 피드 업데이트
- ⏰ **유연한 스케줄링**: 간격 기반(매 N분/시간) 및 크론 기반(매일 특정 시간) 스케줄링
- 📊 **멀티피드 지원**: 여러 키워드에 대한 개별 피드 및 통합 피드 생성
- 🎯 **커스터마이징**: 피드 제목, 설명, 카테고리 등 완전한 커스터마이징
- 💾 **설정 저장/로드**: 스케줄 설정을 JSON 파일로 저장 및 로드

```python
from rss_feed_generator import create_feed_from_crawler_data
from feed_scheduler import FeedManager

# 간단한 RSS 피드 생성
feed_path = create_feed_from_crawler_data("AI", crawled_data)

# 자동 스케줄링 (매 30분마다 업데이트)
manager = FeedManager()
manager.quick_start(
    keywords=["AI", "블록체인", "메타버스"],
    schedule_type='interval',
    interval_minutes=30,
    run_immediately=True
)
```

### 🆕 인기 급상승 키워드 탐지 및 알림

- 🔥 **자동 급상승 탐지**: 성장률, 순위 상승, 변동성 기반 다중 기준 탐지
- 📊 **스코어링 시스템**: 가중치 기반 종합 점수 계산 (0-100점)
- 📧 **실시간 알림**: 이메일 자동 발송 및 쿨다운 시스템
- 📝 **알림 히스토리**: 중복 알림 방지 및 로그 관리
- 🎯 **커스터마이징**: 탐지 기준, 알림 빈도, 수신자 설정

```python
from keyword_trend_alert_system import KeywordAlertSystem

# 시스템 초기화
alert_system = KeywordAlertSystem(email_notifier=email_notifier)

# 급상승 키워드 탐지 및 알림
result = alert_system.monitor_and_alert(
    trend_df=trend_data,
    growth_df=growth_data,
    recipients=["user@example.com"]
)

print(f"탐지: {result['detected']}개, 알림: {result['alerted']}개")
```

### 🆕 Excel 차트 자동 삽입

- 📊 **5가지 차트 타입**: 빈도 막대그래프, 트렌드 라인, 성장률 히트맵, 네트워크, 워드클라우드
- 🖼️ **고해상도 이미지**: 150-200 DPI 차트 자동 생성
- 📈 **Excel 네이티브 차트**: openpyxl 기반 인터랙티브 차트
- 🎨 **커스터마이징**: 크기, 색상, 폰트, 레이아웃 설정
- 📋 **종합 리포트**: 한 번의 호출로 모든 차트 자동 생성

```python
from excel_chart_integration import ExcelReportGenerator

# 리포트 생성기 초기화
generator = ExcelReportGenerator()

# 종합 Excel 리포트 생성 (모든 차트 포함)
generator.generate_comprehensive_report(
    excel_path="analysis.xlsx",
    trend_df=trend_data,
    growth_df=growth_data,
    keyword_freq=keyword_freq,
    network_graph=network,
    word_freq=word_freq
)
```

### 🆕 키워드 트렌드 분석 시스템

- 🇰🇷 **한국어 형태소 분석**: KoNLPy 기반 형태소 분석 (Okt, Mecab, Komoran 등)
- 📈 **키워드 트렌드 분석**: 일별/주별/월별 키워드 빈도 추이 분석
- 🌐 **연관 키워드 네트워크**: 동시 출현 기반 키워드 네트워크 분석
- 🎯 **키워드 클러스터링**: K-means 기반 키워드 군집화
- 📊 **인터랙티브 시각화**: Plotly 기반 인터랙티브 차트 및 네트워크 그래프
- ☁️ **워드클라우드**: 키워드 빈도 기반 워드클라우드 생성

**Excel 리포트 및 알림 통합:**
```python
from keyword_trend_analyzer import KeywordTrendSystem

system = KeywordTrendSystem()
results = system.analyze_from_logs('logs')

# Excel 리포트 생성 (차트 포함)
excel_path = system.generate_excel_report(results, include_charts=True)

# 급상승 키워드 알림
alert_result = system.monitor_and_alert_trending(results, recipients=["user@example.com"])
```

```python
from keyword_trend_analyzer import KeywordTrendSystem

# 시스템 초기화
system = KeywordTrendSystem(analyzer_type='okt')

# 로그 파일 분석
results = system.analyze_from_logs('logs')

# 결과 요약 출력
system.print_summary(results)

# 리포트 생성 (트렌드 차트, 네트워크, 워드클라우드)
report_files = system.generate_report(results)
```

**상세 가이드:** [KEYWORD_ANALYSIS_GUIDE.md](KEYWORD_ANALYSIS_GUIDE.md)

### 🆕 이메일 알림 시스템

- 📧 **Gmail SMTP 연동**: 안전하고 신뢰할 수 있는 Gmail SMTP 서버 사용
- 📊 **자동 리포트 생성**: 크롤링 완료 시 HTML 형식의 이쁜 리포트 자동 생성
- 📎 **Excel 파일 자동 첨부**: 크롤링 결과 Excel 파일 자동 첨부
- 🔔 **다중 수신자 지원**: 여러 수신자에게 동시 전송 가능
- ⚠️ **오류 알림**: 크롤링 실패 시 오류 리포트 자동 전송
- 🔐 **안전한 인증**: 앱 비밀번호를 사용한 안전한 인증 방식

```python
from email_notifier import EmailNotifier, EmailAuth

# 이메일 알림 시스템 초기화
auth = EmailAuth()
notifier = EmailNotifier(auth)

# 크롤링 완료 후 자동 이메일 전송
notifier.send_crawling_report(
    to_email="recipient@example.com",
    keyword="인공지능",
    data=crawled_data,
    excel_file="result.xlsx"
)
```

### 🆕 데이터 시각화 기능

- 📊 **matplotlib/plotly 기반 시각화**: 인터랙티브 차트 자동 생성
- 📈 **키워드별 게시글 수 막대그래프**: 키워드별 데이터 분포 시각화
- 📉 **일자별 게시글 추이 라인차트**: 시간에 따른 데이터 변화 추적
- 🥧 **출처별 비율 파이차트**: 데이터 출처 분석
- 🎯 **종합 대시보드**: 모든 분석 결과를 하나의 HTML 대시보드로 통합 제공
- 🌐 **브라우저 자동 열기**: HTML 대시보드 생성 후 자동으로 브라우저에서 확인

```python
from web_crawler import DataVisualizer

visualizer = DataVisualizer()

# 단일 차트 생성
visualizer.create_bar_chart(data, "키워드별 게시글 수", "키워드", "게시글 수")
visualizer.create_line_chart(data, "일자별 게시글 추이", "날짜", "게시글 수")
visualizer.create_pie_chart(data, "출처별 게시글 비율")

# 인터랙티브 차트 생성 (Plotly)
visualizer.create_interactive_bar(data, "키워드별 게시글 수 (인터랙티브)")
visualizer.create_interactive_line(data, "일자별 게시글 추이 (인터랙티브)")

# 모든 차트 한번에 생성
all_charts = visualizer.generate_all_charts(data, "analysis")
```

### 기본 기능

- 🔍 **Google News 검색**: 키워드로 뉴스 검색 및 크롤링
- 📝 **네이버 블로그 검색**: 블로그 포스트 검색 및 수집
- 🌐 **사용자 정의 URL 크롤링**: 특정 URL에서 데이터 추출
- 📊 **Excel 자동 저장**: 자동 열 너비 조정 및 다중 시트 지원

### ⚡ 업그레이드 기능

#### 1. 📦 결과 캐싱

- 동일 키워드 검색 시 캐시 활용으로 속도 개선
- 디스크 기반 캐시 (지속성 보장)
- 자동 만료 관리 (기본 24시간)

```python
crawler = WebCrawler(use_cache=True)
data = crawler.search_google_news("인공지능")  # 첫 검색은 크롤링
data = crawler.search_google_news("인공지능")  # 두 번째는 캐시 사용
```

#### 2. 📊 진행률 표시

- 크롤링 진행 상황을 프로그레스 바로 시각화
- 실시간 진행률 및 처리 속도 표시
- 멀티키워드 검색 시 총 진행률 표시

```
검색 중... ████████████████░░░░░░░░ 60% | 12/20 항목 | 2.3초/항목
```

#### 3. 🚀 비동기 요청

- `aiohttp` 활용으로 병렬 크롤링 지원
- 최대 5개의 동시 요청 처리
- 멀티키워드 검색 시 속도 대폭 개선

```python
# 비동기 검색 활성화
results = crawler.search_multiple_keywords(
    ["AI", "블록체인", "메타버스"],
    max_results=10,
    use_async=True  # 병렬 처리
)
```

#### 4. 🛡️ 프록시 지원

- IP 차단 방지를 위한 프록시 로테이션
- 라운드 로빈 방식으로 프록시 순환 사용
- HTTP/HTTPS/SOCKS5 프록시 지원

```python
# 프록시 활성화
crawler = WebCrawler(use_proxy=True)

# 프록시 리스트: proxies.txt
# http://proxy1.example.com:8080
# http://user:pass@proxy2.example.com:3128
```

#### 5. 📋 로그 시스템

- `logging` 모듈 도입으로 체계적인 로그 관리
- 파일 및 콘솔 로그 동시 출력
- 날짜별 로그 파일 자동 생성

```
logs/crawler_20260413.log
```

```python
from web_crawler import logger

logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("오류 메시지")
```

#### 6. 🔍 결과 필터링

- **날짜 범위**: 특정 기간 내 결과만 필터링
- **출처 필터**: 특정 출처 포함/제외
- **키워드 필터**: 제목/내용 키워드 기반 필터
- **길이 필터**: 제목 길이 기반 필터

```python
from web_crawler import FilterCriteria
from datetime import datetime, timedelta

# 필터링 기준 설정
criteria = FilterCriteria(
    start_date=datetime.now() - timedelta(days=7),  # 최근 7일
    allowed_sources={"연합뉴스", "Reuters"},          # 특정 출처만
    keywords_in_title={"AI", "인공지능"},              # 제목 키워드
    min_title_length=10                              # 최소 길이
)

# 필터 적용 검색
data = crawler.search_google_news(
    "인공지능",
    filter_criteria=criteria
)
```

## 📦 설치

### 요구사항

- Python 3.8+
- pip
- Gmail 계정 (이메일 알림 사용 시)

### 패키지 설치

```bash
pip install -r requirements.txt
```

### 의존성

```
requests>=2.31.0         # HTTP 요청
beautifulsoup4>=4.12.0   # HTML 파싱
pandas>=2.0.0            # 데이터 처리
openpyxl>=3.1.0          # Excel 저장
lxml>=4.9.0              # XML/HTML 파싱
aiohttp>=3.9.0           # 비동기 HTTP 요청
tqdm>=4.66.0             # 진행률 표시
diskcache>=5.6.0         # 디스크 캐싱
matplotlib>=3.7.0        # 데이터 시각화
plotly>=5.14.0           # 인터랙티브 차트
kaleido>=0.2.1           # 정적 이미지 변환
konlpy>=0.6.0            # 한국어 형태소 분석
networkx>=3.1            # 네트워크 분석
wordcloud>=1.9.0         # 워드클라우드 생성
scikit-learn>=1.3.0      # 머신러닝 (클러스터링)
numpy>=1.24.0            # 수치 연산
apscheduler>=3.10.0      # 스케줄링 (RSS 피드 자동 업데이트)
smtplib (내장)           # 이메일 전송 (Python 내장)
```

## 🚀 사용법

### 1. 이메일 설정 (이메일 알림 사용 시)

이메일 알림 기능을 사용하려면 먼저 Gmail SMTP 설정이 필요합니다.

#### 1단계: Gmail 앱 비밀번호 생성

1. [Google 계정](https://myaccount.google.com/)에 로그인
2. **[보안]** 섹션으로 이동
3. **[2단계 인증]** 활성화 (필수)
4. **[앱 비밀번호]** 섹션에서 새 앱 비밀번호 생성
5. **[메일]** 및 **[Windows 컴퓨터]** 선택 후 생성
6. 생성된 16자리 비밀번호 복사

#### 2단계: 이메일 설정 실행

```bash
# 이메일 설정 도구 실행
python email_example.py

# 옵션 1: 이메일 설정 선택
```

### 2. 기본 사용 (대화형 모드)

```bash
python web_crawler.py
```

### 2. 코드로 사용

#### 기본 검색

```python
from web_crawler import WebCrawler, ExcelExporter

crawler = WebCrawler()
exporter = ExcelExporter()

# Google News 검색
data = crawler.search_google_news("인공지능", max_results=10)

# Excel 저장
if data:
    exporter.save_to_excel(data, "result.xlsx", "뉴스")
```

#### 캐싱 활용

```python
# 캐시 활성화
crawler = WebCrawler(use_cache=True)

# 첫 번째 검색 (실제 크롤링)
data1 = crawler.search_google_news("파이썬")

# 두 번째 검색 (캐시 사용 - 매우 빠름)
data2 = crawler.search_google_news("파이썬")

# 캐시 비우기
crawler.clear_cache()
crawler.close()
```

#### 필터링 적용

```python
from web_crawler import FilterCriteria
from datetime import datetime, timedelta

crawler = WebCrawler(use_cache=True)

# 필터 설정
criteria = FilterCriteria(
    start_date=datetime.now() - timedelta(days=7),
    keywords_in_title={"파이썬", "Python"},
    min_title_length=15
)

# 필터 적용 검색
data = crawler.search_google_news(
    "파이썬",
    max_results=20,
    filter_criteria=criteria
)
```

#### 다중 키워드 검색

```python
keywords = ["AI", "블록체인", "메타버스"]

# 동기 검색
results = crawler.search_multiple_keywords(
    keywords,
    max_results=10,
    use_async=False
)

# 비동기 검색 (병렬 처리)
results = crawler.search_multiple_keywords(
    keywords,
    max_results=10,
    use_async=True
)

# 결과 저장
all_data = {f"News_{k}": v for k, v in results.items()}
exporter.save_multiple_sheets(all_data, "tech_trends.xlsx")
```

#### 수동 필터링 체이닝

```python
from web_crawler import ResultFilter

# 데이터 수집
data = crawler.search_google_news("코딩", max_results=50)

# 1단계: 날짜 필터링
filtered = ResultFilter.filter_by_date(
    data,
    start_date=datetime.now() - timedelta(days=30)
)

# 2단계: 키워드 필터링
filtered = ResultFilter.filter_by_keywords(
    filtered,
    keywords_in_title={"프로그래밍", "개발"}
)

# 3단계: 출처 필터링
filtered = ResultFilter.filter_by_source(
    filtered,
    allowed_sources={"연합뉴스", "뉴시스"}
)

# 결과 저장
exporter.save_to_excel(filtered, "filtered_result.xlsx")
```

#### 데이터 시각화

```python
from web_crawler import DataVisualizer, DataAnalyzer

# 데이터 수집
data = crawler.search_google_news("인공지능", max_results=30)

# 시각화 객체 초기화
visualizer = DataVisualizer()
analyzer = DataAnalyzer()

# 단일 차트 생성
keyword_counts = analyzer.analyze_by_keyword(data)
visualizer.create_bar_chart(keyword_counts, "키워드별 게시글 수", "키워드", "게시글 수")

date_counts = analyzer.analyze_by_date(data)
visualizer.create_line_chart(date_counts, "일자별 게시글 추이", "날짜", "게시글 수")

source_counts = analyzer.analyze_by_source(data)
visualizer.create_pie_chart(source_counts, "출처별 게시글 비율", open_browser=False)

# 인터랙티브 차트 생성 (Plotly)
visualizer.create_interactive_bar(keyword_counts, "키워드별 게시글 수 (인터랙티브)")
visualizer.create_interactive_line(date_counts, "일자별 게시글 추이 (인터랙티브)")

# HTML 대시보드 생성 (브라우저 자동 열기)
visualizer.create_dashboard(data, "인공지능 뉴스 분석", open_browser=True)

# 모든 차트 한번에 생성
all_charts = visualizer.generate_all_charts(data, "ai_analysis", open_browser=True)

# 결과 확인
for chart_type, path in all_charts.items():
    print(f"{chart_type}: {path}")
# 출력:
# bar_keyword: charts/bar_chart_20260413_143022.png
# pie_source: charts/pie_chart_20260413_143025.png
# line_date: charts/line_chart_20260413_143028.png
# interactive_bar: charts/interactive_bar_20260413_143031.html
# interactive_line: charts/interactive_line_20260413_143034.html
# dashboard: dashboard/dashboard_20260413_143037.html
```

#### 이메일 알림 시스템

```python
from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth

# 크롤러 및 이메일 알림 시스템 초기화
crawler = WebCrawler(use_cache=True)
exporter = ExcelExporter()
auth = EmailAuth()
notifier = EmailNotifier(auth)

# 데이터 수집
keyword = "인공지능"
data = crawler.search_google_news(keyword, max_results=10)

# Excel 저장
excel_file = f"{keyword}_result.xlsx"
exporter.save_to_excel(data, excel_file, "뉴스")

# 이메일 전송
notifier.send_crawling_report(
    to_email=auth.get_email(),
    keyword=keyword,
    data=data,
    excel_file=excel_file,
    search_type="Google News"
)

crawler.close()
```

**이메일 예시 옵션:**
- `send_crawling_report`: 기본 크롤링 완료 리포트 전송
- `send_multiple_keywords_report`: 다중 키워드 검색 결과 리포트 전송
- `send_error_report`: 오류 발생 시 알림 전송
- `send_email`: 사용자 정의 이메일 전송

#### RSS 피드 자동 생성

```python
from web_crawler import WebCrawler
from rss_feed_generator import create_feed_from_crawler_data
from feed_scheduler import FeedManager

# 1. 기본 RSS 피드 생성
crawler = WebCrawler(use_cache=True)
data = crawler.search_google_news("인공지능", max_results=20)

# RSS 피드 생성
feed_path = create_feed_from_crawler_data("AI", data)
print(f"RSS 피드 생성: {feed_path}")

# 2. 커스텀 RSS 피드 설정
from rss_feed_generator import RSSFeedGenerator, RSSFeedConfig, WebCrawlerToRSSConverter

config = RSSFeedConfig(
    title="내 블로그 - AI 뉴스",
    description="최신 AI 기술 뉴스를 제공합니다",
    link="https://myblog.com/ai",
    language="ko"
)

converter = WebCrawlerToRSSConverter()
rss_items = converter.convert_to_rss_items(data)

generator = RSSFeedGenerator(config)
generator.save_feed(rss_items, "rss_feeds/ai_custom.xml")

# 3. 멀티피드 생성 (여러 키워드)
from rss_feed_generator import MultiFeedGenerator

keywords = ["AI", "블록체인", "메타버스"]
data_by_keyword = {k: crawler.search_google_news(k, max_results=10) for k in keywords}

base_config = RSSFeedConfig(
    title="테크 뉴스 허브",
    description="최신 기술 뉴스",
    link="https://technews.com"
)

multi_gen = MultiFeedGenerator(base_config)

# 개별 피드 생성
feed_paths = multi_gen.generate_feeds(data_by_keyword, output_dir="rss_feeds/tech")

# 통합 피드 생성
multi_gen.generate_combined_feed(data_by_keyword, "rss_feeds/tech/combined.xml")

# 4. 자동 스케줄링 (매 30분마다 업데이트)
manager = FeedManager()

# 간격 기반 스케줄링
scheduler = manager.create_scheduler(
    keywords=["AI", "블록체인"],
    schedule_type='interval',
    interval_minutes=30  # 30분마다
)

# 크론 기반 스케줄링 (매일 9시)
scheduler = manager.create_scheduler(
    keywords=["AI"],
    schedule_type='cron',
    cron_hour=9,
    cron_minute=0
)

# 스케줄러 시작 (백그라운드에서 실행)
scheduler.start(run_immediately=True)

# 설정 저장
scheduler.save_config("my_scheduler_config.json")

# 설정 로드
from feed_scheduler import RSSFeedScheduler
loaded_scheduler = RSSFeedScheduler.load_config("my_scheduler_config.json")
```

**스케줄링 옵션:**
- `schedule_type='interval'`: 간격 기반 (매 N분/시간)
- `schedule_type='cron'`: 크론 기반 (매일 특정 시간)
- `run_immediately=True`: 시작 즉시 실행 후 스케줄링
- `use_background=True`: 백그라운드 스케줄러 사용

```bash
# RSS 피드 예시 실행
python rss_feed_example.py
```

```bash
# 이메일 예시 실행
python email_example.py
```

### 3. 예시 실행

```bash
python example_usage.py
```

사용 가능한 예시:

1. 기본 검색 (캐싱)
2. 필터링 옵션
3. 다중 키워드 비동기 검색
4. 출처 기반 필터링
5. 수동 필터링 체이닝
6. 로그 시스템
7. 캐시 관리
8. 종합 검색
9. 프록시 설정
10. 데이터 시각화

**키워드 분석 예시:**
```bash
python test_keyword_analyzer.py
```

## 📁 프로젝트 구조

```
.
├── web_crawler.py          # 메인 크롤러 모듈
├── email_notifier.py       # 이메일 알림 시스템
├── keyword_trend_analyzer.py  # 키워드 트렌드 분석 시스템 (신규)
├── rss_feed_generator.py   # RSS 피드 생성 모듈 (신규)
├── feed_scheduler.py       # RSS 피드 스케줄러 (신규)
├── example_usage.py        # 사용 예시 스크립트
├── email_example.py        # 이메일 알림 예시 스크립트
├── rss_feed_example.py     # RSS 피드 예시 스크립트 (신규)
├── test_keyword_analyzer.py  # 키워드 분석 테스트 스크립트 (신규)
├── requirements.txt        # 의존성 패키지
├── README.md              # 이 파일
├── EMAIL_GUIDE.md         # 이메일 알림 시스템 가이드
├── KEYWORD_ANALYSIS_GUIDE.md  # 키워드 분석 가이드 (신규)
├── .cache/                # 캐시 디렉토리 (자동 생성)
├── logs/                  # 로그 디렉토리 (자동 생성)
├── charts/                # 차트 저장 디렉토리 (자동 생성)
├── dashboard/             # 대시보드 저장 디렉토리 (자동 생성)
├── rss_feeds/             # RSS 피드 저장 디렉토리 (자동 생성, 신규)
├── email_templates/       # 이메일 템플릿 디렉토리 (자동 생성)
├── email_config.json      # 이메일 설정 파일 (자동 생성)
├── scheduler_config.json  # 스케줄러 설정 파일 (자동 생성, 신규)
└── proxies.txt            # 프록시 리스트 (선택사항)
```

## ⚙️ 설정

### 크롤러 설정

```python
from web_crawler import Config

# 설정 값
Config.REQUEST_TIMEOUT = 10           # 요청 타임아웃 (초)
Config.REQUEST_DELAY = 2.0            # 요청 간격 (초)
Config.DEFAULT_MAX_RESULTS = 20       # 기본 최대 결과 수
Config.CACHE_EXPIRE_HOURS = 24        # 캐시 만료 시간
Config.MAX_CONCURRENT_REQUESTS = 5    # 최대 동시 요청 수

# 시각화 설정
Config.CHART_DIR = "charts"           # 차트 저장 디렉토리
Config.DASHBOARD_DIR = "dashboard"    # 대시보드 저장 디렉토리
Config.CHART_WIDTH = 12               # 차트 너비
Config.CHART_HEIGHT = 6               # 차트 높이
Config.PLOTLY_WIDTH = 1200            # Plotly 차트 너비
Config.PLOTLY_HEIGHT = 600            # Plotly 차트 높이
```

### 프록시 설정

`proxies.txt` 파일 생성:

```
# 프록시 리스트
# 형식: protocol://user:pass@host:port

http://proxy1.example.com:8080
http://user:password@proxy2.example.com:3128
socks5://proxy3.example.com:1080
```

## 📊 Excel 출력 예시

| 키워드   | 제목                        | 요약                   | 출처/날짜             | 링크        | 수집일시            |
| -------- | --------------------------- | ---------------------- | --------------------- | ----------- | ------------------- |
| 인공지능 | OpenAI, 새로운 모델 발표... | AI 기술 혁신 가속화... | 테크미디어 · 2시간 전 | https://... | 2026-04-13 14:30:00 |

## 🔧 고급 기능

### 필터링 기준 상세

```python
from web_crawler import FilterCriteria
from datetime import datetime

criteria = FilterCriteria(
    # 날짜 필터
    start_date=datetime(2026, 4, 1),
    end_date=datetime(2026, 4, 30),

    # 출처 필터
    allowed_sources={"연합뉴스", "Reuters"},
    blocked_sources={"광고"},

    # 키워드 필터
    keywords_in_title={"AI", "인공지능"},
    keywords_in_content={"딥러닝", "신경망"},

    # 길이 필터
    min_title_length=10,
    max_title_length=100
)
```

### 로그 확인

```python
from web_crawler import logger

logger.info("정보 로그")
logger.warning("경고 로그")
logger.error("에러 로그")

# 로그 파일: logs/crawler_YYYYMMDD.log
```

### 캐시 관리

```python
crawler = WebCrawler(use_cache=True)

# 캐시 자동 사용
data = crawler.search_google_news("키워드")

# 캐시 수동 비우기
crawler.clear_cache()

# 리소스 정리
crawler.close()
```

## 🐛 문제 해결

### 키워드 분석 시스템 관련

1. **KoNLPy 설치 오류**
   - Java JDK 8 이상 설치 확인
   - JAVA_HOME 환경변수 설정
   - `pip install konlpy` 재실행

2. **Mecab 형태소 분석기 오류**
   - Windows: `pip install eunjeon`
   - macOS/Linux: `bash <(curl -s https://raw.githubusercontent.com/konlpy/konlpy/master/scripts/mecab.sh)`

3. **한글 폰트 오류**
   - 워드클라우드 생성 시 한글 폰트 필요
   - AnalyzerConfig에서 FONT_PATH 설정

### 일반적인 문제

1. **캐시 관련 오류**
   - `.cache/` 디렉토리 삭제 후 재시도

2. **프록시 연결 오류**
   - `proxies.txt` 파일 확인
   - 프록시 서버 상태 확인

3. **크롤링 속도가 느린 경우**
   - 캐싱 활성화
   - 비동기 검색 사용 (`use_async=True`)
   - 최대 결과 수 줄이기

### 로그 확인

```bash
# 최신 로그 확인
tail -f logs/crawler_$(date +%Y%m%d).log
```
