"""
리포트 시스템 테스트

리포트 생성, PDF 변환, 스케줄링 등의 기능을 테스트합니다.
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 테스트를 위해 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestReportConfig(unittest.TestCase):
    """설정 관리 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.temp_dir)

    def test_default_config(self):
        """기본 설정 테스트"""
        from report_system.config import ReportConfig

        config = ReportConfig()

        self.assertIsNotNone(config.general)
        self.assertIsNotNone(config.pdf_settings)
        self.assertIn("daily", config.report_types)
        self.assertIn("weekly", config.report_types)
        self.assertIn("monthly", config.report_types)

    def test_config_save_load(self):
        """설정 저장/로드 테스트"""
        from report_system.config import ReportConfig

        # 설정 생성 및 저장
        config = ReportConfig()
        config.general.output_dir = "test_output"
        config.to_json(self.config_file)

        # 설정 로드
        loaded_config = ReportConfig.from_json(self.config_file)

        self.assertEqual(loaded_config.general.output_dir, "test_output")
        self.assertEqual(loaded_config.general.timezone, config.general.timezone)

    def test_report_type_config(self):
        """리포트 타입 설정 테스트"""
        from report_system.config import ReportConfig, ReportTypeConfig

        config = ReportConfig()
        daily_config = config.get_report_config("daily")

        self.assertIsInstance(daily_config, ReportTypeConfig)
        self.assertTrue(daily_config.enabled)
        self.assertEqual(daily_config.schedule, "09:00")


class TestDataAggregator(unittest.TestCase):
    """데이터 수집기 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.data_aggregator import DataAggregator
        self.aggregator = DataAggregator()

    def test_daily_data_collection(self):
        """일일 데이터 수집 테스트"""
        date = datetime.now()
        data = self.aggregator.get_daily_data(date)

        self.assertIsNotNone(data)
        self.assertIsNotNone(data.summary)
        self.assertIsNotNone(data.keyword_data)
        self.assertIsNotNone(data.sentiment_data)

    def test_weekly_data_collection(self):
        """주간 데이터 수집 테스트"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        data = self.aggregator.get_weekly_data(start_date, end_date)

        self.assertIsNotNone(data)
        self.assertIsNotNone(data.trend_data)
        self.assertIsNotNone(data.growth_metrics)

    def test_monthly_data_collection(self):
        """월간 데이터 수집 테스트"""
        now = datetime.now()
        data = self.aggregator.get_monthly_data(now.year, now.month)

        self.assertIsNotNone(data)
        self.assertIsNotNone(data.custom_data)
        self.assertIn("yearly_comparison", data.custom_data)

    def test_sentiment_summary(self):
        """감성 분석 요약 테스트"""
        test_data = [
            {"text": "좋은 결과"},
            {"text": "나쁜 상황"},
            {"text": "평범한 일"}
        ]

        summary = self.aggregator.get_sentiment_summary(test_data)

        self.assertIn("total", summary)
        self.assertIn("positive", summary)
        self.assertIn("negative", summary)
        self.assertIn("neutral", summary)


