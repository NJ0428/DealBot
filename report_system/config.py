"""
리포트 시스템 설정 관리

ReportConfig 데이터클래스 및 설정 로드 기능을 제공합니다.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import pytz


@dataclass
class PDFSettings:
    """PDF 변환 설정"""
    converter: str = "weasyprint"
    page_size: str = "A4"
    margin: str = "20mm"
    orientation: str = "portrait"
    encoding: str = "UTF-8"
    compress: bool = True
    dpi: int = 300


@dataclass
class ReportTypeConfig:
    """리포트 타입별 설정"""
    enabled: bool = True
    schedule: str = "09:00"
    retention_days: int = 30
    include_sections: List[str] = field(default_factory=list)
    email_recipients: List[str] = field(default_factory=list)


@dataclass
class EmailNotificationConfig:
    """이메일 알림 설정"""
    enabled: bool = False
    recipients: List[str] = field(default_factory=list)
    subject_template: str = "Report: {report_type} - {date}"
    attach_pdf: bool = True


@dataclass
class GeneralConfig:
    """일반 설정"""
    output_dir: str = "reports"
    template_dir: str = "report_templates"
    default_language: str = "ko"
    timezone: str = "Asia/Seoul"


@dataclass
class ReportConfig:
    """리포트 시스템 전체 설정"""
    general: GeneralConfig = field(default_factory=GeneralConfig)
    pdf_settings: PDFSettings = field(default_factory=PDFSettings)
    report_types: Dict[str, ReportTypeConfig] = field(default_factory=dict)
    email_notification: EmailNotificationConfig = field(default_factory=EmailNotificationConfig)

    # 추가 설정
    debug_mode: bool = False
    log_level: str = "INFO"
    max_retries: int = 3
    timeout_seconds: int = 300

    def __post_init__(self):
        """설정 초기화 후 처리"""
        # 기본 리포트 타입 설정
        if not self.report_types:
            self.report_types = {
                "daily": ReportTypeConfig(
                    enabled=True,
                    schedule="09:00",
                    retention_days=30,
                    include_sections=[
                        "summary",
                        "top_keywords",
                        "sentiment_overview",
                        "recent_items",
                        "quick_stats"
                    ]
                ),
                "weekly": ReportTypeConfig(
                    enabled=True,
                    schedule="monday 09:00",
                    retention_days=90,
                    include_sections=[
                        "weekly_summary",
                        "keyword_trends",
                        "sentiment_analysis",
                        "growth_metrics",
                        "recommendations"
                    ]
                ),
                "monthly": ReportTypeConfig(
                    enabled=True,
                    schedule="1st 09:00",
                    retention_days=365,
                    include_sections=[
                        "monthly_overview",
                        "detailed_trends",
                        "comprehensive_analysis",
                        "yearly_comparison",
                        "strategic_insights"
                    ]
                )
            }

    @classmethod
    def from_json(cls, config_path: str) -> 'ReportConfig':
        """JSON 파일에서 설정 로드"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # 각 섹션 파싱
        general_data = config_data.get('general', {})
        pdf_data = config_data.get('pdf_settings', {})
        email_data = config_data.get('email_notification', {})
        report_types_data = config_data.get('report_types', {})

        # ReportTypeConfig 객체 생성
        report_types = {}
        for report_type, type_data in report_types_data.items():
            report_types[report_type] = ReportTypeConfig(
                enabled=type_data.get('enabled', True),
                schedule=type_data.get('schedule', '09:00'),
                retention_days=type_data.get('retention_days', 30),
                include_sections=type_data.get('include_sections', []),
                email_recipients=type_data.get('email_recipients', [])
            )

        return cls(
            general=GeneralConfig(**general_data),
            pdf_settings=PDFSettings(**pdf_data),
            report_types=report_types,
            email_notification=EmailNotificationConfig(**email_data),
            debug_mode=config_data.get('debug_mode', False),
            log_level=config_data.get('log_level', 'INFO'),
            max_retries=config_data.get('max_retries', 3),
            timeout_seconds=config_data.get('timeout_seconds', 300)
        )

    def to_json(self, output_path: str) -> None:
        """설정을 JSON 파일로 저장"""
        config_data = {
            'general': {
                'output_dir': self.general.output_dir,
                'template_dir': self.general.template_dir,
                'default_language': self.general.default_language,
                'timezone': self.general.timezone
            },
            'pdf_settings': {
                'converter': self.pdf_settings.converter,
                'page_size': self.pdf_settings.page_size,
                'margin': self.pdf_settings.margin,
                'orientation': self.pdf_settings.orientation,
                'encoding': self.pdf_settings.encoding,
                'compress': self.pdf_settings.compress,
                'dpi': self.pdf_settings.dpi
            },
            'report_types': {
                report_type: {
                    'enabled': config.enabled,
                    'schedule': config.schedule,
                    'retention_days': config.retention_days,
                    'include_sections': config.include_sections,
                    'email_recipients': config.email_recipients
                }
                for report_type, config in self.report_types.items()
            },
            'email_notification': {
                'enabled': self.email_notification.enabled,
                'recipients': self.email_notification.recipients,
                'subject_template': self.email_notification.subject_template,
                'attach_pdf': self.email_notification.attach_pdf
            },
            'debug_mode': self.debug_mode,
            'log_level': self.log_level,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def get_timezone(self) -> pytz.timezone:
        """타임존 객체 반환"""
        return pytz.timezone(self.general.timezone)

    def get_current_time(self) -> datetime:
        """현재 시간 반환 (설정된 타임존 기준)"""
        return datetime.now(self.get_timezone())

    def is_report_type_enabled(self, report_type: str) -> bool:
        """리포트 타입 활성화 여부 확인"""
        return self.report_types.get(report_type, ReportTypeConfig()).enabled

    def get_report_config(self, report_type: str) -> Optional[ReportTypeConfig]:
        """특정 리포트 타입 설정 반환"""
        return self.report_types.get(report_type)


class ReportParams:
    """리포트 생성 파라미터"""

    def __init__(
        self,
        report_type: str,
        date: Optional[datetime] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        keywords: Optional[List[str]] = None,
        include_sections: Optional[List[str]] = None,
        custom_data: Optional[Dict] = None
    ):
        self.report_type = report_type
        self.date = date or datetime.now()
        self.start_date = start_date
        self.end_date = end_date
        self.keywords = keywords or []
        self.include_sections = include_sections or []
        self.custom_data = custom_data or {}

    def validate(self) -> bool:
        """파라미터 유효성 검사"""
        if self.report_type not in ['daily', 'weekly', 'monthly', 'custom']:
            raise ValueError(f"잘못된 리포트 타입: {self.report_type}")

        if self.report_type == 'weekly' and (not self.start_date or not self.end_date):
            raise ValueError("주간 리포트는 시작일과 종료일이 필요합니다")

        if self.report_type == 'monthly' and not self.date:
            raise ValueError("월간 리포트는 날짜가 필요합니다")

        return True


def create_default_config(output_path: str = "report_config.json") -> ReportConfig:
    """기본 설정 파일 생성"""
    config = ReportConfig()
    config.to_json(output_path)
    return config