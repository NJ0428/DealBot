# 🌐 DealBot 웹 인터페이스 사용 가이드

## 📋 개요

DealBot 웹 인터페이스는 간단한 웹 브라우저를 통해 크롤러 기능을 사용할 수 있는 Flask 기반 웹 애플리케이션입니다.

## ✨ 주요 기능

### 🔍 웹 검색
- **검색어 입력**: 원하는 키워드로 웹 검색 수행
- **검색 유형 선택**: 네이버 블로그, 구글, 다중 검색 지원
- **결과 수 조절**: 1~100개까지 결과 수 설정 가능

### 📥 결과 다운로드
- **Excel 형식**: .xlsx 파일로 다운로드
- **CSV 형식**: .csv 파일로 다운로드 (UTF-8 BOM)
- **자동 파일명**: 검색어_타임스탬프 형식

### 📊 결과 시각화
- **통계 요약**: 총 결과 수, 성공/실패 카운트
- **테이블 뷰**: 검색 결과를 테이블 형태로 표시
- **링크 제공**: 원본 페이지로 바로 이동

### 📋 검색 이력
- **파일 관리**: 이전 검색 결과 목록 확인
- **다시 다운로드**: 저장된 결과 파일 다시 다운로드
- **정보 표시**: 파일 크기, 생성일 정보 제공

## 🚀 시작 방법

### 1. 의존성 설치

```bash
pip install flask werkzeug
```

또는 모든 의존성 설치:

```bash
pip install -r requirements.txt
```

### 2. 웹 서버 시작

**Linux/Mac:**
```bash
chmod +x start_web.sh
./start_web.sh
```

**Windows:**
```bash
start_web.bat
```

**직접 실행:**
```bash
python web_interface.py
```

### 3. 웹 브라우저 접속

```
http://localhost:5000
```

## 📱 사용 방법

### 1. 검색하기

1. 메인 페이지에서 검색어 입력
2. 최대 결과 수 설정 (기본값: 20)
3. 검색 유형 선택:
   - **네이버 블로그**: 네이버 블로그 검색
   - **구글**: 구글 웹 검색
   - **다중 검색**: 여러 검색 엔진 동시 사용
4. "검색 시작" 버튼 클릭

### 2. 결과 확인

- 검색 결과가 자동으로 표시됩니다
- 상단에 통계 요약이 표시됩니다
- 결과 테이블에서 상세 정보를 확인할 수 있습니다

### 3. 다운로드

- **Excel 다운로드**: .xlsx 파일로 전체 결과 다운로드
- **CSV 다운로드**: .csv 파일로 데이터 다운로드

### 4. 이력 관리

- 상단 메뉴에서 "검색 이력" 클릭
- 이전 검색 결과 파일 목록 확인
- 필요한 파일 다시 다운로드

## 🛠️ 기술 스택

### 백엔드
- **Flask 3.0+**: 경량 웹 프레임워크
- **Pandas**: 데이터 처리
- **OpenPyXL**: Excel 파일 생성
- **BeautifulSoup4**: HTML 파싱

### 프론트엔드
- **HTML5/CSS3**: 반응형 디자인
- **JavaScript**: 동적 기능 (선택적)
- **Bootstrap 스타일**: 모던한 UI

## 📂 디렉토리 구조

```
DealBot/
├── web_interface.py          # 웹 인터페이스 메인 파일
├── templates/                # HTML 템플릿 폴더
│   ├── base.html            # 베이스 템플릿
│   ├── index.html           # 메인 페이지
│   ├── results.html         # 결과 페이지
│   └── history.html         # 이력 페이지
├── results/                  # 검색 결과 저장 폴더
├── downloads/                # 다운로드 폴더
└── uploads/                  # 업로드 폴더 (향후 확장용)
```

## 🔧 API 엔드포인트

### 웹 페이지
- `GET /`: 메인 페이지
- `POST /search`: 검색 처리
- `GET /download/<filename>`: 파일 다운로드
- `GET /download_csv/<filename>`: CSV 다운로드
- `GET /history`: 검색 이력

### REST API
- `POST /api/search`: AJAX 검색 API
  ```json
  {
    "keyword": "검색어",
    "max_results": 20,
    "search_type": "naver"
  }
  ```
- `GET /health`: 헬스체크

## 🎨 커스터마이징

### 색상 테마 변경

`web_interface.py`의 CSS 색상 수정:

```python
# 기본 색상
'--primary': '#667eea',
'--secondary': '#764ba2'
```

### 결과 제한 변경

```python
# 기본 최대 결과 수
DEFAULT_MAX_RESULTS: int = 50  # 기본값: 20
```

### 포트 변경

```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

## 🔒 보안 고려사항

### 배포 시 변경 필요:

1. **Secret Key 변경**:
```python
app.secret_key = 'your-secret-key-here'
```

2. **Debug Mode 비활성화**:
```python
app.run(debug=False)
```

3. **HTTPS 사용**: 프로덕션에서는 HTTPS 설정 필요

4. **인증 추가**: 사용자 인증 시스템 구현 권장

## 🐛 문제 해결

### 포트 충돌
```
Address already in use
```
**해결**: 다른 포트 사용
```python
app.run(port=8080)
```

### 템플릿 오류
```
TemplateNotFound
```
**해결**: 템플릿 폴더 확인
```bash
mkdir templates
```

### 의존성 오류
```
ModuleNotFoundError: No module named 'flask'
```
**해결**: Flask 설치
```bash
pip install flask
```

## 🚀 향후 개선 계획

- [ ] 사용자 인증 시스템
- [ ] 실시간 검색 (AJAX)
- [ ] 검색 결과 차트 시각화
- [ ] 키워드 알림 설정
- [ ] 배치 작업 스케줄링
- [ ] API 키 인증
- [ ] 데이터베이스 저장소 연동

## 📞 지원

문제가 발생하면:
1. 로그 확인: `logs/` 폴더
2. Flask 개발자 모드에서 에러 메시지 확인
3. 이슈 트래커에 버그 리포트

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다.

---

**마지막 업데이트**: 2024년 5월
**버전**: 1.0.0