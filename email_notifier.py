#!/usr/bin/env python3
"""
이메일 알림 시스템
Gmail SMTP를 활용한 이메일 자동 발송 기능을 제공합니다.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import json

from web_crawler import logger, Config
from email_template_manager import EmailTemplateManager, RecipientGroupManager


class EmailConfig:
    """이메일 설정"""

    # SMTP 설정
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    # 설정 파일 경로
    CONFIG_FILE: str = "email_config.json"

    # 기본 설정
    DEFAULT_ENCODING: str = "utf-8"


class EmailAuth:
    """이메일 인증 정보 관리"""

    def __init__(self, config_file: str = EmailConfig.CONFIG_FILE):
        """
        이메일 인증 정보 초기화

        Args:
            config_file: 설정 파일 경로
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """
        설정 파일에서 인증 정보 로드

        Returns:
            설정 딕셔너리
        """
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"이메일 설정 로드 완료: {self.config_file}")
                    return config
            except Exception as e:
                logger.error(f"설정 파일 로드 실패: {e}")
                return {}
        else:
            logger.warning(f"설정 파일 없음: {self.config_file}")
            return {}

    def save_config(self, email: str, app_password: str) -> bool:
        """
        이메일 인증 정보 저장

        Args:
            email: Gmail 주소
            app_password: Gmail 앱 비밀번호

        Returns:
            저장 성공 여부
        """
        try:
            config = {
                "email": email,
                "app_password": app_password,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self.config = config
            logger.info(f"이메일 설정 저장 완료: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
            return False

    def get_email(self) -> Optional[str]:
        """이메일 주소 반환"""
        return self.config.get("email")

    def get_app_password(self) -> Optional[str]:
        """앱 비밀번호 반환"""
        return self.config.get("app_password")

    def is_configured(self) -> bool:
        """설정 여부 확인"""
        return bool(self.config.get("email") and self.config.get("app_password"))

    def clear_config(self) -> bool:
        """설정 삭제"""
        try:
            if Path(self.config_file).exists():
                Path(self.config_file).unlink()
                self.config = {}
                logger.info("이메일 설정 삭제 완료")
                return True
            return False
        except Exception as e:
            logger.error(f"설정 삭제 실패: {e}")
            return False


class EmailNotifier:
    """이메일 알림 시스템"""

    def __init__(self, auth: Optional[EmailAuth] = None, use_templates: bool = True):
        """
        이메일 알림 시스템 초기화

        Args:
            auth: 이메일 인증 정보 (None인 경우 자동 생성)
            use_templates: HTML 템플릿 사용 여부
        """
        self.auth = auth or EmailAuth()
        self.smtp_server = EmailConfig.SMTP_SERVER
        self.smtp_port = EmailConfig.SMTP_PORT
        self.use_templates = use_templates

        # 템플릿 관리자 초기화
        if use_templates:
            try:
                self.template_manager = EmailTemplateManager()
                self.recipient_manager = RecipientGroupManager()
            except Exception as e:
                logger.warning(f"템플릿 시스템 초기화 실패: {e}")
                self.use_templates = False
                self.template_manager = None
                self.recipient_manager = None
        else:
            self.template_manager = None
            self.recipient_manager = None

        logger.info("이메일 알림 시스템 초기화")

    def _create_email_message(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        is_html: bool = False
    ) -> MIMEMultipart:
        """
        이메일 메시지 생성

        Args:
            from_email: 발신자 이메일
            to_email: 수신자 이메일
            subject: 이메일 제목
            body: 이메일 본문
            is_html: HTML 형식 여부

        Returns:
            이메일 메시지 객체
        """
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Date'] = formatdate(localtime=True)

        # 본문 추가
        content_type = 'html' if is_html else 'plain'
        msg.attach(MIMEText(body, content_type, _charset=EmailConfig.DEFAULT_ENCODING))

        return msg

    def _attach_file(self, msg: MIMEMultipart, file_path: str) -> bool:
        """
        이메일에 파일 첨부

        Args:
            msg: 이메일 메시지 객체
            file_path: 첨부할 파일 경로

        Returns:
            첨부 성공 여부
        """
        try:
            if not Path(file_path).exists():
                logger.error(f"파일 없음: {file_path}")
                return False

            with open(file_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=Path(file_path).name)

            part['Content-Disposition'] = f'attachment; filename="{Path(file_path).name}"'
            msg.attach(part)

            logger.info(f"파일 첨부 완료: {file_path}")
            return True
        except Exception as e:
            logger.error(f"파일 첨부 실패 ({file_path}): {e}")
            return False

    def _send_email(
        self,
        to_email: str,
        msg: MIMEMultipart
    ) -> bool:
        """
        이메일 전송

        Args:
            to_email: 수신자 이메일
            msg: 이메일 메시지 객체

        Returns:
            전송 성공 여부
        """
        if not self.auth.is_configured():
            logger.error("이메일 인증 정보 없음. 먼저 설정을 완료해주세요.")
            return False

        try:
            from_email = self.auth.get_email()
            app_password = self.auth.get_app_password()

            # SMTP 서버 연결
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS 보안 시작
                server.login(from_email, app_password)
                server.send_message(msg)

            logger.info(f"이메일 전송 완료: {to_email}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP 인증 실패. 이메일과 앱 비밀번호를 확인해주세요.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP 오류: {e}")
            return False
        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False
    ) -> bool:
        """
        이메일 전송

        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            body: 이메일 본문
            attachments: 첨부 파일 경로 리스트
            is_html: HTML 형식 여부

        Returns:
            전송 성공 여부
        """
        if not self.auth.is_configured():
            logger.error("이메일 인증 정보 없음. 먼저 설정을 완료해주세요.")
            return False

        from_email = self.auth.get_email()

        # 이메일 메시지 생성
        msg = self._create_email_message(from_email, to_email, subject, body, is_html)

        # 파일 첨부
        if attachments:
            for file_path in attachments:
                self._attach_file(msg, file_path)

        # 이메일 전송
        return self._send_email(to_email, msg)

    def send_crawling_report(
        self,
        to_email: str,
        keyword: str,
        data: List[Dict],
        excel_file: str,
        search_type: str = "Google News"
    ) -> bool:
        """
        크롤링 결과 리포트 전송

        Args:
            to_email: 수신자 이메일
            keyword: 검색 키워드
            data: 크롤링 데이터
            excel_file: Excel 파일 경로
            search_type: 검색 유형

        Returns:
            전송 성공 여부
        """
        # 현재 시간
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 이메일 제목
        subject = f"[크롤링 완료] '{keyword}' {search_type} 검색 결과 ({now})"

        # 이메일 본문 (HTML)
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px #ddd; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-item {{ text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
                .stat-label {{ font-size: 14px; color: #666; }}
                .footer {{ background-color: #f9f9f9; padding: 10px; text-align: center; font-size: 12px; color: #666; border: 1px #ddd; border-radius: 0 0 5px 5px; }}
                .attachment {{ background-color: #e3f2fd; padding: 15px; margin: 20px 0; border-left: 4px solid #2196F3; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #4CAF50; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🕷️ 웹 크롤링 완료 리포트</h2>
                    <p>{search_type} 검색 결과</p>
                </div>

                <div class="content">
                    <h3>📊 검색 개요</h3>
                    <table>
                        <tr>
                            <th>항목</th>
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
                            <td>{now}</td>
                        </tr>
                        <tr>
                            <td><strong>수집 항목 수</strong></td>
                            <td>{len(data)}개</td>
                        </tr>
                    </table>

                    <div class="attachment">
                        <p><strong>📎 첨부 파일:</strong></p>
                        <ul>
                            <li>{Path(excel_file).name} - 크롤링 결과 Excel 파일</li>
                        </ul>
                    </div>

                    <p>이 이메일은 웹 크롤러가 자동으로 생성했습니다.</p>
                </div>

                <div class="footer">
                    <p>© 2026 웹 크롤러 | 자동 발송된 이메일입니다. 회신하지 마세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 이메일 전송
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=[excel_file] if Path(excel_file).exists() else [],
            is_html=True
        )

    def send_multiple_keywords_report(
        self,
        to_email: str,
        results: Dict[str, List[Dict]],
        excel_file: str,
        search_type: str = "Google News"
    ) -> bool:
        """
        다중 키워드 크롤링 결과 리포트 전송

        Args:
            to_email: 수신자 이메일
            results: {키워드: 데이터} 딕셔너리
            excel_file: Excel 파일 경로
            search_type: 검색 유형

        Returns:
            전송 성공 여부
        """
        # 현재 시간
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 총 데이터 수 계산
        total_items = sum(len(data) for data in results.values())

        # 이메일 제목
        subject = f"[크롤링 완료] 다중 키워드 검색 결과 ({len(results)}개 키워드, {now})"

        # 키워드별 통계 테이블 생성
        keywords_table = ""
        for keyword, data in results.items():
            keywords_table += f"""
            <tr>
                <td>{keyword}</td>
                <td>{len(data)}개</td>
            </tr>
            """

        # 이메일 본문 (HTML)
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px #ddd; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
                .stat-item {{ text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .stat-label {{ font-size: 14px; color: #666; }}
                .footer {{ background-color: #f9f9f9; padding: 10px; text-align: center; font-size: 12px; color: #666; border: 1px #ddd; border-radius: 0 0 5px 5px; }}
                .attachment {{ background-color: #e3f2fd; padding: 15px; margin: 20px 0; border-left: 4px solid #2196F3; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #2196F3; color: white; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🕷️ 다중 키워드 크롤링 완료 리포트</h2>
                    <p>{search_type} 검색 결과</p>
                </div>

                <div class="content">
                    <div class="stats">
                        <div class="stat-item">
                            <div class="stat-value">{len(results)}</div>
                            <div class="stat-label">검색 키워드 수</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{total_items}</div>
                            <div class="stat-label">총 수집 항목 수</div>
                        </div>
                    </div>

                    <h3>📊 키워드별 검색 결과</h3>
                    <table>
                        <tr>
                            <th>키워드</th>
                            <th>수집 항목 수</th>
                        </tr>
                        {keywords_table}
                    </table>

                    <div class="attachment">
                        <p><strong>📎 첨부 파일:</strong></p>
                        <ul>
                            <li>{Path(excel_file).name} - 크롤링 결과 Excel 파일 (다중 시트)</li>
                        </ul>
                    </div>

                    <p><strong>검색 시간:</strong> {now}</p>
                    <p>이 이메일은 웹 크롤러가 자동으로 생성했습니다.</p>
                </div>

                <div class="footer">
                    <p>© 2026 웹 크롤러 | 자동 발송된 이메일입니다. 회신하지 마세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 이메일 전송
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            attachments=[excel_file] if Path(excel_file).exists() else [],
            is_html=True
        )

    def send_error_report(
        self,
        to_email: str,
        error_message: str,
        keyword: Optional[str] = None
    ) -> bool:
        """
        오류 리포트 전송

        Args:
            to_email: 수신자 이메일
            error_message: 오류 메시지
            keyword: 검색 키워드 (선택)

        Returns:
            전송 성공 여부
        """
        # 현재 시간
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 이메일 제목
        subject = f"[❌ 크롤링 오류] {keyword if keyword else '알 수 없는 키워드'} ({now})"

        # 이메일 본문 (HTML)
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px #ddd; }}
                .error-box {{ background-color: #ffebee; padding: 15px; margin: 20px 0; border-left: 4px solid #f44336; }}
                .footer {{ background-color: #f9f9f9; padding: 10px; text-align: center; font-size: 12px; color: #666; border: 1px #ddd; border-radius: 0 0 5px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>❌ 크롤링 오류 발생</h2>
                </div>

                <div class="content">
                    <p><strong>검색 키워드:</strong> {keyword if keyword else '알 수 없음'}</p>
                    <p><strong>발생 시간:</strong> {now}</p>

                    <div class="error-box">
                        <p><strong>오류 메시지:</strong></p>
                        <p>{error_message}</p>
                    </div>

                    <p>자세한 내용은 로그 파일을 확인해주세요.</p>
                </div>

                <div class="footer">
                    <p>© 2026 웹 크롤러 | 자동 발송된 이메일입니다. 회신하지 마세요.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # 이메일 전송
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=True
        )

    # ========== 템플릿 기반 이메일 발송 ==========

    def send_crawling_report_with_template(
        self,
        to_email: str,
        keyword: str,
        data: List[Dict],
        excel_file: str,
        search_type: str = "Google News",
        show_preview: bool = True
    ) -> bool:
        """
        템플릿 기반 크롤링 리포트 전송

        Args:
            to_email: 수신자 이메일
            keyword: 검색 키워드
            data: 크롤링 데이터
            excel_file: Excel 파일 경로
            search_type: 검색 유형
            show_preview: 데이터 미리보기 표시 여부

        Returns:
            전송 성공 여부
        """
        if not self.use_templates or not self.template_manager:
            # 템플릿을 사용하지 않는 경우 기존 방식으로 전환
            return self.send_crawling_report(to_email, keyword, data, excel_file, search_type)

        try:
            # 현재 시간
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 첨부 파일 리스트
            attachment_files = [excel_file] if Path(excel_file).exists() else []

            # 미리보기 데이터
            preview_data = data[:5] if show_preview and data else None

            # 템플릿 렌더링
            body = self.template_manager.render_crawling_report(
                keyword=keyword,
                search_type=search_type,
                item_count=len(data),
                timestamp=timestamp,
                attachment_files=attachment_files,
                preview_data=preview_data
            )

            # 이메일 제목
            subject = f"[크롤링 완료] '{keyword}' {search_type} 검색 결과 ({timestamp})"

            # 이메일 전송
            return self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachment_files,
                is_html=True
            )
        except Exception as e:
            logger.error(f"템플릿 기반 크롤링 리포트 전송 실패: {e}")
            # 실패 시 기존 방식으로 시도
            return self.send_crawling_report(to_email, keyword, data, excel_file, search_type)

    def send_multiple_keywords_report_with_template(
        self,
        to_email: str,
        results: Dict[str, List[Dict]],
        excel_file: str,
        search_type: str = "Google News"
    ) -> bool:
        """
        템플릿 기반 다중 키워드 리포트 전송

        Args:
            to_email: 수신자 이메일
            results: {키워드: 데이터} 딕셔너리
            excel_file: Excel 파일 경로
            search_type: 검색 유형

        Returns:
            전송 성공 여부
        """
        if not self.use_templates or not self.template_manager:
            return self.send_multiple_keywords_report(to_email, results, excel_file, search_type)

        try:
            # 현재 시간
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 키워드별 데이터 준비
            keywords_data = [
                {"keyword": kw, "count": len(data)}
                for kw, data in results.items()
            ]

            # 첨부 파일
            attachment_files = [excel_file] if Path(excel_file).exists() else []

            # 템플릿 렌더링
            body = self.template_manager.render_multiple_keywords_report(
                keywords_data=keywords_data,
                search_type=search_type,
                timestamp=timestamp,
                attachment_files=attachment_files
            )

            # 이메일 제목
            subject = f"[크롤링 완료] 다중 키워드 검색 결과 ({len(results)}개 키워드, {timestamp})"

            # 이메일 전송
            return self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachment_files,
                is_html=True
            )
        except Exception as e:
            logger.error(f"템플릿 기반 다중 키워드 리포트 전송 실패: {e}")
            return self.send_multiple_keywords_report(to_email, results, excel_file, search_type)

    def send_error_report_with_template(
        self,
        to_email: str,
        error_message: str,
        keyword: Optional[str] = None,
        error_type: str = "크롤링 오류"
    ) -> bool:
        """
        템플릿 기반 오류 리포트 전송

        Args:
            to_email: 수신자 이메일
            error_message: 오류 메시지
            keyword: 검색 키워드 (선택)
            error_type: 오류 유형

        Returns:
            전송 성공 여부
        """
        if not self.use_templates or not self.template_manager:
            return self.send_error_report(to_email, error_message, keyword)

        try:
            # 현재 시간
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 템플릿 렌더링
            body = self.template_manager.render_error_report(
                error_message=error_message,
                keyword=keyword,
                error_type=error_type,
                timestamp=timestamp
            )

            # 이메일 제목
            subject = f"[❌ {error_type}] {keyword if keyword else '알 수 없는 키워드'} ({timestamp})"

            # 이메일 전송
            return self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                is_html=True
            )
        except Exception as e:
            logger.error(f"템플릿 기반 오류 리포트 전송 실패: {e}")
            return self.send_error_report(to_email, error_message, keyword)

    def send_custom_email_with_template(
        self,
        to_email: str,
        subject: str,
        title: str,
        content: str,
        icon: str = "📧",
        subtitle: str = "",
        footer_text: str = "",
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        템플릿 기반 사용자 정의 이메일 전송

        Args:
            to_email: 수신자 이메일
            subject: 이메일 제목
            title: 이메일 내 제목
            content: 이메일 본문 (HTML)
            icon: 아이콘
            subtitle: 부제목
            footer_text: 푸터 텍스트
            attachments: 첨부 파일

        Returns:
            전송 성공 여부
        """
        if not self.use_templates or not self.template_manager:
            # 템플릿을 사용하지 않는 경우 기본 HTML 전송
            return self.send_email(to_email, subject, content, attachments, is_html=True)

        try:
            # 템플릿 렌더링
            body = self.template_manager.render_custom_email(
                title=title,
                content=content,
                icon=icon,
                subtitle=subtitle,
                footer_text=footer_text
            )

            # 이메일 전송
            return self.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments,
                is_html=True
            )
        except Exception as e:
            logger.error(f"템플릿 기반 사용자 정의 이메일 전송 실패: {e}")
            return self.send_email(to_email, subject, content, attachments, is_html=True)

    # ========== 대량 발송 기능 ==========

    def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False,
        delay: float = 1.0
    ) -> Dict[str, bool]:
        """
        대량 이메일 발송

        Args:
            recipients: 수신자 이메일 리스트
            subject: 이메일 제목
            body: 이메일 본문
            attachments: 첨부 파일
            is_html: HTML 형식 여부
            delay: 전송 지연 시간 (초) - 스팸 방지

        Returns:
            {이메일: 성공여부} 딕셔너리
        """
        import time

        results = {}
        total = len(recipients)
        success_count = 0

        logger.info(f"대량 이메일 발송 시작: {total}명")

        for idx, recipient in enumerate(recipients, 1):
            try:
                logger.info(f"이메일 전송 중... ({idx}/{total}): {recipient}")

                success = self.send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body,
                    attachments=attachments,
                    is_html=is_html
                )

                results[recipient] = success

                if success:
                    success_count += 1
                    logger.info(f"✅ 전송 성공: {recipient}")
                else:
                    logger.warning(f"❌ 전송 실패: {recipient}")

                # 지연 시간 (스팸 방지)
                if idx < total:
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"이메일 전송 오류 ({recipient}): {e}")
                results[recipient] = False

        # 결과 요약
        logger.info(f"대량 이메일 발송 완료: {success_count}/{total} 성공")

        return results

    def send_email_to_group(
        self,
        group_name: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        is_html: bool = False,
        delay: float = 1.0
    ) -> Dict[str, bool]:
        """
        그룹에 이메일 발송

        Args:
            group_name: 그룹명
            subject: 이메일 제목
            body: 이메일 본문
            attachments: 첨부 파일
            is_html: HTML 형식 여부
            delay: 전송 지연 시간 (초)

        Returns:
            {이메일: 성공여부} 딕셔너리
        """
        if not self.recipient_manager:
            logger.error("수신자 관리자가 초기화되지 않았습니다.")
            return {}

        recipients = self.recipient_manager.get_group_recipients(group_name)

        if not recipients:
            logger.warning(f"그룹 '{group_name}'에 수신자가 없습니다.")
            return {}

        logger.info(f"그룹 '{group_name}'에 이메일 발송: {len(recipients)}명")

        return self.send_bulk_email(
            recipients=recipients,
            subject=subject,
            body=body,
            attachments=attachments,
            is_html=is_html,
            delay=delay
        )

    def send_crawling_report_to_group(
        self,
        group_name: str,
        keyword: str,
        data: List[Dict],
        excel_file: str,
        search_type: str = "Google News",
        use_template: bool = True,
        delay: float = 2.0
    ) -> Dict[str, bool]:
        """
        그룹에 크롤링 리포트 발송

        Args:
            group_name: 그룹명
            keyword: 검색 키워드
            data: 크롤링 데이터
            excel_file: Excel 파일 경로
            search_type: 검색 유형
            use_template: 템플릿 사용 여부
            delay: 전송 지연 시간 (초)

        Returns:
            {이메일: 성공여부} 딕셔너리
        """
        if not self.recipient_manager:
            logger.error("수신자 관리자가 초기화되지 않았습니다.")
            return {}

        recipients = self.recipient_manager.get_group_recipients(group_name)

        if not recipients:
            logger.warning(f"그룹 '{group_name}'에 수신자가 없습니다.")
            return {}

        results = {}
        total = len(recipients)

        logger.info(f"그룹 '{group_name}'에 크롤링 리포트 발송: {total}명")

        for idx, recipient in enumerate(recipients, 1):
            try:
                logger.info(f"리포트 전송 중... ({idx}/{total}): {recipient}")

                if use_template:
                    success = self.send_crawling_report_with_template(
                        to_email=recipient,
                        keyword=keyword,
                        data=data,
                        excel_file=excel_file,
                        search_type=search_type
                    )
                else:
                    success = self.send_crawling_report(
                        to_email=recipient,
                        keyword=keyword,
                        data=data,
                        excel_file=excel_file,
                        search_type=search_type
                    )

                results[recipient] = success

                # 지연 시간
                if idx < total:
                    import time
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"리포트 전송 오류 ({recipient}): {e}")
                results[recipient] = False

        success_count = sum(1 for v in results.values() if v)
        logger.info(f"그룹 리포트 발송 완료: {success_count}/{total} 성공")

        return results

    # ========== 수신자 그룹 관리 기능 ==========

    def get_recipient_manager(self) -> Optional[RecipientGroupManager]:
        """수신자 관리자 반환"""
        return self.recipient_manager

    def list_recipient_groups(self) -> List[str]:
        """수신자 그룹 리스트 조회"""
        if self.recipient_manager:
            return self.recipient_manager.list_groups()
        return []

    def create_recipient_group(
        self,
        group_name: str,
        name: str,
        description: str = "",
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        수신자 그룹 생성

        Args:
            group_name: 그룹 ID (영문)
            name: 그룹 이름
            description: 그룹 설명
            recipients: 수신자 리스트

        Returns:
            생성 성공 여부
        """
        if self.recipient_manager:
            return self.recipient_manager.create_group(group_name, name, description, recipients)
        return False

    def add_recipient_to_group(self, group_name: str, email: str) -> bool:
        """그룹에 수신자 추가"""
        if self.recipient_manager:
            return self.recipient_manager.add_recipient_to_group(group_name, email)
        return False

    def remove_recipient_from_group(self, group_name: str, email: str) -> bool:
        """그룹에서 수신자 제거"""
        if self.recipient_manager:
            return self.recipient_manager.remove_recipient_from_group(group_name, email)
        return False

    def get_group_recipients(self, group_name: str) -> List[str]:
        """그룹 수신자 리스트 조회"""
        if self.recipient_manager:
            return self.recipient_manager.get_group_recipients(group_name)
        return []


def setup_email_config():
    """
    이메일 설정을 위한 대화형 설정 도구

    Returns:
        EmailAuth 객체
    """
    print("\n" + "=" * 60)
    print("📧 Gmail SMTP 설정")
    print("=" * 60)

    print("\nGmail SMTP를 사용하여 이메일을 전송합니다.")
    print("앱 비밀번호는 Google 계정 설정에서 생성해야 합니다.")
    print("\n📋 앱 비밀번호 생성 방법:")
    print("1. Google 계정에 로그인")
    print("2. [보안] 섹션으로 이동")
    print("3. [2단계 인증]이 활성화되어 있는지 확인")
    print("4. [앱 비밀번호] 섹션에서 새 앱 비밀번호 생성")
    print("5. [메일] 및 [Windows 컴퓨터] 선택 후 생성")
    print("6. 생성된 16자리 비밀번호를 복사\n")

    email = input("Gmail 주소를 입력하세요: ").strip()

    if not email.endswith("@gmail.com"):
        print("⚠️  Gmail 주소(@gmail.com)를 입력해주세요.")
        return None

    app_password = input("앱 비밀번호(16자리)를 입력하세요: ").strip()

    if len(app_password) != 16:
        print("⚠️  앱 비밀번호는 16자리여야 합니다.")
        return None

    # 설정 저장
    auth = EmailAuth()
    if auth.save_config(email, app_password):
        print("✅ 이메일 설정이 완료되었습니다.")
        print(f"   - 설정 파일: {EmailConfig.CONFIG_FILE}")

        # 테스트 이메일 전송 여부 확인
        test_email = input("\n테스트 이메일을 전송하시겠습니까? (y/n): ").strip().lower()
        if test_email == 'y':
            notifier = EmailNotifier(auth)
            success = notifier.send_email(
                to_email=email,
                subject="📧 테스트 이메일",
                body="이것은 웹 크롤러의 테스트 이메일입니다.\n\n이메일 설정이 성공적으로 완료되었습니다!"
            )
            if success:
                print("✅ 테스트 이메일 전송 완료!")
            else:
                print("❌ 테스트 이메일 전송 실패. 설정을 확인해주세요.")

        return auth
    else:
        print("❌ 설정 저장 실패")
        return None


if __name__ == "__main__":
    print("\n📧 이메일 알림 시스템 설정")
    print("=" * 60)

    auth = setup_email_config()

    if auth and auth.is_configured():
        print("\n✅ 이메일 알림 시스템이 준비되었습니다!")
        print(f"   발신자: {auth.get_email()}")
    else:
        print("\n❌ 설정이 완료되지 않았습니다.")
