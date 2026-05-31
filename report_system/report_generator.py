"""
리포트 생성기 메인 모듈

모든 리포트 생성 기능을 조율하는 메인 클래스를 제공합니다.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from .config import ReportConfig, ReportParams
from .data_aggregator import DataAggregator
from .html_report_template import HTMLReportTemplate
from .pdf_converter import PDFConverter, get_pdf_filename, validate_pdf_path

logger = logging.getLogger(__name__)


class ReportGenerator:
    """리포트 생성기 메인 클래스"""

    def __init__(self, config: ReportConfig = None):
        """
        리포트 생성기 초기화

        Args:
            config: 리포트 설정
        """
        self.config = config or ReportConfig()
        self.template_manager = HTMLReportTemplate(
            template_dir=self.config.general.template_dir
        )
        self.pdf_converter = PDFConverter(self.config.pdf_settings)
        self.data_aggregator = DataAggregator(self.config.general.timezone)

        # 출력 디렉토리 설정
        self._setup_output_directories()

        logger.info("리포트 생성기 초기화 완료")

    def _setup_output_directories(self):
        """출력 디렉토리 설정"""
        base_dir = self.config.general.output_dir

        directories = [
            base_dir,
            os.path.join(base_dir, "daily"),
            os.path.join(base_dir, "weekly"),
            os.path.join(base_dir, "monthly"),
            os.path.join(base_dir, "archive"),
            os.path.join(base_dir, "logs")
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"디렉토리 생성/확인: {directory}")

    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """
        일일 요약 리포트 생성

        Args:
            date: 리포트 날짜 (None인 경우 오늘)

        Returns:
            생성 결과 정보
        """
        if date is None:
            date = self.config.get_current_time()

        logger.info(f"일일 리포트 생성 시작: {date.date()}")

        try:
            # 데이터 수집
            data = self.data_aggregator.get_daily_data(date)

            # HTML 렌더링
            html_content = self.template_manager.render_daily_summary(data)

            # PDF 변환
            filename = get_pdf_filename("daily", date)
            output_path = os.path.join(
                self.config.general.output_dir,
                "daily",
                filename
            )

            success = self.pdf_converter.convert_html_to_pdf(html_content, output_path)

            if success:
                logger.info(f"일일 리포트 생성 완료: {output_path}")

                # 메타데이터 저장
                self._save_report_metadata("daily", date, output_path, data)

                return {
                    'success': True,
                    'report_type': 'daily',
                    'date': date.isoformat(),
                    'output_path': output_path,
                    'filename': filename,
                    'size_bytes': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                    'data_summary': {
                        'total_items': len(data.keyword_data),
                        'sentiment_avg': data.sentiment_data.get('average_score', 0)
                    }
                }
            else:
                logger.error("일일 리포트 PDF 변환 실패")
                return {
                    'success': False,
                    'report_type': 'daily',
                    'error': 'PDF 변환 실패'
                }

        except Exception as e:
            logger.error(f"일일 리포트 생성 실패: {e}")
            return {
                'success': False,
                'report_type': 'daily',
                'error': str(e)
            }

    def generate_weekly_report(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """
        주간 분석 리포트 생성

        Args:
            start_date: 시작 날짜 (None인 경우 이번 주 월요일)
            end_date: 종료 날짜 (None인 경우 이번 주 일요일)

        Returns:
            생성 결과 정보
        """
        if start_date is None or end_date is None:
            start_date, end_date = self._get_week_range()

        logger.info(f"주간 리포트 생성 시작: {start_date.date()} ~ {end_date.date()}")

        try:
            # 데이터 수집
            data = self.data_aggregator.get_weekly_data(start_date, end_date)

            # HTML 렌더링
            html_content = self.template_manager.render_weekly_analysis(data)

            # PDF 변환
            filename = get_pdf_filename("weekly", start_date)
            output_path = os.path.join(
                self.config.general.output_dir,
                "weekly",
                filename
            )

            success = self.pdf_converter.convert_html_to_pdf(html_content, output_path)

            if success:
                logger.info(f"주간 리포트 생성 완료: {output_path}")

                # 메타데이터 저장
                self._save_report_metadata("weekly", start_date, output_path, data)

                return {
                    'success': True,
                    'report_type': 'weekly',
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'output_path': output_path,
                    'filename': filename,
                    'size_bytes': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                    'data_summary': {
                        'total_items': len(data.keyword_data),
                        'sentiment_avg': data.sentiment_data.get('average_score', 0),
                        'growth_rate': data.growth_metrics.get('growth_percentage', 0) if data.growth_metrics else 0
                    }
                }
            else:
                logger.error("주간 리포트 PDF 변환 실패")
                return {
                    'success': False,
                    'report_type': 'weekly',
                    'error': 'PDF 변환 실패'
                }

        except Exception as e:
            logger.error(f"주간 리포트 생성 실패: {e}")
            return {
                'success': False,
                'report_type': 'weekly',
                'error': str(e)
            }

    def generate_monthly_report(self, year: int = None, month: int = None) -> Dict[str, Any]:
        """
        월간 개요 리포트 생성

        Args:
            year: 연도 (None인 경우 현재 연도)
            month: 월 (None인 경우 현재 월)

        Returns:
            생성 결과 정보
        """
        if year is None or month is None:
            now = self.config.get_current_time()
            year = now.year
            month = now.month

        logger.info(f"월간 리포트 생성 시작: {year}년 {month}월")

        try:
            # 데이터 수집
            data = self.data_aggregator.get_monthly_data(year, month)

            # HTML 렌더링
            html_content = self.template_manager.render_monthly_overview(data)

            # PDF 변환
            report_date = datetime(year, month, 1)
            filename = get_pdf_filename("monthly", report_date)
            output_path = os.path.join(
                self.config.general.output_dir,
                "monthly",
                filename
            )

            success = self.pdf_converter.convert_html_to_pdf(html_content, output_path)

            if success:
                logger.info(f"월간 리포트 생성 완료: {output_path}")

                # 메타데이터 저장
                self._save_report_metadata("monthly", report_date, output_path, data)

                return {
                    'success': True,
                    'report_type': 'monthly',
                    'year': year,
                    'month': month,
                    'output_path': output_path,
                    'filename': filename,
                    'size_bytes': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                    'data_summary': {
                        'total_items': len(data.keyword_data),
                        'sentiment_avg': data.sentiment_data.get('average_score', 0),
                        'yoy_growth': data.custom_data.get('yearly_comparison', {}).get('yoy_growth', 0)
                    }
                }
            else:
                logger.error("월간 리포트 PDF 변환 실패")
                return {
                    'success': False,
                    'report_type': 'monthly',
                    'error': 'PDF 변환 실패'
                }

        except Exception as e:
            logger.error(f"월간 리포트 생성 실패: {e}")
            return {
                'success': False,
                'report_type': 'monthly',
                'error': str(e)
            }

    def generate_custom_report(self, params: ReportParams) -> Dict[str, Any]:
        """
        사용자 정의 리포트 생성

        Args:
            params: 리포트 파라미터

        Returns:
            생성 결과 정보
        """
        logger.info(f"사용자 정의 리포트 생성 시작: {params.report_type}")

        try:
            # 파라미터 유효성 검사
            params.validate()

            # 데이터 준비
            if params.custom_data:
                data = params.custom_data
            else:
                # 기본 데이터 수집
                if params.report_type == 'daily':
                    data = self.data_aggregator.get_daily_data(params.date)
                elif params.report_type == 'weekly':
                    data = self.data_aggregator.get_weekly_data(params.start_date, params.end_date)
                elif params.report_type == 'monthly':
                    data = self.data_aggregator.get_monthly_data(params.date.year, params.date.month)
                else:
                    data = {
                        'summary': {'period': {}},
                        'keyword_data': [],
                        'sentiment_data': {},
                        'custom_data': params.custom_data
                    }

            # HTML 렌더링
            template_name = params.custom_data.get('template_name', 'custom') if params.custom_data else 'custom'
            html_content = self.template_manager.render_custom_report(template_name, data)

            # PDF 변환
            filename = get_pdf_filename(params.report_type, params.date, "custom")
            output_path = os.path.join(
                self.config.general.output_dir,
                "archive",
                filename
            )

            success = self.pdf_converter.convert_html_to_pdf(html_content, output_path)

            if success:
                logger.info(f"사용자 정의 리포트 생성 완료: {output_path}")

                return {
                    'success': True,
                    'report_type': 'custom',
                    'output_path': output_path,
                    'filename': filename,
                    'size_bytes': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                    'params': {
                        'report_type': params.report_type,
                        'date': params.date.isoformat() if params.date else None,
                        'keywords': params.keywords,
                        'include_sections': params.include_sections
                    }
                }
            else:
                logger.error("사용자 정의 리포트 PDF 변환 실패")
                return {
                    'success': False,
                    'report_type': 'custom',
                    'error': 'PDF 변환 실패'
                }

        except ValueError as e:
            logger.error(f"파라미터 유효성 검사 실패: {e}")
            return {
                'success': False,
                'report_type': 'custom',
                'error': f'파라미터 오류: {str(e)}'
            }
        except Exception as e:
            logger.error(f"사용자 정의 리포트 생성 실패: {e}")
            return {
                'success': False,
                'report_type': 'custom',
                'error': str(e)
            }

    def generate_html_only(self, report_type: str, **kwargs) -> str:
        """
        HTML만 생성 (PDF 변환 없음)

        Args:
            report_type: 리포트 타입
            **kwargs: 리포트 파라미터

        Returns:
            HTML 내용
        """
        logger.info(f"HTML만 생성 시작: {report_type}")

        try:
            # 데이터 수집
            if report_type == 'daily':
                date = kwargs.get('date', self.config.get_current_time())
                data = self.data_aggregator.get_daily_data(date)
                html_content = self.template_manager.render_daily_summary(data)

            elif report_type == 'weekly':
                start_date = kwargs.get('start_date')
                end_date = kwargs.get('end_date')
                if not start_date or not end_date:
                    start_date, end_date = self._get_week_range()
                data = self.data_aggregator.get_weekly_data(start_date, end_date)
                html_content = self.template_manager.render_weekly_analysis(data)

            elif report_type == 'monthly':
                year = kwargs.get('year', self.config.get_current_time().year)
                month = kwargs.get('month', self.config.get_current_time().month)
                data = self.data_aggregator.get_monthly_data(year, month)
                html_content = self.template_manager.render_monthly_overview(data)

            else:
                raise ValueError(f"지원하지 않는 리포트 타입: {report_type}")

            logger.info(f"HTML 생성 완료: {report_type}")
            return html_content

        except Exception as e:
            logger.error(f"HTML 생성 실패: {e}")
            raise

    def get_report_history(self, report_type: str = None, limit: int = 10) -> list:
        """
        리포트 생성 이력 가져오기

        Args:
            report_type: 리포트 타입 필터 (None인 경우 전체)
            limit: 최대 개수

        Returns:
            리포트 정보 목록
        """
        history = []

        try:
            # 메타데이터 파일에서 읽기
            metadata_file = os.path.join(
                self.config.general.output_dir,
                "logs",
                "report_metadata.json"
            )

            if os.path.exists(metadata_file):
                import json
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)

                # 필터링
                if report_type:
                    history = [r for r in all_history if r.get('report_type') == report_type]
                else:
                    history = all_history

                # 정렬 및 제한
                history = sorted(history, key=lambda x: x.get('created_at', ''), reverse=True)[:limit]

        except Exception as e:
            logger.error(f"리포트 이력 가져오기 실패: {e}")

        return history

    def cleanup_old_reports(self, report_type: str = None) -> Dict[str, Any]:
        """
        오래된 리포트 정리

        Args:
            report_type: 리포트 타입 (None인 경우 전체)

        Returns:
            정리 결과 정보
        """
        logger.info("오래된 리포트 정리 시작")

        results = {
            'deleted': [],
            'failed': [],
            'freed_space': 0
        }

        try:
            # 대상 디렉토리 결정
            if report_type:
                directories = [os.path.join(self.config.general.output_dir, report_type)]
                retention_days = self.config.report_types.get(report_type, {}).retention_days
            else:
                directories = [
                    os.path.join(self.config.general.output_dir, "daily"),
                    os.path.join(self.config.general.output_dir, "weekly"),
                    os.path.join(self.config.general.output_dir, "monthly")
                ]
                retention_days = max(
                    config.retention_days
                    for config in self.config.report_types.values()
                )

            cutoff_time = datetime.now(pytz.timezone(self.config.general.timezone)) - timedelta(days=retention_days)

            for directory in directories:
                if not os.path.exists(directory):
                    continue

                for filename in os.listdir(directory):
                    if not filename.endswith('.pdf'):
                        continue

                    filepath = os.path.join(directory, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))

                    if file_time < cutoff_time:
                        try:
                            file_size = os.path.getsize(filepath)
                            os.remove(filepath)
                            results['deleted'].append(filename)
                            results['freed_space'] += file_size
                            logger.info(f"오래된 리포트 삭제: {filename}")
                        except Exception as e:
                            logger.error(f"리포트 삭제 실패: {filename} - {e}")
                            results['failed'].append(filename)

            logger.info(f"리포트 정리 완료: {len(results['deleted'])}개 삭제, {results['freed_space'] / 1024 / 1024:.2f}MB 확보")

        except Exception as e:
            logger.error(f"리포트 정리 실패: {e}")

        return results

    def _get_week_range(self) -> tuple:
        """이번 주의 월요일과 일요일 반환"""
        now = self.config.get_current_time()
        monday = now - timedelta(days=now.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = monday + timedelta(days=6)
        sunday = sunday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return monday, sunday

    def _save_report_metadata(self, report_type: str, date: datetime, output_path: str, data: Any):
        """리포트 메타데이터 저장"""
        try:
            metadata_file = os.path.join(
                self.config.general.output_dir,
                "logs",
                "report_metadata.json"
            )

            # 기존 메타데이터 로드
            existing_metadata = []
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    import json
                    existing_metadata = json.load(f)

            # 새 메타데이터 추가
            new_metadata = {
                'report_type': report_type,
                'date': date.isoformat(),
                'output_path': output_path,
                'created_at': datetime.now().isoformat(),
                'file_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                'data_summary': {
                    'keyword_count': len(data.keyword_data) if hasattr(data, 'keyword_data') else 0,
                    'sentiment_avg': data.sentiment_data.get('average_score', 0) if hasattr(data, 'sentiment_data') else 0
                }
            }

            existing_metadata.append(new_metadata)

            # 메타데이터 저장
            os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
            with open(metadata_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(existing_metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")


class ReportGenerationError(Exception):
    """리포트 생성 예외"""
    pass


def create_report_generator(config_path: str = None) -> ReportGenerator:
    """
    리포트 생성기 팩토리 함수

    Args:
        config_path: 설정 파일 경로 (None인 경우 기본 설정 사용)

    Returns:
        리포트 생성기 인스턴스
    """
    if config_path and os.path.exists(config_path):
        config = ReportConfig.from_json(config_path)
    else:
        config = ReportConfig()

    return ReportGenerator(config)