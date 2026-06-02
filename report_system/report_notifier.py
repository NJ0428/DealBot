"""
리포트 알림 모듈

생성된 리포트를 이메일 등으로 전송하는 기능을 제공합니다.
"""

import os
import smtplib
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders

logger = logging.getLogger(__name__)


class ReportNotifier:
    """리포트 알림 클래스"""

    def __init__(self, config=None):
        """
        리포트 알림 초기화

        Args:
            config: 알림 설정
        """
        self.config = config or self._get_default_config()
        self.smtp_config = self._get_smtp_config()
        self.email_notifier = None
        self._initialize_email_notifier()

    def _get_default_config(self):
        """기본 설정 반환"""
        from .config import EmailNotificationConfig
        return EmailNotificationConfig()

    def _get_smtp_config(self) -> Dict[str, Any]:
        """SMTP 설정 가져오기"""
        return {
            'host': os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            'port': int(os.getenv('SMTP_PORT', '587')),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'email': os.getenv('EMAIL_ADDRESS', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'from_name': os.getenv('EMAIL_FROM_NAME', 'DealBot Report System')
        }

    def _initialize_email_notifier(self):
        """이메일 알림기 초기화"""
        if not self.config.enabled:
            logger.info("이메일 알림이 비활성화되어 있습니다.")
            return

        # 이메일 설정 확인
        if not self.smtp_config['email'] or not self.smtp_config['password']:
            logger.warning("이메일 계정 정보가 설정되지 않았습니다.")
            logger.warning("환경 변수 설정: EMAIL_ADDRESS, EMAIL_PASSWORD")
            return

        logger.info("이메일 알림기 초기화 완료")

    def send_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        이메일 전송

        Args:
            recipients: 수신자 목록
            subject: 이메일 제목
            body: 이메일 본문 (HTML)
            attachments: 첨부 파일 경로 목록

        Returns:
            전송 성공 여부
        """
        if not self.smtp_config['email'] or not self.smtp_config['password']:
            logger.error("SMTP 설정이 되지 않았습니다.")
            return False

        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['email']}>"
            msg['To'] = ', '.join(recipients)

            # HTML 본문 추가
            html_part = MIMEText(body, 'html', 'utf-8')
            msg.attach(html_part)

            # 첨부 파일 추가
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            file_data = f.read()

                        file_name = os.path.basename(file_path)

                        # 파일 타입 결정
                        if file_name.endswith('.pdf'):
                            mime_type = 'application'
                            subtype = 'pdf'
                        elif file_name.endswith('.png'):
                            mime_type = 'image'
                            subtype = 'png'
                        elif file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
                            mime_type = 'image'
                            subtype = 'jpeg'
                        else:
                            mime_type = 'application'
                            subtype = 'octet-stream'

                        part = MIMEBase(mime_type, subtype)
                        part.set_payload(file_data)
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{file_name}"'
                        )
                        msg.attach(part)
                        logger.info(f"첨부 파일 추가: {file_name}")
                    else:
                        logger.warning(f"첨부 파일을 찾을 수 없습니다: {file_path}")

            # SMTP 서버 연결 및 전송
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()

                server.login(self.smtp_config['email'], self.smtp_config['password'])
                server.send_message(msg)

            logger.info(f"이메일 전송 완료: {subject} -> {recipients}")
            return True

        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False

    def send_report_notification(
        self,
        report_result: Dict[str, Any],
        recipients: Optional[List[str]] = None,
        custom_message: Optional[str] = None
    ) -> bool:
        """
        리포트 알림 전송

        Args:
            report_result: 리포트 생성 결과
            recipients: 수신자 목록 (None인 경우 설정 사용)
            custom_message: 사용자 정의 메시지

        Returns:
            전송 성공 여부
        """
        if not self.config.enabled:
            logger.warning("이메일 알림이 비활성화되어 있습니다.")
            return False

        try:
            # 수신자 결정
            if recipients:
                final_recipients = recipients
            elif self.config.recipients:
                final_recipients = self.config.recipients
            else:
                logger.warning("수신자가 지정되지 않았습니다.")
                return False

            # 이메일 제목 생성
            subject = self._create_email_subject(report_result)

            # 이메일 본문 생성
            body = self._create_email_body(report_result, custom_message)

            # 첨부 파일 처리
            attachments = []
            if self.config.attach_pdf and report_result.get('output_path'):
                pdf_path = report_result['output_path']
                if os.path.exists(pdf_path):
                    attachments.append(pdf_path)
                else:
                    logger.warning(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")

            # 이메일 전송
            success = self.send_email(
                recipients=final_recipients,
                subject=subject,
                body=body,
                attachments=attachments
            )

            if success:
                logger.info(f"리포트 알림 전송 완료: {subject}")
                return True
            else:
                logger.error("리포트 알림 전송 실패")
                return False

        except Exception as e:
            logger.error(f"리포트 알림 전송 중 예외 발생: {e}")
            return False

    def send_report_batch_notification(
        self,
        report_results: List[Dict[str, Any]],
        recipients: Optional[List[str]] = None,
        summary_message: Optional[str] = None
    ) -> bool:
        """
        여러 리포트 알림 일괄 전송

        Args:
            report_results: 리포트 생성 결과 목록
            recipients: 수신자 목록 (None인 경우 설정 사용)
            summary_message: 요약 메시지

        Returns:
            전송 성공 여부
        """
        if not report_results:
            logger.warning("전송할 리포트가 없습니다.")
            return False

        try:
            # 수신자 결정
            if recipients:
                final_recipients = recipients
            elif self.config.recipients:
                final_recipients = self.config.recipients
            else:
                logger.warning("수신자가 지정되지 않았습니다.")
                return False

            # 이메일 제목
            success_count = sum(1 for r in report_results if r.get('success', False))
            subject = f"리포트 일괄 생성 완료: {success_count}/{len(report_results)}개 성공"

            # 이메일 본문
            body = self._create_batch_email_body(report_results, summary_message)

            # 첨부 파일 (성공한 리포트만)
            attachments = []
            if self.config.attach_pdf:
                for result in report_results:
                    if result.get('success') and result.get('output_path'):
                        pdf_path = result['output_path']
                        if os.path.exists(pdf_path):
                            attachments.append(pdf_path)

            # 이메일 전송
            success = self.send_email(
                recipients=final_recipients,
                subject=subject,
                body=body,
                attachments=attachments
            )

            if success:
                logger.info(f"리포트 일괄 알림 전송 완료: {len(report_results)}개 리포트")
                return True
            else:
                logger.error("리포트 일괄 알림 전송 실패")
                return False

        except Exception as e:
            logger.error(f"리포트 일괄 알림 전송 중 예외 발생: {e}")
            return False

    def send_error_notification(
        self,
        error_message: str,
        report_type: str,
        recipients: Optional[List[str]] = None
    ) -> bool:
        """
        오류 알림 전송

        Args:
            error_message: 오류 메시지
            report_type: 리포트 타입
            recipients: 수신자 목록 (None인 경우 설정 사용)

        Returns:
            전송 성공 여부
        """
        if not self.config.enabled:
            return False

        try:
            # 수신자 결정
            final_recipients = recipients or self.config.recipients
            if not final_recipients:
                return False

            # 이메일 제목 및 본문
            subject = f"[오류] {report_type} 리포트 생성 실패"
            body = f"""
            <h2>리포트 생성 오류</h2>
            <p><strong>리포트 타입:</strong> {report_type}</p>
            <p><strong>발생 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>오류 메시지:</strong></p>
            <pre>{error_message}</pre>
            <p>자동 리포트 시스템에서 오류가 발생했습니다. 관리자가 확인해 주시기 바랍니다.</p>
            """

            # 이메일 전송
            success = self.send_email(
                recipients=final_recipients,
                subject=subject,
                body=body
            )

            if success:
                logger.info(f"오류 알림 전송 완료: {report_type}")
                return True
            else:
                logger.error("오류 알림 전송 실패")
                return False

        except Exception as e:
            logger.error(f"오류 알림 전송 중 예외 발생: {e}")
            return False

    def _create_email_subject(self, report_result: Dict[str, Any]) -> str:
        """이메일 제목 생성"""
        report_type = report_result.get('report_type', 'report')
        date = report_result.get('date') or report_result.get('start_date') or report_result.get('created_at', '')

        if date:
            try:
                # ISO 형식 날짜 파싱
                from datetime import datetime
                if isinstance(date, str):
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    date_str = date_obj.strftime('%Y년 %m월 %d일')
                else:
                    date_str = str(date)
            except:
                date_str = str(date)
        else:
            date_str = datetime.now().strftime('%Y년 %m월 %d일')

        # 설정된 템플릿 사용 또는 기본 형식
        if self.config.subject_template:
            subject = self.config.subject_template.format(
                report_type=report_type,
                date=date_str
            )
        else:
            subject = f"리포트: {report_type} - {date_str}"

        return subject

    def _create_email_body(self, report_result: Dict[str, Any], custom_message: Optional[str] = None) -> str:
        """이메일 본문 생성"""
        report_type = report_result.get('report_type', 'report')
        success = report_result.get('success', False)

        if success:
            # 성공 메시지
            type_names = {
                'daily': '일일 요약',
                'weekly': '주간 분석',
                'monthly': '월간 개요',
                'custom': '사용자 정의'
            }
            type_name = type_names.get(report_type, report_type)

            body = f"""
            <h2>{type_name} 리포트 생성 완료</h2>
            <p><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>리포트 타입:</strong> {type_name}</p>

            """

            # 데이터 요약 추가
            if 'data_summary' in report_result:
                summary = report_result['data_summary']
                body += "<h3>데이터 요약</h3><ul>"

                for key, value in summary.items():
                    body += f"<li><strong>{key}:</strong> {value}</li>"
                body += "</ul>"

            # 파일 정보 추가
            if 'output_path' in report_result:
                body += f"<p><strong>파일 경로:</strong> {report_result['output_path']}</p>"

            if 'size_bytes' in report_result:
                size_mb = report_result['size_bytes'] / (1024 * 1024)
                body += f"<p><strong>파일 크기:</strong> {size_mb:.2f} MB</p>"

        else:
            # 실패 메시지
            body = f"""
            <h2>리포트 생성 실패</h2>
            <p><strong>리포트 타입:</strong> {report_type}</p>
            <p><strong>실패 사유:</strong> {report_result.get('error', '알 수 없는 오류')}</p>
            """

        # 사용자 정의 메시지 추가
        if custom_message:
            body += f"<h3>추가 메시지</h3><p>{custom_message}</p>"

        # 안내 문구
        body += """
        <hr>
        <p><em>이 리포트는 DealBot 자동 리포트 시스템에 의해 생성되었습니다.</em></p>
        <p><em>문의사항이 있으시면 관리자에게 연락해 주세요.</em></p>
        """

        return body

    def _create_batch_email_body(self, report_results: List[Dict[str, Any]], summary_message: Optional[str] = None) -> str:
        """일괄 전송용 이메일 본문 생성"""
        total = len(report_results)
        success_count = sum(1 for r in report_results if r.get('success', False))
        failed_count = total - success_count

        body = f"""
        <h2>리포트 일괄 생성 결과</h2>
        <p><strong>생성 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>전체 리포트:</strong> {total}개</p>
        <p><strong>성공:</strong> {success_count}개</p>
        <p><strong>실패:</strong> {failed_count}개</p>

        <h3>상세 결과</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>리포트 타입</th>
                <th>상태</th>
                <th>파일</th>
                <th>크기</th>
            </tr>
        """

        for result in report_results:
            report_type = result.get('report_type', 'unknown')
            success = result.get('success', False)
            output_path = result.get('output_path', '-')
            size_bytes = result.get('size_bytes', 0)

            if success:
                status = "✅ 성공"
                size_mb = f"{size_bytes / (1024 * 1024):.2f} MB"
            else:
                status = f"❌ 실패: {result.get('error', '알 수 없는 오류')}"
                size_mb = "-"

            body += f"""
            <tr>
                <td>{report_type}</td>
                <td>{status}</td>
                <td>{output_path}</td>
                <td>{size_mb}</td>
            </tr>
            """

        body += "</table>"

        # 요약 메시지 추가
        if summary_message:
            body += f"<h3>요약</h3><p>{summary_message}</p>"

        # 안내 문구
        body += """
        <hr>
        <p><em>이 리포트는 DealBot 자동 리포트 시스템에 의해 생성되었습니다.</em></p>
        """

        return body

    def send_test_email(self, recipient: str = None) -> bool:
        """
        테스트 이메일 전송

        Args:
            recipient: 수신자 (None인 경우 설정된 수신자 사용)

        Returns:
            전송 성공 여부
        """
        try:
            final_recipient = recipient or (self.config.recipients[0] if self.config.recipients else None)
            if not final_recipient:
                logger.error("수신자가 지정되지 않았습니다.")
                return False

            subject = "DealBot 리포트 시스템 테스트"
            body = f"""
            <h2>테스트 이메일</h2>
            <p>DealBot 자동 리포트 시스템이 정상적으로 작동하고 있습니다.</p>
            <p><strong>전송 시간:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>이 이메일을 받으셨다면 시스템이 정상적으로 구성된 것입니다.</p>
            """

            success = self.send_email(
                recipients=[final_recipient],
                subject=subject,
                body=body
            )

            if success:
                logger.info(f"테스트 이메일 전송 완료: {final_recipient}")
                return True
            else:
                logger.error("테스트 이메일 전송 실패")
                return False

        except Exception as e:
            logger.error(f"테스트 이메일 전송 중 예외 발생: {e}")
            return False


def create_report_notifier(config_path: str = None) -> ReportNotifier:
    """
    리포트 알림기 팩토리 함수

    Args:
        config_path: 설정 파일 경로 (None인 경우 기본 설정 사용)

    Returns:
        리포트 알림기 인스턴스
    """
    if config_path and os.path.exists(config_path):
        from .config import ReportConfig
        config = ReportConfig.from_json(config_path)
        notifier_config = config.email_notification
    else:
        notifier_config = None

    return ReportNotifier(notifier_config)