"""
백업 알림 시스템

백업 및 복구 작업에 대한 알림을 제공합니다.
- 이메일 알림
- Slack 알림
- 웹훅 알림
- SMS 알림 (선택 사항)
- 알림 템플릿
- 알림 이력 관리
"""

import os
import json
import logging
import smtplib
import requests
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading


class NotificationType(Enum):
    """알림 타입"""
    BACKUP_SUCCESS = "backup_success"
    BACKUP_FAILED = "backup_failed"
    BACKUP_STARTED = "backup_started"
    RESTORE_SUCCESS = "restore_success"
    RESTORE_FAILED = "restore_failed"
    STORAGE_FULL = "storage_full"
    RETENTION_ALERT = "retention_alert"
    SYSTEM_ERROR = "system_error"
    WEEKLY_REPORT = "weekly_report"


class NotificationChannel(Enum):
    """알림 채널"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(Enum):
    """알림 우선순위"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationMessage:
    """알림 메시지"""
    notification_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    timestamp: str
    title: str
    message: str
    details: Dict = field(default_factory=dict)
    channels: List[NotificationChannel] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, sent, failed
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            'notification_id': self.notification_id,
            'notification_type': self.notification_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'channels': [c.value for c in self.channels],
            'recipients': self.recipients,
            'status': self.status,
            'error_message': self.error_message
        }


