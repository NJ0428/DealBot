"""
자동 리포트 생성 및 PDF 출력 시스템 사용 예제

이 모듈은 리포트 시스템의 다양한 기능을 사용하는 방법을 보여줍니다.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_report_generation():
    """예제 1: 기본 리포트 생성"""
    print("\n=== 예제 1: 기본 리포트 생성 ===")

    try:
        from report_system import ReportGenerator

        # 리포트 생성기 초기화
        generator = ReportGenerator()

        # 일일 리포트 생성
        print("일일 리포트 생성 중...")
        daily_result = generator.generate_daily_report()

        if daily_result['success']:
            print(f"✅ 일일 리포트 생성 완료: {daily_result['output_path']}")
            print(f"   파일 크기: {daily_result['size_bytes'] / 1024:.2f} KB")
        else:
            print(f"❌ 일일 리포트 생성 실패: {daily_result['error']}")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_2_weekly_monthly_reports():
    """예제 2: 주간 및 월간 리포트 생성"""
    print("\n=== 예제 2: 주간 및 월간 리포트 생성 ===")

    try:
        from report_system import ReportGenerator

        generator = ReportGenerator()

        # 주간 리포트 생성
        print("주간 리포트 생성 중...")
        weekly_result = generator.generate_weekly_report()

        if weekly_result['success']:
            print(f"✅ 주간 리포트 생성 완료: {weekly_result['output_path']}")
            print(f"   기간: {weekly_result['start_date']} ~ {weekly_result['end_date']}")
        else:
            print(f"❌ 주간 리포트 생성 실패: {weekly_result['error']}")

        # 월간 리포트 생성
        print("월간 리포트 생성 중...")
        now = datetime.now()
        monthly_result = generator.generate_monthly_report(now.year, now.month)

        if monthly_result['success']:
            print(f"✅ 월간 리포트 생성 완료: {monthly_result['output_path']}")
            print(f"   대상: {monthly_result['year']}년 {monthly_result['month']}월")
        else:
            print(f"❌ 월간 리포트 생성 실패: {monthly_result['error']}")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_3_html_only_generation():
    """예제 3: HTML만 생성"""
    print("\n=== 예제 3: HTML만 생성 ===")

    try:
        from report_system import ReportGenerator

        generator = ReportGenerator()

        # 일일 리포트 HTML만 생성
        print("일일 리포트 HTML 생성 중...")
        html_content = generator.generate_html_only('daily')

        # HTML 파일로 저장
        output_file = "report_daily_example.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML 파일 생성 완료: {output_file}")
        print(f"   파일 크기: {len(html_content)} bytes")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_4_custom_report():
    """예제 4: 사용자 정의 리포트"""
    print("\n=== 예제 4: 사용자 정의 리포트 ===")

    try:
        from report_system import ReportGenerator, ReportParams

        generator = ReportGenerator()

        # 사용자 정의 파라미터
        params = ReportParams(
            report_type='custom',
            date=datetime.now(),
            keywords=['AI', '데이터', '기술'],
            include_sections=['summary', 'top_keywords', 'sentiment_overview'],
            custom_data={
                'template_name': 'custom',
                'title': '맞춤형 분석 리포트',
                'subtitle': '사용자 정의 키워드 분석'
            }
        )

        print("사용자 정의 리포트 생성 중...")
        custom_result = generator.generate_custom_report(params)

        if custom_result['success']:
            print(f"✅ 사용자 정의 리포트 생성 완료: {custom_result['output_path']}")
            print(f"   포함 섹션: {', '.join(params.include_sections)}")
        else:
            print(f"❌ 사용자 정의 리포트 생성 실패: {custom_result['error']}")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_5_pdf_operations():
    """예제 5: PDF 고급 기능"""
    print("\n=== 예제 5: PDF 고급 기능 ===")

    try:
        from report_system import PDFConverter

        converter = PDFConverter()

        # PDF 정보 가져오기
        test_pdf = "reports/daily/report_daily_20250528.pdf"  # 예제 파일 경로
        if os.path.exists(test_pdf):
            print(f"PDF 정보 조회 중: {test_pdf}")
            info = converter.get_pdf_info(test_pdf)

            print(f"✅ PDF 정보:")
            print(f"   파일 크기: {info.get('size_mb', 0):.2f} MB")
            print(f"   페이지 수: {info.get('pages', 0)}")
            print(f"   생성일: {info.get('created_at', 'N/A')}")

            # 워터마크 추가 (선택적)
            # print("워터마크 추가 중...")
            # success = converter.add_watermark(test_pdf, "DEALBOT - CONFIDENTIAL")
            # if success:
            #     print(f"✅ 워터마크 추가 완료")

        else:
            print(f"⚠️  테스트 PDF 파일이 없습니다: {test_pdf}")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_6_scheduling():
    """예제 6: 리포트 스케줄링"""
    print("\n=== 예제 6: 리포트 스케줄링 ===")

    try:
        from report_system import ReportScheduler

        # 스케줄러 초기화
        scheduler = ReportScheduler()

        # 기본 스케줄 설정
        print("기본 스케줄 설정 중...")
        scheduler.setup_default_schedules()

        # 현재 등록된 작업 확인
        jobs = scheduler.get_all_jobs()
        print(f"✅ 등록된 작업 수: {len(jobs)}")

        for job in jobs:
            print(f"   - {job['name']}")
            print(f"     다음 실행: {job['next_run_time']}")

        # 스케줄러 시작 (실제 실행은 주석 처리)
        print("\n스케줄러 시작 준비 완료")
        print("실제 시작하려면 scheduler.start()를 호출하세요")
        # scheduler.start()

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_7_configuration():
    """예제 7: 설정 파일 사용"""
    print("\n=== 예제 7: 설정 파일 사용 ===")

    try:
        from report_system.config import ReportConfig, create_default_config

        # 기본 설정 생성
        config_file = "example_report_config.json"
        print(f"기본 설정 파일 생성 중: {config_file}")
        config = create_default_config(config_file)

        print("✅ 설정 파일 생성 완료")
        print(f"   출력 디렉토리: {config.general.output_dir}")
        print(f"   타임존: {config.general.timezone}")

        # 설정 수정
        config.general.output_dir = "custom_reports"
        config.report_types['daily'].schedule = "10:00"

        # 수정된 설정 저장
        config.to_json(config_file)
        print(f"✅ 수정된 설정 저장 완료")

        # 설정에서 리포트 생성기 생성
        from report_system import create_report_generator
        generator = create_report_generator(config_file)

        print("✅ 설정 파일을 통한 리포트 생성기 초기화 완료")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_8_report_history():
    """예제 8: 리포트 이력 관리"""
    print("\n=== 예제 8: 리포트 이력 관리 ===")

    try:
        from report_system import ReportGenerator

        generator = ReportGenerator()

        # 리포트 이력 조회
        print("리포트 이력 조회 중...")
        history = generator.get_report_history(limit=5)

        print(f"✅ 최근 리포트 {len(history)}개:")
        for report in history:
            print(f"   - {report['report_type']}: {report.get('date', 'N/A')}")
            print(f"     파일: {os.path.basename(report.get('output_path', 'N/A'))}")

        # 오래된 리포트 정리 (테스트용으로 주석 처리)
        # print("\n오래된 리포트 정리 중...")
        # cleanup_result = generator.cleanup_old_reports()
        # print(f"✅ 정리 완료: {len(cleanup_result['deleted'])}개 파일 삭제")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_9_email_notification():
    """예제 9: 이메일 알림"""
    print("\n=== 예제 9: 이메일 알림 ===")

    try:
        from report_system import ReportGenerator, create_report_notifier

        # 리포트 생성
        generator = ReportGenerator()
        report_result = generator.generate_daily_report()

        # 알림기 초기화
        notifier = create_report_notifier()

        # 이메일 전송 (실제 전송은 주석 처리)
        print("이메일 알림 준비 완료")
        print("실제 전송하려면 이메일 계정 정보를 설정하세요")

        if report_result['success']:
            print(f"리포트 생성 완료: {report_result['output_path']}")

            # 테스트 이메일 전송 (설정된 경우)
            # success = notifier.send_test_email()
            # if success:
            #     print("✅ 테스트 이메일 전송 완료")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def example_10_batch_processing():
    """예제 10: 일괄 처리"""
    print("\n=== 예제 10: 일괄 처리 ===")

    try:
        from report_system import ReportGenerator
        from datetime import timedelta

        generator = ReportGenerator()

        # 여러 날짜의 일일 리포트 생성
        print("최근 3일간의 일일 리포트 생성 중...")

        results = []
        for i in range(3):
            date = datetime.now() - timedelta(days=i)
            result = generator.generate_daily_report(date)
            results.append(result)

            if result['success']:
                print(f"✅ {date.date()} 리포트 생성 완료")
            else:
                print(f"❌ {date.date()} 리포트 생성 실패")

        # 성공한 리포트 수 확인
        success_count = sum(1 for r in results if r.get('success', False))
        print(f"\n총 {len(results)}개 중 {success_count}개 리포트 생성 완료")

    except Exception as e:
        print(f"❌ 예제 실행 실패: {e}")
        import traceback
        traceback.print_exc()


def main():
    """메인 함수"""
    print("=" * 60)
    print("DealBot 자동 리포트 생성 및 PDF 출력 시스템 예제")
    print("=" * 60)

    # 예제 실행
    examples = [
        example_1_basic_report_generation,
        example_2_weekly_monthly_reports,
        example_3_html_only_generation,
        example_4_custom_report,
        example_5_pdf_operations,
        example_6_scheduling,
        example_7_configuration,
        example_8_report_history,
        example_9_email_notification,
        example_10_batch_processing
    ]

    # 모든 예제 실행
    for example in examples:
        try:
            example()
        except KeyboardInterrupt:
            print("\n\n사용자 중단")
            break
        except Exception as e:
            logger.error(f"예제 실행 중 오류 발생: {e}")
            continue

    print("\n" + "=" * 60)
    print("모든 예제 실행 완료")
    print("=" * 60)


if __name__ == "__main__":
    # 개별 예제 실행 (원하는 예제의 주석을 해제하세요)
    # example_1_basic_report_generation()
    # example_2_weekly_monthly_reports()
    # example_3_html_only_generation()
    # example_4_custom_report()
    # example_5_pdf_operations()
    # example_6_scheduling()
    # example_7_configuration()
    # example_8_report_history()
    # example_9_email_notification()
    # example_10_batch_processing()

    # 전체 예제 실행
    main()