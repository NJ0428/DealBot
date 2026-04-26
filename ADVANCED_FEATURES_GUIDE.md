# 고급 기능 사용 가이드

인기 급상승 키워드 탐지 및 Excel 차트 자동 삽입 기능에 대한 상세 가이드입니다.

## 📋 목차

1. [인기 급상승 키워드 탐지](#인기-급상승-키워드-탐지)
2. [Excel 차트 자동 삽입](#excel-차트-자동-삽입)
3. [이메일 알림 통합](#이메일-알림-통합)
4. [종합 사용 예시](#종합-사용-예시)

## 🚀 인기 급상승 키워드 탐지

### 기능 소개

자동으로 급상승하는 키워드를 탐지하고 알림을 발송하는 시스템입니다.

**탐지 기준:**
- 성장률 50% 이상
- 순위 5계급 이상 상승
- 종합 점수 60점 이상

**점수 계산:**
- 성장률 (40%)
- 빈도수 (30%)
- 순위 상승 (20%)
- 변동성 (10%)

### 기본 사용법

```python
from keyword_trend_alert_system import KeywordAlertSystem
import pandas as pd
from datetime import datetime, timedelta

# 알림 시스템 초기화
alert_system = KeywordAlertSystem()

# 트렌드 데이터 준비
trend_df = pd.DataFrame({
    'date': pd.date_range(end=datetime.now(), periods=7, freq='D'),
    'keyword': ['AI'] * 7,
    'frequency': [10, 20, 40, 80, 160, 320, 640]  # 급상승
})

# 모니터링 및 알림
result = alert_system.monitor_and_alert(trend_df)

print(f"탐지된 키워드: {result['detected']}개")
print(f"알림 발송: {result['alerted']}개")
```

### 이메일 알림 연동

```python
from email_notifier import EmailNotifier, EmailAuth

# 이메일 설정
auth = EmailAuth()
email_notifier = EmailNotifier(auth)

# 알림 시스템 초기화
alert_system = KeywordAlertSystem(email_notifier=email_notifier)

# 모니터링 및 이메일 발송
recipients = ["user@example.com"]
result = alert_system.monitor_and_alert(
    trend_df,
    recipients=recipients
)
```

### 알림 설정 커스터마이징

```python
from keyword_trend_alert_system import AlertConfig, KeywordAlertSystem

# 커스텀 설정
config = AlertConfig()
config.GROWTH_RATE_THRESHOLD = 100.0     # 성장률 100% 이상
config.MIN_FREQUENCY_THRESHOLD = 10      # 최소 10회
config.ALERT_COOLDOWN_MINUTES = 120      # 2시간 쿨다운
config.MAX_KEYWORDS_PER_ALERT = 20       # 최대 20개 키워드

# 알림 시스템 초기화
alert_system = KeywordAlertSystem(config=config)
```

### 급상승 키워드 리포트

```python
# 리포트 생성
report = alert_system.get_trending_report(trend_df)
print(report)

# 출력 예시:
# ============================================================
# 🔥 인기 급상승 키워드 리포트
# ============================================================
#
# 1. ChatGPT
#    빈도: 320회 | 성장: 320.0% | 점수: 95.5
# 2. AI
#    빈도: 640회 | 성장: 630.0% | 점수: 98.2
# ============================================================
```

## 📊 Excel 차트 자동 삽입

### 기능 소개

분석 결과를 Excel 파일에 자동으로 차트로 삽입합니다.

**지원 차트:**
1. 키워드 빈도 막대 그래프
2. 트렌드 라인 차트
3. 성장률 히트맵
4. 네트워크 다이어그램
5. 워드클라우드

### 기본 사용법

```python
from excel_chart_integration import ExcelReportGenerator
import pandas as pd

# 리포트 생성기 초기화
generator = ExcelReportGenerator()

# 데이터 준비
trend_df = pd.DataFrame({
    'date': pd.date_range(end=datetime.now(), periods=7, freq='D'),
    'keyword': ['AI', 'AI', '블록체인', '블록체인'],
    'frequency': [100, 150, 80, 90]
})

# Excel 리포트 생성
keyword_freq = [('AI', 250), ('블록체인', 170), ('메타버스', 120)]

results = generator.generate_comprehensive_report(
    excel_path="analysis_report.xlsx",
    trend_df=trend_df,
    growth_df=pd.DataFrame(),
    keyword_freq=keyword_freq,
    network_graph=None,
    word_freq={'AI': 250, '블록체인': 170}
)

print(f"생성된 차트: {sum(results.values())}개")
```

### 개별 차트 삽입

```python
from excel_chart_integration import ExcelChartInserter

inserter = ExcelChartInserter()

# 1. 키워드 빈도 차트
keyword_data = [('AI', 100), ('블록체인', 80), ('메타버스', 60)]
inserter.insert_keyword_frequency_chart(
    "report.xlsx",
    keyword_data,
    sheet_name="빈도 분석",
    position="H2"
)

# 2. 트렌드 라인 차트
inserter.insert_trend_line_chart(
    "report.xlsx",
    trend_df,
    sheet_name="트렌드 분석",
    position="H2"
)

# 3. 성장률 히트맵
inserter.insert_growth_heatmap(
    "report.xlsx",
    growth_df,
    sheet_name="성장률 분석",
    position="H2"
)

# 4. 네트워크 다이어그램
inserter.insert_network_diagram(
    "report.xlsx",
    network_graph,
    sheet_name="네트워크 분석",
    position="A2"
)

# 5. 워드클라우드
word_freq = {'AI': 100, '블록체인': 80, '메타버스': 60}
inserter.insert_wordcloud(
    "report.xlsx",
    word_freq,
    sheet_name="워드클라우드",
    position="A2"
)
```

### Excel 네이티브 차트

```python
# Excel 기본 차트 삽입 (openpyxl)
data_df = pd.DataFrame({
    '키워드': ['AI', '블록체인', '메타버스'],
    '빈도': [100, 80, 60]
})

inserter.insert_native_excel_chart(
    "report.xlsx",
    data_df,
    chart_type="bar",  # "bar", "line", "pie"
    sheet_name="Excel 차트",
    position="A2"
)
```

### 차트 설정 커스터마이징

```python
from excel_chart_integration import ExcelChartConfig, ExcelChartInserter

# 커스텀 설정
config = ExcelChartConfig()
config.CHART_WIDTH = 20
config.CHART_HEIGHT = 12
config.CHART_DPI = 200
config.FONT_NAME = '나눔고딕'

# 삽입기 초기화
inserter = ExcelChartInserter(config=config)
```

## 📧 이메일 알림 통합

### 키워드 분석 시스템과 통합

```python
from keyword_trend_analyzer import KeywordTrendSystem
from email_notifier import EmailNotifier, EmailAuth

# 시스템 초기화
auth = EmailAuth()
email_notifier = EmailNotifier(auth)
system = KeywordTrendSystem()

# 문서 분석
documents = [
    {'title': 'AI 기사', 'content': '...', 'date': '2026-04-25'},
    # ...
]
results = system.analyze_documents(documents)

# Excel 리포트 생성
excel_path = system.generate_excel_report(
    results,
    excel_path="keyword_analysis.xlsx",
    include_charts=True
)

# 급상승 키워드 알림
alert_result = system.monitor_and_alert_trending(
    results,
    recipients=[auth.get_email()]
)

print(f"Excel 리포트: {excel_path}")
print(f"알림 발송: {alert_result['alerted']}개")
```

## 💡 종합 사용 예시

### 완전한 자동화 파이�라인

```python
from keyword_trend_analyzer import KeywordTrendSystem
from email_notifier import EmailNotifier, EmailAuth
from datetime import datetime, timedelta
import pandas as pd

def complete_keyword_analysis_pipeline():
    """완전한 키워드 분석 파이�라인"""

    # 1. 시스템 초기화
    auth = EmailAuth()
    email_notifier = EmailNotifier(auth)
    system = KeywordTrendSystem(analyzer_type='okt')

    # 2. 데이터 수집 (로그 파일)
    results = system.analyze_from_logs('logs')

    if not results:
        print("분석할 데이터가 없습니다.")
        return

    # 3. 결과 요약 출력
    system.print_summary(results)

    # 4. Excel 리포트 생성 (차트 포함)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_path = f"reports/keyword_analysis_{timestamp}.xlsx"

    excel_file = system.generate_excel_report(
        results,
        excel_path=excel_path,
        include_charts=True
    )

    # 5. 시각화 리포트 생성
    chart_files = system.generate_report(results, output_dir='charts')

    # 6. 급상승 키워드 모니터링 및 알림
    alert_result = system.monitor_and_alert_trending(
        results,
        recipients=[auth.get_email()]
    )

    # 7. 종합 리포트 이메일 발송
    if excel_file:
        # 이메일 본문 생성
        email_body = create_summary_email(results, alert_result)

        # 첨부파일
        attachments = [excel_file]
        attachments.extend(chart_files.values())

        # 이메일 발송
        email_notifier.send_email(
            to_email=auth.get_email(),
            subject=f"🔑 키워드 분석 리포트 - {datetime.now().strftime('%Y-%m-%d')}",
            body=email_body
        )

    print(f"\n✅ 분석 완료!")
    print(f"📊 Excel 리포트: {excel_file}")
    print(f"🔔 알림 발송: {alert_result['alerted']}개")

def create_summary_email(results, alert_result):
    """요약 이메일 본문 생성"""

    body = """
    <h2>🔑 키워드 분석 리포트</h2>

    <h3>📊 주요 통계</h3>
    <ul>
    """

    # 인기 키워드
    if 'hot_keywords' in results:
        body += "<li><b>상위 인기 키워드:</b><ul>"
        for keyword, freq in results['hot_keywords'][:5]:
            body += f"<li>{keyword}: {freq}회</li>"
        body += "</ul></li>"

    # 급상승 키워드
    if alert_result['alerted'] > 0:
        body += f"<li><b>급상승 키워드:</b> {alert_result['alerted']}개</li>"

    # 네트워크 통계
    if 'network' in results:
        import networkx as nx
        G = results['network']
        body += f"<li><b>네트워크:</b> {G.number_of_nodes()}개 노드, {G.number_of_edges()}개 엣지</li>"

    body += """
    </ul>

    <p>상세 분석 결과는 첨부파일을 확인하세요.</p>

    <hr>
    <p><small>이 메일은 키워드 분석 시스템이 자동으로 생성했습니다.</small></p>
    """

    return body

# 실행
if __name__ == "__main__":
    complete_keyword_analysis_pipeline()
```

### 실시간 키워드 모니터링

```python
import time
from keyword_trend_analyzer import KeywordTrendSystem
from keyword_trend_alert_system import KeywordAlertSystem

def real_time_keyword_monitoring(interval_minutes=60):
    """실시간 키워드 모니터링"""

    system = KeywordTrendSystem()
    alert_system = KeywordAlertSystem()

    print(f"실시간 키워드 모니터링 시작 (간격: {interval_minutes}분)")

    while True:
        try:
            # 최신 데이터 분석
            results = system.analyze_from_logs('logs')

            if results:
                # 급상승 키워드 탐지
                trend_df = results.get('trend_data', pd.DataFrame())
                growth_df = results.get('growth_data', pd.DataFrame())

                alert_result = alert_system.monitor_and_alert(
                    trend_df=trend_df,
                    growth_df=growth_df
                )

                if alert_result['detected'] > 0:
                    print(f"🔥 급상승 키워드 {alert_result['detected']}개 탐지!")
                    for kw in alert_result['keywords']:
                        print(f"   - {kw['keyword']}: {kw['trending_score']:.1f}점")

            # 대기
            print(f"\n다음 분석까지 {interval_minutes}분 대기...\n")
            time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n모니터링 중지")
            break
        except Exception as e:
            print(f"오류: {e}")
            time.sleep(60)  # 오류 시 1분 대기

# 실행
if __name__ == "__main__":
    real_time_keyword_monitoring(interval_minutes=30)
```

## ⚙️ 고급 설정

### 알림 시스템 설정

```python
from keyword_trend_alert_system import AlertConfig

config = AlertConfig()

# 급상승 기준
config.MIN_FREQUENCY_THRESHOLD = 10     # 최소 빈도
config.GROWTH_RATE_THRESHOLD = 100.0    # 성장률 100%
config.RANK_JUMP_THRESHOLD = 10         # 순위 10계급 상승
config.VOLATILITY_THRESHOLD = 3.0       # 변동성 계수

# 알림 설정
config.ALERT_COOLDOWN_MINUTES = 120     # 2시간 쿨다운
config.MAX_KEYWORDS_PER_ALERT = 15      # 최대 15개

# 점수 가중치
config.GROWTH_WEIGHT = 0.5              # 성장률 50%
config.FREQUENCY_WEIGHT = 0.2           # 빈도 20%
config.RANK_WEIGHT = 0.2                # 순위 20%
config.VOLATILITY_WEIGHT = 0.1          # 변동성 10%
```

### Excel 차트 설정

```python
from excel_chart_integration import ExcelChartConfig

config = ExcelChartConfig()

# 차트 크기
config.CHART_WIDTH = 20
config.CHART_HEIGHT = 12
config.CHART_DPI = 200

# 색상 테마
config.COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']

# 폰트
config.FONT_NAME = '나눔고딕'
config.TITLE_FONT_SIZE = 16
config.LABEL_FONT_SIZE = 11
```

## 📁 파일 구조

```
.
├── keyword_trend_analyzer.py          # 메인 분석 시스템
├── keyword_trend_alert_system.py      # 급상승 키워드 탐지 (신규)
├── excel_chart_integration.py         # Excel 차트 삽입 (신규)
├── test_advanced_features.py          # 고급 기능 테스트 (신규)
├── ADVANCED_FEATURES_GUIDE.md         # 이 가이드 (신규)
├── charts/                             # 차트 저장 디렉토리
├── alerts/                             # 알림 로그 디렉토리 (신규)
└── alert_history.json                 # 알림 히스토리 (신규)
```

## 🔧 문제 해결

### 1. 급상승 키워드가 탐지되지 않을 때

```python
# 기준 완화
config = AlertConfig()
config.GROWTH_RATE_THRESHOLD = 30.0  # 30%로 낮춤
config.MIN_FREQUENCY_THRESHOLD = 3   # 최소 3회

alert_system = KeywordAlertSystem(config=config)
```

### 2. Excel 차트가 삽입되지 않을 때

```python
# 데이터 확인
if not trend_df.empty:
    print("트렌드 데이터 있음")
else:
    print("트렌드 데이터 없음")

# 개별 삽입 시도
from excel_chart_integration import ExcelChartInserter
inserter = ExcelChartInserter()
success = inserter.insert_keyword_frequency_chart(
    "test.xlsx",
    [('키워드', 100)]
)
```

### 3. 이메일 발송 실패

```python
# 이메일 설정 확인
from email_notifier import EmailAuth
try:
    auth = EmailAuth()
    print("이메일 설정 완료")
except Exception as e:
    print(f"이메일 설정 오류: {e}")
    print("먼저 python email_example.py로 설정하세요")
```

## 💡 팁

1. **데이터 수집 주기**: 최소 1주일 이상의 데이터를 수집하세요
2. **알림 빈도**: 너무 잦은 알림을 피하기 위해 쿨다운을 설정하세요
3. **Excel 크기**: 차트가 많으면 파일이 커지니 필요한 차트만 선택하세요
4. **성능 최적화**: 대용량 데이터는 샘플링하여 분석하세요

---

*마지막 업데이트: 2026-04-25*