class EmailNotifier:
    """이메일 알림 매니저"""

    def __init__(self, smtp_server: str, smtp_port: int,
                 username: str, password: str,
                 from_email: str, use_tls: bool = True):
        """
        이메일 알림 매니저 초기화

        Args:
            smtp_server: SMTP 서버 주소
            smtp_port: SMTP 포트
            username: SMTP 사용자명
            password: SMTP 비밀번호
            from_email: 발신자 이메일
            use_tls: TLS 사용 여부
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls
        self.logger = logging.getLogger(__name__)

    def send_notification(self, notification: NotificationMessage) -> bool:
        """
        이메일 알림 발송

        Args:
            notification: 알림 메시지

        Returns:
            발송 성공 여부
        """
        try:
            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = notification.title
            msg['From'] = self.from_email
            msg['To'] = ', '.join(notification.recipients)

            # HTML 본문 생성
            html_body = self._generate_html_body(notification)
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP 연결 및 발송
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"이메일 발송 완료: {notification.notification_id}")
            return True

        except Exception as e:
            self.logger.error(f"이메일 발송 실패: {e}")
            return False

    def _generate_html_body(self, notification: NotificationMessage) -> str:
        """HTML 이메일 본문 생성"""
        priority_color = {
            NotificationPriority.LOW: "#6c757d",
            NotificationPriority.NORMAL: "#007bff",
            NotificationPriority.HIGH: "#ffc107",
            NotificationPriority.CRITICAL: "#dc3545"
        }

        color = priority_color.get(notification.priority, "#007bff")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f8f9fa; }}
                .details {{ background-color: white; padding: 15px; margin-top: 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{notification.title}</h2>
                </div>
                <div class="content">
                    <p>{notification.message}</p>
                </div>
                <div class="details">
                    <h3>상세 정보</h3>
                    <ul>
        """

        # 상세 정보 추가
        for key, value in notification.details.items():
            html += f"                        <li><strong>{key}:</strong> {value}</li>\n"

        html += f"""
                    </ul>
                    <p><strong>시간:</strong> {notification.timestamp}</p>
                    <p><strong>우선순위:</strong> {notification.priority.value}</p>
                </div>
                <div class="footer">
                    <p>이 알림은 데이터베이스 백업 시스템에서 자동으로 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


class SlackNotifier:
    """Slack 알림 매니저"""

    def __init__(self, webhook_url: str, channel: Optional[str] = None,
                 username: str = "Backup Bot", icon_emoji: str = ":floppy_disk:"):
        """
        Slack 알림 매니저 초기화

        Args:
            webhook_url: Slack 웹훅 URL
            channel: Slack 채널 (선택 사항)
            username: 봇 사용자명
            icon_emoji: 봇 아이콘 이모지
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji
        self.logger = logging.getLogger(__name__)

    def send_notification(self, notification: NotificationMessage) -> bool:
        """
        Slack 알림 발송

        Args:
            notification: 알림 메시지

        Returns:
            발송 성공 여부
        """
        try:
            # Slack 메시지 생성
            slack_message = self._generate_slack_message(notification)

            # 웹훅 발송
            response = requests.post(
                self.webhook_url,
                json=slack_message,
                headers={'Content-Type': 'application/json'}
            )

            response.raise_for_status()

            self.logger.info(f"Slack 알림 발송 완료: {notification.notification_id}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Slack 알림 발송 실패: {e}")
            return False

    def _generate_slack_message(self, notification: NotificationMessage) -> Dict:
        """Slack 메시지 생성"""
        # 색상 결정
        color_map = {
            NotificationPriority.LOW: "#6c757d",
            NotificationPriority.NORMAL: "#007bff",
            NotificationPriority.HIGH: "#ffc107",
            NotificationPriority.CRITICAL: "#dc3545"
        }

        color = color_map.get(notification.priority, "#007bff")

        # 기본 메시지
        message = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [
                {
                    "color": color,
                    "title": notification.title,
                    "text": notification.message,
                    "fields": [
                        {
                            "title": "우선순위",
                            "value": notification.priority.value,
                            "short": True
                        },
                        {
                            "title": "시간",
                            "value": notification.timestamp,
                            "short": True
                        }
                    ],
                    "footer": "Database Backup System",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }

        # 채널 지정 (선택 사항)
        if self.channel:
            message["channel"] = self.channel

        # 상세 정보 필드 추가
        if notification.details:
            fields = message["attachments"][0]["fields"]

            for key, value in notification.details.items():
                fields.append({
                    "title": key,
                    "value": str(value),
                    "short": True
                })

        return message


class WebhookNotifier:
    """웹훅 알림 매니저"""

    def __init__(self, webhook_url: str, headers: Optional[Dict] = None):
        """
        웹훅 알림 매니저 초기화

        Args:
            webhook_url: 웹훅 URL
            headers: 추가 HTTP 헤더
        """
        self.webhook_url = webhook_url
        self.headers = headers or {}
        self.logger = logging.getLogger(__name__)

    def send_notification(self, notification: NotificationMessage) -> bool:
        """
        웹훅 알림 발송

        Args:
            notification: 알림 메시지

        Returns:
            발송 성공 여부
        """
        try:
            # 웹훅 페이로드 생성
            payload = {
                "notification_id": notification.notification_id,
                "type": notification.notification_type.value,
                "priority": notification.priority.value,
                "timestamp": notification.timestamp,
                "title": notification.title,
                "message": notification.message,
                "details": notification.details
            }

            # 기본 헤더
            headers = {
                'Content-Type': 'application/json',
                **self.headers
            }

            # 웹훅 발송
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            self.logger.info(f"웹훅 알림 발송 완료: {notification.notification_id}")
            return True

        except requests.exceptions.RequestException as e:
            self.logger.error(f"웹훅 알림 발송 실패: {e}")
            return False


class BackupNotificationSystem:
    """백업 알림 시스템"""

    def __init__(self, config: Dict):
        """
        알림 시스템 초기화

        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

        # 알림 이력
        self.notification_history: List[NotificationMessage] = []

        # 메타데이터 파일
        self.history_file = Path(config.get('backup_dir', 'backups')) / 'notification_history.json'

        # 이력 로드
        self._load_history()

        # 알림 채널 초기화
        self.email_notifier: Optional[EmailNotifier] = None
        self.slack_notifier: Optional[SlackNotifier] = None
        self.webhook_notifier: Optional[WebhookNotifier] = None

        self._init_channels()

    def _init_channels(self):
        """알림 채널 초기화"""
        # 이메일 초기화
        email_config = self.config.get('email', {})
        if email_config.get('enabled', False):
            try:
                self.email_notifier = EmailNotifier(
                    smtp_server=email_config['smtp_server'],
                    smtp_port=email_config['smtp_port'],
                    username=email_config['username'],
                    password=email_config['password'],
                    from_email=email_config['from_email'],
                    use_tls=email_config.get('use_tls', True)
                )
                self.logger.info("이메일 알림 채널 초기화 완료")
            except Exception as e:
                self.logger.error(f"이메일 알림 채널 초기화 실패: {e}")

        # Slack 초기화
        slack_config = self.config.get('slack', {})
        if slack_config.get('enabled', False):
            try:
                self.slack_notifier = SlackNotifier(
                    webhook_url=slack_config['webhook_url'],
                    channel=slack_config.get('channel'),
                    username=slack_config.get('username', 'Backup Bot'),
                    icon_emoji=slack_config.get('icon_emoji', ':floppy_disk:')
                )
                self.logger.info("Slack 알림 채널 초기화 완료")
            except Exception as e:
                self.logger.error(f"Slack 알림 채널 초기화 실패: {e}")

        # 웹훅 초기화
        webhook_config = self.config.get('webhook', {})
        if webhook_config.get('enabled', False):
            try:
                self.webhook_notifier = WebhookNotifier(
                    webhook_url=webhook_config['url'],
                    headers=webhook_config.get('headers')
                )
                self.logger.info("웹훅 알림 채널 초기화 완료")
            except Exception as e:
                self.logger.error(f"웹훅 알림 채널 초기화 실패: {e}")

    def _load_history(self):
        """알림 이력 로드"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notification_history = [
                        NotificationMessage(
                            notification_id=item['notification_id'],
                            notification_type=NotificationType(item['notification_type']),
                            priority=NotificationPriority(item['priority']),
                            timestamp=item['timestamp'],
                            title=item['title'],
                            message=item['message'],
                            details=item.get('details', {}),
                            channels=[NotificationChannel(c) for c in item.get('channels', [])],
                            recipients=item.get('recipients', []),
                            status=item.get('status', 'pending'),
                            error_message=item.get('error_message')
                        )
                        for item in data
                    ]
                self.logger.info(f"로드된 알림 이력: {len(self.notification_history)}개")
            except Exception as e:
                self.logger.error(f"알림 이력 로드 실패: {e}")

    def _save_history(self):
        """알림 이력 저장"""
        try:
            data = [notification.to_dict() for notification in self.notification_history]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"알림 이력 저장 실패: {e}")

    def send_notification(self, notification_type: NotificationType,
                         title: str, message: str,
                         details: Optional[Dict] = None,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         channels: Optional[List[NotificationChannel]] = None,
                         recipients: Optional[List[str]] = None) -> str:
        """
        알림 발송

        Args:
            notification_type: 알림 타입
            title: 알림 제목
            message: 알림 메시지
            details: 상세 정보
            priority: 우선순위
            channels: 알림 채널 (None이면 설정된 모든 채널)
            recipients: 수신자 (None이면 설정된 수신자)

        Returns:
            알림 ID
        """
        with self._lock:
            # 알림 ID 생성
            notification_id = f"{notification_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 알림 채널 결정
            if channels is None:
                channels = []
                if self.email_notifier:
                    channels.append(NotificationChannel.EMAIL)
                if self.slack_notifier:
                    channels.append(NotificationChannel.SLACK)
                if self.webhook_notifier:
                    channels.append(NotificationChannel.WEBHOOK)

            # 수신자 결정
            if recipients is None:
                recipients = self.config.get('default_recipients', [])

            # 알림 메시지 생성
            notification = NotificationMessage(
                notification_id=notification_id,
                notification_type=notification_type,
                priority=priority,
                timestamp=datetime.now().isoformat(),
                title=title,
                message=message,
                details=details or {},
                channels=channels,
                recipients=recipients
            )

            # 알림 발송
            success_count = 0

            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL and self.email_notifier:
                        if self.email_notifier.send_notification(notification):
                            success_count += 1
                        else:
                            notification.error_message = "이메일 발송 실패"

                    elif channel == NotificationChannel.SLACK and self.slack_notifier:
                        if self.slack_notifier.send_notification(notification):
                            success_count += 1
                        else:
                            notification.error_message = "Slack 발송 실패"

                    elif channel == NotificationChannel.WEBHOOK and self.webhook_notifier:
                        if self.webhook_notifier.send_notification(notification):
                            success_count += 1
                        else:
                            notification.error_message = "웹훅 발송 실패"

                except Exception as e:
                    self.logger.error(f"{channel.value} 알림 발송 중 오류: {e}")

            # 상태 업데이트
            notification.status = "sent" if success_count > 0 else "failed"

            # 이력에 추가
            self.notification_history.append(notification)

            # 이력 저장
            self._save_history()

            # 이력 정리 (최근 1000개만 유지)
            if len(self.notification_history) > 1000:
                self.notification_history = self.notification_history[-1000:]
                self._save_history()

            self.logger.info(f"알림 발송 완료: {notification_id} "
                           f"(성공: {success_count}/{len(channels)})")

            return notification_id

    def notify_backup_success(self, backup_id: str, backup_type: str,
                              size_bytes: int, duration_seconds: float,
                              providers: Optional[List[str]] = None):
        """백업 성공 알림"""
        details = {
            '백업 ID': backup_id,
            '백업 타입': backup_type,
            '파일 크기': f"{size_bytes:,} bytes",
            '소요 시간': f"{duration_seconds:.2f}초"
        }

        if providers:
            details['클라우드 저장소'] = ', '.join(providers)

        self.send_notification(
            notification_type=NotificationType.BACKUP_SUCCESS,
            title="✅ 데이터베이스 백업 완료",
            message=f"데이터베이스 백업이 성공적으로 완료되었습니다.",
            details=details,
            priority=NotificationPriority.NORMAL
        )

    def notify_backup_failed(self, backup_type: str, error_message: str,
                             retry_count: int = 0):
        """백업 실패 알림"""
        details = {
            '백업 타입': backup_type,
            '오류 메시지': error_message,
            '재시도 횟수': retry_count
        }

        self.send_notification(
            notification_type=NotificationType.BACKUP_FAILED,
            title="❌ 데이터베이스 백업 실패",
            message=f"데이터베이스 백업이 실패했습니다.",
            details=details,
            priority=NotificationPriority.HIGH
        )

    def notify_restore_success(self, backup_id: str, restore_path: str,
                               safety_backup_id: Optional[str] = None):
        """복구 성공 알림"""
        details = {
            '백업 ID': backup_id,
            '복구 경로': restore_path
        }

        if safety_backup_id:
            details['안전 백업 ID'] = safety_backup_id

        self.send_notification(
            notification_type=NotificationType.RESTORE_SUCCESS,
            title="✅ 데이터베이스 복구 완료",
            message=f"데이터베이스 복구가 성공적으로 완료되었습니다.",
            details=details,
            priority=NotificationPriority.NORMAL
        )

    def notify_restore_failed(self, backup_id: str, error_message: str):
        """복구 실패 알림"""
        details = {
            '백업 ID': backup_id,
            '오류 메시지': error_message
        }

        self.send_notification(
            notification_type=NotificationType.RESTORE_FAILED,
            title="❌ 데이터베이스 복구 실패",
            message=f"데이터베이스 복구가 실패했습니다.",
            details=details,
            priority=NotificationPriority.CRITICAL
        )

    def notify_storage_full(self, provider: str, threshold_percent: float,
                           current_usage_percent: float):
        """저장소 용량 부족 알림"""
        details = {
            '제공자': provider,
            '임계값': f"{threshold_percent}%",
            '현재 사용량': f"{current_usage_percent}%"
        }

        self.send_notification(
            notification_type=NotificationType.STORAGE_FULL,
            title="⚠️ 저장소 용량 부족",
            message=f"클라우드 저장소 용량이 부족합니다.",
            details=details,
            priority=NotificationPriority.HIGH
        )

    def send_weekly_report(self, stats: Dict):
        """주간 보고서 발송"""
        # HTML 형식의 주간 보고서
        details = {
            '총 백업 수': stats.get('total_backups', 0),
            '전체 백업': stats.get('full_backups', 0),
            '증분 백업': stats.get('incremental_backups', 0),
            '총 크기': f"{stats.get('total_size_bytes', 0):,} bytes",
            '성공률': f"{stats.get('success_rate', 0):.1f}%"
        }

        self.send_notification(
            notification_type=NotificationType.WEEKLY_REPORT,
            title="📊 주간 백업 시스템 보고서",
            message="지난 주간 백업 시스템 활동 요약입니다.",
            details=details,
            priority=NotificationPriority.LOW
        )

    def get_notification_history(self, limit: int = 100) -> List[Dict]:
        """알림 이력 조회"""
        history = self.notification_history[-limit:]
        return [notification.to_dict() for notification in reversed(history)]

    def get_notification_stats(self) -> Dict:
        """알림 통계 조회"""
        total = len(self.notification_history)

        if total == 0:
            return {
                'total_notifications': 0,
                'by_type': {},
                'by_status': {},
                'by_channel': {}
            }

        by_type = {}
        by_status = {}
        by_channel = {}

        for notification in self.notification_history:
            # 타입별 통계
            ntype = notification.notification_type.value
            by_type[ntype] = by_type.get(ntype, 0) + 1

            # 상태별 통계
            status = notification.status
            by_status[status] = by_status.get(status, 0) + 1

            # 채널별 통계
            for channel in notification.channels:
                cname = channel.value
                by_channel[cname] = by_channel.get(cname, 0) + 1

        return {
            'total_notifications': total,
            'by_type': by_type,
            'by_status': by_status,
            'by_channel': by_channel
        }