class TestHTMLReportTemplate(unittest.TestCase):
    """HTML 템플릿 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.html_report_template import HTMLReportTemplate
        self.template_dir = tempfile.mkdtemp()
        self.template = HTMLReportTemplate(self.template_dir)

    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.template_dir)

    def test_template_initialization(self):
        """템플릿 초기화 테스트"""
        self.assertIsNotNone(self.template)
        self.assertEqual(self.template.template_dir, self.template_dir)

    def test_daily_summary_rendering(self):
        """일일 요약 렌더링 테스트"""
        test_data = {
            "summary": {
                "period": {
                    "start": "2025-01-01T00:00:00",
                    "end": "2025-01-02T00:00:00"
                },
                "total_items": 100
            },
            "keyword_data": [
                {
                    "keyword": "테스트",
                    "count": 50,
                    "growth_rate": 10.5,
                    "sentiment": "positive"
                }
            ],
            "sentiment_data": {
                "total_items": 100,
                "positive": 60,
                "negative": 20,
                "neutral": 20,
                "average_score": 0.4
            },
            "recent_items": [
                {
                    "title": "테스트 뉴스",
                    "summary": "테스트 내용",
                    "keywords": ["테스트"],
                    "sentiment": "positive"
                }
            ]
        }

        html_content = self.template.render_daily_summary(test_data)

        self.assertIsNotNone(html_content)
        self.assertIn("DOCTYPE html", html_content)
        self.assertIn("테스트", html_content)
        self.assertIn("일일 요약 리포트", html_content)

    def test_weekly_analysis_rendering(self):
        """주간 분석 렌더링 테스트"""
        test_data = {
            "summary": {
                "period": {
                    "start": "2025-01-01T00:00:00",
                    "end": "2025-01-08T00:00:00"
                }
            },
            "keyword_data": [],
            "sentiment_data": {},
            "growth_metrics": {
                "current_period": {"total_items": 500},
                "previous_period": {"total_items": 450},
                "growth_percentage": 11.11
            }
        }

        html_content = self.template.render_weekly_analysis(test_data)

        self.assertIsNotNone(html_content)
        self.assertIn("주간 분석 리포트", html_content)
        self.assertIn("성장률", html_content)

    def test_monthly_overview_rendering(self):
        """월간 개요 렌더링 테스트"""
        test_data = {
            "summary": {"period": {}},
            "keyword_data": [],
            "sentiment_data": {},
            "custom_data": {
                "yearly_comparison": {
                    "current_year": {"year": 2025, "month": 1, "total_items": 500, "avg_sentiment": 0.4},
                    "previous_year": {"year": 2024, "month": 1, "total_items": 420, "avg_sentiment": 0.35},
                    "yoy_growth": 19.05
                }
            }
        }

        html_content = self.template.render_monthly_overview(test_data)

        self.assertIsNotNone(html_content)
        self.assertIn("월간 개요 리포트", html_content)
        self.assertIn("연간 비교", html_content)


class TestPDFConverter(unittest.TestCase):
    """PDF 변환기 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.pdf_converter import PDFConverter
        self.temp_dir = tempfile.mkdtemp()
        self.converter = PDFConverter()
        self.converter._weasyprint_available = False  # 테스트용으로 비활성화

    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.temp_dir)

    def test_converter_initialization(self):
        """변환기 초기화 테스트"""
        self.assertIsNotNone(self.converter)
        self.assertIsNotNone(self.converter.config)

    def test_pdf_filename_generation(self):
        """PDF 파일명 생성 테스트"""
        from report_system.pdf_converter import get_pdf_filename

        date = datetime(2025, 1, 15)
        filename = get_pdf_filename("daily", date)

        self.assertEqual(filename, "report_daily_20250115.pdf")

    def test_pdf_path_validation(self):
        """PDF 경로 유효성 검사 테스트"""
        from report_system.pdf_converter import validate_pdf_path

        # 유효한 경로
        self.assertTrue(validate_pdf_path("test.pdf"))
        self.assertTrue(validate_pdf_path("/path/to/report.pdf"))

        # 유효하지 않은 경로
        self.assertFalse(validate_pdf_path("test.txt"))
        self.assertFalse(validate_pdf_path("report|test.pdf"))

    def test_html_to_pdf_without_weasyprint(self):
        """WeasyPrint 없는 경우 테스트"""
        html_content = "<html><body>테스트</body></html>"
        output_path = os.path.join(self.temp_dir, "test.pdf")

        # WeasyPrint가 없으므로 실패해야 함
        success = self.converter.convert_html_to_pdf(html_content, output_path)
        self.assertFalse(success)


