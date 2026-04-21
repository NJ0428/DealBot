#!/usr/bin/env python3
"""
이메일 알림 시스템과 웹 크롤러 통합 예시
크롤링 완료 후 자동으로 이메일을 전송하는 간단한 예제입니다.
"""

from web_crawler import WebCrawler, ExcelExporter, FilterCriteria
from email_notifier import EmailNotifier, EmailAuth, setup_email_config
from datetime import datetime, timedelta


def check_email_setup():
    """이메일 설정 확인"""
    auth = EmailAuth()

    if not auth.is_configured():
        print("\n❌ 이메일이 설정되지 않았습니다.")
        print("이메일 알림을 사용하려면 먼저 설정을 완료해주세요.\n")

        setup = input("지금 설정하시겠습니까? (y/n): ").strip().lower()
        if setup == 'y':
            auth = setup_email_config()
            if not auth or not auth.is_configured():
                print("\n⚠️  이메일 설정이 완료되지 않았습니다.")
                print("이메일 없이 크롤링을 계속합니다.\n")
                return None
        else:
            print("\n⚠️  이메일 없이 크롤링을 계속합니다.\n")
            return None

    return auth


def simple_crawling_with_email():
    """간단한 크롤링 후 이메일 전송"""
    print("=" * 60)
    print("🕷️ 간단한 크롤링 및 이메일 전송")
    print("=" * 60)

    # 이메일 설정 확인
    auth = check_email_setup()

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 키워드 입력
    keyword = input("\n검색할 키워드: ").strip()

    if not keyword:
        print("❌ 키워드를 입력해주세요.")
        return

    # 최대 결과 수 입력
    max_results_input = input("최대 결과 수 (기본값: 10): ").strip()
    max_results = int(max_results_input) if max_results_input.isdigit() else 10

    print(f"\n🔍 '{keyword}' 검색 중...")

    try:
        # 데이터 수집
        data = crawler.search_google_news(keyword, max_results=max_results)

        if data:
            # Excel 저장
            excel_file = f"{keyword}_result.xlsx"
            exporter.save_to_excel(data, excel_file, "뉴스")

            print(f"✅ 데이터 수집 완료: {len(data)}개 항목")
            print(f"✅ Excel 저장 완료: {excel_file}")

            # 이메일 전송
            if auth and auth.is_configured():
                print(f"\n📧 이메일 전송 중...")

                notifier = EmailNotifier(auth)
                success = notifier.send_crawling_report(
                    to_email=auth.get_email(),
                    keyword=keyword,
                    data=data,
                    excel_file=excel_file,
                    search_type="Google News"
                )

                if success:
                    print(f"✅ 이메일 전송 완료!")
                    print(f"   수신자: {auth.get_email()}")
                else:
                    print(f"❌ 이메일 전송 실패")
            else:
                print("\n⚠️  이메일 알림이 설정되지 않았습니다.")

        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

        # 오류 리포트 전송
        if auth and auth.is_configured():
            notifier = EmailNotifier(auth)
            notifier.send_error_report(
                to_email=auth.get_email(),
                error_message=str(e),
                keyword=keyword
            )

    crawler.close()


