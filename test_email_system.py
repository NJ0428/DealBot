#!/usr/bin/env python3
"""
이메일 알림 시스템 테스트 스크립트
"""

from email_notifier import EmailNotifier, EmailAuth, setup_email_config
from pathlib import Path


def test_email_config():
    """이메일 설정 테스트"""
    print("=" * 60)
    print("테스트 1: 이메일 설정 확인")
    print("=" * 60)

    auth = EmailAuth()

    if auth.is_configured():
        print("✅ 이메일이 설정되어 있습니다.")
        print(f"   발신자: {auth.get_email()}")
        print(f"   설정 파일: {auth.config_file}")
        return True
    else:
        print("❌ 이메일이 설정되지 않았습니다.")
        return False


def test_basic_email():
    """기본 이메일 전송 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 기본 이메일 전송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    notifier = EmailNotifier(auth)

    # 테스트 이메일 전송
    to_email = auth.get_email()
    subject = "📧 테스트: 기본 이메일 전송"
    body = """
    <html>
    <body>
        <h2>테스트 이메일</h2>
        <p>이것은 웹 크롤러 이메일 알림 시스템의 테스트 이메일입니다.</p>
        <p>이메일이 정상적으로 전송되는지 확인합니다.</p>
        <hr>
        <p><strong>전송 시간:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    </body>
    </html>
    """

    print(f"📧 테스트 이메일 전송 중... (수신자: {to_email})")

    success = notifier.send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        is_html=True
    )

    if success:
        print("✅ 기본 이메일 전송 성공!")
        return True
    else:
        print("❌ 기본 이메일 전송 실패!")
        return False


def test_email_with_attachment():
    """파일 첨부 이메일 전송 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 파일 첨부 이메일 전송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    # 테스트용 파일 생성
    test_file = "test_attachment.txt"
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("이것은 테스트 첨부파일입니다.\n")
        f.write(f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    notifier = EmailNotifier(auth)

    # 파일 첨부 이메일 전송
    to_email = auth.get_email()
    subject = "📎 테스트: 파일 첨부 이메일"
    body = """
    <html>
    <body>
        <h2>파일 첨부 테스트</h2>
        <p>이메일에 파일이 첨부되어 있는지 확인하세요.</p>
        <p>첨부파일: test_attachment.txt</p>
    </body>
    </html>
    """

    print(f"📧 파일 첨부 이메일 전송 중... (수신자: {to_email})")

    success = notifier.send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=[test_file],
        is_html=True
    )

    # 테스트 파일 삭제
    if Path(test_file).exists():
        Path(test_file).unlink()

    if success:
        print("✅ 파일 첨부 이메일 전송 성공!")
        return True
    else:
        print("❌ 파일 첨부 이메일 전송 실패!")
        return False


def test_crawling_report():
    """크롤링 리포트 이메일 전송 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 크롤링 리포트 전송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    # 테스트용 Excel 파일 생성
    from web_crawler import ExcelExporter

    # 가짜 데이터 생성
    test_data = [
        {
            "키워드": "테스트",
            "제목": "테스트 뉴스 제목",
            "요약": "테스트 뉴스 요약 내용",
            "출처/날짜": "테스트 언론사 · 1시간 전",
            "링크": "https://example.com",
            "수집일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]

    exporter = ExcelExporter()
    test_excel = "test_crawling_result.xlsx"
    exporter.save_to_excel(test_data, test_excel, "테스트_뉴스")

    notifier = EmailNotifier(auth)

    # 크롤링 리포트 전송
    to_email = auth.get_email()
    keyword = "테스트"

    print(f"📧 크롤링 리포트 전송 중... (수신자: {to_email})")

    success = notifier.send_crawling_report(
        to_email=to_email,
        keyword=keyword,
        data=test_data,
        excel_file=test_excel,
        search_type="Google News (테스트)"
    )

    # 테스트 파일 삭제
    if Path(test_excel).exists():
        Path(test_excel).unlink()

    if success:
        print("✅ 크롤링 리포트 전송 성공!")
        return True
    else:
        print("❌ 크롤링 리포트 전송 실패!")
        return False


def run_all_tests():
    """모든 테스트 실행"""
    print("\n📧 이메일 알림 시스템 테스트")
    print("=" * 60)
    print("이메일 알림 시스템의 각 기능을 테스트합니다.\n")

    results = []

    # 테스트 1: 설정 확인
    results.append(("이메일 설정 확인", test_email_config()))

    # 설정이 완료된 경우에만 나머지 테스트 실행
    if results[0][1]:
        # 테스트 2: 기본 이메일
        results.append(("기본 이메일 전송", test_basic_email()))

        # 테스트 3: 파일 첨부 이메일
        results.append(("파일 첨부 이메일 전송", test_email_with_attachment()))

        # 테스트 4: 크롤링 리포트
        results.append(("크롤링 리포트 전송", test_crawling_report()))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n총 테스트: {len(results)}개")
    print(f"성공: {passed}개")
    print(f"실패: {failed}개")

    if failed == 0:
        print("\n🎉 모든 테스트가 통과했습니다!")
    else:
        print(f"\n⚠️  {failed}개 테스트가 실패했습니다.")


if __name__ == "__main__":
    from datetime import datetime

    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