class TestReportGenerator(unittest.TestCase):
    """리포트 생성기 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.report_generator import ReportGenerator
        self.temp_dir = tempfile.mkdtemp()

        # 임시 설정 생성
        from report_system.config import ReportConfig
        config = ReportConfig()
        config.general.output_dir = self.temp_dir

        self.generator = ReportGenerator(config)

    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.temp_dir)

    def test_generator_initialization(self):
        """생성기 초기화 테스트"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.template_manager)
        self.assertIsNotNone(self.generator.pdf_converter)
        self.assertIsNotNone(self.generator.data_aggregator)

    def test_html_only_generation(self):
        """HTML만 생성 테스트"""
        html_content = self.generator.generate_html_only('daily')

        self.assertIsNotNone(html_content)
        self.assertIn("DOCTYPE html", html_content)
        self.assertIn("일일 요약 리포트", html_content)

    @patch('report_system.pdf_converter.PDFConverter.convert_html_to_pdf')
    def test_daily_report_generation(self, mock_convert):
        """일일 리포트 생성 테스트"""
        mock_convert.return_value = True

        result = self.generator.generate_daily_report()

        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('report_type', result)

        if result['success']:
            self.assertEqual(result['report_type'], 'daily')
            self.assertIn('output_path', result)

    @patch('report_system.pdf_converter.PDFConverter.convert_html_to_pdf')
    def test_weekly_report_generation(self, mock_convert):
        """주간 리포트 생성 테스트"""
        mock_convert.return_value = True

        result = self.generator.generate_weekly_report()

        self.assertIsNotNone(result)
        if result['success']:
            self.assertEqual(result['report_type'], 'weekly')

    @patch('report_system.pdf_converter.PDFConverter.convert_html_to_pdf')
    def test_monthly_report_generation(self, mock_convert):
        """월간 리포트 생성 테스트"""
        mock_convert.return_value = True

        result = self.generator.generate_monthly_report(2025, 1)

        self.assertIsNotNone(result)
        if result['success']:
            self.assertEqual(result['report_type'], 'monthly')
            self.assertEqual(result['year'], 2025)
            self.assertEqual(result['month'], 1)

    def test_custom_report_generation(self):
        """사용자 정의 리포트 생성 테스트"""
        from report_system.config import ReportParams

        params = ReportParams(
            report_type='custom',
            date=datetime.now(),
            keywords=['테스트'],
            custom_data={'title': '테스트 리포트'}
        )

        result = self.generator.generate_custom_report(params)

        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('report_type', result)

    def test_get_week_range(self):
        """주간 범위 계산 테스트"""
        start_date, end_date = self.generator._get_week_range()

        self.assertIsNotNone(start_date)
        self.assertIsNotNone(end_date)
        self.assertLess(start_date, end_date)

        # 월요일이어야 함
        self.assertEqual(start_date.weekday(), 0)

        # 일요일이어야 함
        self.assertEqual(end_date.weekday(), 6)


