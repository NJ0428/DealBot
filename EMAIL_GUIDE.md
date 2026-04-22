# 📧 이메일 알림 시스템 사용 가이드

이 가이드는 Gmail SMTP를 활용한 이메일 알림 시스템의 설정과 사용법을 설명합니다.

## ✨ 주요 기능

- **Gmail SMTP 연동**: 안전하고 신뢰할 수 있는 Gmail SMTP 서버 사용
- **자동 리포트 생성**: 크롤링 완료 시 HTML 형식의 이쁜 리포트 자동 생성
- **Excel 파일 첨부**: 크롤링 결과 Excel 파일 자동 첨부
- **다중 수신자 지원**: 여러 수신자에게 동시 전송 가능
- **다중 첨부파일**: 여러 파일을 한 이메일에 첨부 가능
- **오류 알림**: 크롤링 실패 시 오류 리포트 자동 전송
- **안전한 인증**: 앱 비밀번호를 사용한 안전한 인증 방식

## 📦 설치

이메일 알림 시스템은 Python의 내장 라이브러리인 `smtplib`을 사용하므로 추가 패키지 설치가 필요 없습니다.

```bash
# 기존 의존성 설치
pip install -r requirements.txt
```

## 🚀 빠른 시작

### 1. 이메일 설정

먼저 Gmail SMTP를 사용하기 위한 설정을 완료해야 합니다.

#### 1-1. Gmail 앱 비밀번호 생성

1. [Google 계정](https://myaccount.google.com/)에 로그인
2. **[보안]** 섹션으로 이동
3. **[2단계 인증]**이 활성화되어 있는지 확인 (필수)
4. **[앱 비밀번호]** 섹션에서 새 앱 비밀번호 생성
5. **[메일]** 및 **[Windows 컴퓨터]** 선택 후 생성
6. 생성된 16자리 비밀번호를 복사 (공백 제외)

#### 1-2. 설정 스크립트 실행

```bash
# 설정 도구 실행
python email_example.py
```

**옵션 1: 이메일 설정**을 선택하고 안내에 따라 정보를 입력하세요.

```
실행할 예시를 선택하세요:
1. 이메일 설정
2. 이메일 설정 확인
3. 기본 검색 후 이메일 전송
...
선택 (0-8): 1
```

#### 1-3. 수동 설정 (선택사항)

`email_config.json` 파일을 직접 생성할 수도 있습니다:

```json
{
  "email": "your_email@gmail.com",
  "app_password": "your_16_char_app_password",
  "updated_at": "2026-04-20 00:00:00"
}
```

### 2. 기본 사용

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
    to_email=auth.get_email(),  # 수신자 이메일
    keyword=keyword,            # 검색 키워드
    data=data,                  # 크롤링 데이터
    excel_file=excel_file,      # 첨부할 Excel 파일
    search_type="Google News"   # 검색 유형
)

crawler.close()
```

## 📋 사용 예시

### 예시 1: 단일 키워드 크롤링 후 이메일 전송

```python
from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth

# 초기화
crawler = WebCrawler(use_cache=True)
exporter = ExcelExporter()
auth = EmailAuth()
notifier = EmailNotifier(auth)

# 검색 및 이메일 전송
keyword = "파이썬"
data = crawler.search_google_news(keyword, max_results=20)

if data:
    excel_file = f"{keyword}_news.xlsx"
    exporter.save_to_excel(data, excel_file)

    # 이메일 전송
    notifier.send_crawling_report(
        to_email=auth.get_email(),
        keyword=keyword,
        data=data,
        excel_file=excel_file
    )

crawler.close()
```

### 예시 2: 다중 키워드 검색 후 이메일 전송

```python
from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth

# 초기화
crawler = WebCrawler(use_cache=True)
exporter = ExcelExporter()
auth = EmailAuth()
notifier = EmailNotifier(auth)

# 다중 키워드 검색
keywords = ["AI", "블록체인", "메타버스"]
results = crawler.search_multiple_keywords(keywords, max_results=10)

# 다중 시트 Excel 저장
all_data = {f"News_{k}": v for k, v in results.items()}
excel_file = "tech_trends.xlsx"
exporter.save_multiple_sheets(all_data, excel_file)

# 이메일 전송
notifier.send_multiple_keywords_report(
    to_email=auth.get_email(),
    results=results,
    excel_file=excel_file
)

crawler.close()
```

### 예시 3: 필터링 검색 후 이메일 전송

```python
from web_crawler import WebCrawler, ExcelExporter, FilterCriteria
from email_notifier import EmailNotifier, EmailAuth
from datetime import datetime, timedelta

