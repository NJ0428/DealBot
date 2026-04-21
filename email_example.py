#!/usr/bin/env python3
"""
이메일 알림 시스템 예시 스크립트
크롤링 완료 시 자동으로 이메일을 전송합니다.
"""

from web_crawler import WebCrawler, ExcelExporter
from email_notifier import EmailNotifier, EmailAuth, setup_email_config
from datetime import datetime, timedelta


def setup_email():
    """이메일 설정"""
    print("=" * 60)
    print("이메일 설정")
    print("=" * 60)
    return setup_email_config()


def example_1_basic_search_with_email():
    """예시 1: 기본 검색 후 이메일 전송"""
    print("\n" + "=" * 60)
    print("예시 1: 기본 검색 후 이메일 전송")
    print("=" * 60)

    # 크롤러 및 내보내기 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 이메일 알림 시스템 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth)

    keyword = "인공지능"
    print(f"\n🔍 '{keyword}' 검색 중...")

    try:
        # 데이터 수집
        data = crawler.search_google_news(keyword, max_results=5)

        if data:
            # Excel 저장
            excel_file = f"{keyword}_news.xlsx"
            exporter.save_to_excel(data, excel_file, "뉴스")

            # 수신자 이메일 (발신자와 동일하게 설정)
            recipient_email = auth.get_email()

            # 이메일 전송
            print(f"\n📧 이메일 전송 중...")
            success = notifier.send_crawling_report(
                to_email=recipient_email,
                keyword=keyword,
                data=data,
                excel_file=excel_file,
                search_type="Google News"
            )

            if success:
                print(f"✅ 이메일 전송 완료: {recipient_email}")
                print(f"   - 제목: [크롤링 완료] '{keyword}' 검색 결과")
                print(f"   - 첨부파일: {excel_file}")
            else:
                print("❌ 이메일 전송 실패")
        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        # 오류 리포트 전송
        notifier.send_error_report(
            to_email=auth.get_email(),
            error_message=str(e),
            keyword=keyword
        )

    crawler.close()


