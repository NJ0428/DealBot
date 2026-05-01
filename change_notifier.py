#!/usr/bin/env python3
"""
변경사항 요약 알림 시스템
새로운 게시물이나 변경사항이 발생했을 때 요약하여 알림을 보냅니다.
"""

import logging
import smtplib
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
import requests
from jinja2 import Template


# 프로젝트 모듈 임포트
from feed_filter import FeedItem


# ============================================================================
# 설정 및 로깅
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# 데이터 모델
# ============================================================================

class NotificationChannel(Enum):
    """알림 채널"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"


@dataclass
class NotificationConfig:
    """알림 설정"""
    enabled: bool = True
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.CONSOLE])

    # 이메일 설정
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)

    # 웹훅 설정
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    # Slack 설정
    slack_webhook_url: str = ""
    slack_channel: str = ""

    # Telegram 설정
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # 알림 조건 설정
    min_items_for_notification: int = 1
    max_items_per_notification: int = 50
    summary_limit: int = 10  # 요약에 포함할 최대 아이템 수

    # 템플릿 설정
    email_template_path: str = ""
    webhook_template_path: str = ""


@dataclass
class NotificationSummary:
    """알림 요약"""
    subscription_name: str
    total_new_items: int
    items: List[FeedItem]
    timestamp: datetime = field(default_factory=datetime.now)
    keyword: str = ""
    categories: Dict[str, int] = field(default_factory=dict)

    def generate_summary_text(self, limit: int = 10) -> str:
        """요약 텍스트 생성"""
        lines = [
            f"구독: {self.subscription_name}",
            f"새로운 아이템: {self.total_new_items}개",
            f"시간: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        # 카테고리별 요약
        if self.categories:
            lines.append("카테고리별 분포:")
            for category, count in sorted(self.categories.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  - {category}: {count}개")
            lines.append("")

        # 주요 아이템
        items_to_show = self.items[:limit]
        lines.append(f"주요 {len(items_to_show)}개 아이템:")
        for i, item in enumerate(items_to_show, 1):
            lines.append(f"\n{i}. {item.title}")
            lines.append(f"   링크: {item.link}")
            if item.description:
                description = item.description[:100] + "..." if len(item.description) > 100 else item.description
                lines.append(f"   설명: {description}")
            if item.pub_date:
                lines.append(f"   날짜: {item.pub_date.strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(lines)

    def calculate_categories(self):
        """카테고리별 카운트 계산"""
        self.categories = {}
        for item in self.items:
            category = item.category or "미분류"
            self.categories[category] = self.categories.get(category, 0) + 1


@dataclass
class NotificationStats:
    """알림 통계"""
    total_notifications: int = 0
    email_notifications: int = 0
    webhook_notifications: int = 0
    console_notifications: int = 0
    slack_notifications: int = 0
    telegram_notifications: int = 0
    failed_notifications: int = 0
    last_notification_time: Optional[datetime] = None
    total_items_sent: int = 0


# ============================================================================
# 알림 전송자
# ============================================================================

class NotificationSender:
    """알림 전송자 기본 클래스"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """
        알림 전송

        Args:
            summary: 알림 요약
            config: 알림 설정

        Returns:
            전송 성공 여부
        """
        raise NotImplementedError


class EmailNotificationSender(NotificationSender):
    """이메일 알림 전송자"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """이메일 알림 전송"""
        try:
            if not config.email_to or not config.email_from:
                logger.warning("이메일 설정이 완료되지 않음")
                return False

            # 이메일 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{summary.subscription_name}] 새로운 {summary.total_new_items}개 아이템"
            msg['From'] = config.email_from
            msg['To'] = ', '.join(config.email_to)

            # HTML 본문 생성
            html_content = self._generate_html_content(summary, config)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # 텍스트 본문 생성
            text_content = summary.generate_summary_text(limit=config.summary_limit)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)

            # SMTP 연결 및 전송
            with smtplib.SMTP(config.email_smtp_host, config.email_smtp_port) as server:
                server.starttls()
                server.login(config.email_username, config.email_password)
                server.send_message(msg)

            logger.info(f"이메일 전송 성공: {config.email_to}")
            return True

        except Exception as e:
            logger.error(f"이메일 전송 실패: {e}")
            return False

    def _generate_html_content(self, summary: NotificationSummary, config: NotificationConfig) -> str:
        """HTML 이메일 내용 생성"""
        # 템플릿 로드
        if config.email_template_path and Path(config.email_template_path).exists():
            with open(config.email_template_path, 'r', encoding='utf-8') as f:
                template = Template(f.read())
        else:
            # 기본 템플릿
            template = Template(self._get_default_template())

        # HTML 생성
        items_data = [
            {
                'title': item.title,
                'link': item.link,
                'description': item.description[:200] + "..." if len(item.description) > 200 else item.description,
                'pub_date': item.pub_date.strftime('%Y-%m-%d %H:%M') if item.pub_date else '',
                'author': item.author,
                'category': item.category
            }
            for item in summary.items[:config.summary_limit]
        ]

        html_content = template.render(
            subscription_name=summary.subscription_name,
            total_items=summary.total_new_items,
            timestamp=summary.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            items=items_data,
            categories=summary.categories,
            keyword=summary.keyword
        )

        return html_content

    def _get_default_template(self) -> str:
        """기본 이메일 템플릿"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px 0; }
        .item { border-bottom: 1px solid #eee; padding: 15px 0; }
        .item:last-child { border-bottom: none; }
        .item-title { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .item-link { color: #4CAF50; text-decoration: none; }
        .item-description { color: #666; margin: 10px 0; }
        .item-meta { font-size: 12px; color: #999; }
        .categories { background: #f5f5f5; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; color: #999; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ subscription_name }} 새로운 아이템 알림</h1>
            <p>{{ total_items }}개의 새로운 아이템이 발견되었습니다</p>
            <p>{{ timestamp }}</p>
        </div>

        <div class="content">
            {% if categories %}
            <div class="categories">
                <h3>카테고리별 분포</h3>
                {% for category, count in categories.items() %}
                <span style="margin-right: 15px;">{{ category }}: {{ count }}개</span>
                {% endfor %}
            </div>
            {% endif %}

            <h2>주요 아이템</h2>
            {% for item in items %}
            <div class="item">
                <div class="item-title">
                    <a href="{{ item.link }}" class="item-link">{{ item.title }}</a>
                </div>
                {% if item.description %}
                <div class="item-description">{{ item.description }}</div>
                {% endif %}
                <div class="item-meta">
                    {% if item.pub_date %}날짜: {{ item.pub_date }}{% endif %}
                    {% if item.author %} | 작성자: {{ item.author }}{% endif %}
                    {% if item.category %} | 카테고리: {{ item.category }}{% endif %}
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="footer">
            <p>이 알림은 DealBot RSS 알림 시스템에서 자동으로 발송되었습니다.</p>
        </div>
    </div>
</body>
</html>
        '''


class WebhookNotificationSender(NotificationSender):
    """웹훅 알림 전송자"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """웹훅 알림 전송"""
        try:
            if not config.webhook_url:
                logger.warning("웹훅 URL이 설정되지 않음")
                return False

            # 페이로드 생성
            payload = {
                'subscription': summary.subscription_name,
                'total_items': summary.total_new_items,
                'timestamp': summary.timestamp.isoformat(),
                'keyword': summary.keyword,
                'categories': summary.categories,
                'items': [
                    {
                        'title': item.title,
                        'link': item.link,
                        'description': item.description[:200] + "..." if len(item.description) > 200 else item.description,
                        'pub_date': item.pub_date.isoformat() if item.pub_date else None,
                        'author': item.author,
                        'category': item.category
                    }
                    for item in summary.items[:config.summary_limit]
                ]
            }

            # 웹훅 전송
            response = requests.post(
                config.webhook_url,
                json=payload,
                headers=config.webhook_headers,
                timeout=30
            )

            response.raise_for_status()
            logger.info(f"웹훅 전송 성공: {config.webhook_url}")
            return True

        except Exception as e:
            logger.error(f"웹훅 전송 실패: {e}")
            return False


class SlackNotificationSender(NotificationSender):
    """Slack 알림 전송자"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """Slack 알림 전송"""
        try:
            if not config.slack_webhook_url:
                logger.warning("Slack 웹훅 URL이 설정되지 않음")
                return False

            # Slack 메시지 생성
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🔔 {summary.subscription_name} 새로운 아이템 알림"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*새로운 아이템:*\n{summary.total_new_items}개"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*시간:*\n{summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]

            # 카테고리 정보 추가
            if summary.categories:
                category_text = "\n".join([f"• {cat}: {count}개" for cat, count in summary.categories.items()])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*카테고리별 분포:*\n{category_text}"
                    }
                })

            # 아이템 정보 추가
            items_to_show = summary.items[:5]
            for item in items_to_show:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"• <{item.link}|{item.title}>"
                    }
                })

            if summary.total_new_items > 5:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"그 외 {summary.total_new_items - 5}개 아이템..."
                        }
                    ]
                })

            payload = {"blocks": blocks}

            # Slack 웹훅 전송
            response = requests.post(config.slack_webhook_url, json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"Slack 알림 전송 성공")
            return True

        except Exception as e:
            logger.error(f"Slack 알림 전송 실패: {e}")
            return False


class TelegramNotificationSender(NotificationSender):
    """Telegram 알림 전송자"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """Telegram 알림 전송"""
        try:
            if not config.telegram_bot_token or not config.telegram_chat_id:
                logger.warning("Telegram 설정이 완료되지 않음")
                return False

            # 메시지 생성
            message = f"🔔 *{summary.subscription_name} 새로운 아이템*\n\n"
            message += f"📊 새로운 아이템: {summary.total_new_items}개\n"
            message += f"⏰ 시간: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if summary.categories:
                message += "\n📁 카테고리별 분포:\n"
                for category, count in summary.categories.items():
                    message += f"  • {category}: {count}개\n"

            message += f"\n📝 주요 아이템:\n"
            for i, item in enumerate(summary.items[:10], 1):
                message += f"\n{i}. [{item.title}]({item.link})"
                if item.description:
                    description = item.description[:100] + "..." if len(item.description) > 100 else item.description
                    message += f"\n   {description}"

            # Telegram API 전송
            url = f"https://api.telegram.org/bot{config.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": config.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False
            }

            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            logger.info(f"Telegram 알림 전송 성공")
            return True

        except Exception as e:
            logger.error(f"Telegram 알림 전송 실패: {e}")
            return False


class ConsoleNotificationSender(NotificationSender):
    """콘솔 알림 전송자"""

    def send(self, summary: NotificationSummary, config: NotificationConfig) -> bool:
        """콘솔 알림 출력"""
        try:
            separator = "=" * 80
            print(f"\n{separator}")
            print(f"🔔 새로운 아이템 알림: {summary.subscription_name}")
            print(f"{separator}")
            print(f"새로운 아이템: {summary.total_new_items}개")
            print(f"시간: {summary.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

            if summary.categories:
                print(f"\n카테고리별 분포:")
                for category, count in summary.categories.items():
                    print(f"  - {category}: {count}개")

            print(f"\n주요 아이템 (최대 {config.summary_limit}개):")
            for i, item in enumerate(summary.items[:config.summary_limit], 1):
                print(f"\n{i}. {item.title}")
                print(f"   링크: {item.link}")
                if item.description:
                    description = item.description[:100] + "..." if len(item.description) > 100 else item.description
                    print(f"   설명: {description}")

            print(f"\n{separator}\n")

            logger.info(f"콘솔 알림 출력 완료")
            return True

        except Exception as e:
            logger.error(f"콘솔 알림 출력 실패: {e}")
            return False


# ============================================================================
# 알림 관리자
# ============================================================================

class ChangeNotifier:
    """변경사항 알림 관리자"""

    def __init__(self, config: NotificationConfig):
        """
        알림 관리자 초기화

        Args:
            config: 알림 설정
        """
        self.config = config
        self.stats = NotificationStats()

        # 전송자 초기화
        self.senders: Dict[NotificationChannel, NotificationSender] = {
            NotificationChannel.EMAIL: EmailNotificationSender(),
            NotificationChannel.WEBHOOK: WebhookNotificationSender(),
            NotificationChannel.CONSOLE: ConsoleNotificationSender(),
            NotificationChannel.SLACK: SlackNotificationSender(),
            NotificationChannel.TELEGRAM: TelegramNotificationSender()
        }

        logger.info("변경사항 알림 관리자 초기화 완료")

    def notify(self, summary: NotificationSummary) -> bool:
        """
        알림 전송

        Args:
            summary: 알림 요약

        Returns:
            전송 성공 여부 (하나 이상 성공 시 True)
        """
        if not self.config.enabled:
            logger.info("알림이 비활성화됨")
            return False

        # 알림 조건 확인
        if summary.total_new_items < self.config.min_items_for_notification:
            logger.info(f"알림 조건 미충족: {summary.total_new_items} < {self.config.min_items_for_notification}")
            return False

        # 아이템 수 제한
        if summary.total_new_items > self.config.max_items_per_notification:
            summary.items = summary.items[:self.config.max_items_per_notification]

        # 카테고리 계산
        summary.calculate_categories()

        # 각 채널로 전송
        success_count = 0
        for channel in self.config.channels:
            sender = self.senders.get(channel)
            if sender:
                try:
                    if sender.send(summary, self.config):
                        success_count += 1
                        self._update_stats(channel, True, len(summary.items))
                    else:
                        self._update_stats(channel, False, 0)
                except Exception as e:
                    logger.error(f"알림 전송 오류 ({channel}): {e}")
                    self._update_stats(channel, False, 0)

        # 통계 업데이트
        self.stats.total_notifications += 1
        self.stats.last_notification_time = datetime.now()
        self.stats.total_items_sent += len(summary.items)

        if success_count == 0:
            self.stats.failed_notifications += 1

        return success_count > 0

    def notify_items(self,
                    items: List[FeedItem],
                    subscription_name: str,
                    keyword: str = "") -> bool:
        """
        아이템 리스트로 알림 전송

        Args:
            items: 피드 아이템 리스트
            subscription_name: 구독 이름
            keyword: 키워드

        Returns:
            전송 성공 여부
        """
        if not items:
            return False

        summary = NotificationSummary(
            subscription_name=subscription_name,
            total_new_items=len(items),
            items=items,
            keyword=keyword
        )

        return self.notify(summary)

    def _update_stats(self, channel: NotificationChannel, success: bool, item_count: int):
        """통계 업데이트"""
        if success:
            if channel == NotificationChannel.EMAIL:
                self.stats.email_notifications += 1
            elif channel == NotificationChannel.WEBHOOK:
                self.stats.webhook_notifications += 1
            elif channel == NotificationChannel.CONSOLE:
                self.stats.console_notifications += 1
            elif channel == NotificationChannel.SLACK:
                self.stats.slack_notifications += 1
            elif channel == NotificationChannel.TELEGRAM:
                self.stats.telegram_notifications += 1
        else:
            self.stats.failed_notifications += 1

    def get_stats(self) -> Dict:
        """통계 조회"""
        return {
            'total_notifications': self.stats.total_notifications,
            'email_notifications': self.stats.email_notifications,
            'webhook_notifications': self.stats.webhook_notifications,
            'console_notifications': self.stats.console_notifications,
            'slack_notifications': self.stats.slack_notifications,
            'telegram_notifications': self.stats.telegram_notifications,
            'failed_notifications': self.stats.failed_notifications,
            'last_notification_time': self.stats.last_notification_time.isoformat() if self.stats.last_notification_time else None,
            'total_items_sent': self.stats.total_items_sent
        }

    def reset_stats(self):
        """통계 리셋"""
        self.stats = NotificationStats()


# ============================================================================
# 유틸리티 함수
# ============================================================================

def create_notifier_from_config(config_path: str) -> ChangeNotifier:
    """
    설정 파일로부터 알림 관리자 생성

    Args:
        config_path: 설정 파일 경로

    Returns:
        ChangeNotifier 인스턴스
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    config = NotificationConfig(**config_data)
    return ChangeNotifier(config)


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 테스트용 알림 설정
    config = NotificationConfig(
        enabled=True,
        channels=[NotificationChannel.CONSOLE],
        min_items_for_notification=1,
        summary_limit=5
    )

    # 알림 관리자 생성
    notifier = ChangeNotifier(config)

    # 테스트용 알림 요약 생성
    test_items = [
        FeedItem(
            title="AI 기술의 혁신",
            link="https://example.com/ai1",
            description="인공지능 기술이 새로운 전기를 맞이하고 있습니다.",
            pub_date=datetime.now(),
            author="테크미디어",
            category="기술"
        ),
        FeedItem(
            title="블록체인의 미래",
            link="https://example.com/blockchain1",
            description="블록체인 기술이 금융 산업을 변화시키고 있습니다.",
            pub_date=datetime.now(),
            author="코인뉴스",
            category="금융"
        )
    ]

    summary = NotificationSummary(
        subscription_name="테스트 구독",
        total_new_items=len(test_items),
        items=test_items,
        keyword="AI"
    )

    # 알림 전송 테스트
    print("알림 전송 테스트:")
    success = notifier.notify(summary)

    # 통계 확인
    print("\n알림 통계:")
    print(json.dumps(notifier.get_stats(), indent=2))

    print(f"\n알림 전송 {'성공' if success else '실패'}")
    print("\n✅ 테스트 완료!")