def multiple_keywords_with_email():
    """다중 키워드 크롤링 후 이메일 전송"""
    print("=" * 60)
    print("🔍 다중 키워드 크롤링 및 이메일 전송")
    print("=" * 60)

    # 이메일 설정 확인
    auth = check_email_setup()

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 키워드 입력
    keywords_input = input("\n검색할 키워드들 (쉼표로 구분): ").strip()
    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]

    if not keywords:
        print("❌ 키워드를 입력해주세요.")
        return

    print(f"\n🔍 {len(keywords)}개 키워드 검색 중: {', '.join(keywords)}")

    try:
        # 다중 키워드 검색
        results = crawler.search_multiple_keywords(keywords, max_results=5, use_async=False)

        # 데이터 정리
        all_data = {f"News_{k}": v for k, v in results.items()}

        # Excel 저장
        excel_file = "multiple_keywords_result.xlsx"
        exporter.save_multiple_sheets(all_data, excel_file)

        total_items = sum(len(data) for data in results.values())
        print(f"✅ 데이터 수집 완료: 총 {total_items}개 항목")
        print(f"✅ Excel 저장 완료: {excel_file}")

        # 키워드별 결과
        for keyword, data in results.items():
            print(f"   - {keyword}: {len(data)}개 항목")

        # 이메일 전송
        if auth and auth.is_configured():
            print(f"\n📧 이메일 전송 중...")

            notifier = EmailNotifier(auth)
            success = notifier.send_multiple_keywords_report(
                to_email=auth.get_email(),
                results=results,
                excel_file=excel_file,
                search_type="Google News"
            )

            if success:
                print(f"✅ 이메일 전송 완료!")
                print(f"   수신자: {auth.get_email()}")
            else:
                print(f"❌ 이메일 전송 실패")
        else:
            print("\n⚠️  이메일 알림이 설정되지 않았습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

        # 오류 리포트 전송
        if auth and auth.is_configured():
            notifier = EmailNotifier(auth)
            notifier.send_error_report(
                to_email=auth.get_email(),
                error_message=str(e),
                keyword=f"다중 키워드: {', '.join(keywords)}"
            )

    crawler.close()


def filtered_search_with_email():
    """필터링 검색 후 이메일 전송"""
    print("=" * 60)
    print("🔍 필터링 검색 및 이메일 전송")
    print("=" * 60)

    # 이메일 설정 확인
    auth = check_email_setup()

    # 크롤러 초기화
    crawler = WebCrawler(use_cache=True)
    exporter = ExcelExporter()

    # 키워드 입력
    keyword = input("\n검색할 키워드: ").strip()

    if not keyword:
        print("❌ 키워드를 입력해주세요.")
        return

    # 최근 며칠 동안의 데이터만 검색할지
    days_input = input("최근 며칠 동안의 데이터를 검색하시겠습니까? (기본값: 7일): ").strip()
    days = int(days_input) if days_input.isdigit() else 7

    # 필터링 기준 설정
    filter_criteria = FilterCriteria(
        start_date=datetime.now() - timedelta(days=days),
        min_title_length=10
    )

    print(f"\n🔍 '{keyword}' 검색 중 (최근 {days}일 데이터만)...")

    try:
        # 필터링 검색
        data = crawler.search_google_news(
            keyword,
            max_results=20,
            filter_criteria=filter_criteria
        )

        if data:
            # Excel 저장
            excel_file = f"{keyword}_filtered.xlsx"
            exporter.save_to_excel(data, excel_file, "필터링_뉴스")

            print(f"✅ 데이터 수집 완료: {len(data)}개 항목")
            print(f"✅ Excel 저장 완료: {excel_file}")

            # 이메일 전송
            if auth and auth.is_configured():
                print(f"\n📧 이메일 전송 중...")

                notifier = EmailNotifier(auth)
                success = notifier.send_crawling_report(
                    to_email=auth.get_email(),
                    keyword=keyword,
                    data=data,
                    excel_file=excel_file,
                    search_type=f"Google News (최근 {days}일 필터링)"
                )

                if success:
                    print(f"✅ 이메일 전송 완료!")
                    print(f"   수신자: {auth.get_email()}")
                else:
                    print(f"❌ 이메일 전송 실패")
            else:
                print("\n⚠️  이메일 알림이 설정되지 않았습니다.")

        else:
            print("❌ 데이터 수집 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

        # 오류 리포트 전송
        if auth and auth.is_configured():
            notifier = EmailNotifier(auth)
            notifier.send_error_report(
                to_email=auth.get_email(),
                error_message=str(e),
                keyword=keyword
            )

    crawler.close()


if __name__ == "__main__":
    import time

    print("\n📧 이메일 알림 시스템 통합 예제")
    print("=" * 60)

    examples = [
        ("간단한 크롤링 후 이메일 전송", simple_crawling_with_email),
        ("다중 키워드 크롤링 후 이메일 전송", multiple_keywords_with_email),
        ("필터링 검색 후 이메일 전송", filtered_search_with_email),
    ]

    print("\n실행할 예제를 선택하세요:")
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
    print("✅ 예제 실행 완료!")
    print("=" * 60)
