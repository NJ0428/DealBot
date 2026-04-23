# 이메일 템플릿 및 수신자 그룹 시스템 사용 가이드

## 📋 목차

1. [개요](#개요)
2. [HTML 템플릿 시스템](#html-템플릿-시스템)
3. [수신자 그룹 관리](#수신자-그룹-관리)
4. [대량 이메일 발송](#대량-이메일-발송)
5. [사용 예시](#사용-예시)
6. [테스트](#테스트)

---

## 개요

이메일 템플릿 및 수신자 그룹 시스템은 다음 기능을 제공합니다:

- 🎨 **예쁜 HTML 이메일 템플릿**: 반응형 디자인의 전문적인 이메일 템플릿
- 👥 **수신자 그룹 관리**: 팀/부서별로 수신자 그룹을 관리
- 📧 **대량 이메일 발송**: 여러 수신자에게 한 번에 이메일 발송
- 🎯 **그룹 타겟팅**: 특정 그룹에 크롤링 리포트 발송

---

## HTML 템플릿 시스템

### 템플릿 특징

- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원
- **그라데이션 색상**: 현대적인 비주얼 디자인
- **카드 레이아웃**: 통계 정보를 카드 형태로 표시
- **테이블 스타일**: 깔끔한 데이터 테이블
- **알림 박스**: 성공, 정보, 경고, 오류 메시지 스타일

### 제공되는 템플릿

1. **크롤링 리포트 템플릿** (`crawling_report_template.html`)
   - 검색 개요 테이블
   - 통계 카드 (수집 항목, 키워드 길이, 완료율)
   - 첨부 파일 박스
   - 데이터 미리보기 (최대 5개)

2. **다중 키워드 리포트 템플릿** (`multiple_keywords_template.html`)
   - 통계 카드 (키워드 수, 총 항목, 평균/키워드)
   - 키워드별 결과 테이블 (비율 그래프 포함)
   - 검색 시간 정보

3. **오류 리포트 템플릿** (`error_report_template.html`)
   - 오류 정보 테이블
   - 오류 메시지 박스
   - 해결 방법 안내
   - 지원팀 문의 버튼

4. **사용자 정의 템플릿** (`custom_notification_template.html`)
   - 자유로운 컨텐츠 구성

### 템플릿 사용 방법

#### 방법 1: EmailNotifier 클래스 사용 (권장)

```python
from email_notifier import EmailNotifier, EmailAuth

# 이메일 알림 시스템 초기화 (템플릿 사용)
auth = EmailAuth()
notifier = EmailNotifier(auth, use_templates=True)

# 템플릿 기반 크롤링 리포트 전송
notifier.send_crawling_report_with_template(
    to_email="recipient@example.com",
    keyword="인공지능",
    data=crawling_data,
    excel_file="result.xlsx",
    search_type="Google News"
)

# 템플릿 기반 다중 키워드 리포트 전송
notifier.send_multiple_keywords_report_with_template(
    to_email="recipient@example.com",
    results={"AI": ai_data, "블록체인": bc_data},
    excel_file="results.xlsx"
)

# 템플릿 기반 오류 리포트 전송
notifier.send_error_report_with_template(
    to_email="admin@example.com",
    error_message="연결 실패",
    keyword="test",
    error_type="네트워크 오류"
)

# 템플릿 기반 사용자 정의 이메일
notifier.send_custom_email_with_template(
    to_email="recipient@example.com",
    subject="주간 보고서",
    title="주간 크롤링 현황",
    content="<p>이번 주 총 100개의 뉴스를 수집했습니다.</p>",
    icon="📊",
    subtitle="2026년 4월 3주차",
    footer_text="더 자세한 내용은 첨부 파일을 확인하세요."
)
```

#### 방법 2: EmailTemplateManager 직접 사용

```python
from email_template_manager import EmailTemplateManager
from email_notifier import EmailNotifier

# 템플릿 관리자 초기화
template_manager = EmailTemplateManager()

# 크롤링 리포트 렌더링
html_content = template_manager.render_crawling_report(
    keyword="인공지능",
    search_type="Google News",
    item_count=50,
    timestamp="2026-04-22 10:00:00",
    attachment_files=["result.xlsx"],
    preview_data=data[:5]
)

# 이메일 전송
notifier = EmailNotifier()
notifier.send_email(
    to_email="recipient@example.com",
    subject="[크롤링 완료] 인공지능",
    body=html_content,
    is_html=True
)
```

---

## 수신자 그룹 관리

### 개요

수신자 그룹을 사용하여 팀/부서별로 수신자를 관리할 수 있습니다.

### 그룹 설정 파일

`recipient_groups.json` 파일에 그룹 정보가 저장됩니다:

```json
{
  "default": {
    "name": "기본 수신자",
    "description": "기본 수신자 그룹",
    "recipients": []
  },
  "admins": {
    "name": "관리자",
    "description": "시스템 관리자 그룹",
    "recipients": ["admin1@example.com", "admin2@example.com"]
  },
  "developers": {
    "name": "개발팀",
    "description": "개발팀 그룹",
    "recipients": ["dev1@example.com", "dev2@example.com"]
  },
  "marketing": {
    "name": "마케팅팀",
    "description": "마케팅 관련 크롤링 결과를 받는 팀",
    "recipients": ["marketing@example.com"]
  }
}
```

### 그룹 관리 방법

#### 방법 1: EmailNotifier 클래스 사용

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

# 그룹 생성
notifier.create_recipient_group(
    group_name="research",  # 영문 ID
    name="연구팀",            # 표시 이름
    description="연구/개발 관련 크롤링 결과를 받는 팀",
    recipients=["research1@example.com", "research2@example.com"]
)

# 그룹에 수신자 추가
notifier.add_recipient_to_group("research", "research3@example.com")

# 그룹에서 수신자 제거
notifier.remove_recipient_from_group("research", "research2@example.com")

# 그룹 리스트 조회
groups = notifier.list_recipient_groups()
print(groups)  # ['default', 'admins', 'developers', 'marketing', 'research']

# 그룹 수신자 리스트 조회
recipients = notifier.recipient_manager.get_group_recipients("research")
print(recipients)
```

#### 방법 2: RecipientGroupManager 직접 사용

```python
from email_template_manager import RecipientGroupManager

group_manager = RecipientGroupManager()

# 그룹 생성
group_manager.create_group(
    group_name="sales",
    name="영업팀",
    description="영업 관련 크롤링 결과를 받는 팀",
    recipients=["sales1@example.com"]
)

# 수신자 추가
group_manager.add_recipient_to_group("sales", "sales2@example.com")

# 그룹 정보 조회
info = group_manager.get_group_info("sales")
print(info)

# 수신자 리스트 조회
recipients = group_manager.get_group_recipients("sales")
print(recipients)

# 그룹 삭제
group_manager.delete_group("sales")
```

---

## 대량 이메일 발송

### 개요

여러 수신자에게 이메일을 한 번에 발송할 수 있습니다. 스팸 방지를 위해 전송 지연 기능이 포함되어 있습니다.

### 사용 방법

#### 1. 개별 수신자 리스트로 대량 발송

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth)

# 수신자 리스트
recipients = [
    "user1@example.com",
    "user2@example.com",
    "user3@example.com"
]

# 대량 이메일 발송
results = notifier.send_bulk_email(
    recipients=recipients,
    subject="📧 공지사항",
    body="<h2>중요 공지</h2><p>이번 주 시스템 점검이 있습니다.</p>",
    is_html=True,
    delay=2.0  # 각 발송 사이 2초 지연
)

# 결과 확인
for email, success in results.items():
    status = "성공" if success else "실패"
    print(f"{email}: {status}")
```

#### 2. 그룹에 대량 발송

```python
# 관리자 그룹에 이메일 발송
results = notifier.send_email_to_group(
    group_name="admins",
    subject="[긴급] 시스템 오류 발생",
    body="<h2>시스템 오류</h2><p>크롤링 시스템에 오류가 발생했습니다.</p>",
    is_html=True,
    delay=1.0
)

# 결과 확인
for email, success in results.items():
    status = "성공" if success else "실패"
    print(f"{email}: {status}")
```

#### 3. 그룹에 크롤링 리포트 발송

```python
# 연구팀에 크롤링 리포트 발송
results = notifier.send_crawling_report_to_group(
    group_name="research",
    keyword="AI",
    data=crawling_data,
    excel_file="ai_research.xlsx",
    search_type="Google News",
    use_template=True,  # 템플릿 사용
    delay=3.0  # 3초 지연
)

# 결과 확인
success_count = sum(1 for v in results.values() if v)
print(f"발송 완료: {success_count}/{len(results)}")
```

### 주의사항

1. **전송 지연 (delay)**: 스팸 방지를 위해 적절한 지연 시간을 설정하세요 (권장: 1-3초)
2. **수신자 수**: 너무 많은 수신자에게 한 번에 발송하는 것을 피하세요 (Gmail 일일 발송 한계: 500개)
3. **실패 처리**: 일부 수신자에게 전송이 실패해도 다른 수신자에게는 계속 발송됩니다

---

## 사용 예시

### 예시 1: 템플릿 기반 크롤링 완료 알림

```python
from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth

# 크롤러 초기화
crawler = WebCrawler(use_cache=True)
exporter = ExcelExporter()

# 이메일 초기화
auth = EmailAuth()
notifier = EmailNotifier(auth, use_templates=True)

# 크롤링 실행
keyword = "인공지능"
data = crawler.search_google_news(keyword, max_results=20)

# Excel 저장
excel_file = f"{keyword}_result.xlsx"
exporter.save_to_excel(data, excel_file, "뉴스")

# 템플릿 기반 이메일 전송
notifier.send_crawling_report_with_template(
    to_email=auth.get_email(),
    keyword=keyword,
    data=data,
    excel_file=excel_file,
    search_type="Google News",
    show_preview=True
)
```

### 예시 2: 다중 키워드 크롤링 후 팀별 리포트 발송

```python
from web_crawler import WebCrawler
from email_notifier import EmailNotifier, EmailAuth

# 크롤러 초기화
crawler = WebCrawler(use_cache=True)

# 이메일 초기화
auth = EmailAuth()
notifier = EmailNotifier(auth, use_templates=True)

# 수신자 그룹 설정
notifier.create_recipient_group(
    group_name="tech_team",
    name="기술팀",
    description="기술 트렌드 관련 크롤링 수신",
    recipients=["tech1@example.com", "tech2@example.com"]
)

# 다중 키워드 크롤링
keywords = ["AI", "블록체인", "메타버스"]
results = crawler.search_multiple_keywords(keywords, max_results=10)

# Excel 저장
from web_crawler import ExcelExporter
exporter = ExcelExporter()
all_data = {f"News_{k}": v for k, v in results.items()}
excel_file = "tech_trends.xlsx"
exporter.save_multiple_sheets(all_data, excel_file)

# 팀에 리포트 발송
notifier.send_crawling_report_to_group(
    group_name="tech_team",
    keyword=", ".join(keywords),
    data=sum(results.values(), []),  # 모든 데이터 병합
    excel_file=excel_file,
    search_type="Google News (다중 키워드)",
    use_template=True
)
```

### 예시 3: 오류 발생 시 관리자에게 알림

```python
from email_notifier import EmailNotifier, EmailAuth

auth = EmailAuth()
notifier = EmailNotifier(auth, use_templates=True)

try:
    # 크롤링 시도
    # ...
except Exception as e:
    # 오류 발생 시 관리자 그룹에 알림
    notifier.send_error_report_to_group(
        group_name="admins",
        error_message=str(e),
        keyword="test_keyword",
        error_type="크롤링 오류"
    )
```

---

## 테스트

### 테스트 스크립트 실행

```bash
python test_email_templates_and_groups.py
```

### 테스트 항목

1. **템플릿 관리자 테스트**
   - 크롤링 리포트 렌더링
   - 다중 키워드 리포트 렌더링
   - 오류 리포트 렌더링
   - HTML 파일 생성

2. **수신자 그룹 관리자 테스트**
   - 그룹 생성/조회/삭제
   - 수신자 추가/제거
   - 그룹 정보 조회

3. **이메일 알림 시스템 테스트 (템플릿 사용)**
   - 템플릿 기반 크롤링 리포트 전송

4. **대량 이메일 발송 테스트**
   - 여러 수신자에게 동시 전송

5. **그룹 이메일 발송 테스트**
   - 특정 그룹에 이메일 전송

### 생성되는 테스트 파일

- `test_crawling_report.html`: 크롤링 리포트 템플릿 예시
- `test_multiple_keywords_report.html`: 다중 키워드 리포트 템플릿 예시
- `test_error_report.html`: 오류 리포트 템플릿 예시

브라우저에서 이 파일들을 열어 템플릿 디자인을 확인할 수 있습니다.

---

## 💡 팁

1. **템플릿 커스터마이징**: `email_templates/` 디렉토리의 HTML 파일을 수정하여 디자인을 변경할 수 있습니다.
2. **수신자 관리**: `recipient_groups.json` 파일을 직접 편집하여 수신자를 관리할 수도 있습니다.
3. **발송 속도**: 수신자 수가 많을 경우 `delay` 값을 늘려 스팸으로 의심받는 것을 방지하세요.
4. **로그 확인**: 발송 실패 시 로그 파일에서 자세한 오류 정보를 확인하세요.

---

## 🆘 문제 해결

### 템플릿이 로드되지 않을 때

```
Error: 템플릿 디렉토리 없음: email_templates
```

**해결 방법**: `email_templates/` 디렉토리가 있는지 확인하세요.

### 수신자 그룹 설정이 로드되지 않을 때

```
Error: 그룹 설정 로드 실패
```

**해결 방법**: `recipient_groups.json` 파일이 올바른 JSON 형식인지 확인하세요.

### 이메일 전송이 실패할 때

```
Error: SMTP 인증 실패
```

**해결 방법**: Gmail 앱 비밀번호가 올바른지 확인하세요. 앱 비밀번호는 Google 계정 설정에서 생성해야 합니다.

---

## 📞 지원

문의사항이 있으면 다음을 통해 문의하세요:

- GitHub Issues: [https://github.com/your-repo/issues](https://github.com/your-repo/issues)
- 이메일: support@dealbot.com