def create_notification_config(
        email_enabled: bool = False,
        email_smtp: str = None,
        email_port: int = 587,
        email_user: str = None,
        email_password: str = None,
        email_from: str = None,
        slack_enabled: bool = False,
        slack_webhook: str = None,
        slack_channel: str = None,
        webhook_enabled: bool = False,
        webhook_url: str = None,
        default_recipients: List[str] = None,
        backup_dir: str = "backups"
) -> Dict:
    """
    알림 시스템 설정 생성

    Returns:
        설정 딕셔너리
    """
    config = {
        'backup_dir': backup_dir,
        'default_recipients': default_recipients or [],
        'email': {
            'enabled': email_enabled,
            'smtp_server': email_smtp or 'smtp.gmail.com',
            'smtp_port': email_port,
            'username': email_user or '',
            'password': email_password or '',
            'from_email': email_from or '',
            'use_tls': True
        },
        'slack': {
            'enabled': slack_enabled,
            'webhook_url': slack_webhook or '',
            'channel': slack_channel,
            'username': 'Backup Bot',
            'icon_emoji': ':floppy_disk:'
        },
        'webhook': {
            'enabled': webhook_enabled,
            'url': webhook_url or '',
            'headers': {}
        }
    }

    # 활성화된 채널 자동 감지
    if email_enabled and email_smtp and email_user and email_password:
        config['email']['enabled'] = True

    if slack_enabled and slack_webhook:
        config['slack']['enabled'] = True

    if webhook_enabled and webhook_url:
        config['webhook']['enabled'] = True

    return config