class TestReportScheduler(unittest.TestCase):
    """리포트 스케줄러 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.report_scheduler import ReportScheduler
        from report_system.config import ReportConfig

        config = ReportConfig()
        # 테스트용으로 모든 리포트 타입 비활성화
        for report_type in config.report_types:
            config.report_types[report_type].enabled = False

        self.scheduler = ReportScheduler(config)

    def tearDown(self):
        """테스트 정리"""
        if self.scheduler.is_running:
            self.scheduler.shutdown()

    def test_scheduler_initialization(self):
        """스케줄러 초기화 테스트"""
        self.assertIsNotNone(self.scheduler)
        self.assertIsNotNone(self.scheduler.generator)
        self.assertFalse(self.scheduler.is_running)

    def test_daily_schedule(self):
        """일일 스케줄 테스트"""
        success = self.scheduler.schedule_daily_report("09:00")

        self.assertTrue(success)
        self.assertIn("daily_report_0900", self.scheduler.jobs)

    def test_weekly_schedule(self):
        """주간 스케줄 테스트"""
        success = self.scheduler.schedule_weekly_report("monday", "10:00")

        self.assertTrue(success)
        self.assertIn("weekly_report_monday_1000", self.scheduler.jobs)

    def test_monthly_schedule(self):
        """월간 스케줄 테스트"""
        success = self.scheduler.schedule_monthly_report(1, "09:00")

        self.assertTrue(success)
        self.assertIn("monthly_report_1_0900", self.scheduler.jobs)

    def test_job_status(self):
        """작업 상태 조회 테스트"""
        job_id = "test_job_0900"
        self.scheduler.schedule_daily_report("09:00", job_id)

        status = self.scheduler.get_job_status(job_id)

        self.assertIsNotNone(status)
        self.assertEqual(status['id'], job_id)
        self.assertEqual(status['type'], 'daily')

    def test_get_all_jobs(self):
        """모든 작업 조회 테스트"""
        self.scheduler.schedule_daily_report("09:00")
        self.scheduler.schedule_weekly_report("monday", "10:00")

        jobs = self.scheduler.get_all_jobs()

        self.assertEqual(len(jobs), 2)

    def test_pause_resume_job(self):
        """작업 일시중지/재개 테스트"""
        job_id = "test_job_0900"
        self.scheduler.schedule_daily_report("09:00", job_id)

        # 일시 중지
        pause_success = self.scheduler.pause_job(job_id)
        self.assertTrue(pause_success)

        status = self.scheduler.get_job_status(job_id)
        self.assertFalse(status['enabled'])

        # 재개
        resume_success = self.scheduler.resume_job(job_id)
        self.assertTrue(resume_success)

        status = self.scheduler.get_job_status(job_id)
        self.assertTrue(status['enabled'])


class TestReportNotifier(unittest.TestCase):
    """리포트 알림 테스트"""

    def setUp(self):
        """테스트 설정"""
        from report_system.report_notifier import ReportNotifier
        self.notifier = ReportNotifier()

    def test_notifier_initialization(self):
        """알림기 초기화 테스트"""
        self.assertIsNotNone(self.notifier)
        self.assertIsNotNone(self.notifier.config)

    def test_email_subject_creation(self):
        """이메일 제목 생성 테스트"""
        report_result = {
            'report_type': 'daily',
            'date': '2025-01-15T10:00:00',
            'success': True
        }

        subject = self.notifier._create_email_subject(report_result)

        self.assertIsNotNone(subject)
        self.assertIn('daily', subject.lower())
        self.assertIn('2025', subject)

    def test_email_body_creation(self):
        """이메일 본문 생성 테스트"""
        report_result = {
            'report_type': 'daily',
            'success': True,
            'output_path': '/path/to/report.pdf',
            'size_bytes': 1024000,
            'data_summary': {
                'total_items': 100,
                'sentiment_avg': 0.5
            }
        }

        body = self.notifier._create_email_body(report_result)

        self.assertIsNotNone(body)
        self.assertIn('완료', body)
        self.assertIn('100', body)


class TestIntegration(unittest.TestCase):
    """통합 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.temp_dir = tempfile.mkdtemp()

        # 임시 설정 생성
        from report_system.config import ReportConfig
        self.config = ReportConfig()
        self.config.general.output_dir = self.temp_dir

    def tearDown(self):
        """테스트 정리"""
        shutil.rmtree(self.temp_dir)

    def test_full_report_generation_workflow(self):
        """전체 리포트 생성 워크플로우 테스트"""
        from report_system.report_generator import ReportGenerator

        generator = ReportGenerator(self.config)

        # HTML 생성
        html_content = generator.generate_html_only('daily')
        self.assertIsNotNone(html_content)

        # 데이터 수집
        data = generator.data_aggregator.get_daily_data(datetime.now())
        self.assertIsNotNone(data)

    def test_scheduler_with_generator(self):
        """스케줄러와 생성기 통합 테스트"""
        from report_system.report_scheduler import ReportScheduler

        scheduler = ReportScheduler(self.config)

        # 스케줄 등록
        scheduler.schedule_daily_report("09:00")

        # 작업 확인
        jobs = scheduler.get_all_jobs()
        self.assertEqual(len(jobs), 1)

        # 정리
        if scheduler.is_running:
            scheduler.shutdown()


def run_tests():
    """테스트 실행"""
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 모든 테스트 클래스 추가
    suite.addTests(loader.loadTestsFromTestCase(TestReportConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestDataAggregator))
    suite.addTests(loader.loadTestsFromTestCase(TestHTMLReportTemplate))
    suite.addTests(loader.loadTestsFromTestCase(TestPDFConverter))
    suite.addTests(loader.loadTestsFromTestCase(TestReportGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestReportScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestReportNotifier))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 결과 요약
    print("\n" + "=" * 60)
    print(f"테스트 실행 완료")
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)