def example_2_multiple_keywords_with_email():
    """예시 2: 다중 키워드 검색 후 이메일 전송"""
    print("\n" + "=" * 60)
    print("예시 2: 다중 키워드 검색 후 이메일 전송")
    print("=" * 60)

    # 크롤러 및 내보내기 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 이메일 알림 시스템 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth)

    keywords = ["AI", "블록체인", "메타버스"]
    print(f"\n🔍 {len(keywords)}개 키워드 검색 중...")

    try:
        # 다중 키워드 검색
        results = crawler.search_multiple_keywords(
            keywords,
            max_results=5,
            use_async=False
        )

        # 데이터 정리
        all_data = {f"News_{k}": v for k, v in results.items()}

        # Excel 저장 (다중 시트)
        excel_file = "tech_trends_multiple.xlsx"
        exporter.save_multiple_sheets(all_data, excel_file)

        # 수신자 이메일
        recipient_email = auth.get_email()

        # 이메일 전송
        print(f"\n📧 이메일 전송 중...")
        success = notifier.send_multiple_keywords_report(
            to_email=recipient_email,
            results=results,
            excel_file=excel_file,
            search_type="Google News"
        )

        if success:
            print(f"✅ 이메일 전송 완료: {recipient_email}")
            print(f"   - 제목: [크롤링 완료] 다중 키워드 검색 결과")
            print(f"   - 검색 키워드: {', '.join(keywords)}")
            print(f"   - 첨부파일: {excel_file}")
        else:
            print("❌ 이메일 전송 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        # 오류 리포트 전송
        notifier.send_error_report(
            to_email=auth.get_email(),
            error_message=str(e),
            keyword=f"다중 키워드: {', '.join(keywords)}"
        )

    crawler.close()


def example_3_filtered_search_with_email():
    """예시 3: 필터링 검색 후 이메일 전송"""
    print("\n" + "=" * 60)
    print("예시 3: 필터링 검색 후 이메일 전송")
    print("=" * 60)

    from web_crawler import FilterCriteria

    # 크롤러 및 내보내기 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 이메일 알림 시스템 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth)

    keyword = "파이썬"

    # 필터링 기준 설정
    filter_criteria = FilterCriteria(
        start_date=datetime.now() - timedelta(days=7),  # 최근 7일
        keywords_in_title={"파이썬", "Python"},
        min_title_length=10
    )

    print(f"\n🔍 '{keyword}' 검색 중 (필터 적용)...")
    print(f"   - 기간: 최근 7일")
    print(f"   - 제목 키워드: 파이썬, Python")

    try:
        # 필터링 적용 검색
        data = crawler.search_google_news(
            keyword,
            max_results=15,
            filter_criteria=filter_criteria
        )

        if data:
            # Excel 저장
            excel_file = f"{keyword}_filtered.xlsx"
            exporter.save_to_excel(data, excel_file, "필터링_뉴스")

            # 수신자 이메일
            recipient_email = auth.get_email()

            # 이메일 전송
            print(f"\n📧 이메일 전송 중...")
            success = notifier.send_crawling_report(
                to_email=recipient_email,
                keyword=keyword,
                data=data,
                excel_file=excel_file,
                search_type="Google News (필터링 적용)"
            )

            if success:
                print(f"✅ 이메일 전송 완료: {recipient_email}")
                print(f"   - 필터링된 결과: {len(data)}개 항목")
                print(f"   - 첨부파일: {excel_file}")
            else:
                print("❌ 이메일 전송 실패")
        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        # 오류 리포트 전송
        notifier.send_error_report(
            to_email=auth.get_email(),
            error_message=str(e),
            keyword=keyword
        )

    crawler.close()


def example_4_custom_email():
    """예시 4: 사용자 정의 이메일 전송"""
    print("\n" + "=" * 60)
    print("예시 4: 사용자 정의 이메일 전송")
    print("=" * 60)

    # 이메일 알림 시스템 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth)

    # 수신자 이메일
    recipient_email = auth.get_email()

    # 사용자 정의 이메일 전송
    subject = "📧 테스트: 사용자 정의 이메일"
    body = """
    <html>
    <body>
        <h2>안녕하세요!</h2>
        <p>이것은 웹 크롤러의 사용자 정의 이메일입니다.</p>
        <p>이 기능을 사용하여 자신만의 이메일을 전송할 수 있습니다.</p>
        <hr>
        <p><strong>보낸 시간:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </body>
    </html>
    """

    print(f"\n📧 사용자 정의 이메일 전송 중...")
    success = notifier.send_email(
        to_email=recipient_email,
        subject=subject,
        body=body,
        is_html=True
    )

    if success:
        print(f"✅ 이메일 전송 완료: {recipient_email}")
        print(f"   - 제목: {subject}")
    else:
        print("❌ 이메일 전송 실패")


def example_5_email_with_attachments():
    """예시 5: 다중 첨부파일 이메일 전송"""
    print("\n" + "=" * 60)
    print("예시 5: 다중 첨부파일 이메일 전송")
    print("=" * 60)

    # 크롤러 및 내보내기 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 이메일 알림 시스템 초기화
    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 먼저 설정을 완료해주세요.")
        return

    notifier = EmailNotifier(auth)

    keyword = "데이터 분석"
    print(f"\n🔍 '{keyword}' 검색 중...")

    try:
        # 데이터 수집
        data = crawler.search_google_news(keyword, max_results=3)

        if data:
            # 여러 Excel 파일 생성
            excel_file_1 = f"{keyword}_part1.xlsx"
            excel_file_2 = f"{keyword}_part2.xlsx"

            # 데이터 분할 저장
            mid = len(data) // 2
            exporter.save_to_excel(data[:mid], excel_file_1, "데이터_분석_1")
            exporter.save_to_excel(data[mid:], excel_file_2, "데이터_분석_2")

            # 수신자 이메일
            recipient_email = auth.get_email()

            # 다중 첨부파일 이메일 전송
            print(f"\n📧 다중 첨부파일 이메일 전송 중...")
            success = notifier.send_email(
                to_email=recipient_email,
                subject=f"[크롤링 완료] '{keyword}' 검색 결과 (다중 첨부)",
                body=f"""
                <html>
                <body>
                    <h2>🔍 검색 완료</h2>
                    <p><strong>키워드:</strong> {keyword}</p>
                    <p><strong>수집 항목 수:</strong> {len(data)}개</p>
                    <p><strong>전송 시간:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    <hr>
                    <p>이 이메일은 {len(data)}개의 항목을 2개의 파일로 나누어 전송합니다.</p>
                </body>
                </html>
                """,
                attachments=[excel_file_1, excel_file_2],
                is_html=True
            )

            if success:
                print(f"✅ 이메일 전송 완료: {recipient_email}")
                print(f"   - 첨부파일 1: {excel_file_1}")
                print(f"   - 첨부파일 2: {excel_file_2}")
            else:
                print("❌ 이메일 전송 실패")
        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

    crawler.close()


def check_email_config():
    """이메일 설정 확인"""
    print("\n" + "=" * 60)
    print("이메일 설정 확인")
    print("=" * 60)

    auth = EmailAuth()

    if auth.is_configured():
        print(f"✅ 이메일이 설정되어 있습니다.")
        print(f"   - 발신자: {auth.get_email()}")
        print(f"   - 설정 파일: {auth.config_file}")
    else:
        print(f"❌ 이메일이 설정되지 않았습니다.")
        print(f"   - 설정 파일: {auth.config_file}")
        print("\n먼저 이메일 설정을 완료해주세요.")


def clear_email_config():
    """이메일 설정 삭제"""
    print("\n" + "=" * 60)
    print("이메일 설정 삭제")
    print("=" * 60)

    auth = EmailAuth()

    if auth.is_configured():
        confirm = input("\n정말로 이메일 설정을 삭제하시겠습니까? (y/n): ").strip().lower()
        if confirm == 'y':
            if auth.clear_config():
                print("✅ 이메일 설정이 삭제되었습니다.")
            else:
                print("❌ 설정 삭제 실패")
        else:
            print("취소되었습니다.")
    else:
        print("❌ 설정된 이메일이 없습니다.")


if __name__ == "__main__":
    import time

    print("\n📧 이메일 알림 시스템 예시")
    print("=" * 60)

    examples = [
        ("이메일 설정", setup_email),
        ("이메일 설정 확인", check_email_config),
        ("기본 검색 후 이메일 전송", example_1_basic_search_with_email),
        ("다중 키워드 검색 후 이메일 전송", example_2_multiple_keywords_with_email),
        ("필터링 검색 후 이메일 전송", example_3_filtered_search_with_email),
        ("사용자 정의 이메일 전송", example_4_custom_email),
        ("다중 첨부파일 이메일 전송", example_5_email_with_attachments),
        ("이메일 설정 삭제", clear_email_config),
    ]

    print("\n실행할 예시를 선택하세요:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")

    print("0. 종료")

    try:
        choice = input("\n선택 (0-{}): ".format(len(examples))).strip()

        if choice == "0":
            print("종료합니다.")
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                name, func = examples[idx]
                try:
                    func()
                except Exception as e:
                    print(f"❌ 오류 발생: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("잘못된 선택입니다.")

    except ValueError:
        print("잘못된 입력입니다.")
    except KeyboardInterrupt:
        print("\n\n사용자가 종료했습니다.")

    print("\n" + "=" * 60)
    print("✅ 예시 실행 완료!")
    print("=" * 60)