# 초기화
crawler = WebCrawler(use_cache=True)
exporter = ExcelExporter()
auth = EmailAuth()
notifier = EmailNotifier(auth)

# 필터 설정
filter_criteria = FilterCriteria(
    start_date=datetime.now() - timedelta(days=7),  # 최근 7일
    keywords_in_title={"파이썬", "Python"},
    min_title_length=10
)

# 필터링 검색
keyword = "파이썬"
data = crawler.search_google_news(
    keyword,
    max_results=20,
    filter_criteria=filter_criteria
)

if data:
    excel_file = f"{keyword}_filtered.xlsx"
    exporter.save_to_excel(data, excel_file)

    # 이메일 전송
    notifier.send_crawling_report(
        to_email=auth.get_email(),
        keyword=keyword,
        data=data,
        excel_file=excel_file,
        search_type="Google News (필터링)"
    )

crawler.close()
```

### 예시 4: 사용자 정의 이메일 전송

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

# 사용자 정의 이메일
subject = "📧 나만의 이메일 제목"
body = """
<html>
<body>
    <h2>안녕하세요!</h2>
    <p>이것은 사용자 정의 이메일입니다.</p>
</body>
</html>
"""

notifier.send_email(
    to_email="recipient@example.com",
    subject=subject,
    body=body,
    is_html=True
)
```

### 예시 5: 다중 첨부파일 이메일 전송

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

# 다중 첨부파일
notifier.send_email(
    to_email="recipient@example.com",
    subject="여러 파일 첨부",
    body="여러 파일을 첨부하여 보냅니다.",
    attachments=["file1.xlsx", "file2.xlsx", "file3.xlsx"]
)
```

### 예시 6: 오류 리포트 전송

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

try:
    # 크롤링 작업 수행
    crawler.search_google_news("키워드")
except Exception as e:
    # 오류 발생 시 이메일로 알림
    notifier.send_error_report(
        to_email=auth.get_email(),
        error_message=str(e),
        keyword="키워드"
    )
```

## 🔧 고급 기능

### 1. 여러 수신자에게 전송

```python
# 여러 수신자 지정
recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

for recipient in recipients:
    notifier.send_crawling_report(
        to_email=recipient,
        keyword=keyword,
        data=data,
        excel_file=excel_file
    )
```

### 2. 예약된 크롤링 및 이메일 전송

```python
import schedule
import time

def job():
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()
    auth = EmailAuth()
    notifier = EmailNotifier(auth)

    keyword = "뉴스"
    data = crawler.search_google_news(keyword, max_results=10)

    if data:
        excel_file = f"daily_{keyword}.xlsx"
        exporter.save_to_excel(data, excel_file)

        notifier.send_crawling_report(
            to_email=auth.get_email(),
            keyword=keyword,
            data=data,
            excel_file=excel_file
        )

    crawler.close()

# 매일 아침 9시에 실행
schedule.every().day.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 3. 이메일 템플릿 사용

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

def create_email_template(keyword, data_count):
    """사용자 정의 이메일 템플릿"""
    return f"""
    <html>
    <body>
        <h1>🔍 검색 결과 알림</h1>
        <p><strong>키워드:</strong> {keyword}</p>
        <p><strong>수집된 데이터:</strong> {data_count}개</p>
        <hr>
        <p>자동 생성된 이메일입니다.</p>
    </body>
    </html>
    """

# 템플릿 사용
notifier.send_email(
    to_email="recipient@example.com",
    subject=f"[검색 완료] {keyword}",
    body=create_email_template(keyword, len(data)),
    is_html=True
)
```

## 🔐 보안 및 개인정보

### 앱 비밀번호 저장

- 앱 비밀번호는 `email_config.json` 파일에 안전하게 저장됩니다.
- 이 파일은 `.gitignore`에 추가하여 Git에 커밋되지 않도록 해야 합니다.

### .gitignore 설정

```bash
# 이메일 설정 파일
email_config.json
```

### 권한 설정

```bash
# 설정 파일 접근 권한 제한 (Linux/Mac)
chmod 600 email_config.json
```

## 🐛 문제 해결

### 1. 인증 오류

**문제**: `SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')`

**해결방법**:
- Gmail 주소와 앱 비밀번호를 다시 확인
- 앱 비밀번호의 공백을 제거했는지 확인
- 2단계 인증이 활성화되어 있는지 확인

### 2. SMTP 연결 오류

**문제**: `smtplib.SMTPException: No suitable authentication method found.`

**해결방법**:
- 인터넷 연결 확인
- 방화벽 설정 확인 (포트 587)
- Gmail SMTP 서버 상태 확인

