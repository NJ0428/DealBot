#!/usr/bin/env python3
"""
이메일 템플릿 관리자
HTML 템플릿 로드 및 렌더링 기능을 제공합니다.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json


class EmailTemplateManager:
    """이메일 템플릿 관리자"""

    def __init__(self, template_dir: str = "email_templates"):
        """
        템플릿 관리자 초기화

        Args:
            template_dir: 템플릿 디렉토리 경로
        """
        self.template_dir = Path(template_dir)
        self.template_cache = {}

        # 템플릿 디렉토리 확인
        if not self.template_dir.exists():
            raise FileNotFoundError(f"템플릿 디렉토리 없음: {self.template_dir}")

    def _load_template(self, template_name: str) -> str:
        """
        템플릿 파일 로드

        Args:
            template_name: 템플릿 파일명

        Returns:
            템플릿 내용
        """
        template_path = self.template_dir / template_name

        # 캐시 확인
        if template_name in self.template_cache:
            return self.template_cache[template_name]

        # 파일 로드
        if not template_path.exists():
            raise FileNotFoundError(f"템플릿 파일 없음: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # 캐시 저장
        self.template_cache[template_name] = template_content

        return template_content

    def _render_template(self, template_content: str, context: Dict) -> str:
        """
        템플릿 렌더링 (간단한 치환 방식)

        Args:
            template_content: 템플릿 내용
            context: 렌더링 컨텍스트

        Returns:
            렌더링된 HTML
        """
        rendered = template_content

        # 간단한 변수 치환
        for key, value in context.items():
            placeholder = "{{ " + key + " }}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def render_crawling_report(
        self,
        keyword: str,
        search_type: str,
        item_count: int,
        timestamp: Optional[str] = None,
        attachment_files: Optional[List[str]] = None,
        preview_data: Optional[List[Dict]] = None
    ) -> str:
        """
        크롤링 리포트 템플릿 렌더링

        Args:
            keyword: 검색 키워드
            search_type: 검색 유형
            item_count: 수집 항목 수
            timestamp: 타임스탬프 (None인 경우 현재 시간 사용)
            attachment_files: 첨부 파일 리스트
            preview_data: 미리보기 데이터

        Returns:
            렌더링된 HTML
        """
        # 기본 템플릿 로드
        template_content = self._load_template("base_template.html")

        # 컨텍스트 설정
        context = {
            "icon": "🕷️",
            "title": "웹 크롤링 완료 리포트",
            "subtitle": f"{search_type} 검색 결과",
            "footer_text": "이 이메일은 웹 크롤러가 자동으로 생성했습니다."
        }

        # 컨텐츠 생성
        content_parts = []

        # 검색 개요 박스
        content_parts.append(f'''
        <div class="info-box">
            <h3 style="color: #667eea; margin-bottom: 15px;">📊 검색 개요</h3>
            <table class="data-table">
                <tr>
                    <th style="width: 30%;">항목</th>
                    <th>내용</th>
                </tr>
                <tr>
                    <td><strong>검색 키워드</strong></td>
                    <td>{keyword}</td>
                </tr>
                <tr>
                    <td><strong>검색 유형</strong></td>
                    <td>{search_type}</td>
                </tr>
                <tr>
                    <td><strong>검색 시간</strong></td>
                    <td>{timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                </tr>
                <tr>
                    <td><strong>수집 항목 수</strong></td>
                    <td><strong>{item_count}개</strong></td>
                </tr>
            </table>
        </div>
        ''')

        # 통계 카드
        content_parts.append(f'''
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{item_count}</div>
                <div class="stat-label">수집 항목</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-value">{len(keyword)}</div>
                <div class="stat-label">키워드 길이</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-value">100%</div>
                <div class="stat-label">완료율</div>
            </div>
        </div>
        ''')

        # 첨부 파일 박스
        if attachment_files:
            file_list = "".join([f"<li>{Path(f).name}</li>" for f in attachment_files])
            content_parts.append(f'''
            <div class="attachment-box">
                <h4>📎 첨부 파일</h4>
                <ul>
                    {file_list}
                </ul>
            </div>
            ''')

        # 미리보기 데이터
        if preview_data:
            preview_rows = ""
            for item in preview_data[:5]:  # 최대 5개
                title = item.get('제목', item.get('title', 'N/A'))
                source_date = item.get('출처/날짜', item.get('source_date', 'N/A'))
                preview_rows += f"""
                <tr>
                    <td>{title}</td>
                    <td>{source_date}</td>
                </tr>
                """

            content_parts.append(f'''
            <div class="info-box" style="background: linear-gradient(135deg, #fff5e6 0%, #ffe6cc 100%);">
                <h4 style="color: #e65100; margin-bottom: 15px;">📋 미리보기 (최대 5개)</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>제목</th>
                            <th>출처/날짜</th>
                        </tr>
                    </thead>
                    <tbody>
                        {preview_rows}
                    </tbody>
                </table>
            </div>
            ''')

        # 알림 박스
        content_parts.append('''
        <div class="alert-box alert-info">
            <h4 style="color: #1976d2; margin-bottom: 10px;">💡 알림</h4>
            <p>첨부된 Excel 파일에서 자세한 크롤링 결과를 확인하실 수 있습니다.</p>
        </div>
        ''')

        context["content"] = "".join(content_parts)

        # 템플릿 렌더링
        return self._render_template(template_content, context)

    def render_multiple_keywords_report(
        self,
        keywords_data: List[Dict],
        search_type: str,
        timestamp: Optional[str] = None,
        attachment_files: Optional[List[str]] = None
    ) -> str:
        """
        다중 키워드 리포트 템플릿 렌더링

        Args:
            keywords_data: 키워드별 데이터 리스트 [{"keyword": str, "count": int}, ...]
            search_type: 검색 유형
            timestamp: 타임스탬프
            attachment_files: 첨부 파일 리스트

        Returns:
            렌더링된 HTML
        """
        template_content = self._load_template("base_template.html")

        # 통계 계산
        keyword_count = len(keywords_data)
        total_items = sum(kw["count"] for kw in keywords_data)
        average_items = total_items / keyword_count if keyword_count > 0 else 0

        # 컨텍스트 설정
        context = {
            "icon": "🚀",
            "title": "다중 키워드 크롤링 완료",
            "subtitle": f"{search_type} 다중 검색 결과",
            "footer_text": "다중 키워드 크롤링이 완료되었습니다."
        }

        content_parts = []

        # 통계 카드
        content_parts.append(f'''
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-value">{keyword_count}</div>
                <div class="stat-label">검색 키워드 수</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-value">{total_items}</div>
                <div class="stat-label">총 수집 항목</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-value">{average_items:.1f}</div>
                <div class="stat-label">평균/키워드</div>
            </div>
        </div>
        ''')

        # 키워드별 테이블
        table_rows = ""
        for kw_data in keywords_data:
            count = kw_data["count"]
            percentage = (count / total_items * 100) if total_items > 0 else 0
            keyword = kw_data["keyword"]

            table_rows += f"""
            <tr>
                <td><strong>{keyword}</strong></td>
                <td>{count}개</td>
                <td>
                    <div style="background-color: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: {percentage}%;"></div>
                    </div>
                    <small>{percentage:.1f}%</small>
                </td>
            </tr>
            """

        content_parts.append(f'''
        <div class="info-box">
            <h3 style="color: #667eea; margin-bottom: 15px;">📊 키워드별 검색 결과</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th style="width: 40%;">키워드</th>
                        <th style="width: 30%;">수집 항목 수</th>
                        <th style="width: 30%;">비율</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        ''')

        # 타임스탬프
        content_parts.append(f'''
        <div class="alert-box alert-info">
            <h4 style="color: #1976d2; margin-bottom: 10px;">📅 검색 시간</h4>
            <p>{timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        ''')

        # 첨부 파일
        if attachment_files:
            file_list = "".join([f"<li>{Path(f).name}</li>" for f in attachment_files])
            content_parts.append(f'''
            <div class="attachment-box">
                <h4>📎 첨부 파일</h4>
                <ul>
                    {file_list}
                </ul>
                <p style="margin-top: 10px; font-size: 13px; color: #666;">
                    * Excel 파일의 각 시트에 키워드별 결과가 저장되어 있습니다.
                </p>
            </div>
            ''')

        context["content"] = "".join(content_parts)

        return self._render_template(template_content, context)

    def render_error_report(
        self,
        error_message: str,
        keyword: Optional[str] = None,
        error_type: str = "크롤링 오류",
        timestamp: Optional[str] = None
    ) -> str:
        """
        오류 리포트 템플릿 렌더링

        Args:
            error_message: 오류 메시지
            keyword: 검색 키워드
            error_type: 오류 유형
            timestamp: 타임스탬프

        Returns:
            렌더링된 HTML
        """
        template_content = self._load_template("base_template.html")

        context = {
            "icon": "❌",
            "title": "크롤링 오류 발생",
            "subtitle": "오류 리포트",
            "footer_text": "자세한 내용은 로그 파일을 확인해주세요."
        }

        content_parts = []

        # 오류 정보 박스
        content_parts.append(f'''
        <div class="alert-box alert-error">
            <h3 style="color: #d32f2f; margin-bottom: 15px;">⚠️ 오류 정보</h3>
            <table class="data-table">
                <tr>
                    <th style="width: 30%;">항목</th>
                    <th>내용</th>
                </tr>
                <tr>
                    <td><strong>검색 키워드</strong></td>
                    <td>{keyword or '알 수 없음'}</td>
                </tr>
                <tr>
                    <td><strong>발생 시간</strong></td>
                    <td>{timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td>
                </tr>
                <tr>
                    <td><strong>오류 유형</strong></td>
                    <td>{error_type}</td>
                </tr>
            </table>
        </div>
        ''')

        # 오류 메시지 박스
        content_parts.append(f'''
        <div class="info-box" style="background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);">
            <h3 style="color: #d32f2f; margin-bottom: 15px;">🔍 오류 메시지</h3>
            <div style="background-color: white; padding: 15px; border-radius: 4px; border-left: 4px solid #f44336; font-family: monospace; font-size: 13px; line-height: 1.8;">
                {error_message}
            </div>
        </div>
        ''')

        # 해결 방법
        content_parts.append('''
        <div class="alert-box alert-warning">
            <h4 style="color: #f57c00; margin-bottom: 10px;">📝 해결 방법</h4>
            <ul style="margin-left: 20px;">
                <li>인터넷 연결 상태를 확인해주세요.</li>
                <li>검색 키워드가 올바른지 확인해주세요.</li>
                <li>크롤링 대상 웹사이트가 접속 가능한지 확인해주세요.</li>
                <li>로그 파일에서 자세한 오류 정보를 확인해주세요.</li>
            </ul>
        </div>
        ''')

        # 버튼
        content_parts.append('''
        <div style="text-align: center; margin-top: 30px;">
            <a href="mailto:support@dealbot.com" class="btn">지원팀에 문의하기</a>
        </div>
        ''')

        context["content"] = "".join(content_parts)

        return self._render_template(template_content, context)

    def render_custom_email(
        self,
        title: str,
        content: str,
        icon: str = "📧",
        subtitle: str = "",
        footer_text: str = ""
    ) -> str:
        """
        사용자 정의 이메일 템플릿 렌더링

        Args:
            title: 이메일 제목
            content: 이메일 본문 (HTML)
            icon: 아이콘
            subtitle: 부제목
            footer_text: 푸터 텍스트

        Returns:
            렌더링된 HTML
        """
        template_content = self._load_template("base_template.html")

        context = {
            "icon": icon,
            "title": title,
            "subtitle": subtitle,
            "footer_text": footer_text,
            "content": content
        }

        return self._render_template(template_content, context)


class RecipientGroupManager:
    """수신자 그룹 관리자"""

    def __init__(self, config_file: str = "recipient_groups.json"):
        """
        수신자 그룹 관리자 초기화

        Args:
            config_file: 그룹 설정 파일 경로
        """
        self.config_file = Path(config_file)
        self.groups = self._load_groups()

    def _load_groups(self) -> Dict:
        """그룹 설정 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"그룹 설정 로드 실패: {e}")
                return {}
        else:
            # 기본 그룹 생성
            default_groups = {
                "default": {
                    "name": "기본 수신자",
                    "description": "기본 수신자 그룹",
                    "recipients": []
                },
                "admins": {
                    "name": "관리자",
                    "description": "시스템 관리자 그룹",
                    "recipients": []
                },
                "developers": {
                    "name": "개발팀",
                    "description": "개발팀 그룹",
                    "recipients": []
                }
            }
            self._save_groups(default_groups)
            return default_groups

    def _save_groups(self, groups: Dict) -> bool:
        """그룹 설정 저장"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(groups, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"그룹 설정 저장 실패: {e}")
            return False

    def list_groups(self) -> List[str]:
        """그룹 리스트 반환"""
        return list(self.groups.keys())

    def get_group_info(self, group_name: str) -> Optional[Dict]:
        """그룹 정보 조회"""
        return self.groups.get(group_name)

    def get_group_recipients(self, group_name: str) -> List[str]:
        """그룹 수신자 리스트 조회"""
        group = self.groups.get(group_name)
        if group:
            return group.get("recipients", [])
        return []

    def create_group(
        self,
        group_name: str,
        name: str,
        description: str = "",
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        새 그룹 생성

        Args:
            group_name: 그룹 ID (영문)
            name: 그룹 이름 (표시용)
            description: 그룹 설명
            recipients: 수신자 리스트

        Returns:
            생성 성공 여부
        """
        if group_name in self.groups:
            print(f"그룹 이미 존재함: {group_name}")
            return False

        self.groups[group_name] = {
            "name": name,
            "description": description,
            "recipients": recipients or []
        }

        return self._save_groups(self.groups)

    def add_recipient_to_group(self, group_name: str, email: str) -> bool:
        """
        그룹에 수신자 추가

        Args:
            group_name: 그룹명
            email: 수신자 이메일

        Returns:
            추가 성공 여부
        """
        if group_name not in self.groups:
            print(f"그룹 없음: {group_name}")
            return False

        recipients = self.groups[group_name]["recipients"]
        if email not in recipients:
            recipients.append(email)
            return self._save_groups(self.groups)

        return False

    def remove_recipient_from_group(self, group_name: str, email: str) -> bool:
        """
        그룹에서 수신자 제거

        Args:
            group_name: 그룹명
            email: 수신자 이메일

        Returns:
            제거 성공 여부
        """
        if group_name not in self.groups:
            print(f"그룹 없음: {group_name}")
            return False

        recipients = self.groups[group_name]["recipients"]
        if email in recipients:
            recipients.remove(email)
            return self._save_groups(self.groups)

        return False

    def delete_group(self, group_name: str) -> bool:
        """그룹 삭제"""
        if group_name in self.groups:
            del self.groups[group_name]
            return self._save_groups(self.groups)
        return False

    def update_group(
        self,
        group_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        그룹 정보 업데이트

        Args:
            group_name: 그룹명
            name: 새 그룹 이름
            description: 새 그룹 설명
            recipients: 새 수신자 리스트

        Returns:
            업데이트 성공 여부
        """
        if group_name not in self.groups:
            print(f"그룹 없음: {group_name}")
            return False

        group = self.groups[group_name]

        if name is not None:
            group["name"] = name
        if description is not None:
            group["description"] = description
        if recipients is not None:
            group["recipients"] = recipients

        return self._save_groups(self.groups)
