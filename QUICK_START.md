# 🚀 빠른 시작 가이드

## 1. 설치

```bash
pip install -r requirements.txt
```

## 2. 기본 사용

### 간단한 시각화 예시 실행

```bash
python simple_dashboard_example.py
```

이 예시는 다음 기능을 보여줍니다:
- ✅ 출처별 비율 파이차트 자동 생성
- ✅ HTML 대시보드 자동 생성 및 브라우저에서 바로 확인
- ✅ 모든 차트 한번에 생성 (막대그래프, 파이차트, 라인차트, 인터랙티브 차트)

### 직접 코드로 사용

```python
from web_crawler import WebCrawler, DataVisualizer, DataAnalyzer

# 1. 데이터 수집
crawler = WebCrawler(use_cache=True)
data = crawler.search_google_news("AI", max_results=20)

# 2. 시각화
visualizer = DataVisualizer()
analyzer = DataAnalyzer()

# 출처별 파이차트
source_counts = analyzer.analyze_by_source(data)
visualizer.create_pie_chart(source_counts, "출처별 비율")

# HTML 대시보드 (브라우저 자동 열기)
visualizer.create_dashboard(data, "AI 뉴스 분석", open_browser=True)

# 또는 모든 차트 한번에 생성
visualizer.generate_all_charts(data, "analysis", open_browser=True)
```

## 3. 생성된 파일 확인

### 차트 파일들
- `charts/` 디렉토리: PNG 차트 파일들
- `dashboard/` 디렉토리: HTML 대시보드 파일들

### 브라우저에서 확인
- HTML 대시보드 파일을 더블클릭하면 브라우저에서 열립니다
- 인터랙티브 차트들은 마우스로 데이터를 확인할 수 있습니다

## 4. 주요 기능

### 📊 파이차트
```python
visualizer.create_pie_chart(data, "제목", open_browser=False)
```

### 🎯 HTML 대시보드 (브라우저 자동 열기)
```python
visualizer.create_dashboard(data, "제목", open_browser=True)
```

### 📈 모든 차트 한번에
```python
all_charts = visualizer.generate_all_charts(data, "prefix", open_browser=True)
```

## 5. 참고사항

- `open_browser=True` 옵션을 사용하면 HTML 파일이 자동으로 브라우저에서 열립니다
- 모든 차트는 `charts/`와 `dashboard/` 디렉토리에 자동 저장됩니다
- 캐시를 사용하면 동일 키워드 검색 시 매우 빠릅니다

## 6. 더 많은 예시

```bash
python example_usage.py
```

10가지 다른 예시들을 체험해볼 수 있습니다!