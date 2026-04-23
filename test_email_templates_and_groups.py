#!/usr/bin/env python3
"""
이메일 템플릿 및 수신자 그룹 시스템 테스트 스크립트
"""

from email_notifier import EmailNotifier, EmailAuth
from email_template_manager import RecipientGroupManager, EmailTemplateManager
from pathlib import Path


def test_template_manager():
    """템플릿 관리자 테스트"""
    print("=" * 60)
    print("테스트 1: 템플릿 관리자")
    print("=" * 60)

    try:
        template_manager = EmailTemplateManager()
        print("✅ 템플릿 관리자 초기화 성공")

        # 크롤링 리포트 템플릿 렌더링 테스트
        print("\n📋 크롤링 리포트 템플릿 렌더링 테스트...")

        # 가짜 데이터 생성
        preview_data = [
            {"제목": "테스트 뉴스 1", "출처/날짜": "테스트 언론사 · 1시간 전"},
            {"제목": "테스트 뉴스 2", "출처/날짜": "테스트 언론사 · 2시간 전"},
        ]

        html = template_manager.render_crawling_report(
            keyword="테스트",
            search_type="Google News",
            item_count=10,
            attachment_files=["test_result.xlsx"],
            preview_data=preview_data
        )

        # 결과를 파일로 저장
        output_file = "test_crawling_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ 크롤링 리포트 렌더링 성공: {output_file}")

        # 다중 키워드 리포트 템플릿 렌더링 테스트
        print("\n📋 다중 키워드 리포트 템플릿 렌더링 테스트...")

        keywords_data = [
            {"keyword": "AI", "count": 15},
            {"keyword": "블록체인", "count": 8},
            {"keyword": "메타버스", "count": 12},
        ]

        html = template_manager.render_multiple_keywords_report(
            keywords_data=keywords_data,
            search_type="Google News",
            attachment_files=["multiple_keywords.xlsx"]
        )

        output_file = "test_multiple_keywords_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ 다중 키워드 리포트 렌더링 성공: {output_file}")

        # 오류 리포트 템플릿 렌더링 테스트
        print("\n📋 오류 리포트 템플릿 렌더링 테스트...")

        html = template_manager.render_error_report(
            error_message="연결 실패: 타임아웃 발생",
            keyword="테스트",
            error_type="네트워크 오류"
        )

        output_file = "test_error_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ 오류 리포트 렌더링 성공: {output_file}")

        return True

    except Exception as e:
        print(f"❌ 템플릿 관리자 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recipient_group_manager():
    """수신자 그룹 관리자 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 수신자 그룹 관리자")
    print("=" * 60)

    try:
        group_manager = RecipientGroupManager()
        print("✅ 수신자 그룹 관리자 초기화 성공")

        # 그룹 리스트 조회
        print("\n📋 그룹 리스트:")
        groups = group_manager.list_groups()
        for group in groups:
            info = group_manager.get_group_info(group)
            print(f"  - {group}: {info['name']} ({info['description']})")

        # 테스트 그룹 생성
        print("\n➕ 테스트 그룹 생성...")
        success = group_manager.create_group(
            group_name="testers",
            name="테스터",
            description="테스트용 그룹",
            recipients=["test1@example.com", "test2@example.com"]
        )

        if success:
            print("✅ 테스트 그룹 생성 성공")
        else:
            print("⚠️  테스트 그룹 이미 존재하거나 생성 실패")

        # 수신자 추가 테스트
        print("\n➕ 수신자 추가 테스트...")
        success = group_manager.add_recipient_to_group("testers", "test3@example.com")
        if success:
            print("✅ 수신자 추가 성공")
        else:
            print("⚠️  수신자 추가 실패 (이미 존재하거나 그룹 없음)")

        # 수신자 리스트 조회
        print("\n📋 테스트 그룹 수신자 리스트:")
        recipients = group_manager.get_group_recipients("testers")
        for recipient in recipients:
            print(f"  - {recipient}")

        # 그룹 삭제 테스트
        print("\n🗑️  테스트 그룹 삭제...")
        success = group_manager.delete_group("testers")
        if success:
            print("✅ 그룹 삭제 성공")
        else:
            print("❌ 그룹 삭제 실패")

        return True

    except Exception as e:
        print(f"❌ 수신자 그룹 관리자 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_notifier_with_templates():
    """이메일 알림 시스템 (템플릿 사용) 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 이메일 알림 시스템 (템플릿 사용)")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    try:
        notifier = EmailNotifier(auth, use_templates=True)
        print("✅ 이메일 알림 시스템 초기화 성공 (템플릿 사용)")

        # 템플릿 기반 크롤링 리포트 전송
        print("\n📧 템플릿 기반 크롤링 리포트 전송 테스트...")

        # 가짜 데이터 생성
        test_data = [
            {
                "키워드": "테스트",
                "제목": "테스트 뉴스 1",
                "요약": "테스트 요약 내용",
                "출처/날짜": "테스트 언론사 · 1시간 전",
                "링크": "https://example.com/1",
                "수집일시": "2026-04-22 10:00:00"
            },
            {
                "키워드": "테스트",
                "제목": "테스트 뉴스 2",
                "요약": "테스트 요약 내용 2",
                "출처/날짜": "테스트 언론사 · 2시간 전",
                "링크": "https://example.com/2",
                "수집일시": "2026-04-22 09:00:00"
            }
        ]

        # 가짜 Excel 파일 생성
        test_excel = "test_template_email.xlsx"
        from web_crawler import ExcelExporter
        exporter = ExcelExporter()
        exporter.save_to_excel(test_data, test_excel, "테스트")

        # 템플릿 기반 이메일 전송
        success = notifier.send_crawling_report_with_template(
            to_email=auth.get_email(),
            keyword="테스트",
            data=test_data,
            excel_file=test_excel,
            search_type="Google News",
            show_preview=True
        )

        # 테스트 파일 삭제
        if Path(test_excel).exists():
            Path(test_excel).unlink()

        if success:
            print("✅ 템플릿 기반 크롤링 리포트 전송 성공!")
        else:
            print("❌ 템플릿 기반 크롤링 리포트 전송 실패!")

        return success

    except Exception as e:
        print(f"❌ 이메일 알림 시스템 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bulk_email_sending():
    """대량 이메일 발송 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 대량 이메일 발송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    try:
        notifier = EmailNotifier(auth, use_templates=False)  # 빠른 테스트를 위해 템플릿 미사용
        print("✅ 이메일 알림 시스템 초기화 성공")

        # 테스트용 수신자 리스트 (본인만)
        recipients = [auth.get_email()]

        print(f"\n📧 대량 이메일 발송 테스트... ({len(recipients)}명)")

        results = notifier.send_bulk_email(
            recipients=recipients,
            subject="📧 테스트: 대량 이메일 발송",
            body="<h2>대량 발송 테스트</h2><p>이것은 대량 이메일 발송 기능의 테스트입니다.</p>",
            is_html=True,
            delay=0.5  # 짧은 지연
        )

        # 결과 출력
        print("\n📊 발송 결과:")
        for email, success in results.items():
            status = "✅ 성공" if success else "❌ 실패"
            print(f"  {status}: {email}")

        success_count = sum(1 for v in results.values() if v)
        print(f"\n총계: {success_count}/{len(results)} 성공")

        return all(results.values())

    except Exception as e:
        print(f"❌ 대량 이메일 발송 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_group_email_sending():
    """그룹 이메일 발송 테스트"""
    print("\n" + "=" * 60)
    print("테스트 5: 그룹 이메일 발송")
    print("=" * 60)

    auth = EmailAuth()

    if not auth.is_configured():
        print("❌ 이메일이 설정되지 않았습니다. 테스트를 건너뜁니다.")
        return False

    try:
        notifier = EmailNotifier(auth, use_templates=False)
        print("✅ 이메일 알림 시스템 초기화 성공")

        # 테스트용 그룹 생성
        test_group_name = "test_group"

        print(f"\n➕ 테스트 그룹 생성: {test_group_name}")
        notifier.create_recipient_group(
            group_name=test_group_name,
            name="테스트 그룹",
            description="일시적인 테스트용 그룹",
            recipients=[auth.get_email()]  # 본인만
        )

        # 그룹에 이메일 발송
        print(f"\n📧 그룹 '{test_group_name}'에 이메일 발송...")

        results = notifier.send_email_to_group(
            group_name=test_group_name,
            subject="📧 테스트: 그룹 이메일 발송",
            body="<h2>그룹 발송 테스트</h2><p>이것은 그룹 이메일 발송 기능의 테스트입니다.</p>",
            is_html=True,
            delay=0.5
        )

        # 결과 출력
        print("\n📊 발송 결과:")
        for email, success in results.items():
            status = "✅ 성공" if success else "❌ 실패"
            print(f"  {status}: {email}")

        # 테스트 그룹 삭제
        print(f"\n🗑️  테스트 그룹 삭제: {test_group_name}")
        notifier.recipient_manager.delete_group(test_group_name)

        return all(results.values())

    except Exception as e:
        print(f"❌ 그룹 이메일 발송 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """모든 테스트 실행"""
    print("\n🎨 이메일 템플릿 및 수신자 그룹 시스템 테스트")
    print("=" * 60)

    results = []

    # 테스트 1: 템플릿 관리자
    results.append(("템플릿 관리자", test_template_manager()))

    # 테스트 2: 수신자 그룹 관리자
    results.append(("수신자 그룹 관리자", test_recipient_group_manager()))

    # 테스트 3: 이메일 알림 시스템 (템플릿 사용) - 이메일 설정 필요
    results.append(("이메일 알림 시스템 (템플릿)", test_email_notifier_with_templates()))

    # 테스트 4: 대량 이메일 발송 - 이메일 설정 필요
    results.append(("대량 이메일 발송", test_bulk_email_sending()))

    # 테스트 5: 그룹 이메일 발송 - 이메일 설정 필요
    results.append(("그룹 이메일 발송", test_group_email_sending()))

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
        print("\n📋 생성된 HTML 파일을 브라우저에서 확인해보세요:")
        print("   - test_crawling_report.html")
        print("   - test_multiple_keywords_report.html")
        print("   - test_error_report.html")
    else:
        print(f"\n⚠️  {failed}개 테스트가 실패했습니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