### 3. 이메일 전송 실패

**문제**: 이메일이 전송되지 않음

**해결방법**:
- 수신자 이메일 주소 확인
- 첨부파일 경로 확인
- 파일 크기 확인 (Gmail 첨부파일 제한: 25MB)

### 4. 첨부파일 없음

**문제**: 이메일에 첨부파일이 없음

**해결방법**:
```python
# 첨부파일 존재 여부 확인
from pathlib import Path

excel_file = "result.xlsx"
if Path(excel_file).exists():
    notifier.send_crawling_report(
        to_email=auth.get_email(),
        keyword=keyword,
        data=data,
        excel_file=excel_file
    )
else:
    print(f"파일 없음: {excel_file}")
```

## 📊 이메일 리포트 예시

### 1. 기본 크롤링 완료 리포트

```
제목: [크롤링 완료] '인공지능' Google News 검색 결과 (2026-04-20 10:30:00)

본문:
- 검색 키워드: 인공지능
- 검색 유형: Google News
- 검색 시간: 2026-04-20 10:30:00
- 수집 항목 수: 20개

첨부파일:
- 인공지능_result.xlsx
```

### 2. 다중 키워드 리포트

```
제목: [크롤링 완료] 다중 키워드 검색 결과 (3개 키워드, 2026-04-20 10:30:00)

본문:
- 검색 키워드 수: 3개
- 총 수집 항목 수: 30개

키워드별 결과:
- AI: 10개
- 블록체인: 10개
- 메타버스: 10개

첨부파일:
- tech_trends.xlsx (다중 시트)
```

## 🔄 자동화 스크립트 예시

### 매일 정기 크롤링 및 이메일 전송

```python
#!/usr/bin/env python3
"""
매일 정기 크롤링 및 이메일 전송 스크립트
"""

from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth
from datetime import datetime
import schedule
import time

def daily_crawling_job():
    """매일 크롤링 작업"""
    print(f"\n{'='*60}")
    print(f"📅 정기 크롤링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    try:
        # 크롤러 초기화
        crawler = WebCrawler(use_cache=True)
        exporter = ExcelExporter()
        auth = EmailAuth()
        notifier = EmailNotifier(auth)

        # 검색 키워드
        keywords = ["AI", "블록체인", "클라우드"]

        # 다중 키워드 검색
        results = crawler.search_multiple_keywords(keywords, max_results=10)

        # Excel 저장
        all_data = {f"News_{k}": v for k, v in results.items()}
        excel_file = f"daily_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        exporter.save_multiple_sheets(all_data, excel_file)

        # 이메일 전송
        notifier.send_multiple_keywords_report(
            to_email=auth.get_email(),
            results=results,
            excel_file=excel_file
        )

        print(f"✅ 정기 크롤링 완료")
        print(f"   - 검색 키워드: {', '.join(keywords)}")
        print(f"   - 총 수집 항목: {sum(len(v) for v in results.values())}개")
        print(f"   - 이메일 전송 완료")

        crawler.close()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        # 오류 리포트 전송
        auth = EmailAuth()
        notifier = EmailNotifier(auth)
        notifier.send_error_report(
            to_email=auth.get_email(),
            error_message=str(e),
            keyword=f"정기 크롤링 ({', '.join(keywords)})"
        )

if __name__ == "__main__":
    # 매일 아침 9시에 실행
    schedule.every().day.at("09:00").do(daily_crawling_job)

    print("📅 정기 크롤링 스케줄러가 시작되었습니다.")
    print("매일 아침 9시에 자동으로 크롤링을 수행합니다.")
    print("Ctrl+C를 누르면 종료합니다.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n스케줄러가 종료되었습니다.")
```

## 📝 추가 정보

### SMTP 설정

```python
from email_notifier import EmailConfig

# SMTP 설정 확인
smtp_server = EmailConfig.SMTP_SERVER  # smtp.gmail.com
smtp_port = EmailConfig.SMTP_PORT      # 587
```

### 이메일 설정 파일 위치

```python
from email_notifier import EmailConfig

config_file = EmailConfig.CONFIG_FILE  # email_config.json
```

## 🆘 지원 및 문의

이메일 알림 시스템 사용 중 문제가 발생하면:

1. 로그 파일 확인: `logs/crawler_YYYYMMDD.log`
2. 이메일 설정 파일 확인: `email_config.json`
3. Gmail 앱 비밀번호 재발급
4. 인터넷 연결 및 방화벽 확인

---

© 2026 웹 크롤러 이메일 알림 시스템
